from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db
from console1701.news.orbital_registry import get_orbital_source_registry_entry
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import list_orbital_items_by_facet

FIXTURE = Path(__file__).parent / "fixtures/orbital/celestrak_iss_gp.json"
SOURCE = {
    "id": "celestrak_iss_gp", "name": "CelesTrak ISS GP metadata", "scope": "ORBITAL",
    "kind": "api_json", "parser": "celestrak_iss_gp_json",
    "source_family": "celestrak", "source_class": "official_iss",
    "url": f"file://{FIXTURE}",
}


def test_iss_gp_fixture_stores_catalog_freshness_without_orbit():
    registry = get_orbital_source_registry_entry("celestrak_iss_gp")
    assert registry["parser"] == "celestrak_iss_gp_json"
    assert registry["enabled"] is False
    item, = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert item["source_published_at"].startswith("2026-10-15T11:59:01")
    assert item["evidence"]["celestrak_iss"]["orbital_elements_stored"] is False
    assert item["evidence"]["orbital_identity"]["public_value_class"] == "background"
    stored = json.dumps(item)
    for raw_element in ("MEAN_MOTION", "ECCENTRICITY", "INCLINATION", "RA_OF_ASC_NODE"):
        assert raw_element not in stored
    assert "live position" in item["description"]


def test_iss_gp_fixture_rejects_other_objects_and_unbounded_data():
    rows = json.loads(FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="exact ORBITAL"):
        parse_fixture_items(dict(SOURCE, id="celestrak_elements"), FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(SOURCE, "{")
    with pytest.raises(NewsParserError, match="at most one"):
        parse_fixture_items(SOURCE, json.dumps(rows * 2))
    rows[0]["NORAD_CAT_ID"] = 12345
    with pytest.raises(NewsParserError, match="identity"):
        parse_fixture_items(SOURCE, json.dumps(rows))


def test_iss_gp_fixture_scan_is_offline_and_broad_catalog_remains_blocked(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    path = tmp_path / "config.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital:
          enabled: true
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: celestrak_iss_gp
                  enabled: true
                  url: "file://{FIXTURE}"
                - id: celestrak_elements
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(conn, "event_type", "iss_catalog_status")) == 1
        rows = conn.execute(
            "SELECT s.source_key,h.state FROM news_source_health h JOIN news_sources s "
            "ON h.source_id=s.id WHERE s.source_key='celestrak_elements'"
        ).fetchall()
        assert rows and rows[-1]["state"] == "sensitivity_blocked"
