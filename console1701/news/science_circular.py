"""Metadata-only parser for a local NASA GCN Circular JSON fixture."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from console1701.news.normalize import bounded_text
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item
from console1701.news.science_sources import exact_science_endpoint

_OFFICIAL_URL = "https://gcn.nasa.gov/circulars"
_STATUS_PREFIXES = (
    (re.compile(r"^(?:retraction|withdrawal)\b", re.I), "retracted"),
    (re.compile(r"^(?:correction|erratum)\b", re.I), "correction"),
    (re.compile(r"^(?:follow[- ]?up|update)\b", re.I), "follow_up"),
    (re.compile(r"^(?:proposal|planned observations?)\b", re.I), "proposal"),
)


def _created_time(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise NewsParserError("GCN Circular requires createdOn as Unix milliseconds")
    try:
        return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat(timespec="seconds")
    except (OverflowError, OSError, ValueError) as exc:
        raise NewsParserError("GCN Circular createdOn is out of range") from exc


def parse_gcn_circular_fixture(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "SYSTEM_SOLAR" or source.get("id") != "gcn_circulars":
        raise NewsParserError("GCN Circular parser requires its exact scope and source")
    if not exact_science_endpoint(source, _OFFICIAL_URL):
        raise NewsParserError("GCN Circular parser requires its official archive identity")
    if source.get("fixture_only") is not True or not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("GCN Circular parser is local fixture only")
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("GCN Circular fixture exceeds the 64 KiB cap")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed GCN Circular JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise NewsParserError("GCN Circular must be one JSON object")

    circular_id = payload.get("circularId")
    if isinstance(circular_id, bool) or not isinstance(circular_id, int) or circular_id <= 0:
        raise NewsParserError("GCN Circular requires a positive circularId")
    subject = bounded_text(payload.get("subject"), max_chars=280)
    if not isinstance(payload.get("subject"), str) or not subject:
        raise NewsParserError("GCN Circular requires a subject")
    event_id = bounded_text(payload.get("eventId"), max_chars=120)
    if payload.get("eventId") is not None and not isinstance(payload["eventId"], str):
        raise NewsParserError("GCN Circular eventId must be text")
    if event_id and ("@" in event_id or "<" in event_id or ">" in event_id):
        raise NewsParserError("GCN Circular eventId contains unsupported characters")
    published = _created_time(payload.get("createdOn"))
    status = next((label for pattern, label in _STATUS_PREFIXES if pattern.search(subject)),
                  "preliminary_report")
    url = f"{_OFFICIAL_URL}/{circular_id}"
    item = _normalize_item(source, {
        "title": subject,
        "url": url,
        "description": "Human-authored astronomy circular; claims require source follow-up.",
        "published_at": published,
        "tags": ["official", "gcn", "transient", status],
    }, index=0)
    item["evidence"]["gcn_circular"] = {
        "circular_id": circular_id,
        "event_id": event_id,
        "event_id_basis": "GCN inferred from subject; aliases need review" if event_id else None,
        "subject": subject,
        "created_on": published,
        "permalink": url,
        "status": status,
        "status_basis": (
            "subject prefix" if status != "preliminary_report" else "default preliminary"
        ),
        "fixture_only": True,
        "body_stored": False,
        "submitter_stored": False,
        "sky_map_downloaded": False,
    }
    return [item]
