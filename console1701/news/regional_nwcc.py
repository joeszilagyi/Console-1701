"""Bounded NWCC Atom metadata parser; no article content or impact inference."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

ATOM_URL = "https://nwccinfo.blogspot.com/feeds/posts/default"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
BLOG_ID = "8946818807005393639"
MAX_BYTES = 65_536
_POST_ID = re.compile(rf"tag:blogger\.com,1999:blog-{BLOG_ID}\.post-(\d+)")
_FIRE_UPDATE = re.compile(r"\b(?:fires?|wildfires?)\b.{0,50}\bupdates?\b", re.I)
_ARTICLE_PATH = re.compile(r"/\d{4}/\d{2}/[a-z0-9-]+\.html")


def parse_nwcc_atom_fixture(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if source.get("scope") != "REGIONAL" or source.get("id") != "nwcc_blog":
        raise NewsParserError("NWCC Atom requires its REGIONAL registry source")
    if not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("NWCC Atom parser is fixture-only")
    if source.get("official_url") != ATOM_URL:
        raise NewsParserError("NWCC fixture requires the exact linked Atom URL")
    if len(payload_text.encode("utf-8")) > MAX_BYTES:
        raise PayloadTooLargeError("NWCC Atom fixture exceeds 64 KiB")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError("Malformed NWCC Atom fixture") from exc
    if root.tag != ATOM_NS + "feed":
        raise NewsParserError("NWCC fixture must be an Atom feed")
    entries = root.findall(ATOM_NS + "entry")
    if len(entries) > 50:
        raise NewsParserError("NWCC Atom fixture exceeds 50 entries")
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        identifier = str(entry.findtext(ATOM_NS + "id") or "").strip()
        match = _POST_ID.fullmatch(identifier)
        if match is None or identifier in seen:
            raise NewsParserError(f"NWCC Atom entry {index} has invalid post identity")
        seen.add(identifier)
        title = bounded_text(entry.findtext(ATOM_NS + "title"), max_chars=240)
        published = normalize_timestamp(entry.findtext(ATOM_NS + "published"))
        updated = normalize_timestamp(entry.findtext(ATOM_NS + "updated"))
        links = [link.get("href") for link in entry.findall(ATOM_NS + "link")
                 if link.get("rel") == "alternate"]
        if not title or not published or not updated or len(links) != 1:
            raise NewsParserError(f"NWCC Atom entry {index} needs title, time and article link")
        article_url = str(links[0])
        parts = urlsplit(article_url)
        if (parts.scheme != "https" or parts.hostname != "nwccinfo.blogspot.com"
                or not _ARTICLE_PATH.fullmatch(parts.path)):
            raise NewsParserError(f"NWCC Atom entry {index} has an unapproved article URL")
        if not _FIRE_UPDATE.search(title):
            continue
        final = bool(re.search(r"\bfinal\b", title, re.I))
        item = _normalize_item(source, {
            "title": title,
            "url": article_url,
            "published_at": published,
            "tags": ["regional", "wildfire", "nwcc", "final" if final else "update"],
        }, index=index)
        item["evidence"]["nwcc_fire_update"] = {
            "post_id": match.group(1),
            "published_at": published,
            "updated_at": updated,
            "final_update": final,
            "source_url": article_url,
            "feed_url": ATOM_URL,
            "geography_basis": "PNW-wide title; Washington impact not established",
            "severity_basis": "No severity or acreage inferred from title",
            "body_stored": False,
            "ranking": {"public_impact_score": 0, "basis": "metadata update only"},
        }
        items.append(item)
    return items
