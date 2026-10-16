from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db
from console1701.news.orbital_events import correlate_orbital_items, orbital_independent_family
from console1701.news.orbital_registry import get_orbital_source_registry_entry
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import list_orbital_items_by_facet

FIXTURE = Path(__file__).parent / "fixtures/orbital/spaceflight_news_articles.json"
SOURCE = {
    "id": "spaceflight_news_articles", "name": "Spaceflight News API",
    "scope": "ORBITAL", "kind": "api_json", "parser": "spaceflight_news_json",
    "source_family": "spaceflight_news_api", "url": f"file://{FIXTURE}",
}


def test_spaceflight_news_parser_keeps_linked_headline_only():
    registry = get_orbital_source_registry_entry("spaceflight_news_articles")
    assert registry["parser"] == "spaceflight_news_json"
    assert registry["enabled"] is False
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 1
    evidence = items[0]["evidence"]["spaceflight_news"]
    assert evidence["article_id"] == 40370
    assert evidence["publisher"] == "Space Scout"
    assert evidence["linked_launch_ids"] == ["bf2c3027-a314-403e-a416-2bfd5d165ad1"]
    assert items[0]["evidence"]["orbital_identity"]["public_value_class"] == "background"
    assert orbital_independent_family("spaceflight_news_api") == "unknown"


def test_spaceflight_news_does_not_supply_independent_corroboration():
    item = parse_fixture_items(SOURCE, FIXTURE.read_text())[0]
    item["id"] = 1
    item["evidence"]["source"] = {
        "source_family": "spaceflight_news_api", "source_key": SOURCE["id"],
    }
    official = {
        "id": 2, "scope": "ORBITAL", "title": "CRS-35 mission launch",
        "source_published_at": "2026-10-14T12:00:00Z",
        "evidence": {
            "source": {"source_family": "nasa", "source_key": "nasa_rss_feeds"},
            "orbital_identity": {
                "event_type": "launch_update",
                "launch_id": "bf2c3027-a314-403e-a416-2bfd5d165ad1",
            },
        },
    }
    groups = correlate_orbital_items([item, official])
    assert len(groups) == 1
    assert groups[0]["corroborated"] is False
    assert groups[0]["families"] == ["nasa"]


def test_spaceflight_news_rejects_untrusted_and_unbounded_shapes():
    payload = json.loads(FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="registered ORBITAL"):
        parse_fixture_items(dict(SOURCE, id="other"), json.dumps(payload))
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(SOURCE, "{")
    payload["results"] = [{}] * 31
    with pytest.raises(NewsParserError, match="bounded"):
        parse_fixture_items(SOURCE, json.dumps(payload))


def test_spaceflight_news_fixture_scan_stays_offline(tmp_path, monkeypatch):
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
                - id: spaceflight_news_articles
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(conn, "event_type", "launch_update")) == 1
