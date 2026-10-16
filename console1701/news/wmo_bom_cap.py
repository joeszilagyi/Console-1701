"""Fixture-only CAP 1.2 metadata from one WMO-hosted BoM warning document."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

_CAP = "{urn:oasis:names:tc:emergency:cap:1.2}"
_CAP_PATH = re.compile(
    r"/v2/cap-alerts/au-bom-en/\d{4}/\d{2}/\d{2}/\d{2}/\d{2}/[^/]+\.xml\Z"
)
_IDENTIFIER = re.compile(r"AusBoM-[A-Z0-9]+-20\d{2}-\d{2}-\d{2}T[^\s]{8,35}\Z")
_SEVERITY = {"Extreme", "Severe", "Moderate", "Minor", "Unknown"}
_URGENCY = {"Immediate", "Expected", "Future", "Past", "Unknown"}
_CERTAINTY = {"Observed", "Likely", "Possible", "Unlikely", "Unknown"}


def _text(row: ET.Element, name: str) -> str:
    node = row.find(f"{_CAP}{name}")
    return "" if node is None or node.text is None else node.text.strip()


def parse_wmo_bom_cap_xml(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Keep area-level alert state, without retaining warning narratives or fetching links."""
    if source.get("scope") != "GLOBAL" or source.get("id") != "wmo_bom_cap_fixture":
        raise NewsParserError("BoM CAP parser requires its GLOBAL fixture source identity")
    url = str(source.get("official_url") or "")
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise NewsParserError("BoM CAP fixture has an invalid official URL") from exc
    if (parts.scheme != "https" or parts.hostname != "severeweather.wmo.int"
            or not _CAP_PATH.fullmatch(parts.path) or parts.username or parts.password
            or port or parts.query or parts.fragment):
        raise NewsParserError("BoM CAP fixture requires an exact WMO-hosted BoM XML URL")
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("BoM CAP fixture exceeds 64 KiB")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", payload_text, re.I):
        raise NewsParserError("BoM CAP fixture cannot contain DTD or entities")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed BoM CAP XML: {exc}") from exc
    if root.tag != f"{_CAP}alert":
        raise NewsParserError("BoM CAP fixture requires the CAP 1.2 alert namespace")
    identifier = _text(root, "identifier")
    sent_at = normalize_timestamp(_text(root, "sent"))
    status = _text(root, "status")
    message_type = _text(root, "msgType")
    scope = _text(root, "scope")
    if (not _IDENTIFIER.fullmatch(identifier) or not identifier.endswith(sent_at or "")
            or _text(root, "sender") != "CAP.Message@bom.gov.au" or not sent_at
            or status not in {"Actual", "Test"}
            or message_type not in {"Alert", "Update", "Cancel"}
            or scope != "Public"):
        raise NewsParserError("BoM CAP fixture lacks public issuing-authority identity")
    if status == "Test":
        return []
    rows = root.findall(f"{_CAP}info")
    if not 1 <= len(rows) <= 12:
        raise NewsParserError("BoM CAP fixture requires 1-12 info blocks")
    infos: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        severity = _text(row, "severity")
        urgency = _text(row, "urgency")
        certainty = _text(row, "certainty")
        effective = normalize_timestamp(_text(row, "effective"))
        expires = normalize_timestamp(_text(row, "expires"))
        event = bounded_text(_text(row, "event"), max_chars=100)
        headline = bounded_text(_text(row, "headline"), max_chars=240)
        if (_text(row, "language") != "en-AU" or _text(row, "category") != "Met"
                or _text(row, "senderName") != "Australian Government Bureau of Meteorology"
                or severity not in _SEVERITY or urgency not in _URGENCY
                or certainty not in _CERTAINTY or not effective or not expires
                or not event or not headline):
            raise NewsParserError(f"BoM CAP info {index} lacks verified warning fields")
        areas = row.findall(f"{_CAP}area")
        if not 1 <= len(areas) <= 20:
            raise NewsParserError(f"BoM CAP info {index} requires bounded areas")
        area_names = [
            bounded_text(_text(area, "areaDesc"), max_chars=180) for area in areas
        ]
        if any(not name for name in area_names):
            raise NewsParserError(f"BoM CAP info {index} lacks an area description")
        cancelled = message_type == "Cancel" or headline.casefold().startswith(
            ("cancellation of ", "cancelled ")
        )
        infos.append({
            "event": event, "headline": headline, "severity": severity,
            "urgency": urgency, "certainty": certainty,
            "effective_at": effective, "expires_at": expires,
            "areas": area_names, "cancelled": cancelled,
        })
    active_infos = [info for info in infos if not info["cancelled"]]
    title = (active_infos or infos)[0]["headline"]
    item = _normalize_item(source, {
        "title": title, "url": url, "published_at": sent_at,
        "tags": ["official", "wmo", "bom", "cap", "weather-warning"],
    }, index=0)
    item["evidence"]["wmo_bom_cap"] = {
        "identifier": identifier, "sender": "CAP.Message@bom.gov.au",
        "issuer": "Australian Government Bureau of Meteorology",
        "aggregator": "WMO Severe Weather Information Centre",
        "sent_at": sent_at, "status": status, "message_type": message_type,
        "scope": scope, "infos": infos, "source_url": url,
        "description_stored": False, "issuer_verified": True,
        "cancelled_area_count": sum(
            len(info["areas"]) for info in infos if info["cancelled"]
        ),
    }
    item["evidence"]["global_identity"] = {
        "cap_identifier": identifier,
        "public_value_class": "background" if (
            not any(
                info["severity"] in {"Severe", "Extreme"}
                and info["urgency"] in {"Immediate", "Expected"}
                and info["certainty"] in {"Observed", "Likely"}
                for info in active_infos
            )
        ) else None,
    }
    return [item]
