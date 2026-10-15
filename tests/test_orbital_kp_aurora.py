from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import ConfigError, load_config
from console1701.db import connect_db
from console1701.news.orbital_registry import get_orbital_source_registry_entry
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_sources_status, list_orbital_items_by_facet

FIXTURES = Path(__file__).parent / "fixtures/orbital"


def _source(key: str, fixture: str, parser: str) -> dict:
    return {
        "id": key, "name": key, "scope": "ORBITAL", "kind": "api_json",
        "parser": parser, "url": f"file://{FIXTURES / fixture}",
    }


@pytest.mark.parametrize(("key", "fixture", "expected", "measurement"), [
    ("swpc_kp_summary_json", "swpc_kp_planetary.json", 6.0, "planetary Kp"),
    ("swpc_kp_1m_json", "swpc_kp_1m.json", 5.67, "planetary Kp"),
    ("swpc_boulder_k_json", "swpc_k_boulder.json", 6.2, "Boulder K-index"),
])
def test_swpc_k_index_parsers_keep_latest_bounded_measurement(
    key, fixture, expected, measurement
):
    assert get_orbital_source_registry_entry(key)["parser"] == "swpc_kp_json"
    source = _source(key, fixture, "swpc_kp_json")
    items = parse_fixture_items(source, (FIXTURES / fixture).read_text())
    assert len(items) == 1
    evidence = items[0]["evidence"]["swpc_k_index"]
    assert evidence["value"] == expected
    assert evidence["measurement"] == measurement
    assert evidence["source_url"].startswith("https://services.swpc.noaa.gov/")
    assert items[0]["evidence"]["orbital_identity"]["event_type"] == (
        "geomagnetic_k_index"
    )
    source["min_k_index"] = 8.0
    assert parse_fixture_items(source, (FIXTURES / fixture).read_text()) == []


def test_aurora_parser_requires_configured_location_and_summarizes_grid():
    source = _source("swpc_aurora_json", "swpc_aurora.json", "swpc_aurora_json")
    payload = (FIXTURES / "swpc_aurora.json").read_text()
    assert parse_fixture_items(source, payload) == []
    source["aurora_locations"] = [{
        "name": "Seattle", "scope": "LOCAL", "latitude": 47.6,
        "longitude": -122.3, "radius_degrees": 2.0, "min_intensity": 50,
    }]
    items = parse_fixture_items(source, payload)
    assert len(items) == 1
    item = items[0]
    assert item["tags"] == ["local-impact"]
    assert item["evidence"]["swpc_aurora"]["model_value"] == 72.0
    assert item["evidence"]["swpc_aurora"]["sample_count"] == 3
    assert item["evidence"]["swpc_aurora"]["model_only"] is True
    assert "coordinates" not in json.dumps(item)
    assert "not a visibility report" in item["description"]
    source["aurora_locations"][0]["min_intensity"] = 80
    assert parse_fixture_items(source, payload) == []


def test_kp_and_aurora_parser_schema_failures_are_bounded():
    kp_source = _source("swpc_kp_summary_json", "swpc_kp_planetary.json", "swpc_kp_json")
    aurora_source = _source("swpc_aurora_json", "swpc_aurora.json", "swpc_aurora_json")
    with pytest.raises(NewsParserError, match="array"):
        parse_fixture_items(kp_source, "{}")
    with pytest.raises(NewsParserError, match="point limit"):
        parse_fixture_items(aurora_source, json.dumps({
            "Observation Time": "2026-10-15T19:48:00Z",
            "Forecast Time": "2026-10-15T20:48:00Z",
            "coordinates": [[]] * 70001,
        }))


def test_kp_aurora_config_validation_and_offline_scan(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    path = tmp_path / "config.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital:
          enabled: true
          kp_min_index: 5.0
          aurora_locations:
            - name: Seattle
              scope: LOCAL
              latitude: 47.6
              longitude: -122.3
              radius_degrees: 2.0
              min_intensity: 50
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: swpc_kp_summary_json
                  enabled: true
                  url: "file://{FIXTURES / 'swpc_kp_planetary.json'}"
                - id: swpc_aurora_json
                  enabled: true
                  url: "file://{FIXTURES / 'swpc_aurora.json'}"
    """).strip() + "\n")
    config = load_config(path)
    assert config["news"]["scopes"]["ORBITAL"]["sources"][1][
        "aurora_locations"
    ][0]["name"] == "Seattle"
    result = run_news_scan(path)
    assert result["status"] == "complete"
    assert result["item_count"] == 2
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(conn, "event_type", "aurora_forecast")) == 1
        assert len(list_orbital_items_by_facet(conn, "impact_tag", "local-impact")) == 1
        conn.execute(
            "UPDATE news_source_health SET stale_after = '2020-01-01T00:00:00+00:00' "
            "WHERE source_id = (SELECT id FROM news_sources WHERE source_key = 'swpc_aurora_json')"
        )
        statuses = {row["source_key"]: row for row in get_news_sources_status(conn, config)}
        assert statuses["swpc_aurora_json"]["health_state"] == "stale"
    path.write_text(path.read_text().replace("latitude: 47.6", "latitude: 147.6"))
    with pytest.raises(ConfigError, match="invalid latitude"):
        load_config(path)
