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

FIXTURE = Path(__file__).parent / "fixtures/orbital/swpc_alerts.json"
SOURCE = {
    "id": "swpc_alerts_json", "name": "SWPC Alerts", "scope": "ORBITAL",
    "kind": "api_json", "parser": "swpc_alerts_json", "source_family": "swpc",
    "url": f"file://{FIXTURE}",
}


def test_swpc_alert_parser_preserves_official_product_fields_and_cancellation():
    assert get_orbital_source_registry_entry("swpc_alerts_json")["parser"] == "swpc_alerts_json"
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 2
    warning, cancellation = items
    assert warning["source_published_at"] == "2026-10-10T17:42:57+00:00"
    assert warning["evidence"]["swpc_alert"] == {
        "product_id": "K07W",
        "issued_at": "2026-10-10T17:42:57+00:00",
        "message_code": "WARK07",
        "serial_number": "153",
        "message_type": "WARNING",
        "noaa_scale": "G3",
        "valid_from": "2026-10-10T17:42:00+00:00",
        "valid_until": "2026-10-10T23:59:00+00:00",
        "cancelled": False,
        "potential_impacts": [
            {"system": "spacecraft",
             "description": "Satellite orientation irregularities may occur."},
            {"system": "radio", "description": "HF propagation can fade at higher latitudes."},
            {"system": "aurora", "description": "Aurora may be seen as low as Washington state."},
        ],
        "source_url": "https://services.swpc.noaa.gov/products/alerts.json",
        "link_note": "Product-specific deep links are unavailable in this JSON feed.",
    }
    assert warning["evidence"]["orbital_safety"]["official_alert"] is True
    assert "message" not in warning["evidence"]["swpc_alert"]
    assert cancellation["evidence"]["swpc_alert"]["cancelled"] is True
    assert cancellation["evidence"]["orbital_safety"]["official_alert"] is False
    assert warning["url"] != cancellation["url"]


def test_swpc_alert_parser_rejects_broken_top_level_and_skips_bad_rows():
    with pytest.raises(NewsParserError, match="array"):
        parse_fixture_items(SOURCE, "{}")
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(SOURCE, "{")
    assert parse_fixture_items(SOURCE, '[{"product_id":"K07W"}]') == []


def test_swpc_alert_fixture_scan_is_offline_and_indexes_identity(tmp_path, monkeypatch):
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
                - id: swpc_alerts_json
                  name: SWPC Alerts fixture
                  enabled: true
                  kind: api_json
                  parser: swpc_alerts_json
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    result = run_news_scan(config_path)
    assert result["status"] == "complete"
    assert result["item_count"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        items = list_orbital_items_by_facet(conn, "event_type", "space_weather_alert")
        assert len(items) == 2
        assert len(list_orbital_items_by_facet(
            conn, "object_id", "K07W:2026-10-10T17:42:57+00:00"
        )) == 1
        assert len(list_orbital_items_by_facet(conn, "safety", "official_alert")) == 1
