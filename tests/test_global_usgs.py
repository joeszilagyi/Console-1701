from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_sources_status

FIXTURE = Path(__file__).parent / "fixtures/news/global_usgs_earthquakes.json"


def _source(**overrides):
    return {
        "scope": "GLOBAL", "kind": "api_json", "parser": "usgs_earthquake_geojson",
        **overrides,
    }


def test_global_usgs_fixture_filters_and_preserves_official_seismic_evidence():
    items = parse_fixture_items(_source(
        min_magnitude=6.0, max_depth_km=300, min_felt=5, min_mmi=3,
        country_terms=["Fiji"], region_terms=["Iceland"],
    ), FIXTURE.read_text())
    assert [item["evidence"]["usgs_earthquake"]["id"] for item in items] == [
        "global-fiji-001", "global-iceland-002"
    ]
    assert all(item["scope"] == "GLOBAL" for item in items)
    assert all("global" in item["tags"] for item in items)
    assert all("regional" not in item["tags"] for item in items)
    fiji = items[0]["evidence"]["usgs_earthquake"]
    assert fiji["magnitude"] == 7.1
    assert fiji["depth_km"] == 35.0
    assert fiji["felt"] == 110
    assert fiji["mmi"] == 6.2
    assert fiji["tsunami"] is True
    assert fiji["updated"] is not None
    assert fiji["source_url"] == items[0]["url"]
    assert fiji["filter"]["geography_basis"] == "source_place_label"
    assert items[0]["evidence"]["global_identity"]["earthquake_id"] == "global-fiji-001"
    assert [item["evidence"]["usgs_earthquake"]["id"] for item in parse_fixture_items(
        _source(tsunami_only=True, min_magnitude=6.0, max_depth_km=300),
        FIXTURE.read_text(),
    )] == ["global-fiji-001"]


def test_global_usgs_time_window_and_filter_validation():
    payload = json.loads(FIXTURE.read_text())
    recent = datetime.now(UTC) - timedelta(hours=2)
    old = datetime.now(UTC) - timedelta(days=4)
    payload["features"][0]["properties"]["time"] = int(recent.timestamp() * 1000)
    payload["features"][2]["properties"]["time"] = int(old.timestamp() * 1000)
    items = parse_fixture_items(
        _source(min_magnitude=6.0, max_age_hours=24, max_depth_km=300,
                country_terms=["Fiji"]),
        json.dumps(payload),
    )
    assert [item["evidence"]["usgs_earthquake"]["id"] for item in items] == [
        "global-fiji-001"
    ]
    for overrides in (
        {"min_magnitude": -1}, {"max_depth_km": -200}, {"min_mmi": 13},
        {"max_age_hours": 0}, {"tsunami_only": "true"},
        {"country_terms": "Fiji"},
    ):
        with pytest.raises(NewsParserError):
            parse_fixture_items(_source(**overrides), FIXTURE.read_text())


def test_global_usgs_scan_uses_global_threshold_and_stores_ranking_offline(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("GLOBAL USGS fixture scan attempted HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "global-usgs.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true, earthquake_min_magnitude: 6.5}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: usgs_eq_geojson_global
                  kind: api_json
                  parser: usgs_earthquake_geojson
                  enabled: true
                  url: "file://{FIXTURE}"
                  max_depth_km: 300
    """).strip() + "\n")
    config = load_config(config_path)
    source = config["news"]["scopes"]["GLOBAL"]["sources"][0]
    assert source["min_magnitude"] == 6.5
    assert run_news_scan(config_path)["status"] == "complete"
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope = 'GLOBAL' ORDER BY id"
        ).fetchall()
        clusters = conn.execute(
            "SELECT score, evidence_json FROM news_clusters WHERE scope = 'GLOBAL'"
        ).fetchall()
        statuses = get_news_sources_status(conn, config)
    assert statuses[0]["health_state"] == "healthy"
    assert len(rows) == 2
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert {item["usgs_earthquake"]["id"] for item in evidence} == {
        "global-fiji-001", "global-japan-005"
    }
    assert all(item["global"]["geography_basis"] == "source_place_unverified"
               for item in evidence)
    assert all(item["global"]["affected_countries"] == [] for item in evidence)
    assert all(item["global_event"]["ranking"]["factors"][
        "official_severity_score"
    ] > 0 for item in evidence)
    assert len(clusters) == 2
    assert all(row["score"] > 0 for row in clusters)
