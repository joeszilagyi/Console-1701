from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db
from console1701.news.orbital_registry import get_orbital_source_registry_entry
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import list_orbital_items_by_facet

FIXTURE = Path(__file__).parent / "fixtures/orbital/swpc_noaa_scales.json"
SOURCE = {
    "id": "swpc_noaa_scales_json", "name": "SWPC NOAA Scales", "scope": "ORBITAL",
    "kind": "api_json", "parser": "swpc_noaa_scales_json", "source_family": "swpc",
    "url": f"file://{FIXTURE}",
}


def test_swpc_scales_parser_separates_current_forecast_and_zero_state():
    assert get_orbital_source_registry_entry("swpc_noaa_scales_json")[
        "parser"
    ] == "swpc_noaa_scales_json"
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 3
    current_g, current_r, forecast_g = items
    assert current_g["evidence"]["swpc_noaa_scale"] == {
        "category": "G", "level": 3, "scale": "G3", "source_text": "Strong",
        "period": "0", "period_kind": "current",
        "timestamp": "2026-10-15T19:58:00+00:00",
        "minor_probability": None, "major_probability": None, "probability": None,
        "source_url": "https://services.swpc.noaa.gov/products/noaa-scales.json",
        "link_note": "Period-specific deep links are unavailable in this JSON product.",
    }
    assert current_g["evidence"]["orbital_safety"] == {
        "official_current_scale": True, "official_forecast_scale": False,
    }
    assert current_r["evidence"]["swpc_noaa_scale"]["scale"] == "R2"
    assert forecast_g["evidence"]["swpc_noaa_scale"]["period_kind"] == "forecast"
    assert forecast_g["evidence"]["orbital_safety"]["official_current_scale"] is False
    assert not any("S0" in item["title"] for item in items)


def test_swpc_scales_parser_handles_missing_and_malformed_fields():
    with pytest.raises(NewsParserError, match="current period 0"):
        parse_fixture_items(SOURCE, "{}")
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(SOURCE, "{")
    assert parse_fixture_items(SOURCE, '{"0":{"DateStamp":"bad","TimeStamp":"bad"}}') == []


def test_swpc_scales_fixture_scan_stays_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    config_path = tmp_path / "config.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: true}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: swpc_noaa_scales_json
                  name: SWPC NOAA Scales fixture
                  enabled: true
                  kind: api_json
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    result = run_news_scan(config_path)
    assert result["status"] == "complete"
    assert result["item_count"] == 3
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(
            conn, "event_type", "space_weather_scale"
        )) == 3
        assert len(list_orbital_items_by_facet(
            conn, "safety", "official_current_scale"
        )) == 2
        assert len(list_orbital_items_by_facet(
            conn, "safety", "official_forecast_scale"
        )) == 1
