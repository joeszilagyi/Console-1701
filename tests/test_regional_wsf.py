from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.regional_wsf import API_URL, BULLETIN_PAGE
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/regional_wsf_alerts_synthetic.json"


def _source() -> dict:
    return {
        "id": "wsf_bulletins", "scope": "REGIONAL", "kind": "api_json",
        "parser": "wsf_alerts_fixture", "url": FIXTURE.as_uri(),
        "official_url": API_URL,
    }


def test_wsf_documented_fixture_keeps_bulletin_identity_and_impact():
    items = parse_fixture_items(_source(), FIXTURE.read_text(encoding="utf-8"))
    assert len(items) == 2
    cancellation = items[0]["evidence"]["wsf_alert"]
    assert items[0]["url"] == BULLETIN_PAGE
    assert items[0]["canonical_url"].endswith("fixture_bulletin_id=260101")
    assert cancellation["bulletin_id"] == 260101
    assert cancellation["affected_route_ids"] == [7]
    assert cancellation["published_at"] == "2026-10-15T21:30:00+00:00"
    assert cancellation["status"] == "cancellation"
    assert cancellation["ranking"]["public_impact_score"] == 25
    assert cancellation["terminal"] is None and cancellation["vessel"] is None
    assert cancellation["start_at"] is None and cancellation["end_at"] is None
    assert items[1]["evidence"]["wsf_alert"]["status"] == "delay"
    assert items[1]["evidence"]["wsf_alert"]["ranking"]["public_impact_score"] == 15


def test_wsf_fixture_rejects_wrong_shape_and_direct_http():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload[1]["BulletinID"] = payload[0]["BulletinID"]
    with pytest.raises(NewsParserError, match="repeated BulletinID"):
        parse_fixture_items(_source(), json.dumps(payload))
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items({**_source(), "url": API_URL}, FIXTURE.read_text())
    payload[1]["BulletinID"] = 260102
    payload[0]["AffectedRouteIDs"] = ["7"]
    with pytest.raises(NewsParserError, match="invalid routes"):
        parse_fixture_items(_source(), json.dumps(payload))


def test_wsf_no_cancellations_notice_has_no_public_impact_boost():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload[0]["AlertFullTitle"] = "No cancellations expected on Route 7"
    payload[0]["DisruptionDescription"] = "No delays expected today."
    payload[0]["BulletinText"] = "Sailings on schedule."
    notice = parse_fixture_items(_source(), json.dumps(payload))[0]["evidence"]["wsf_alert"]
    assert notice["status"] == "notice"
    assert notice["ranking"]["public_impact_score"] == 0


def test_wsf_offline_scan_and_live_block(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("WSF fixture/live-block tests must not fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    fixture_config = tmp_path / "fixture.yml"
    fixture_config.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - id: wsf_bulletins
                  enabled: true
                  url: "{FIXTURE.as_uri()}"
                  official_url: "{API_URL}"
    """).strip() + "\n", encoding="utf-8")
    result = run_news_scan(fixture_config)
    assert result["status"] == "complete" and result["item_count"] == 2
    config = load_config(fixture_config)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='REGIONAL'"
        ).fetchall()
    evidence = [json_loads(str(row["evidence_json"]), {}) for row in rows]
    assert {row["regional_event"]["event_type"] for row in evidence} == {"ferry_alert"}
    impact = {
        row["ranking"]["factors"]["regional_public_impact_bonus"]
        for row in evidence
    }
    assert impact == {15, 25}

    live_config = tmp_path / "live.yml"
    live_config.write_text(dedent("""
        paths: {repo_roots: [], explicit_repos: []}
        news:
          enabled: true
          fetch_policy: {allow_official_http: true}
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - {id: wsf_bulletins, enabled: true}
    """).strip() + "\n", encoding="utf-8")
    assert run_news_scan(live_config)["status"] == "partial"
    config = load_config(live_config)
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute(
            "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert run["status"] == "policy_blocked"
