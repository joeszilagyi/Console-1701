"""Fixture-only metadata parser for two verified BLS release Atom feeds."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

_ATOM = "http://www.w3.org/2005/Atom"
_FEEDS = {
    "bls_employment_situation_atom": ("empsit", "Employment Situation"),
    "bls_cpi_atom": ("cpi", "Consumer Price Index"),
}
_ID_RE = re.compile(r"^(empsit|cpi)-\d{4}_\d{2}_\d{2}__\d{2}_\d{2}_\d{2}$")


def _text(row: ET.Element, name: str) -> str:
    element = row.find(f"{{{_ATOM}}}{name}")
    return "" if element is None or element.text is None else element.text.strip()


def parse_bls_release_atom(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    key = str(source.get("id") or "")
    if source.get("scope") != "NATIONAL" or key not in _FEEDS:
        raise NewsParserError("BLS release parser requires a verified NATIONAL source")
    series, feed_title = _FEEDS[key]
    feed_url = f"https://www.bls.gov/feed/{series}.rss"
    if (source.get("official_url") or source.get("url")) != feed_url:
        raise NewsParserError("BLS release parser requires its exact official feed")
    if len(payload_text.encode("utf-8")) > 262_144:
        raise PayloadTooLargeError("BLS release feed exceeds the 256 KiB parser cap")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", payload_text, re.I):
        raise NewsParserError("BLS release feed must not contain DTD or entity declarations")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed BLS release Atom: {exc}") from exc
    if (root.tag != f"{{{_ATOM}}}feed" or _text(root, "id") != f"bls.gov:feed:{series}"
            or _text(root, "title") != feed_title):
        raise NewsParserError("BLS release feed has an unverified channel identity")
    rows = root.findall(f"{{{_ATOM}}}entry")
    if len(rows) > 30:
        raise NewsParserError("BLS release feed exceeds the 30-entry snapshot cap")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        title = bounded_text(_text(row, "title"), max_chars=280)
        entry_id = _text(row, "id")
        links = row.findall(f"{{{_ATOM}}}link")
        url = str(links[0].get("href") or "") if len(links) == 1 else ""
        parts = urlsplit(url)
        published = normalize_timestamp(_text(row, "published"))
        updated = normalize_timestamp(_text(row, "updated"))
        categories = row.findall(f"{{{_ATOM}}}category")
        if (not title or not _ID_RE.fullmatch(entry_id) or not entry_id.startswith(series + "-")
                or entry_id in seen or parts.scheme != "https"
                or parts.hostname != "www.bls.gov" or parts.username or parts.password
                or parts.port or parts.query or parts.fragment
                or not re.fullmatch(
                    rf"/news\.release/archives/{series}_\d{{8}}\.htm", parts.path
                ) or not published or not updated
                or len(categories) != 1
                or (categories[0].text or "").strip() != "News Release"):
            raise NewsParserError(f"BLS release entry {index} lacks official identity")
        seen.add(entry_id)
        item = _normalize_item(source, {
            "title": title, "url": url, "description": None,
            "published_at": published, "tags": ["official", "bls", "economic-release", series],
        }, index=index)
        item["evidence"]["bls_release"] = {
            "series": series, "feed_url": feed_url, "entry_id": entry_id,
            "published_at": published, "updated_at": updated,
            "source_url": url, "body_stored": False,
        }
        item["evidence"]["national_identity"] = {
            "event_type": "economic_release", "agency": "BLS",
            "official_event_ids": [f"bls:{entry_id}"],
        }
        items.append(item)
    return items
