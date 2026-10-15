from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.orbital_registry import get_orbital_source_registry_entry
from console1701.news.orbital_rss import NASA_SCIENCE_RSS_URL
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/orbital/nasa_science_news_malformed.rss"


def _source() -> dict:
    return {
        "id": "nasa_science_news", "scope": "ORBITAL", "kind": "rss",
        "parser": "nasa_orbital_rss", "url": FIXTURE.as_uri(),
        "official_url": NASA_SCIENCE_RSS_URL,
    }


def test_science_feed_repair_is_exact_and_keeps_only_orbital_mission_item():
    entry = get_orbital_source_registry_entry("nasa_science_news")
    assert entry["raw_url"] == NASA_SCIENCE_RSS_URL
    assert entry["enabled"] is False
    items = parse_fixture_items(_source(), FIXTURE.read_text(encoding="utf-8"))
    assert len(items) == 1
    assert items[0]["evidence"]["nasa_rss"]["story_type"] == "science_mission_update"
    assert items[0]["evidence"]["nasa_rss"]["xml_header_repair"] == (
        "single_missing_namespace_separator"
    )


def test_science_feed_rejects_live_and_other_malformed_xml():
    fixture = FIXTURE.read_text(encoding="utf-8")
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items({**_source(), "url": NASA_SCIENCE_RSS_URL}, fixture)
    with pytest.raises(NewsParserError, match="Malformed NASA RSS"):
        parse_fixture_items(_source(), fixture.replace("</channel>", "</wrong>"))


def test_science_feed_offline_scan_and_live_block(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("NASA Science fixture/live-block tests must not fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "fixture.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: true}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: nasa_science_news
                  enabled: true
                  url: "{FIXTURE.as_uri()}"
                  official_url: "{NASA_SCIENCE_RSS_URL}"
    """).strip() + "\n", encoding="utf-8")
    result = run_news_scan(config_path)
    assert result["status"] == "complete" and result["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='ORBITAL'"
        ).fetchone()
    evidence = json_loads(str(row["evidence_json"]), {})
    assert evidence["nasa_rss"]["xml_header_repair"] == "single_missing_namespace_separator"

    blocked_path = tmp_path / "blocked.yml"
    blocked_path.write_text(dedent("""
        paths: {repo_roots: [], explicit_repos: []}
        orbital: {enabled: true}
        news:
          enabled: true
          fetch_policy: {allow_official_http: true}
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - {id: nasa_science_news, enabled: true}
    """).strip() + "\n", encoding="utf-8")
    assert run_news_scan(blocked_path)["status"] == "partial"
