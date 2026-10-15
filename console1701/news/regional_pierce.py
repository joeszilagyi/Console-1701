"""Fixture-only Pierce County road-alert RSS metadata parser."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import parse_qs, urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

FEED_URL = "https://www.piercecountywa.gov/RSSFeed.aspx?CID=Road-Alert-29&ModID=63"
CHANNEL_TITLE = "Pierce County, WA - Alert Center - Road Alert"
_GUID_RE = re.compile(r"https://www\.piercecountywa\.gov/AlertCenter\.aspx\?AID=(\d+)/(\d+)")
_HIGH_IMPACT = re.compile(
    r"\b(?:closed|closure|flood(?:ing|ed)?|washout|landslide|downed trees?)\b", re.I
)
_WEATHER = re.compile(r"\b(?:inclement weather|storm|snow|ice|windy weather)\b", re.I)
_TEST = re.compile(r"\b(?:test|exercise|drill)\b", re.I)


def parse_pierce_road_rss_fixture(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "REGIONAL" or source.get("id") != "pierce_road_alert_rss":
        raise NewsParserError("Pierce road RSS requires its REGIONAL registry source")
    if not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("Pierce road RSS parser is fixture-only")
    if source.get("official_url") != FEED_URL:
        raise NewsParserError("Pierce road fixture requires the exact official feed URL")
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("Pierce road RSS fixture exceeds 64 KiB")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError("Malformed Pierce road RSS fixture") from exc
    channel = root.find("channel") if root.tag == "rss" else None
    if channel is None or channel.findtext("title") != CHANNEL_TITLE:
        raise NewsParserError("Pierce road RSS has an unexpected channel")
    entries = channel.findall("item")
    if len(entries) > 50:
        raise NewsParserError("Pierce road RSS fixture exceeds 50 entries")

    latest: dict[str, tuple[str, int, ET.Element]] = {}
    for index, entry in enumerate(entries):
        link = str(entry.findtext("link") or "").strip()
        parts = urlsplit(link)
        aid = parse_qs(parts.query).get("AID", [])
        guid = str(entry.findtext("guid") or "").strip()
        match = _GUID_RE.fullmatch(guid)
        published = normalize_timestamp(entry.findtext("pubDate"))
        title = bounded_text(entry.findtext("title"), max_chars=240)
        if (parts.scheme != "https" or parts.hostname != "www.piercecountywa.gov"
                or parts.path != "/AlertCenter.aspx" or len(aid) != 1
                or not aid[0].isdigit() or match is None or aid[0] != match.group(1)
                or not published or not title):
            raise NewsParserError(f"Pierce road RSS item {index} lacks official identity or time")
        if aid[0] not in latest or published > latest[aid[0]][0]:
            latest[aid[0]] = (published, index, entry)

    items: list[dict[str, Any]] = []
    for aid, (published, index, entry) in latest.items():
        title = str(entry.findtext("title") or "").strip()
        description = bounded_text(entry.findtext("description"), max_chars=500)
        combined = f"{title} {description or ''}"
        if _TEST.search(combined):
            classification, impact = "test", 0
        elif _HIGH_IMPACT.search(combined):
            classification, impact = "road_hazard_or_closure", 20
        elif _WEATHER.search(combined):
            classification, impact = "weather_advisory", 5
        else:
            classification, impact = "routine_road_notice", 0
        link = str(entry.findtext("link") or "").strip()
        item = _normalize_item(source, {
            "title": title,
            "url": link,
            "published_at": published,
            "tags": ["official", "county-emergency", "road-alert", classification],
        }, index=index)
        item["evidence"]["pierce_road_alert"] = {
            "alert_id": aid,
            "revision_guid": str(entry.findtext("guid") or "").strip(),
            "county": "Pierce County",
            "geography_basis": "publisher_jurisdiction_only",
            "published_at": published,
            "source_url": link,
            "feed_url": FEED_URL,
            "classification": classification,
            "ranking": {"public_impact_score": impact},
            "body_stored": False,
        }
        items.append(item)
    return items
