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

FIXTURE = Path(__file__).parent / "fixtures/orbital/nasa_news_releases.rss"
SOURCE = {
    "id": "nasa_rss_feeds", "name": "NASA News Releases", "scope": "ORBITAL",
    "kind": "rss", "parser": "nasa_orbital_rss", "source_family": "nasa",
    "url": f"file://{FIXTURE}",
}


def test_nasa_rss_parser_keeps_orbital_actions_and_provenance():
    assert get_orbital_source_registry_entry("nasa_rss_feeds")["parser"] == (
        "nasa_orbital_rss"
    )
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 2
    station, launch = items
    assert station["url"].startswith("https://www.nasa.gov/missions/station/")
    assert station["description"] == "NASA reports a station power system update."
    assert station["evidence"]["nasa_rss"] == {
        "feed_url": "https://www.nasa.gov/news-release/feed/",
        "story_url": station["url"],
        "guid": "https://www.nasa.gov/?p=1056401",
        "categories": ["International Space Station (ISS)"],
        "published_at": "2026-10-15T17:30:00+00:00",
        "story_type": "iss_update",
        "scope_basis": "official_path_and_title_action",
    }
    assert launch["evidence"]["nasa_rss"]["story_type"] == "launch_update"
    assert "El Niño" not in " ".join(item["title"] for item in items)


def test_nasa_rss_parser_requires_official_channel():
    with pytest.raises(NewsParserError, match="official NASA channel"):
        parse_fixture_items(SOURCE, "<rss><channel><title>Other</title></channel></rss>")
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(SOURCE, "<rss>")


def test_nasa_rss_fixture_scan_stays_offline(tmp_path, monkeypatch):
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
                - id: nasa_rss_feeds
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(conn, "event_type", "iss_update")) == 1
        assert len(list_orbital_items_by_facet(conn, "source_family", "nasa")) == 2


def test_nasa_hosted_jpl_fixture_filters_science_and_stays_offline(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures/orbital/nasa_jpl_mission.rss"
    source = {"id": "jpl_rss", "scope": "ORBITAL", "kind": "rss",
              "parser": "nasa_orbital_rss", "url": f"file://{fixture}"}
    items = parse_fixture_items(source, fixture.read_text())
    assert len(items) == 2
    assert {item["evidence"]["nasa_rss"]["story_type"] for item in items} == {
        "jpl_mission_update", "launch_update",
    }
    assert all(item["evidence"]["nasa_rss"]["feed_url"] == (
        "https://www.nasa.gov/centers-and-facilities/jpl/feed/"
    ) for item in items)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    path = tmp_path / "jpl.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: true}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: jpl_rss
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(conn, "source_family", "nasa_jpl")) == 2
