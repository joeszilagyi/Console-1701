from __future__ import annotations

from pathlib import Path

import pytest

from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.science_rss import ESA_SPACE_SCIENCE_FEED, NASA_JPL_SCIENCE_FEED

FIXTURE = Path(__file__).parent / "fixtures" / "science" / "nasa_jpl_science.rss"
ESA_FIXTURE = Path(__file__).parent / "fixtures" / "science" / "esa_space_science.rss"


def _source():
    return {
        "id": "nasa_jpl_science_feed",
        "scope": "SYSTEM_SOLAR",
        "kind": "rss",
        "parser": "nasa_jpl_science_rss",
        "url": NASA_JPL_SCIENCE_FEED,
    }


def test_nasa_jpl_science_parser_keeps_only_bounded_official_science_metadata():
    items = parse_fixture_items(_source(), FIXTURE.read_text())
    assert len(items) == 2
    assert {item["title"] for item in items} == {
        "NASA’s SPHEREx Telescope Sees Brown Dwarfs",
        "NASA Telescope Finds a New Exoplanet",
    }
    assert items[0]["description"] == "A bounded science release."
    assert items[0]["source_published_at"] == "2026-10-08T18:22:48+00:00"
    assert items[0]["evidence"]["science_rss"]["science_categories"] == [
        "Astrophysics", "Brown Dwarfs"
    ]
    assert items[1]["description"] == "New finding."
    assert items[1]["evidence"]["science_rss"]["data_product_downloaded"] is False


@pytest.mark.parametrize(("change", "value"), [
    ("scope", "SYSTEM"),
    ("id", "nasa_rss_feeds"),
    ("url", "https://www.jpl.nasa.gov/feeds/news/"),
])
def test_nasa_jpl_science_parser_requires_exact_source(change, value):
    source = _source()
    source[change] = value
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())


def test_nasa_jpl_science_parser_rejects_bad_channel_xml_and_large_payload():
    content = FIXTURE.read_text()
    for invalid in (content.replace("Jet Propulsion Laboratory – NASA", "Other"), "<rss>"):
        with pytest.raises(NewsParserError):
            parse_fixture_items(_source(), invalid)
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), content + " " * 1_048_576)


def _esa_source():
    return {
        "id": "esa_space_science_feed",
        "scope": "SYSTEM_SOLAR",
        "kind": "rss",
        "parser": "esa_science_rss",
        "url": ESA_SPACE_SCIENCE_FEED,
    }


def test_esa_science_parser_keeps_article_metadata_and_source_mission_label():
    items = parse_fixture_items(_esa_source(), ESA_FIXTURE.read_text())
    assert len(items) == 1
    assert items[0]["title"] == "Solar Orbiter tracks origin of magnetic switchbacks"
    assert items[0]["description"] == "Solar physics finding."
    assert items[0]["source_published_at"] == "2026-10-08T09:00:00+00:00"
    evidence = items[0]["evidence"]["science_rss"]
    assert evidence["mission_label"] == "Solar Orbiter"
    assert evidence["guid"] == "verified-esa-guid"
    assert evidence["data_product_downloaded"] is False


def test_esa_science_parser_rejects_wrong_source_channel_and_oversize():
    content = ESA_FIXTURE.read_text()
    source = _esa_source()
    source["url"] = "https://www.esa.int/rssfeed/Our_Activities/Space_News"
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, content)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_esa_source(), content.replace("ESA Space Science", "ESA Top News"))
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_esa_source(), content + " " * 1_048_576)
