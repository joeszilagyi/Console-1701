"""Small, source-specific agency feed parsers for ORBITAL."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp

NASA_NEWS_RSS_URL = "https://www.nasa.gov/news-release/feed/"
NASA_SCIENCE_RSS_URL = "https://science.nasa.gov/blogs/science-news/feed/"
_SCIENCE_MALFORMED_HEADER = (
    'xmlns:apod="https://science.nasa.gov/apod/"xmlns:media='
)
NASA_FEEDS = {
    "nasa_rss_feeds": (NASA_NEWS_RSS_URL, "NASA", ()),
    "nasa_iss_page": (
        "https://www.nasa.gov/missions/station/feed/", "International Space Station",
        ("/missions/station/",),
    ),
    "nasa_spacestation_blog": (
        "https://www.nasa.gov/blogs/spacestation/feed/", "International Space Station",
        ("/blogs/spacestation/",),
    ),
    "nasa_artemis": (
        "https://www.nasa.gov/missions/artemis/feed/", "Artemis",
        ("/missions/artemis/",),
    ),
    "nasa_artemis_blog": (
        "https://www.nasa.gov/blogs/artemis/feed/", "Artemis",
        ("/blogs/artemis/",),
    ),
    "nasa_kennedy_blog": (
        "https://www.nasa.gov/blogs/kennedy/feed/", "Kennedy Space Center",
        ("/blogs/kennedy/",),
    ),
    "jpl_rss": (
        "https://www.nasa.gov/centers-and-facilities/jpl/feed/",
        "Jet Propulsion Laboratory", ("/missions/", "/news-release/"),
    ),
    "nasa_science_news": (
        NASA_SCIENCE_RSS_URL, "The Latest in NASA Science News - NASA Science",
        ("/blogs/science-news/",),
    ),
}
ESA_FEEDS = {
    "esa_rss": ("https://www.esa.int/rssfeed/Our_Activities/Space_News", "ESA Top News"),
    "esa_iss": (
        "https://www.esa.int/rssfeed/Our_Activities/Human_Spaceflight",
        "ESA Human and Robotic Exploration",
    ),
}
_NASA_ACTION_RE = re.compile(
    r"\b(launch|liftoff|dock|undock|return|arriv|depart|spacewalk|crew|"
    r"station power|solar array|mission milestone|reentry|space weather|"
    r"complet|confirm|test|stack|heat shield)\w*\b",
    re.I,
)
_NASA_LOW_VALUE_RE = re.compile(
    r"\b(student|podcast|challenge|award|career|intern|media event|press conference)\b",
    re.I,
)
_TAG_RE = re.compile(r"<[^>]+>")
_ESA_ACTION_RE = re.compile(
    r"\b(launch|liftoff|dock|undock|return|arriv|depart|crew|astronaut|"
    r"mission|station|spacewalk|complet|confirm|test|deployment)\w*\b",
    re.I,
)
_ESA_ROUTINE_RE = re.compile(
    r"\b(week in images|earth from space|facts and figures|podcast|"
    r"education|student|gallery|video)\b",
    re.I,
)


def _xml_text(element: ET.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def _plain_description(value: str) -> str:
    return bounded_text(" ".join(html.unescape(_TAG_RE.sub(" ", value)).split()), max_chars=500)


def parse_nasa_orbital_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    from console1701.news.parsers import NewsParserError, _normalize_item

    if str(source.get("scope") or "").upper() != "ORBITAL":
        raise NewsParserError("NASA RSS parser requires ORBITAL scope")
    source_key = str(source.get("id") or "")
    if source_key not in NASA_FEEDS:
        raise NewsParserError("NASA RSS parser requires a verified feed candidate")
    feed_url, expected_channel, path_prefixes = NASA_FEEDS[source_key]
    repaired_header = False
    if source_key == "nasa_science_news":
        if not str(source.get("url") or "").startswith("file://"):
            raise NewsParserError("NASA Science RSS parser is fixture-only")
        if source.get("official_url") != NASA_SCIENCE_RSS_URL:
            raise NewsParserError("NASA Science fixture requires its exact official feed URL")
        if payload_text.count(_SCIENCE_MALFORMED_HEADER) == 1:
            payload_text = payload_text.replace(
                _SCIENCE_MALFORMED_HEADER,
                'xmlns:apod="https://science.nasa.gov/apod/" xmlns:media=',
                1,
            )
            repaired_header = True
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed NASA RSS: {exc}") from exc
    channel = root.find("./channel") if root.tag == "rss" else None
    if channel is None or expected_channel not in _xml_text(channel.find("./title")):
        raise NewsParserError("NASA RSS requires the official NASA channel")
    items: list[dict[str, Any]] = []
    for index, row in enumerate(channel.findall("./item")[:100]):
        title = bounded_text(_xml_text(row.find("./title")), max_chars=280)
        link = _xml_text(row.find("./link"))
        parts = urlsplit(link)
        if (
            not title or parts.scheme != "https"
            or parts.hostname not in (
                {"science.nasa.gov"} if source_key == "nasa_science_news"
                else {"nasa.gov", "www.nasa.gov"}
            )
        ):
            continue
        path = parts.path.casefold()
        title_folded = title.casefold()
        official_orbital_path = path.startswith(path_prefixes or (
            "/missions/station/", "/missions/artemis/", "/launches/",
            "/humans-in-space/", "/news-release/",
        ))
        if (
            not official_orbital_path or not _NASA_ACTION_RE.search(title)
            or _NASA_LOW_VALUE_RE.search(title)
        ):
            continue
        published = normalize_timestamp(_xml_text(row.find("./pubDate")))
        if not published:
            continue
        categories = [
            bounded_text(_xml_text(category), max_chars=64)
            for category in row.findall("./category")[:12]
            if _xml_text(category)
        ]
        story_type = (
            "iss_update" if source_key in {"nasa_iss_page", "nasa_spacestation_blog"}
            or "/station/" in path else
            "launch_update" if "launch" in title_folded or "liftoff" in title_folded else
            "crewed_mission_update" if source_key in {"nasa_artemis", "nasa_artemis_blog"}
            or "crew" in title_folded else
            "jpl_mission_update" if source_key == "jpl_rss" else
            "science_mission_update" if source_key == "nasa_science_news" else
            "orbital_agency_update"
        )
        item = _normalize_item(source, {
            "title": title,
            "url": link,
            "description": _plain_description(_xml_text(row.find("./description"))),
            "published_at": published,
            "tags": ["official", "nasa", "orbital"],
        }, index=index)
        item["evidence"]["nasa_rss"] = {
            "feed_url": feed_url,
            "story_url": link,
            "guid": bounded_text(_xml_text(row.find("./guid")), max_chars=500),
            "categories": categories,
            "published_at": published,
            "story_type": story_type,
            "scope_basis": "official_path_and_title_action",
            **({"xml_header_repair": "single_missing_namespace_separator"}
               if repaired_header else {}),
        }
        item["evidence"]["orbital_identity"] = {
            "event_type": story_type,
            "object_id": path.rstrip("/").rsplit("/", 1)[-1][:100],
        }
        items.append(item)
    return items


def parse_esa_orbital_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    from console1701.news.parsers import NewsParserError, _normalize_item

    if str(source.get("scope") or "").upper() != "ORBITAL":
        raise NewsParserError("ESA RSS parser requires ORBITAL scope")
    source_key = str(source.get("id") or "")
    if source_key not in ESA_FEEDS:
        raise NewsParserError("ESA RSS parser requires a verified feed candidate")
    feed_url, expected_channel = ESA_FEEDS[source_key]
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed ESA RSS: {exc}") from exc
    channel = root.find("./channel") if root.tag == "rss" else None
    if channel is None or _xml_text(channel.find("./title")) != expected_channel:
        raise NewsParserError("ESA RSS requires the verified ESA channel")
    items: list[dict[str, Any]] = []
    for index, row in enumerate(channel.findall("./item")[:100]):
        title = bounded_text(_xml_text(row.find("./title")), max_chars=280)
        link = _xml_text(row.find("./link"))
        parts = urlsplit(link)
        if (
            not title or parts.scheme != "https"
            or parts.hostname not in {"esa.int", "www.esa.int"}
        ):
            continue
        path = parts.path.casefold()
        if (
            path.startswith(("/esa_multimedia/", "/about_us/week_in_images/"))
            or not _ESA_ACTION_RE.search(title) or _ESA_ROUTINE_RE.search(title)
            or "reentry" in title.casefold() or "space debris" in title.casefold()
        ):
            continue
        published = normalize_timestamp(_xml_text(row.find("./pubDate")))
        if not published:
            continue
        mission = (
            "ISS" if "international space station" in title.casefold()
            or "iss" in title.casefold().split()
            or "international_space_station" in path else
            "Artemis" if "artemis" in title.casefold() else None
        )
        story_type = (
            "esa_iss_update" if source_key == "esa_iss" or mission == "ISS" else
            "esa_launch_update" if "launch" in title.casefold() else
            "esa_mission_update"
        )
        item = _normalize_item(source, {
            "title": title,
            "url": link,
            "description": _plain_description(_xml_text(row.find("./description"))),
            "published_at": published,
            "tags": ["official", "esa", "orbital"],
        }, index=index)
        item["evidence"]["esa_rss"] = {
            "feed_url": feed_url,
            "story_url": link,
            "guid": bounded_text(_xml_text(row.find("./guid")), max_chars=120),
            "published_at": published,
            "story_type": story_type,
            "mission_label": mission,
            "scope_basis": "official_feed_and_title_action",
            "reentry_or_debris_reviewed": False,
        }
        item["evidence"]["orbital_identity"] = {
            "event_type": story_type,
            "object_id": path.rstrip("/").rsplit("/", 1)[-1][:100],
            "mission_id": mission,
        }
        items.append(item)
    return items
