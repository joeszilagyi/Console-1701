from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db
from console1701.news.orbital_registry import get_orbital_source_registry_entry
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import list_orbital_items_by_facet

FIXTURE = Path(__file__).parent / "fixtures/orbital/nasa_station_blog.rss"
FEEDS = [
    ("nasa_iss_page", "International Space Station (ISS) – NASA",
     "/missions/station/", "Station Crew Completes Spacewalk"),
    ("nasa_spacestation_blog", "International Space Station - NASA",
     "/blogs/spacestation/", "SpaceX Dragon Docks at Station"),
    ("nasa_artemis", "Artemis – NASA",
     "/missions/artemis/", "NASA Confirms Artemis Heat Shield Test"),
    ("nasa_artemis_blog", "Artemis - NASA",
     "/blogs/artemis/", "NASA Completes Artemis Booster Stacking"),
    ("nasa_kennedy_blog", "Kennedy Space Center - NASA",
     "/blogs/kennedy/", "Kennedy Teams Complete Launch Test"),
]


@pytest.mark.parametrize(("key", "channel", "path", "title"), FEEDS)
def test_dedicated_nasa_feeds_use_verified_endpoint_and_channel(key, channel, path, title):
    registry = get_orbital_source_registry_entry(key)
    assert registry["parser"] == "nasa_orbital_rss"
    assert registry["verification_status"] == "official_feed_seen"
    assert registry["raw_url"].endswith("/feed/")
    payload = f"""<rss><channel><title>{channel}</title>
      <item><title>{title}</title>
      <link>https://www.nasa.gov{path}test-update/</link>
      <pubDate>Thu, 15 Oct 2026 18:30:00 +0000</pubDate></item>
      <item><title>Routine Student Feature</title>
      <link>https://www.nasa.gov{path}routine-feature/</link>
      <pubDate>Thu, 15 Oct 2026 17:30:00 +0000</pubDate></item>
    </channel></rss>"""
    source = {"id": key, "scope": "ORBITAL", "kind": "rss", "parser": "nasa_orbital_rss"}
    items = parse_fixture_items(source, payload)
    assert len(items) == 1
    assert items[0]["evidence"]["nasa_rss"]["feed_url"] == registry["raw_url"]
    assert items[0]["url"].startswith("https://www.nasa.gov" + path)


def test_station_blog_fixture_scan_offline(tmp_path, monkeypatch):
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
                - id: nasa_spacestation_blog
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(conn, "event_type", "iss_update")) == 1
