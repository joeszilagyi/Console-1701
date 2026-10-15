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
from console1701.news.storage import list_orbital_items_by_facet

FIXTURE = Path(__file__).parent / "fixtures/orbital/jpl_cad.json"
SOURCE = {
    "id": "jpl_cad_api", "name": "JPL CAD", "scope": "ORBITAL", "kind": "api_json",
    "parser": "jpl_cad_json", "source_family": "jpl_cneos", "url": f"file://{FIXTURE}",
}


def test_jpl_cad_parser_preserves_geometry_and_suppresses_distant_objects():
    assert get_orbital_source_registry_entry("jpl_cad_api")["parser"] == "jpl_cad_json"
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert [item["evidence"]["jpl_close_approach"]["designation"] for item in items] == [
        "2026 AB", "2026 CD", "2026 IJ",
    ]
    close = items[0]
    evidence = close["evidence"]["jpl_close_approach"]
    assert evidence["approach_time_tdb"] == "2028-Jun-26 05:23"
    assert evidence["time_scale"] == "TDB"
    assert evidence["distance_lunar"] == 0.646
    assert evidence["distance_min_au"] == 0.00165
    assert evidence["relative_velocity_km_s"] == 10.24
    assert evidence["diameter_km"] == 0.93
    assert evidence["risk_framing"] == "close_approach_not_impact_prediction"
    assert "does not establish impact risk" in close["description"]
    assert close["evidence"]["orbital_identity"]["object_id"] == "2026 AB"
    assert "date-min=2028-06-26" in close["url"]
    source = dict(SOURCE, max_lunar_distance=1.0)
    assert len(parse_fixture_items(source, FIXTURE.read_text())) == 2


def test_jpl_cad_parser_checks_signature_schema_and_zero_count():
    with pytest.raises(NewsParserError, match="signature version"):
        parse_fixture_items(SOURCE, '{"signature":{"version":"2.0"},"count":0}')
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(SOURCE, "{")
    assert parse_fixture_items(SOURCE, json.dumps({
        "signature": {"version": "1.5"}, "count": 0,
    })) == []
    with pytest.raises(NewsParserError, match="required field names"):
        parse_fixture_items(SOURCE, json.dumps({
            "signature": {"version": "1.5"}, "count": 1,
            "fields": ["des"], "data": [["2026 AB"]],
        }))


def test_jpl_cad_fixture_scan_offline_and_config_thresholds(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    path = tmp_path / "config.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital:
          enabled: true
          neo_max_lunar_distance: 5.0
          neo_min_diameter_km: 0.05
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: jpl_cad_api
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 3
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(
            conn, "event_type", "neo_close_approach"
        )) == 3
        assert len(list_orbital_items_by_facet(conn, "object_id", "2026 ab")) == 1
    path.write_text(path.read_text().replace(
        "neo_max_lunar_distance: 5.0", "neo_max_lunar_distance: 500.0"
    ))
    with pytest.raises(ConfigError, match="neo_max_lunar_distance"):
        load_config(path)
