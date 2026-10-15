from __future__ import annotations

import json
from pathlib import Path

import pytest

from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.science_rss import NASA_SCIENCE_NEWS_FEED

FIXTURE = Path(__file__).parent / "fixtures/science/nasa_science_news_malformed.rss"


def _source():
    return {
        "id": "nasa_science_news", "scope": "SYSTEM_SOLAR", "kind": "rss",
        "parser": "nasa_science_news_fixture", "fixture_only": True,
        "official_url": NASA_SCIENCE_NEWS_FEED, "url": FIXTURE.as_uri(),
    }


def test_nasa_science_news_keeps_space_science_and_excludes_bodies():
    items = parse_fixture_items(_source(), FIXTURE.read_text())
    assert len(items) == 2
    assert [item["source_published_at"] for item in items] == [
        "2026-08-05T13:57:18+00:00", "2026-07-06T17:29:03+00:00",
    ]
    evidence = items[0]["evidence"]["science_rss"]
    assert evidence["science_categories"] == ["Planetary Science", "Pluto"]
    assert evidence["xml_header_repair"] == "single_missing_namespace_separator"
    assert evidence["article_body_fetched"] is False
    assert "private@example.test" not in json.dumps(items)
    assert all("Earth" not in item["title"] for item in items)
    assert all("Mission Milestone" not in item["title"] for item in items)


def test_nasa_science_news_rejects_wrong_scope_live_and_other_malformed_xml():
    fixture = FIXTURE.read_text()
    with pytest.raises(NewsParserError):
        parse_fixture_items({**_source(), "scope": "ORBITAL"}, fixture)
    with pytest.raises(NewsParserError, match="local fixture only"):
        parse_fixture_items({**_source(), "url": NASA_SCIENCE_NEWS_FEED,
                             "fixture_only": False}, fixture)
    with pytest.raises(NewsParserError, match="Malformed NASA Science News RSS"):
        parse_fixture_items(_source(), fixture.replace("</channel>", "</wrong>"))
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 131_073)
