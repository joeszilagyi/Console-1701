"""Fixture-only Launch Library 2 upcoming launch and event metadata."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp

_BASE = "https://ll.thespacedevs.com/2.3.0"
_LAUNCH_ID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")
_EVENT_TYPES = {"Docking", "EVA", "Undocking", "Spacecraft Event"}


def _time(value: Any) -> str | None:
    timestamp = normalize_timestamp(value)
    if not timestamp:
        return None
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC).isoformat() if parsed.tzinfo else None


def _name(value: Any, *, limit: int = 100) -> str | None:
    return bounded_text(value, max_chars=limit) if isinstance(value, str) else None


def _webcast_url(value: Any) -> str | None:
    if not isinstance(value, list):
        return None
    for entry in value[:10]:
        if not isinstance(entry, dict):
            continue
        kind = entry.get("type") or {}
        if not isinstance(kind, dict) or kind.get("name") != "Official Webcast":
            continue
        candidate = str(entry.get("url") or "")
        parts = urlsplit(candidate)
        if (
            parts.scheme == "https"
            and parts.hostname
            in {
                "plus.nasa.gov",
                "youtube.com",
                "www.youtube.com",
            }
            and not parts.username
            and not parts.password
        ):
            return candidate[:500]
    return None


def parse_launch_library_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Store launch schedules and operational events without provider endorsement."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    key = str(source.get("id") or "")
    if source.get("scope") != "ORBITAL" or key not in {
        "launch_library_upcoming",
        "launch_library_events",
    }:
        raise NewsParserError("Launch Library parser requires a registered ORBITAL source")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed Launch Library JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise NewsParserError("Launch Library JSON must be an object")
    rows = payload.get("results")
    if not isinstance(rows, list) or len(rows) > 20:
        raise NewsParserError("Launch Library results must be a bounded array")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        is_launch = key == "launch_library_upcoming"
        raw_id = row.get("id")
        if is_launch:
            if not isinstance(raw_id, str) or not _LAUNCH_ID.fullmatch(raw_id):
                continue
            identifier = raw_id.lower()
        else:
            if not isinstance(raw_id, int) or isinstance(raw_id, bool) or raw_id < 1:
                continue
            identifier = str(raw_id)
        if identifier in seen:
            continue
        name = _name(row.get("name"), limit=120)
        event_at = _time(row.get("net") if is_launch else row.get("date"))
        updated_at = _time(row.get("last_updated"))
        if not name or not event_at or not updated_at:
            continue
        if is_launch:
            event_type = "launch_update"
            kind = "launches"
            status = row.get("status") if isinstance(row.get("status"), dict) else {}
            status_name = _name(status.get("name"), limit=60)
            provider = row.get("launch_service_provider") or {}
            rocket = row.get("rocket") or {}
            configuration = rocket.get("configuration") if isinstance(rocket, dict) else {}
            mission = row.get("mission") or {}
            pad = row.get("pad") or {}
            provider_name = _name(provider.get("name")) if isinstance(provider, dict) else None
            rocket_name = (
                _name(configuration.get("full_name")) if isinstance(configuration, dict) else None
            )
            mission_name = _name(mission.get("name")) if isinstance(mission, dict) else None
            pad_name = _name(pad.get("name")) if isinstance(pad, dict) else None
            window_start = _time(row.get("window_start"))
            window_end = _time(row.get("window_end"))
            if window_start and window_end and window_end < window_start:
                continue
            detail = {
                "launch_id": identifier,
                "status": status_name,
                "provider": provider_name,
                "vehicle": rocket_name,
                "payload_or_mission": mission_name,
                "pad": pad_name,
                "net": event_at,
                "window_start": window_start,
                "window_end": window_end,
                "last_updated": updated_at,
                "webcast_url": _webcast_url(row.get("vid_urls")),
            }
        else:
            kind = "events"
            event_kind = row.get("type") or {}
            event_kind_name = (
                _name(event_kind.get("name")) if isinstance(event_kind, dict) else None
            )
            if event_kind_name not in _EVENT_TYPES:
                continue
            event_type = (
                "iss_update"
                if event_kind_name in {"Docking", "Undocking", "EVA"}
                else "mission_update"
            )
            detail = {
                "event_id": identifier,
                "event_kind": event_kind_name,
                "event_time": event_at,
                "last_updated": updated_at,
                "webcast_url": _webcast_url(row.get("vid_urls")),
            }
        seen.add(identifier)
        item = _normalize_item(
            source,
            {
                "title": name,
                "url": f"{_BASE}/{kind}/{identifier}/",
                "description": (
                    "Launch Library schedule metadata; confirm changes with the provider."
                    if is_launch
                    else "Launch Library event metadata; confirm with the responsible agency."
                ),
                "published_at": updated_at,
            },
            index=index,
        )
        item["evidence"]["launch_library"] = {
            **detail,
            "source_url": f"{_BASE}/{kind}/",
            "source_kind": "launch" if is_launch else "event",
            "status_basis": "source_current_snapshot_not_transition_history",
        }
        item["evidence"]["orbital_identity"] = {
            "event_type": event_type,
            "launch_id" if is_launch else "object_id": identifier,
            "public_value_class": "background",
            **({
                "mission_name": mission_name,
                "launch_vehicle": rocket_name,
                "provider": provider_name,
            } if is_launch else {}),
        }
        items.append(item)
    return items
