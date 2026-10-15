from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_registry import get_global_source_registry_entry
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_sources_status

FIXTURE = Path(__file__).parent / "fixtures/news/global_un_news.rss"
SOURCE = {"scope": "GLOBAL", "kind": "rss", "parser": "un_news_rss"}


def test_un_news_official_rss_shape_and_low_value_filter():
    entry = get_global_source_registry_entry("un_news_rss")
    assert entry is not None
    assert entry["raw_url"] == "https://news.un.org/feed/subscribe/en/news/all/rss.xml"
    assert entry["verification_status"] == "official_feed_seen"
    homepage = get_global_source_registry_entry("un_news")
    assert homepage is not None and homepage["kind"] == "reference_only"
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 1
    item = items[0]
    evidence = item["evidence"]["un_news_rss"]
    assert item["url"] == "https://news.un.org/en/story/2026/10/1168602"
    assert item["source_published_at"] == "2026-10-15T12:00:00+00:00"
    assert item["description"] == "The UN health agency supports a response. More details."
    assert evidence["feed_link"] == "https://news.un.org/feed/view/en/story/2026/10/1168602"
    assert evidence["categories"] == []
    assert evidence["source_label"] == "UN News - Global perspective Human stories"
    assert evidence["impact_geography_assessed"] is False
    assert item["evidence"]["global_identity"]["institution"] == "United Nations"


def test_un_news_rss_rejects_unofficial_story_and_wrong_scope():
    fixture = FIXTURE.read_text()
    with pytest.raises(NewsParserError, match="official story URL"):
        parse_fixture_items(SOURCE, fixture.replace(
            "news.un.org/en/story/2026/10/1168602",
            "example.org/en/story/2026/10/1168602",
        ))
    with pytest.raises(NewsParserError, match="GLOBAL scope"):
        parse_fixture_items({**SOURCE, "scope": "NATIONAL"}, fixture)
    with pytest.raises(NewsParserError, match="Malformed UN News"):
        parse_fixture_items(SOURCE, "<rss><channel>")


def test_un_news_fixture_scan_is_offline_and_no_impact_inference(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("UN News fixture scan attempted HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "un-news.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: un_news_rss
                  kind: rss
                  parser: un_news_rss
                  enabled: true
                  url: "file://{FIXTURE}"
                - id: un_news
                  enabled: true
                  url: 'file:///missing-un-news-homepage.html'
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope = 'GLOBAL'"
        ).fetchall()
        states = get_news_sources_status(conn, config)
    assert len(rows) == 1
    assert {row["source_key"]: row["health_state"] for row in states} == {
        "un_news_rss": "healthy",
        "un_news": "unsupported",
    }
    evidence = json_loads(rows[0]["evidence_json"], {})
    assert evidence["global"]["affected_countries"] == []
    assert evidence["global"]["public_impact_basis"] is None
