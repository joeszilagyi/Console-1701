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

FIXTURE = Path(__file__).parent / "fixtures/orbital/mpc_mpec_2025_a18.json"
SOURCE = {
    "id": "mpc_mpecs_api", "name": "MPC MPECs API", "scope": "ORBITAL",
    "kind": "api_json", "parser": "mpc_mpec_json", "source_family": "mpc",
    "url": f"file://{FIXTURE}",
}


def test_mpc_mpec_fixture_stores_notice_metadata_only():
    registry = get_orbital_source_registry_entry("mpc_mpecs_api")
    assert registry["parser"] == "mpc_mpec_json"
    assert registry["enabled"] is False
    item, = parse_fixture_items(SOURCE, FIXTURE.read_text())
    evidence = item["evidence"]["mpc_mpec"]
    assert evidence["mpec_id"] == "2025-A18"
    assert evidence["notice_title"] == "2025 AA"
    assert evidence["body_stored"] is False
    assert item["source_published_at"] == "2025-01-02T09:25:27+00:00"
    assert item["evidence"]["orbital_identity"]["mpc_designation"] == "2025 AA"
    assert item["evidence"]["orbital_identity"]["public_value_class"] == "background"
    assert "impact implied" in item["description"]


def test_mpc_mpec_rejects_wildcards_and_unbounded_response():
    payload = json.loads(FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="identity"):
        parse_fixture_items(dict(SOURCE, id="other"), json.dumps(payload))
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(SOURCE, "{")
    payload["request"]["terms"] = ["2025%"]
    payload["results"] = {"2025%": []}
    with pytest.raises(NewsParserError, match="exact bounded"):
        parse_fixture_items(SOURCE, json.dumps(payload))
    payload["request"]["terms"] = ["2025-A18"]
    payload["results"] = {"2025-A18": [{}] * 21}
    with pytest.raises(NewsParserError, match="bounded array"):
        parse_fixture_items(SOURCE, json.dumps(payload))


def test_mpc_mpec_fixture_scan_is_offline(tmp_path, monkeypatch):
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
                - id: mpc_mpecs_api
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(conn, "event_type", "minor_planet_notice")) == 1
