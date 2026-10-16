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
SWPC_KP_URLS = {
    "swpc_kp_summary_json": "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",
    "swpc_kp_1m_json": "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json",
    "swpc_boulder_k_json": "https://services.swpc.noaa.gov/json/boulder_k_index_1m.json",
}
SWPC_AURORA_URL = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"
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
            "noaa_scale": noaa_scale,
            "valid_from": valid.get("from"),
            "valid_until": valid.get("until"),
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
                "noaa_scale": scale_label,
                "scale_period": period_kind,
                "scale_observed_at": stamp,
            }
            item["evidence"]["orbital_safety"] = {
                "official_current_scale": period_kind == "current",
                "official_forecast_scale": period_kind == "forecast",
            }
            items.append(item)
    return items


def parse_swpc_kp_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Keep the latest qualifying Kp/K measurement, not the minute-level history."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    source_key = str(source.get("id") or "")
    source_url = SWPC_KP_URLS.get(source_key)
    if str(source.get("scope") or "").upper() != "ORBITAL" or not source_url:
        raise NewsParserError("SWPC K-index parser requires a known ORBITAL product")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed SWPC K-index JSON: {exc}") from exc
    if not isinstance(payload, list):
        raise NewsParserError("SWPC K-index JSON must be an array")
    if len(payload) > 10000:
        raise NewsParserError("SWPC K-index JSON exceeds the bounded sample limit")
    value_key = "Kp" if source_key == "swpc_kp_summary_json" else (
        "k_index" if source_key == "swpc_boulder_k_json" else "estimated_kp"
    )
    candidates = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        observed_at = normalize_timestamp(row.get("time_tag"))
        try:
            value = float(row.get(value_key))
        except (TypeError, ValueError):
            continue
        if observed_at and 0 <= value <= 9:
            candidates.append((observed_at, value, row))
    if not candidates:
        return []
    observed_at, value, row = max(candidates, key=lambda candidate: candidate[0])
    threshold = float(source.get("min_k_index", 5.0))
    if value < threshold:
        return []
    measurement = "Boulder K-index" if source_key == "swpc_boulder_k_json" else "planetary Kp"
    noaa_scale = (
        f"G{min(5, int(value) - 4)}"
        if source_key == "swpc_kp_summary_json" and value >= 5 else None
    )
    hour_key = observed_at[:13]
    query = urlencode({"time": hour_key, "product": source_key})
    item = _normalize_item(source, {
        "title": f"SWPC {measurement} {value:g}",
        "url": f"{source_url}?{query}",
        "description": f"Official {measurement} measurement: {value:g}.",
        "published_at": observed_at,
    }, index=0)
    item["evidence"]["swpc_k_index"] = {
        "measurement": measurement,
        "value": value,
        "observed_at": observed_at,
        "threshold": threshold,
        "a_running": row.get("a_running") if source_key == "swpc_kp_summary_json" else None,
        "station_count": row.get("station_count")
        if source_key == "swpc_kp_summary_json" else None,
        "kp_label": row.get("kp") if source_key == "swpc_kp_1m_json" else None,
        "source_url": source_url,
        "source_kind": "regional" if source_key == "swpc_boulder_k_json" else "planetary",
        "observation_type": (
            "observed_3h_summary" if source_key == "swpc_kp_summary_json" else
            "estimated_1m" if source_key == "swpc_kp_1m_json" else "regional_local"
        ),
        "noaa_scale": noaa_scale,
        "scale_basis": "NOAA planetary Kp geomagnetic thresholds" if noaa_scale else None,
        "link_note": "Measurement-specific deep links are unavailable in this JSON product.",
    }
    item["evidence"]["orbital_identity"] = {
        "event_type": "geomagnetic_k_index",
        "object_id": f"{source_key}:{hour_key}",
        "noaa_scale": noaa_scale,
        "kp_window": hour_key if noaa_scale else None,
    }
    return [item]


def parse_swpc_aurora_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Summarize the OVATION grid only near explicitly configured locations."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    if str(source.get("scope") or "").upper() != "ORBITAL":
        raise NewsParserError("SWPC aurora parser requires ORBITAL scope")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed SWPC aurora JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("coordinates"), list):
        raise NewsParserError("SWPC aurora JSON requires a coordinates array")
    if len(payload["coordinates"]) > 70000:
        raise NewsParserError("SWPC aurora grid exceeds the bounded point limit")
    observed_at = normalize_timestamp(payload.get("Observation Time"))
    forecast_at = normalize_timestamp(payload.get("Forecast Time"))
    if not observed_at or not forecast_at:
        raise NewsParserError("SWPC aurora JSON requires observation and forecast times")
    locations = source.get("aurora_locations") or []
    if not isinstance(locations, list):
        raise NewsParserError("SWPC aurora locations must be configured as a list")
    items: list[dict[str, Any]] = []
    for location in locations[:8]:
        if not isinstance(location, dict):
            continue
        target_lon = float(location["longitude"]) % 360
        target_lat = float(location["latitude"])
        radius = float(location["radius_degrees"])
        minimum = float(location["min_intensity"])
        samples: list[tuple[float, float, float]] = []
        for point in payload["coordinates"]:
            if not isinstance(point, list) or len(point) != 3:
                continue
            try:
                longitude, latitude, value = (float(part) for part in point)
            except (TypeError, ValueError):
                continue
            distance_lon = abs((longitude % 360) - target_lon)
            distance_lon = min(distance_lon, 360 - distance_lon)
            if (
                abs(latitude - target_lat) <= radius and distance_lon <= radius
                and 0 <= value <= 100
            ):
                samples.append((value, longitude, latitude))
        if not samples:
            continue
        value, peak_lon, peak_lat = max(samples)
        if value < minimum:
            continue
        name = str(location["name"])
        scope = str(location["scope"])
        hour_key = forecast_at[:13]
        query = urlencode({"location": name, "forecast": hour_key})
        item = _normalize_item(source, {
            "title": f"SWPC aurora model near {name}: {value:g}",
            "url": f"{SWPC_AURORA_URL}?{query}",
            "description": (
                "OVATION model value near a configured location; "
                "not a visibility report."
            ),
            "published_at": observed_at,
            "tags": ["local-impact" if scope == "LOCAL" else "regional-impact"],
        }, index=len(items))
        item["evidence"]["swpc_aurora"] = {
            "observation_time": observed_at,
            "forecast_time": forecast_at,
            "location_name": name,
            "location_scope": scope,
            "grid_match_basis": "configured_coordinate_box",
            "radius_degrees": radius,
            "model_value": value,
            "minimum_value": minimum,
            "sample_count": len(samples),
            "peak_grid_point": {"longitude": peak_lon, "latitude": peak_lat},
            "source_url": SWPC_AURORA_URL,
            "model_only": True,
        }
        item["evidence"]["orbital_identity"] = {
            "event_type": "aurora_forecast",
            "object_id": f"{name.casefold()}:{hour_key}",
        }
        items.append(item)
    return items
