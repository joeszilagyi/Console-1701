"""Fixture-first metadata parser for ATel's official RSS 1.0 feed."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item
from console1701.news.science_sources import exact_science_endpoint

ATEL_RSS_URL = "https://www.astronomerstelegram.org/?rss"
_RSS = "{http://purl.org/rss/1.0/}"
_DC = "{http://purl.org/dc/elements/1.1/}"
_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
_TITLE_RE = re.compile(r"^ATel\s+(\d{1,7}):\s+(.+)$", re.I)
_IDENTIFIER_RE = re.compile(r"ATel(\d{1,7})", re.I)
_OBJECT_RE = re.compile(
    r"\b(?:AT\s?20\d{2}[a-z]{2,7}|SN\s?20\d{2}[a-z]{1,7}|"
    r"GRB\s?\d{6}[A-Z]?|FRB\s?\d{8}[A-Z]?|EP\d{6}[A-Za-z]?)\b",
    re.I,
)
_TAG_RE = re.compile(r"<[^>]*>")


def _text(element: ET.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def parse_atel_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if (source.get("scope") != "SYSTEM_SOLAR"
            or source.get("id") != "astronomers_telegram_rss"
            or source.get("kind") != "rss"):
        raise NewsParserError("ATel parser requires its exact COSMIC source")
    if not exact_science_endpoint(source, ATEL_RSS_URL):
        raise NewsParserError("ATel parser requires the official all-telegrams feed")
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("ATel RSS exceeds the 64 KiB fixture cap")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", payload_text, re.I):
        raise NewsParserError("ATel RSS must not contain DTD or entity declarations")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed ATel RSS: {exc}") from exc
    channel = root.find(f"{_RSS}channel") if root.tag == f"{_RDF}RDF" else None
    if channel is None or not _text(channel.find(f"{_RSS}title")).startswith(
        "The Astronomer's Telegram:"
    ):
        raise NewsParserError("ATel RSS requires the official RSS 1.0 channel")
    rows = root.findall(f"{_RSS}item")
    if len(rows) > 20:
        raise NewsParserError("ATel RSS exceeds the 20-item snapshot cap")
    items: list[dict[str, Any]] = []
    seen: set[int] = set()
    for index, row in enumerate(rows):
        match = _TITLE_RE.fullmatch(_text(row.find(f"{_RSS}title")))
        identifier = _IDENTIFIER_RE.fullmatch(_text(row.find(f"{_RSS}identifier")))
        url = _text(row.find(f"{_RSS}link"))
        parts = urlsplit(url)
        number = int(match.group(1)) if match else None
        published = normalize_timestamp(_text(row.find(f"{_DC}date")))
        if (
            not match or not identifier or number != int(identifier.group(1))
            or number in seen or parts.scheme != "https"
            or parts.hostname != "www.astronomerstelegram.org"
            or parts.username or parts.password or parts.port or parts.fragment
            or parts.path != "/" or parts.query != f"read={number}" or not published
        ):
            raise NewsParserError(f"ATel RSS item {index} lacks official identity")
        seen.add(number)
        title = bounded_text(match.group(2), max_chars=280)
        summary = " ".join(html.unescape(
            _TAG_RE.sub(" ", _text(row.find(f"{_RSS}description")))
        ).split())
        object_tokens = sorted({value.upper().replace(" ", "") for value in
                                _OBJECT_RE.findall(title)})[:10]
        item = _normalize_item(source, {
            "title": title, "url": url,
            "description": bounded_text(summary, max_chars=400),
            "published_at": published,
            "tags": ["astronomy", "atel", "preliminary_communication"],
        }, index=index)
        item["evidence"]["atel_telegram"] = {
            "feed_url": ATEL_RSS_URL,
            "atel_number": number,
            "source_url": url,
            "published_at": published,
            "object_tokens": object_tokens,
            "communication_status": "preliminary_unreviewed",
            "full_body_stored": False,
            "article_body_fetched": False,
            "data_product_downloaded": False,
        }
        item["evidence"]["science_identity"] = {
            "event_type": "science_communication",
            "atel_number": number,
            "object_name": object_tokens[0] if len(object_tokens) == 1 else None,
            "public_value_class": "preliminary",
        }
        items.append(item)
    return items
