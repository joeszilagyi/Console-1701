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

FIXTURE = Path(__file__).parent / "fixtures/orbital/jpl_scout.json"
SOURCE = {
    "id": "jpl_scout_api", "name": "JPL Scout", "scope": "ORBITAL", "kind": "api_json",
    "parser": "jpl_scout_json", "source_family": "jpl_cneos", "url": f"file://{FIXTURE}",
}


def test_scout_fixture_retains_metadata_without_promoting_scores():
    registry = get_orbital_source_registry_entry("jpl_scout_api")
    assert registry["parser"] == "jpl_scout_json"
    assert registry["enabled"] is False
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 2
    assert items[0]["url"] == "https://ssd-api.jpl.nasa.gov/scout.api?tdes=6K72D21"
    assert items[0]["evidence"]["jpl_scout"]["observation_count"] == 24
    assert items[0]["evidence"]["orbital_identity"]["public_value_class"] == "background"
    assert items[0]["source_published_at"] is None
    assert "impact prediction" in items[0]["description"]
    assert "phaScore" not in json.dumps(items)
    assert "neoScore" not in json.dumps(items)
    assert "caDist" not in json.dumps(items)


def test_scout_rejects_changed_contract_and_untrusted_source():
    payload = json.loads(FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="identity"):
        parse_fixture_items(dict(SOURCE, id="other"), FIXTURE.read_text())
    payload["signature"]["version"] = "2.0"
    with pytest.raises(NewsParserError, match="signature"):
        parse_fixture_items(SOURCE, json.dumps(payload))
    payload["signature"]["version"] = "1.3"
    payload["count"] = 2000
    with pytest.raises(NewsParserError, match="bounded"):
        parse_fixture_items(SOURCE, json.dumps(payload))
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(SOURCE, "{")


def test_scout_fixture_scan_stays_offline_and_persists_background(tmp_path, monkeypatch):
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
                - id: jpl_scout_api
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = list_orbital_items_by_facet(conn, "event_type", "neo_candidate")
        assert len(rows) == 2
        assert len(list_orbital_items_by_facet(conn, "object_id", "6k72d21")) == 1
