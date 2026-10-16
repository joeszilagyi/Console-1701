from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.facets import regional_item_facets
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.regional_contract import build_regional_event_contract
from console1701.news.regional_nifc import QUERY_URL
from console1701.news.regional_registry import regional_registry_config_defaults
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/regional_nifc_imsr_wa.json"


def _source() -> dict:
    source = regional_registry_config_defaults("nifc_imsr_current_wa")
    source["official_url"] = source["url"]
    source["url"] = FIXTURE.as_uri()
    return source


def test_nifc_imsr_fixture_preserves_current_report_without_active_claim():
    source = _source()
    assert source["official_url"] == QUERY_URL
    items = parse_fixture_items(source, FIXTURE.read_text())
    assert len(items) == 2
    by_name = {item["evidence"]["nifc_imsr"]["fire_name"]: item for item in items}
    sisi = by_name["Sisi"]
    large = by_name["Little Giant"]
    assert sisi["source_published_at"] == "2026-10-15T00:00:00+00:00"
    assert sisi["evidence"]["nifc_imsr"]["unique_fire_identifier"] == (
        "2026-WAOWF-260664"
    )
    assert sisi["evidence"]["nifc_imsr"]["active_fire_claimed"] is False
    assert sisi["evidence"]["nifc_imsr"]["evacuation_claimed"] is False
    assert sisi["evidence"]["nifc_imsr"]["ranking"]["official_current_report_context"] == 6
    assert large["evidence"]["nifc_imsr"]["ranking"]["official_current_report_context"] == 12
    assert "incident_id=WA-OWF-260664" in sisi["canonical_url"]
    event = build_regional_event_contract(source, sisi, hashed_url="a" * 64)
    assert event["event_type"] == "wildfire_update"
    assert event["confidence"] == "high"
    assert event["matching_basis"] == "official_nifc_unique_fire_identifier"
    assert event["geography"]["matched"] is True
    assert event["public_impact_basis"].endswith("public impact unverified")
    assert ("fire_incident", "sisi") in regional_item_facets({
        "regional_event": event,
    })


def test_nifc_imsr_containment_and_report_revision():
    source = _source()
    first = parse_fixture_items(source, FIXTURE.read_text())[0]
    revised = json.loads(FIXTURE.read_text())
    revised["features"][0]["attributes"]["post_date_isoformat"] = 20261016
    revised["features"][0]["attributes"]["x100pct"] = "c"
    update = parse_fixture_items(source, json.dumps(revised))[0]
    original = build_regional_event_contract(source, first, hashed_url="a" * 64)
    later = build_regional_event_contract(source, update, hashed_url="b" * 64)
    assert original["event_key"] == later["event_key"]
    assert update["evidence"]["nifc_imsr"]["ranking"]["official_current_report_context"] == 0
    assert update["evidence"]["nifc_imsr"]["reported_100_percent_contained"] is True


@pytest.mark.parametrize("change", [
    lambda payload: payload.update(exceededTransferLimit=True),
    lambda payload: payload["features"][0]["attributes"].update(incident_id="OR-OWF-260664"),
    lambda payload: payload["features"][0]["attributes"].update(IsLatest=""),
    lambda payload: payload["features"][0]["attributes"].update(latitude=35.0),
    lambda payload: payload["features"][0]["attributes"].update(
        UniqueFireIdentifier="2026-WAOWF-999999"
    ),
])
def test_nifc_imsr_rejects_incomplete_or_wrong_identity(change):
    payload = json.loads(FIXTURE.read_text())
    change(payload)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(payload))


def test_nifc_imsr_offline_scan_and_live_gate(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    config_path = tmp_path / "regional.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - id: nifc_imsr_current_wa
                  enabled: true
                  url: "{FIXTURE.as_uri()}"
                  official_url: "{QUERY_URL}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT title, evidence_json FROM news_items WHERE scope='REGIONAL'"
        ).fetchall()
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='REGIONAL'"
        ).fetchall()
    assert len(rows) == len(clusters) == 2
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert {row["regional_event"]["event_type"] for row in evidence} == {
        "wildfire_update"
    }
    assert sorted(
        row["ranking"]["factors"]["regional_wildfire_report_bonus"]
        for row in evidence
    ) == [6, 12]
    assert all(row["ranking"]["factors"]["regional_public_impact_bonus"] == 0
               for row in evidence)
    assert all(json_loads(row["evidence_json"], {})["corroborated"] is False
               for row in clusters)

    live_source = regional_registry_config_defaults("nifc_imsr_current_wa")
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items(live_source, FIXTURE.read_text())
    wrong_source = deepcopy(_source())
    wrong_source["official_url"] = "https://example.test/other"
    with pytest.raises(NewsParserError, match="exact official query"):
        parse_fixture_items(wrong_source, FIXTURE.read_text())

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
                - {id: nifc_imsr_current_wa, enabled: true}
    """).strip() + "\n")
    assert run_news_scan(live_config)["status"] == "partial"
    live = load_config(live_config)
    with connect_db(live["_db_path"]) as conn:
        run = conn.execute(
            "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert run["status"] == "policy_blocked"
