"""Small, source-specific agency feed parsers for ORBITAL."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp

NASA_NEWS_RSS_URL = "https://www.nasa.gov/news-release/feed/"
_NASA_ACTION_RE = re.compile(
    r"\b(launch|liftoff|dock|undock|return|arriv|depart|spacewalk|crew|"
    r"station power|solar array|mission milestone|reentry|space weather)\w*\b",
    re.I,
)
_NASA_LOW_VALUE_RE = re.compile(
    r"\b(student|podcast|challenge|award|career|intern|media event|press conference)\b",
    re.I,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _xml_text(element: ET.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def _plain_description(value: str) -> str:
    return bounded_text(" ".join(html.unescape(_TAG_RE.sub(" ", value)).split()), max_chars=500)


def parse_nasa_orbital_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    from console1701.news.parsers import NewsParserError, _normalize_item

    if str(source.get("scope") or "").upper() != "ORBITAL":
        raise NewsParserError("NASA RSS parser requires ORBITAL scope")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed NASA RSS: {exc}") from exc
    channel = root.find("./channel") if root.tag == "rss" else None
    if channel is None or _xml_text(channel.find("./title")) != "NASA":
        raise NewsParserError("NASA RSS requires the official NASA channel")
    items: list[dict[str, Any]] = []
    for index, row in enumerate(channel.findall("./item")[:100]):
        title = bounded_text(_xml_text(row.find("./title")), max_chars=280)
        link = _xml_text(row.find("./link"))
        parts = urlsplit(link)
        if (
            not title or parts.scheme != "https"
            or parts.hostname not in {"nasa.gov", "www.nasa.gov"}
        ):
            continue
        path = parts.path.casefold()
        title_folded = title.casefold()
        official_orbital_path = path.startswith((
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
            "iss_update" if "/station/" in path else
            "launch_update" if "launch" in title_folded or "liftoff" in title_folded else
            "crewed_mission_update" if "crew" in title_folded else
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
            "feed_url": NASA_NEWS_RSS_URL,
            "story_url": link,
            "guid": bounded_text(_xml_text(row.find("./guid")), max_chars=500),
            "categories": categories,
            "published_at": published,
            "story_type": story_type,
            "scope_basis": "official_path_and_title_action",
        }
        item["evidence"]["orbital_identity"] = {
            "event_type": story_type,
            "object_id": path.rstrip("/").rsplit("/", 1)[-1][:100],
        }
        items.append(item)
    return items
