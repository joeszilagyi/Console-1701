"""Public GraceDB metadata assembled from bounded REST reads or fixtures."""

from __future__ import annotations

import json
import math
import re
from typing import Any

from console1701.news.normalize import normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item
from console1701.news.science_sources import exact_science_endpoint

_ENDPOINT = "https://gracedb.ligo.org/api/v2/superevents/"
_ID = re.compile(r"S\d{6}[a-z]{1,4}")
_TYPES = {"EW", "PR", "IN", "UP", "RE"}
_STATUS = {
    "EW": "early_warning", "PR": "preliminary", "IN": "initial",
    "UP": "update", "RE": "retracted",
}


def public_gracedb_event_id(value: Any) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _gracedb_time(value: Any) -> str | None:
    text = str(value or "").strip()
    if text.endswith(" UTC"):
        text = text[:-4] + "+00:00"
    return normalize_timestamp(text)


def parse_gracedb_public_alert_fixture(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "SYSTEM_SOLAR" or source.get("id") != "gracedb_public_alerts":
        raise NewsParserError("GraceDB parser requires its exact COSMIC source")
    if not exact_science_endpoint(source, _ENDPOINT):
        raise NewsParserError("GraceDB parser requires its exact official source")
    fixture_only = source.get("fixture_only") is True
    if not fixture_only and (
        source.get("url") != _ENDPOINT or source.get("verification_status") != "verified"
    ):
        raise NewsParserError("GraceDB live parser requires its verified exact endpoint")
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("GraceDB fixture exceeds the 64 KiB cap")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed GraceDB fixture: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("assembly_version") != 1:
        raise NewsParserError("GraceDB fixture requires a versioned REST metadata assembly")
    query = payload.get("query")
    records = payload.get("records")
    if (not isinstance(query, dict) or query.get("category") != "Production"
            or query.get("is_public") is not True
            or type(query.get("count")) is not int or not 1 <= query["count"] <= 10
            or not isinstance(records, list) or len(records) > query["count"]):
        raise NewsParserError("GraceDB fixture needs a bounded public production query")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise NewsParserError("GraceDB fixture record must be an object")
        event = record.get("superevent")
        notices = record.get("voevents")
        if not isinstance(event, dict) or not isinstance(notices, dict):
            raise NewsParserError("GraceDB fixture needs superevent and VOEvent metadata")
        event_id = str(event.get("superevent_id") or "")
        if not public_gracedb_event_id(event_id) or event_id in seen:
            raise NewsParserError("GraceDB fixture has invalid or duplicate superevent ID")
        seen.add(event_id)
        if event.get("category") != "Production":
            raise NewsParserError("GraceDB fixture contains a nonproduction event")
        links = event.get("links") or {}
        if (not isinstance(links, dict)
                or links.get("self") != f"{_ENDPOINT}{event_id}/"
                or links.get("voevents") != f"{_ENDPOINT}{event_id}/voevents/"):
            raise NewsParserError("GraceDB fixture has nonpublic or mismatched REST links")
        entries = notices.get("voevents")
        if (not isinstance(entries, list) or not 1 <= len(entries) <= 20
                or notices.get("numRows") != len(entries)):
            raise NewsParserError("GraceDB fixture needs bounded VOEvent metadata")
        revisions = []
        for entry in entries:
            if not isinstance(entry, dict):
                raise NewsParserError("GraceDB VOEvent metadata must be an object")
            kind = entry.get("voevent_type")
            number = entry.get("N")
            created = _gracedb_time(entry.get("created"))
            if kind not in _TYPES or type(number) is not int or number < 1 or not created:
                raise NewsParserError("GraceDB VOEvent has unsupported revision metadata")
            revisions.append((number, kind, created))
        revisions.sort()
        if len({number for number, _, _ in revisions}) != len(revisions):
            raise NewsParserError("GraceDB VOEvent revision numbers must be unique")
        latest_number, latest_type, latest_at = revisions[-1]
        status = "retracted" if any(kind == "RE" for _, kind, _ in revisions) else (
            _STATUS[latest_type]
        )
        far = event.get("far")
        if far is not None and (
            isinstance(far, bool) or not isinstance(far, (int, float))
            or not math.isfinite(far) or far < 0
        ):
            raise NewsParserError("GraceDB false-alarm rate is invalid")
        gps = event.get("t_0")
        if gps is not None and (
            isinstance(gps, bool) or not isinstance(gps, (int, float))
            or not math.isfinite(gps) or gps < 0
        ):
            raise NewsParserError("GraceDB event GPS time is invalid")
        created_at = _gracedb_time(event.get("created"))
        if not created_at:
            raise NewsParserError("GraceDB superevent lacks a creation time")
        public_url = f"https://gracedb.ligo.org/superevents/{event_id}/view/"
        item = _normalize_item(source, {
            "title": f"GraceDB {event_id} candidate {status.replace('_', ' ')}",
            "url": public_url,
            "canonical_url": public_url,
            "description": (
                "Public gravitational-wave candidate metadata; retracted by LVK."
                if status == "retracted" else
                "Public gravitational-wave candidate metadata; confirmation not implied."
            ),
            "published_at": latest_at,
            "tags": ["official", "gracedb", "transient", status],
        }, index=index)
        item["evidence"]["gracedb_public_alert"] = {
            "superevent_id": event_id,
            "status": status,
            "latest_voevent_type": latest_type,
            "latest_revision": latest_number,
            "revision_types": [kind for _, kind, _ in revisions],
            "notice_at": latest_at,
            "created_at": created_at,
            "event_time_gps": gps,
            "false_alarm_rate_hz": far,
            "confirmed_gw_id": event.get("gw_id"),
            "source_url": public_url,
            "source_rest_url": links["self"],
            "query_bounds": query,
            "fixture_only": fixture_only,
            "sky_map_downloaded": False,
            "earth_impact_inferred": False,
        }
        item["evidence"]["science_identity"] = {
            "event_type": "transient",
            "gracedb_superevent_id": event_id,
            "public_value_class": "background" if status == "retracted" else None,
        }
        items.append(item)
    return items
