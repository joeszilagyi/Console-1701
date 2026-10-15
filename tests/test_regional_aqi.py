from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.regional_aqi import QUERY_URL
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/regional_ecology_aqi.json"


def _source() -> dict:
    return {
        "id": "wa_ecology_aqi", "scope": "REGIONAL", "kind": "api_json",
        "parser": "ecology_aqi_fixture", "url": FIXTURE.as_uri(),
        "official_url": QUERY_URL,
    }


def test_ecology_aqi_fixture_keeps_categories_without_station_addresses():
    items = parse_fixture_items(_source(), FIXTURE.read_text(encoding="utf-8"))
    assert len(items) == 3
    assert {item["evidence"]["ecology_aqi"]["site_id"] for item in items} == {42, 46, 76}
    south = next(item for item in items if item["evidence"]["ecology_aqi"]["site_id"] == 46)
    evidence = south["evidence"]["ecology_aqi"]
    assert evidence["sample_at"] == "2026-10-15T22:00:00+00:00"
    assert evidence["aqi_value"] == 53 and evidence["aqi_category"] == "Moderate"
    assert evidence["pm25_aqi"] == 53 and evidence["pm25_concentration"] == 9.8
    assert evidence["ranking"]["public_impact_score"] == 0
    assert "SiteLocation" not in str(items)
    assert "8201 10th" not in str(items)


def test_ecology_aqi_rejects_mismatched_station_band_and_live_source():
    fixture = FIXTURE.read_text(encoding="utf-8")
    payload = json.loads(fixture)
    payload["features"][0]["attributes"]["SiteId"] = 999
    with pytest.raises(NewsParserError, match="site identity"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload["features"][0]["attributes"]["SiteId"] = 42
    payload["features"][0]["attributes"]["AQIValue"] = 180
    with pytest.raises(NewsParserError, match="category band"):
        parse_fixture_items(_source(), json.dumps(payload))
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items({**_source(), "url": QUERY_URL}, fixture)


def test_ecology_aqi_offline_scan_and_live_block(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("AQI fixture/live-block tests must not fetch HTTP")

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
                - id: wa_ecology_aqi
                  enabled: true
                  url: "{FIXTURE.as_uri()}"
                  official_url: "{QUERY_URL}"
    """).strip() + "\n", encoding="utf-8")
    result = run_news_scan(fixture_config)
    assert result["status"] == "complete" and result["item_count"] == 3
    config = load_config(fixture_config)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='REGIONAL'"
        ).fetchall()
    evidence = [json_loads(str(row["evidence_json"]), {}) for row in rows]
    assert {row["regional_event"]["event_type"] for row in evidence} == {
        "air_quality_observation"
    }
    assert all("8201 10th" not in str(row) for row in evidence)

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
                - {id: wa_ecology_aqi, enabled: true}
    """).strip() + "\n", encoding="utf-8")
    assert run_news_scan(live_config)["status"] == "partial"
    config = load_config(live_config)
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute(
            "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert run["status"] == "policy_blocked"
