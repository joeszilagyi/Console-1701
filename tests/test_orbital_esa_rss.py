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

FIXTURES = Path(__file__).parent / "fixtures/orbital"


@pytest.mark.parametrize(("key", "file", "event_type"), [
    ("esa_rss", "esa_top_news.rss", "iss_update"),
    ("esa_iss", "esa_human_spaceflight.rss", "iss_update"),
])
def test_esa_rss_parser_preserves_official_metadata_and_filters_routine(key, file, event_type):
    registry = get_orbital_source_registry_entry(key)
    assert registry["parser"] == "esa_orbital_rss"
    assert registry["verification_status"] == "official_feed_seen"
    source = {"id": key, "scope": "ORBITAL", "kind": "rss", "parser": "esa_orbital_rss"}
    items = parse_fixture_items(source, (FIXTURES / file).read_text())
    assert len(items) == 1
    item = items[0]
    assert item["evidence"]["esa_rss"]["feed_url"] == registry["raw_url"]
    assert item["evidence"]["esa_rss"]["guid"]
    assert item["evidence"]["esa_rss"]["mission_label"] == "ISS"
    assert item["evidence"]["esa_rss"]["reentry_or_debris_reviewed"] is False
    assert item["evidence"]["orbital_identity"]["event_type"] == event_type
    assert "<" not in item["description"]
    assert item["source_published_at"].endswith("+00:00")


def test_esa_rss_parser_requires_verified_channel():
    source = {"id": "esa_rss", "scope": "ORBITAL", "kind": "rss", "parser": "esa_orbital_rss"}
    with pytest.raises(NewsParserError, match="verified ESA channel"):
        parse_fixture_items(source, "<rss><channel><title>Fake</title></channel></rss>")
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(source, "<rss>")


def test_esa_rss_fixture_scan_stays_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    path = tmp_path / "config.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: true}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: esa_rss
                  enabled: true
                  url: "file://{FIXTURES / 'esa_top_news.rss'}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(conn, "source_family", "esa")) == 1
        assert len(list_orbital_items_by_facet(conn, "mission_id", "ISS")) == 1
