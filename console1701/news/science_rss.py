"""Fixture-first, metadata-only RSS parser for the NASA-hosted JPL feed."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

NASA_JPL_SCIENCE_FEED = "https://www.nasa.gov/centers-and-facilities/jpl/feed/"
ESA_SPACE_SCIENCE_FEED = "https://www.esa.int/rssfeed/Our_Activities/Space_Science"
ESA_TELESCOPE_FEEDS = {
    "esa_hubble_science_rss": (
        "https://feeds.feedburner.com/hubble_news/", "ESAHubble News", "Hubble",
        "esahubble.org", re.compile(r"heic\d{4}"),
    ),
    "esa_webb_science_rss": (
        "https://feeds.feedburner.com/esawebb/news/", "ESAWebb News", "JWST",
        "esawebb.org", re.compile(r"weic\d{4}"),
    ),
}
_CHANNEL_TITLE = "Jet Propulsion Laboratory – NASA"
_TAG_RE = re.compile(r"<[^>]+>")
_SCIENCE_CATEGORY_RE = re.compile(
    r"\b(astro(?:physics|nomy)|planetary science|solar system|exoplanet\w*|"
    r"brown dwarf\w*|mars|jupiter|saturn|venus|mercury|uranus|neptune|pluto|"
    r"earth's moon|moon science|galax|cosmolog|star|supernova|spherex|"
    r"roman space telescope|james webb space telescope)\b",
    re.I,
)
_OPERATIONS_RE = re.compile(
    r"\b(launch(?:es|ed)?|liftoff|testing|test readies|readies|"
    r"landing schedule|crew|dock(?:ing|ed)?|deployment|mission operations)\b",
    re.I,
)


def _text(element: ET.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def parse_nasa_jpl_science_rss(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "SYSTEM_SOLAR" or source.get("id") != "nasa_jpl_science_feed":
        raise NewsParserError("NASA JPL science parser requires its exact working scope and source")
    if source.get("url") != NASA_JPL_SCIENCE_FEED:
        raise NewsParserError("NASA JPL science parser requires the verified feed URL")
    if len(payload_text.encode("utf-8")) > 1_048_576:
        raise PayloadTooLargeError("NASA JPL science RSS exceeds the 1 MiB parser cap")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed NASA JPL science RSS: {exc}") from exc
    channel = root.find("channel") if root.tag == "rss" else None
    if channel is None or _text(channel.find("title")) != _CHANNEL_TITLE:
        raise NewsParserError("NASA JPL science RSS requires the verified channel")

    items: list[dict[str, Any]] = []
    for index, row in enumerate(channel.findall("item")[:100]):
        title = bounded_text(_text(row.find("title")), max_chars=280)
        url = _text(row.find("link"))
        parts = urlsplit(url)
        if not title or parts.scheme != "https" or parts.hostname not in {
            "www.nasa.gov", "nasa.gov", "science.nasa.gov",
        }:
            continue
        published = normalize_timestamp(_text(row.find("pubDate")))
        if not published or _OPERATIONS_RE.search(title):
            continue
        categories = [
            bounded_text(_text(category), max_chars=100)
            for category in row.findall("category")[:20]
            if _text(category)
        ]
        science_categories = [
            category for category in categories
            if category and _SCIENCE_CATEGORY_RE.search(category)
        ]
        if not science_categories:
            continue
        description = " ".join(html.unescape(
            _TAG_RE.sub(" ", _text(row.find("description")))
        ).split())
        item = _normalize_item(source, {
            "title": title,
            "url": url,
            "description": bounded_text(description, max_chars=500),
            "published_at": published,
            "tags": ["official", "nasa", "jpl", "science"],
        }, index=index)
        item["evidence"]["science_rss"] = {
            "feed_url": NASA_JPL_SCIENCE_FEED,
            "source_family": "nasa_jpl",
            "official": True,
            "guid": bounded_text(_text(row.find("guid")), max_chars=300),
            "categories": categories,
            "science_categories": science_categories,
            "scope_basis": "official_science_category_and_nonoperational_title",
            "published_at": published,
            "article_body_fetched": False,
            "data_product_downloaded": False,
        }
        items.append(item)
    return items


def parse_esa_science_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if source.get("scope") != "SYSTEM_SOLAR" or source.get("id") != "esa_space_science_feed":
        raise NewsParserError("ESA science parser requires its exact working scope and source")
    if source.get("url") != ESA_SPACE_SCIENCE_FEED:
        raise NewsParserError("ESA science parser requires the verified feed URL")
    if len(payload_text.encode("utf-8")) > 1_048_576:
        raise PayloadTooLargeError("ESA science RSS exceeds the 1 MiB parser cap")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed ESA science RSS: {exc}") from exc
    channel = root.find("channel") if root.tag == "rss" else None
    if channel is None or _text(channel.find("title")) != "ESA Space Science":
        raise NewsParserError("ESA science RSS requires the verified channel")

    items: list[dict[str, Any]] = []
    for index, row in enumerate(channel.findall("item")[:100]):
        title = bounded_text(_text(row.find("title")), max_chars=280)
        url = _text(row.find("link"))
        parts = urlsplit(url)
        path = parts.path
        if (
            not title or parts.scheme != "https" or parts.hostname not in {"esa.int", "www.esa.int"}
            or not path.startswith("/Science_Exploration/Space_Science/")
            or _OPERATIONS_RE.search(title)
        ):
            continue
        published = normalize_timestamp(_text(row.find("pubDate")))
        if not published:
            continue
        path_parts = path.split("/")
        mission_label = path_parts[3].replace("_", " ") if len(path_parts) > 4 else None
        description = " ".join(html.unescape(
            _TAG_RE.sub(" ", _text(row.find("description")))
        ).split())
        item = _normalize_item(source, {
            "title": title,
            "url": url,
            "description": bounded_text(description, max_chars=500),
            "published_at": published,
            "tags": ["official", "esa", "science"],
        }, index=index)
        item["evidence"]["science_rss"] = {
            "feed_url": ESA_SPACE_SCIENCE_FEED,
            "source_family": "esa_science",
            "official": True,
            "guid": bounded_text(_text(row.find("guid")), max_chars=120),
            "mission_label": mission_label,
            "scope_basis": "dedicated_space_science_feed_and_article_path",
            "published_at": published,
            "article_body_fetched": False,
            "data_product_downloaded": False,
        }
        items.append(item)
    return items


def parse_esa_telescope_science_rss(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    key = str(source.get("id") or "")
    if source.get("scope") != "SYSTEM_SOLAR" or key not in ESA_TELESCOPE_FEEDS:
        raise NewsParserError("ESA telescope parser requires a known science source")
    feed_url, channel_title, telescope, host, release_re = ESA_TELESCOPE_FEEDS[key]
    if source.get("url") != feed_url:
        raise NewsParserError("ESA telescope parser requires the publisher-linked feed URL")
    if len(payload_text.encode("utf-8")) > 1_048_576:
        raise PayloadTooLargeError("ESA telescope RSS exceeds the 1 MiB parser cap")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed ESA telescope RSS: {exc}") from exc
    channel = root.find("channel") if root.tag == "rss" else None
    if channel is None or _text(channel.find("title")) != channel_title:
        raise NewsParserError("ESA telescope RSS requires the verified channel")

    items: list[dict[str, Any]] = []
    for index, row in enumerate(channel.findall("item")[:100]):
        raw_title = _text(row.find("title"))
        if not raw_title.startswith("Science Release: "):
            continue
        title = bounded_text(raw_title.removeprefix("Science Release: "), max_chars=280)
        url = _text(row.find("link"))
        parts = urlsplit(url)
        release_id = parts.path.strip("/").split("/")[-1]
        if (
            not title or parts.scheme != "https" or parts.hostname not in {host, f"www.{host}"}
            or not parts.path.startswith("/news/") or not release_re.fullmatch(release_id)
        ):
            continue
        published = normalize_timestamp(_text(row.find("pubDate")))
        if not published:
            continue
        description = " ".join(html.unescape(
            _TAG_RE.sub(" ", _text(row.find("description")))
        ).split())
        item = _normalize_item(source, {
            "title": title,
            "url": url,
            "description": bounded_text(description, max_chars=500),
            "published_at": published,
            "tags": ["official", "esa", "telescope_science", telescope.casefold()],
        }, index=index)
        item["evidence"]["science_rss"] = {
            "feed_url": feed_url,
            "source_family": "esa_telescope",
            "official_publisher_link": True,
            "feed_host": "feeds.feedburner.com",
            "live_policy_status": "third_party_feed_host_review_required",
            "telescope": telescope,
            "instrument": None,
            "release_id": release_id,
            "guid": bounded_text(_text(row.find("guid")), max_chars=300),
            "release_type": "Science Release",
            "published_at": published,
            "article_body_fetched": False,
            "image_downloaded": False,
            "data_product_downloaded": False,
        }
        items.append(item)
    return items
