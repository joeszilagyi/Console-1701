from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.ranking import build_rank_result
from console1701.news.regional_water import OBSERVATIONS_URL
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/regional_usgs_water_latest.json"


def _source() -> dict:
    return {
        "id": "usgs_water_api",
        "scope": "REGIONAL",
        "kind": "api_json",
        "parser": "usgs_water_latest_fixture",
        "url": FIXTURE.as_uri(),
        "official_url": OBSERVATIONS_URL,
    }


def test_usgs_water_fixture_preserves_observation_and_no_flood_claim():
    fixture = FIXTURE.read_text(encoding="utf-8")
    items = parse_fixture_items(_source(), fixture)
    assert len(items) == 1
    item = items[0]
    water = item["evidence"]["usgs_water"]
    assert water["gauge_id"] == "USGS-12119000"
    assert water["huc8"] == "17110012"
    assert water["county"] == "King County"
    assert water["streamflow"]["value"] == 315.0
    assert water["streamflow"]["unit"] == "ft^3/s"
    assert water["stage"]["value"] == 8.56
    assert water["stage"]["approval_status"] == "Provisional"
    assert water["stage"]["age_minutes_at_snapshot"] == 39.9
    assert water["stale_at_snapshot"] is False
    assert water["stage_category"] is None
    assert water["flood_status"] == "unknown_no_threshold"
    assert water["ranking"]["flood_severity_score"] == 0
    assert item["evidence"]["regional_identity"]["river_basin"] == "17110012"


def test_usgs_water_rejects_wrong_station_and_source():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["observations"]["features"][0]["properties"]["monitoring_location_id"] = "USGS-OTHER"
    with pytest.raises(NewsParserError, match="different gauge"):
        parse_fixture_items(_source(), json.dumps(payload))
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items({**_source(), "url": OBSERVATIONS_URL}, FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="allowlist"):
        parse_fixture_items({**_source(), "huc8_allowlist": ["17110013"]}, FIXTURE.read_text())


def test_usgs_water_stale_reading_has_no_flood_boost_and_is_penalized():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["observations"]["timeStamp"] = "2026-10-16T03:00:00Z"
    item = parse_fixture_items(_source(), json.dumps(payload))[0]
    assert item["evidence"]["usgs_water"]["stale_at_snapshot"] is True
    rank = build_rank_result(
        _source(),
        item,
        seen_at="2026-10-16T03:00:00+00:00",
        combined_tags=item["tags"],
        latest_health_state="healthy",
        repeat_count=0,
    )
    assert rank["factors"]["regional_hydrology_stale_penalty"] == -25
    assert rank["factors"]["regional_public_impact_bonus"] == 0


def test_usgs_water_offline_scan_stores_only_bounded_evidence(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("fixture scan must not fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - id: usgs_water_api
                  enabled: true
                  url: "{FIXTURE.as_uri()}"
                  official_url: "{OBSERVATIONS_URL}"
    """).strip()
        + "\n",
        encoding="utf-8",
    )
    result = run_news_scan(config_path)
    assert result["status"] == "complete"
    assert result["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='REGIONAL' LIMIT 1"
        ).fetchone()
    evidence = json_loads(str(row["evidence_json"]), {})
    assert evidence["usgs_water"]["ranking"]["flood_severity_score"] == 0
    assert evidence["regional_event"]["event_type"] == "hydrology_observation"
    assert evidence["regional_event"]["geography"]["matched"] is True
    assert "revision_note" not in str(evidence)


def test_usgs_water_registry_cannot_be_enabled_as_live_join(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("fixture-only USGS water source must not fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "live.yml"
    config_path.write_text(dedent("""
        paths: {repo_roots: [], explicit_repos: []}
        news:
          enabled: true
          fetch_policy: {allow_official_http: true}
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - {id: usgs_water_api, enabled: true}
    """).strip() + "\n", encoding="utf-8")
    result = run_news_scan(config_path)
    assert result["status"] == "partial"
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute(
            "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row["status"] == "policy_blocked"
