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

FIXTURES = Path(__file__).parent / "fixtures/orbital"


def _source(key: str) -> dict[str, str]:
    filename = (
        "launch_library_upcoming.json"
        if key == "launch_library_upcoming"
        else "launch_library_events.json"
    )
    return {
        "id": key,
        "name": "Launch Library",
        "scope": "ORBITAL",
        "kind": "api_json",
        "parser": "launch_library_json",
        "source_family": "launch_library",
        "url": f"file://{FIXTURES / filename}",
    }


def test_launch_library_launch_and_event_shapes_are_bounded_metadata():
    launch_source = _source("launch_library_upcoming")
    event_source = _source("launch_library_events")
    for source in (launch_source, event_source):
        assert get_orbital_source_registry_entry(source["id"])["parser"] == "launch_library_json"
        assert get_orbital_source_registry_entry(source["id"])["enabled"] is False
    launches = parse_fixture_items(
        launch_source, (FIXTURES / "launch_library_upcoming.json").read_text()
    )
    events = parse_fixture_items(
        event_source, (FIXTURES / "launch_library_events.json").read_text()
    )
    assert len(launches) == len(events) == 1
    evidence = launches[0]["evidence"]["launch_library"]
    assert evidence["provider"] == "SpaceX"
    assert evidence["vehicle"] == "Falcon 9 Block 5"
    assert evidence["status"] == "Go for Launch"
    assert evidence["window_end"] == "2026-10-16T03:44:00+00:00"
    assert evidence["status_basis"] == "source_current_snapshot_not_transition_history"
    assert (
        launches[0]["evidence"]["orbital_identity"]["launch_id"]
        == "df88cfbf-f504-4e11-8370-e33dd6280b5b"
    )
    assert "sensitive payload speculation" not in json.dumps(launches).lower()
    assert events[0]["evidence"]["launch_library"]["webcast_url"].startswith(
        "https://plus.nasa.gov/"
    )
    assert events[0]["evidence"]["orbital_identity"]["event_type"] == "iss_update"


def test_launch_library_rejects_untrusted_source_and_unbounded_rows():
    source = _source("launch_library_upcoming")
    payload = json.loads((FIXTURES / "launch_library_upcoming.json").read_text())
    with pytest.raises(NewsParserError, match="registered ORBITAL"):
        parse_fixture_items(dict(source, id="arbitrary"), json.dumps(payload))
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(source, "{")
    payload["results"] = [{}] * 21
    with pytest.raises(NewsParserError, match="bounded"):
        parse_fixture_items(source, json.dumps(payload))


def test_launch_library_fixture_scans_are_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    path = tmp_path / "config.yml"
    path.write_text(
        dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital:
          enabled: true
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: launch_library_upcoming
                  enabled: true
                  url: "file://{FIXTURES / "launch_library_upcoming.json"}"
                - id: launch_library_events
                  enabled: true
                  url: "file://{FIXTURES / "launch_library_events.json"}"
    """).strip()
        + "\n"
    )
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(conn, "event_type", "launch_update")) == 1
        assert len(list_orbital_items_by_facet(conn, "event_type", "iss_update")) == 1
