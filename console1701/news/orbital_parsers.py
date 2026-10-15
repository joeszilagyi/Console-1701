"""Fixture-first parsers for bounded ORBITAL source products."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

from console1701.news.normalize import bounded_text, normalize_timestamp

SWPC_ALERTS_URL = "https://services.swpc.noaa.gov/products/alerts.json"
SWPC_SCALES_URL = "https://services.swpc.noaa.gov/products/noaa-scales.json"
_PRODUCT_ID_RE = re.compile(r"^[A-Z0-9]{3,8}$")
_MESSAGE_CODE_RE = re.compile(r"^Space Weather Message Code:\s*(\S+)", re.I | re.M)
_SERIAL_RE = re.compile(r"^Serial Number:\s*(\d+)", re.I | re.M)
_KIND_RE = re.compile(
    r"^(CANCEL WATCH|EXTENDED WARNING|WATCH|WARNING|ALERT|SUMMARY)\s*:", re.I | re.M
)
_SCALE_RE = re.compile(r"\b(?:NOAA Scale\s*:|Category\s+)\s*([GRS][1-5])\b", re.I)
_VALID_RE = re.compile(
    r"^(?:Now )?Valid (From|To|Until):\s*(\d{4} [A-Z][a-z]{2} \d{1,2} \d{4} UTC)",
    re.I | re.M,
)
_IMPACT_KEYS = {"aurora", "induced currents", "spacecraft", "radio", "gps"}


def _swpc_utc(value: str) -> str | None:
    try:
        return datetime.strptime(value, "%Y %b %d %H%M UTC").replace(
            tzinfo=UTC
        ).isoformat(timespec="seconds")
    except ValueError:
        return None


def parse_swpc_alerts_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Keep NOAA's product fields and short parsed facts, never the full message text."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    if str(source.get("scope") or "").upper() != "ORBITAL":
        raise NewsParserError("SWPC alerts parser requires ORBITAL scope")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed SWPC alerts JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise NewsParserError("SWPC alerts JSON must be an array")
    items: list[dict[str, Any]] = []
    for index, raw in enumerate(payload[:200]):
        if not isinstance(raw, dict):
            continue
        product_id = str(raw.get("product_id") or "").strip().upper()
        issued_at = normalize_timestamp(raw.get("issue_datetime"))
        message = raw.get("message")
        if not _PRODUCT_ID_RE.fullmatch(product_id) or not issued_at or not isinstance(
            message, str
        ):
            continue
        message = message[:12000]
        kind_match = _KIND_RE.search(message)
        if kind_match is None:
            continue
        kind = kind_match.group(1).upper()
        heading = next(
            (line.strip() for line in message.splitlines()
             if _KIND_RE.match(line.strip())),
            f"{kind}: SWPC {product_id}",
        )
        scale_match = _SCALE_RE.search(message)
        noaa_scale = scale_match.group(1).upper() if scale_match else None
        valid: dict[str, str] = {}
        for match in _VALID_RE.finditer(message):
            timestamp = _swpc_utc(match.group(2))
            if timestamp:
                valid["from" if match.group(1).lower() == "from" else "until"] = timestamp
        impacts = []
        for line in message.splitlines():
            label, separator, detail = line.partition(" - ")
            if separator and label.strip().lower() in _IMPACT_KEYS:
                impacts.append({
                    "system": label.strip().lower(),
                    "description": bounded_text(detail, max_chars=220),
                })
        identity = {
            "product_id": product_id,
            "issued_at": issued_at,
            "message_code": _MESSAGE_CODE_RE.search(message).group(1)
            if _MESSAGE_CODE_RE.search(message) else None,
            "serial_number": _SERIAL_RE.search(message).group(1)
            if _SERIAL_RE.search(message) else None,
            "message_type": kind,
            "noaa_scale": noaa_scale,
            "valid_from": valid.get("from"),
            "valid_until": valid.get("until"),
            "cancelled": kind == "CANCEL WATCH",
            "potential_impacts": impacts[:8],
            "source_url": SWPC_ALERTS_URL,
            "link_note": "Product-specific deep links are unavailable in this JSON feed.",
        }
        query = urlencode({"product_id": product_id, "issue_datetime": issued_at})
        item = _normalize_item(source, {
            "title": heading,
            "url": f"{SWPC_ALERTS_URL}?{query}",
            "description": heading,
            "published_at": issued_at,
        }, index=index)
        item["evidence"]["swpc_alert"] = identity
        item["evidence"]["orbital_identity"] = {
            "event_type": "space_weather_alert",
            "object_id": f"{product_id}:{issued_at}",
        }
        item["evidence"]["orbital_safety"] = {
            "official_alert": kind in {"ALERT", "WARNING", "EXTENDED WARNING", "WATCH"}
            and kind != "CANCEL WATCH",
        }
        items.append(item)
    return items


def parse_swpc_noaa_scales_json(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    """Parse only explicit nonzero G/R/S scales; distinguish current from forecast."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    if str(source.get("scope") or "").upper() != "ORBITAL":
        raise NewsParserError("SWPC NOAA scales parser requires ORBITAL scope")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed SWPC NOAA scales JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("0"), dict):
        raise NewsParserError("SWPC NOAA scales JSON requires current period 0")
    items: list[dict[str, Any]] = []
    labels = {"G": "Geomagnetic storm", "R": "Radio blackout", "S": "Solar radiation storm"}
    for period in ("0", "1", "2", "3"):
        row = payload.get(period)
        if not isinstance(row, dict):
            continue
        date = row.get("DateStamp")
        time = row.get("TimeStamp")
        if not isinstance(date, str) or not isinstance(time, str):
            continue
        stamp = normalize_timestamp(f"{date}T{time}+00:00")
        if not stamp:
            continue
        for category in ("G", "R", "S"):
            scale = row.get(category)
            if not isinstance(scale, dict):
                continue
            raw_level = scale.get("Scale")
            if not isinstance(raw_level, (str, int)) or str(raw_level) not in {
                "1", "2", "3", "4", "5"
            }:
                continue
            level = int(raw_level)
            period_kind = "current" if period == "0" else "forecast"
            scale_label = f"{category}{level}"
            source_text = bounded_text(scale.get("Text"), max_chars=120)
            query = urlencode({
                "period": period, "scale": scale_label, "timestamp": stamp,
            })
            title = f"NOAA {scale_label} {labels[category]} ({period_kind})"
            item = _normalize_item(source, {
                "title": title,
                "url": f"{SWPC_SCALES_URL}?{query}",
                "description": source_text or title,
                "published_at": stamp,
            }, index=len(items))
            item["evidence"]["swpc_noaa_scale"] = {
                "category": category,
                "level": level,
                "scale": scale_label,
                "source_text": source_text,
                "period": period,
                "period_kind": period_kind,
                "timestamp": stamp,
                "minor_probability": scale.get("MinorProb") if category == "R" else None,
                "major_probability": scale.get("MajorProb") if category == "R" else None,
                "probability": scale.get("Prob") if category == "S" else None,
                "source_url": SWPC_SCALES_URL,
                "link_note": "Period-specific deep links are unavailable in this JSON product.",
            }
            item["evidence"]["orbital_identity"] = {
                "event_type": "space_weather_scale",
                "object_id": f"{period}:{scale_label}:{stamp}",
            }
            item["evidence"]["orbital_safety"] = {
                "official_current_scale": period_kind == "current",
                "official_forecast_scale": period_kind == "forecast",
            }
            items.append(item)
    return items
