from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.regional_pierce import FEED_URL
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/regional_pierce_road_alerts.rss"


def _source() -> dict:
    return {
        "id": "pierce_road_alert_rss", "scope": "REGIONAL", "kind": "rss",
        "parser": "pierce_road_rss_fixture", "url": FIXTURE.as_uri(),
        "official_url": FEED_URL,
    }


def test_pierce_road_rss_keeps_latest_revision_and_ranks_routine_notice_low():
    items = parse_fixture_items(_source(), FIXTURE.read_text(encoding="utf-8"))
    assert len(items) == 2
    by_id = {item["evidence"]["pierce_road_alert"]["alert_id"]: item for item in items}
    assert by_id["2889"]["source_published_at"] == "2026-09-26T00:52:15+00:00"
    assert by_id["2889"]["evidence"]["pierce_road_alert"]["classification"] == "weather_advisory"
    assert by_id["2892"]["evidence"]["pierce_road_alert"]["ranking"]["public_impact_score"] == 0
    assert all(item["description"] is None for item in items)


def test_pierce_road_rss_rejects_live_source_and_identity_mismatch():
    fixture = FIXTURE.read_text(encoding="utf-8")
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items({**_source(), "url": FEED_URL}, fixture)
    with pytest.raises(NewsParserError, match="official identity"):
        parse_fixture_items(_source(), fixture.replace("?AID=2892/", "?AID=9999/", 1))


def test_pierce_road_rss_offline_scan_and_live_block(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("Pierce fixture/live-block tests must not fetch HTTP")

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
                - id: pierce_road_alert_rss
                  enabled: true
                  url: "{FIXTURE.as_uri()}"
                  official_url: "{FEED_URL}"
    """).strip() + "\n", encoding="utf-8")
    result = run_news_scan(fixture_config)
    assert result["status"] == "complete" and result["item_count"] == 2
    config = load_config(fixture_config)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='REGIONAL'"
        ).fetchall()
    evidence = [json_loads(str(row["evidence_json"]), {}) for row in rows]
    assert all(row["pierce_road_alert"]["body_stored"] is False for row in evidence)
    by_id = {row["pierce_road_alert"]["alert_id"]: row for row in evidence}
    assert by_id["2892"]["ranking"]["factors"]["regional_public_impact_bonus"] == 0
    assert by_id["2889"]["ranking"]["factors"]["regional_public_impact_bonus"] == 5

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
                - {id: pierce_road_alert_rss, enabled: true}
    """).strip() + "\n", encoding="utf-8")
    assert run_news_scan(live_config)["status"] == "partial"
