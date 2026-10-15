"""Fixture-only GCN Unified Schema notice metadata parser."""

from __future__ import annotations

import json
import math
from typing import Any
from urllib.parse import quote, urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item
from console1701.news.science_sources import exact_science_endpoint

_SCHEMA_PREFIX = "https://gcn.nasa.gov/schema/"
_ALERT_TYPES = {"initial", "subsequent", "update", "retraction"}
_CURRENT_TENSES = {"current", "archival"}


def _event_value(value: Any) -> str | None:
    if isinstance(value, list):
        value = value[0] if value and isinstance(value[0], str) else None
    return bounded_text(value, max_chars=120) if isinstance(value, str) else None


def parse_gcn_notice_fixture(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if source.get("scope") != "SYSTEM_SOLAR" or source.get("id") != "gcn_notices":
        raise NewsParserError("GCN notice parser requires its exact working scope and source")
    if not exact_science_endpoint(source, "https://gcn.nasa.gov/docs/notices"):
        raise NewsParserError("GCN notice parser requires the official documentation source")
    if not source.get("fixture_only"):
        raise NewsParserError("GCN notice parser is fixture-only")
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("GCN notice fixture exceeds the 64 KiB cap")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed GCN notice JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise NewsParserError("GCN notice must be one JSON object")
    schema = payload.get("$schema")
    if not isinstance(schema, str) or not schema.startswith(_SCHEMA_PREFIX):
        raise NewsParserError("GCN notice requires an official unified schema URL")
    parts = urlsplit(schema)
    if parts.hostname != "gcn.nasa.gov" or "/gcn/notices/" not in parts.path:
        raise NewsParserError("GCN notice schema is outside the official notice tree")
    alert_type, alert_tense = payload.get("alert_type"), payload.get("alert_tense")
    if alert_type not in _ALERT_TYPES or alert_tense not in _CURRENT_TENSES:
        raise NewsParserError("GCN notice has unsupported alert type or test/future tense")
    event_name = _event_value(payload.get("event_name"))
    trigger_id = _event_value(payload.get("id"))
    if not event_name and not trigger_id:
        raise NewsParserError("GCN notice lacks an event name or trigger ID")
    mission = bounded_text(payload.get("mission"), max_chars=100)
    instrument = bounded_text(payload.get("instrument"), max_chars=100)
    trigger_time = normalize_timestamp(payload.get("trigger_time"))
    alert_time = normalize_timestamp(payload.get("alert_datetime"))
    if not mission or not trigger_time:
        raise NewsParserError("GCN notice lacks mission or trigger time")
    ra, dec = payload.get("ra"), payload.get("dec")
    if (ra is None) != (dec is None):
        raise NewsParserError("GCN notice coordinates must be paired")
    if ra is not None and (
        isinstance(ra, bool) or isinstance(dec, bool)
        or not isinstance(ra, (int, float)) or not isinstance(dec, (int, float))
        or not math.isfinite(ra) or not math.isfinite(dec)
        or not 0 <= ra < 360 or not -90 <= dec <= 90
    ):
        raise NewsParserError("GCN notice coordinates are invalid")
    event_id = event_name or trigger_id
    status = "retracted" if alert_type == "retraction" else "preliminary"
    reference_url = "https://gcn.nasa.gov/docs/notices?event=" + quote(event_id)
    item = _normalize_item(source, {
        "title": f"GCN {mission} {alert_type}: {event_id}",
        "url": reference_url,
        "description": "Machine-readable transient alert metadata; follow-up required.",
        "published_at": alert_time or trigger_time,
        "tags": ["official", "gcn", "transient", status],
    }, index=0)
    item["evidence"]["gcn_notice"] = {
        "schema_url": schema,
        "notice_type": parts.path.rsplit("/", 1)[-1],
        "event_id": event_id,
        "event_name": event_name,
        "trigger_id": trigger_id,
        "mission": mission,
        "instrument": instrument,
        "trigger_time": trigger_time,
        "alert_time": alert_time,
        "alert_type": alert_type,
        "alert_tense": alert_tense,
        "status": status,
        "coordinates_icrs_deg": [ra, dec] if ra is not None else None,
        "source_url_kind": "official_notice_docs_not_event_permalink",
        "fixture_only": True,
        "sky_map_downloaded": False,
        "raw_notice_stored": False,
    }
    return [item]
