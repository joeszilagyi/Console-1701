"""Fixture-only PBS NewsHour RSS metadata for NATIONAL context."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

FEED_URL = "https://www.pbs.org/newshour/feeds/rss/headlines"
_CREATOR = "{http://purl.org/dc/elements/1.1/}creator"
_NATION_PATH = re.compile(r"/newshour/nation/[a-z0-9][a-z0-9-]{1,220}/?\Z")


def _text(row: ET.Element, tag: str) -> str:
    node = row.find(tag)
    return "" if node is None or node.text is None else node.text.strip()


def parse_pbs_newshour_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Keep only nation-section article metadata; infer no event or impact."""
    if source.get("scope") != "NATIONAL" or source.get("id") != "pbs_newshour_rss":
        raise NewsParserError("PBS RSS parser requires its NATIONAL source identity")
    if (source.get("official_url") or source.get("url")) != FEED_URL:
        raise NewsParserError("PBS RSS parser requires its exact published feed URL")
    if len(payload_text.encode("utf-8")) > 131_072:
        raise PayloadTooLargeError("PBS RSS fixture exceeds 128 KiB")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", payload_text, re.I):
        raise NewsParserError("PBS RSS fixture cannot contain DTD or entities")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed PBS RSS fixture: {exc}") from exc
    channel = root.find("./channel") if root.tag == "rss" else None
    if (channel is None or _text(channel, "title") != "PBS News Hour - The Latest"
            or _text(channel, "link") != "https://www.pbs.org/newshour/"):
        raise NewsParserError("PBS RSS fixture has an unverified channel identity")
    rows = channel.findall("./item")
    if len(rows) > 50:
        raise NewsParserError("PBS RSS fixture exceeds 50 entries")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        url = _text(row, "link")
        try:
            parts = urlsplit(url)
            port = parts.port
        except ValueError as exc:
            raise NewsParserError(f"PBS RSS item {index} has an invalid publisher URL") from exc
        if (parts.scheme != "https" or parts.hostname != "www.pbs.org"
                or parts.username or parts.password or port or parts.query
                or parts.fragment):
            raise NewsParserError(f"PBS RSS item {index} has an invalid publisher URL")
        if not _NATION_PATH.fullmatch(parts.path):
            continue
        guid = _text(row, "guid")
        guid_node = row.find("guid")
        title = bounded_text(_text(row, "title"), max_chars=280)
        published = normalize_timestamp(_text(row, "pubDate"))
        if (not title or not published or guid != url or guid in seen
                or guid_node is None or guid_node.get("isPermaLink") != "true"):
            raise NewsParserError(f"PBS RSS item {index} lacks stable article metadata")
        seen.add(guid)
        creator = bounded_text(_text(row, _CREATOR), max_chars=120)
        item = _normalize_item(source, {
            "title": title, "url": url, "published_at": published,
            "tags": ["pbs", "national-news", "nation-section"],
        }, index=index)
        item["evidence"]["pbs_newshour"] = {
            "feed_url": FEED_URL, "article_guid": guid,
            "section": "nation", "creator": creator,
            "published_at": published, "source_url": url,
            "description_stored": False, "article_body_stored": False,
            "impact_verified": False, "original_reporting_verified": False,
        }
        item["evidence"]["national_identity"] = {
            "agency": None, "event_type": None,
            "national_impact": False, "multi_state_impact": False,
            "public_value_class": "background",
            "impact_scope_basis": "publisher nation section is context, not verified impact",
        }
        items.append(item)
    return items
