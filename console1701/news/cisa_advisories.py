"""Metadata-only parser for CISA's bounded all-advisories RSS snapshot."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

CISA_ADVISORIES_RSS_URL = "https://www.cisa.gov/cybersecurity-advisories/all.xml"
_CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)
_CVSS_RE = re.compile(
    r"CVSS Version Base Score Base Severity Vector String\s+"
    r"(?:3\.0|3\.1|4\.0)\s+(\d{1,2}(?:\.\d)?)\s+(CRITICAL|HIGH|MEDIUM|LOW)\b",
    re.I,
)
_NODE_RE = re.compile(r"/node/(\d{1,9})")
_KEV_RELEASE_RE = re.compile(
    r"^CISA Adds?\s+\w+(?:\s+\w+)?\s+Known Exploited Vulnerabilit", re.I
)
_DIRECTIVE_RE = re.compile(r"\b(?:Emergency Directive|ED\s*\d{2}-\d{2})\b", re.I)
_MITIGATION_RE = re.compile(r"\b(?:Mitigations?|Remediations?|Actions to Take|CISA urges)\b", re.I)
_SECTOR_RE = re.compile(
    r"Critical Infrastructure Sectors:\s*(.{1,100}?)\s*"
    r"(?:Countries/Areas Deployed:|Company Headquarters Location:|Vulnerabilities\b)",
    re.I,
)
_TAG_RE = re.compile(r"<[^>]*>")


def _text(element: ET.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def _kind(path: str, title: str) -> str | None:
    if path.startswith("/news-events/ics-medical-advisories/"):
        return "ics_medical_advisory"
    if path.startswith("/news-events/ics-advisories/"):
        return "ics_advisory"
    if path.startswith("/news-events/cybersecurity-advisories/"):
        return "cybersecurity_advisory"
    if path.startswith("/news-events/directives/") or _DIRECTIVE_RE.search(title):
        return "emergency_directive"
    if path.startswith("/news-events/alerts/") and not _KEV_RELEASE_RE.search(title):
        return "cyber_alert"
    if path.startswith("/news-events/bulletins/"):
        return "cyber_bulletin"
    return None


def parse_cisa_advisories_rss(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "NATIONAL" or source.get("id") != "cisa_advisories":
        raise NewsParserError("CISA advisory parser requires its exact NATIONAL source")
    if (source.get("official_url") or source.get("url")) != CISA_ADVISORIES_RSS_URL:
        raise NewsParserError("CISA advisory parser requires the verified official feed")
    if len(payload_text.encode("utf-8")) > 2_097_152:
        raise PayloadTooLargeError("CISA advisory RSS exceeds the 2 MiB parser cap")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", payload_text, re.I):
        raise NewsParserError("CISA advisory RSS must not contain DTD or entity declarations")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed CISA advisory RSS: {exc}") from exc
    channel = root.find("./channel") if root.tag == "rss" else None
    if channel is None or _text(channel.find("./title")) != "All CISA Advisories":
        raise NewsParserError("CISA advisory RSS requires the official channel")
    rows = channel.findall("./item")
    if len(rows) > 50:
        raise NewsParserError("CISA advisory RSS exceeds the 50-item snapshot cap")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        title = bounded_text(_text(row.find("./title")), max_chars=280)
        url = _text(row.find("./link"))
        parts = urlsplit(url)
        guid = _text(row.find("./guid"))
        created = normalize_timestamp(_text(row.find("./pubDate")))
        creator = _text(row.find("./{http://purl.org/dc/elements/1.1/}creator"))
        if (not title or parts.scheme != "https" or parts.hostname != "www.cisa.gov"
                or parts.username or parts.password or parts.port or parts.query or parts.fragment
                or not _NODE_RE.fullmatch(guid) or not created or creator != "CISA"
                or guid in seen):
            raise NewsParserError(f"CISA advisory item {index} lacks official identity")
        seen.add(guid)
        kind = _kind(parts.path, title)
        if not kind:
            continue
        description = _text(row.find("./description"))
        if len(description.encode("utf-8")) > 524_288:
            raise NewsParserError(f"CISA advisory item {index} has an oversized body")
        body_text = " ".join(html.unescape(_TAG_RE.sub(" ", description)).split())
        cves = sorted({value.upper() for value in _CVE_RE.findall(body_text)})
        cvss = [
            (float(score), label.upper()) for score, label in _CVSS_RE.findall(body_text)
            if 0 <= float(score) <= 10
        ]
        highest_cvss = max(cvss, default=None)
        match = _SECTOR_RE.search(body_text)
        sector = bounded_text(match.group(1), max_chars=100) if match else None
        advisory_id = parts.path.rstrip("/").rsplit("/", 1)[-1] if kind in {
            "ics_medical_advisory", "ics_advisory", "cybersecurity_advisory",
        } else None
        node_id = _NODE_RE.fullmatch(guid).group(1)
        event_ids = [f"cisa_node:{node_id}"]
        if advisory_id:
            event_ids.append(f"cisa_advisory:{advisory_id}")
        if len(cves) == 1:
            event_ids.append(f"cve:{cves[0].lower()}")
        directive = kind == "emergency_directive"
        public_alert = kind == "cyber_alert"
        score = 30 if directive else 24 if public_alert else 20 if (
            kind == "cybersecurity_advisory"
        ) else 12
        if highest_cvss and highest_cvss[0] >= 9:
            score = min(35, score + 5)
        item = _normalize_item(source, {
            "title": title, "url": url, "description": None, "published_at": created,
            "tags": ["official", "cisa", "cybersecurity", kind],
        }, index=index)
        item["evidence"]["cisa_advisory"] = {
            "feed_url": CISA_ADVISORIES_RSS_URL,
            "source_url": url,
            "feed_item_id": guid,
            "advisory_id": advisory_id,
            "kind": kind,
            "published_at": created,
            "updated_at": None,
            "cve_ids": cves[:20],
            "cve_ids_truncated": len(cves) > 20,
            "vendor_product_title": title if kind.startswith("ics_") else None,
            "highest_cvss_score": highest_cvss[0] if highest_cvss else None,
            "highest_cvss_severity": highest_cvss[1] if highest_cvss else None,
            "infrastructure_sector": sector,
            "mitigation_section_present": bool(_MITIGATION_RE.search(body_text)),
            "mitigation_url": url if _MITIGATION_RE.search(body_text) else None,
            "directive_flag": directive,
            "ranking": {"cyber_score": score, "severity_from_cvss_only": True},
            "body_stored": False,
        }
        item["evidence"]["national_identity"] = {
            "event_type": "cyber_advisory",
            "agency": "CISA",
            "official_event_ids": event_ids,
            "infrastructure_sectors": [sector] if sector else [],
            "official_public_alert": public_alert,
            "cyber_emergency_directive": directive,
        }
        items.append(item)
    return items
