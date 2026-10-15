"""Fixture-only USGS latest-continuous observation and station metadata join."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from typing import Any

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

OBSERVATIONS_URL = (
    "https://api.waterdata.usgs.gov/ogcapi/v1/collections/latest-continuous/items"
    "?f=json&monitoring_location_id=USGS-12119000&parameter_code=00060,00065&limit=5"
)
LOCATION_URL = (
    "https://api.waterdata.usgs.gov/ogcapi/v1/collections/monitoring-locations/"
    "items/USGS-12119000?f=json"
)
GAUGE_ID = "USGS-12119000"
HUC8 = "17110012"
MAX_BYTES = 65_536


def _time(value: Any) -> datetime:
    stamp = normalize_timestamp(value)
    if not stamp:
        raise NewsParserError("USGS water fixture has an invalid observation timestamp")
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(UTC)


def _point(feature: dict[str, Any]) -> tuple[float, float]:
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        raise NewsParserError("USGS water feature requires Point geometry")
    coords = geometry.get("coordinates")
    if not isinstance(coords, list) or len(coords) != 2:
        raise NewsParserError("USGS water feature requires two coordinates")
    try:
        lon, lat = float(coords[0]), float(coords[1])
    except (TypeError, ValueError) as exc:
        raise NewsParserError("USGS water coordinates are invalid") from exc
    if (
        not math.isfinite(lon)
        or not math.isfinite(lat)
        or not (-180 <= lon <= 180 and -90 <= lat <= 90)
    ):
        raise NewsParserError("USGS water coordinates are out of range")
    return lon, lat


def parse_usgs_water_latest_fixture(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "REGIONAL" or source.get("id") != "usgs_water_api":
        raise NewsParserError("USGS water fixture requires its REGIONAL registry source")
    if not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("USGS water station join is fixture-only")
    if source.get("official_url") != OBSERVATIONS_URL:
        raise NewsParserError("USGS water fixture requires the exact official observation URL")
    gauges = source.get("gauge_ids", [GAUGE_ID])
    basins = source.get("huc8_allowlist", [HUC8])
    if gauges != [GAUGE_ID] or basins != [HUC8]:
        raise NewsParserError("USGS water gauge and HUC8 filters must use the verified allowlist")
    if len(payload_text.encode("utf-8")) > MAX_BYTES:
        raise PayloadTooLargeError("USGS water fixture exceeds 64 KiB")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError("Malformed USGS water JSON fixture") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("observation_url") != OBSERVATIONS_URL
        or payload.get("location_url") != LOCATION_URL
    ):
        raise NewsParserError("USGS water fixture requires both exact official source URLs")
    observations = payload.get("observations")
    location = payload.get("location")
    if not isinstance(observations, dict) or observations.get("type") != "FeatureCollection":
        raise NewsParserError("USGS water observations must be a FeatureCollection")
    if (
        not isinstance(location, dict)
        or location.get("type") != "Feature"
        or location.get("id") != GAUGE_ID
    ):
        raise NewsParserError("USGS water station identity is invalid")
    station = location.get("properties")
    if (
        not isinstance(station, dict)
        or station.get("id") != GAUGE_ID
        or station.get("state_name") != "Washington"
    ):
        raise NewsParserError("USGS water station metadata is invalid")
    huc12 = station.get("hydrologic_unit_code")
    if not isinstance(huc12, str) or len(huc12) != 12 or not huc12.isdigit() or huc12[:8] != HUC8:
        return []
    name = bounded_text(station.get("monitoring_location_name"), max_chars=120)
    county = bounded_text(station.get("county_name"), max_chars=80)
    if not name or not county:
        raise NewsParserError("USGS water station name or county is missing")
    point = _point(location)
    features = observations.get("features")
    if not isinstance(features, list) or len(features) > 5:
        raise NewsParserError("USGS water response exceeds its five-feature query limit")
    snapshot = _time(observations.get("timeStamp"))
    readings: dict[str, dict[str, Any]] = {}
    for feature in features:
        if (
            not isinstance(feature, dict)
            or feature.get("type") != "Feature"
            or _point(feature) != point
        ):
            raise NewsParserError("USGS water feature is not at the allowlisted station")
        props = feature.get("properties")
        if not isinstance(props, dict) or props.get("monitoring_location_id") != GAUGE_ID:
            raise NewsParserError("USGS water observation has a different gauge id")
        code = props.get("parameter_code")
        if code not in {"00060", "00065"} or code in readings:
            raise NewsParserError("USGS water parameter is unsupported or duplicated")
        expected_unit = "ft^3/s" if code == "00060" else "ft"
        if props.get("unit_of_measure") != expected_unit:
            raise NewsParserError("USGS water observation has an unexpected unit")
        try:
            value = float(props.get("value"))
        except (TypeError, ValueError) as exc:
            raise NewsParserError("USGS water observation value is invalid") from exc
        observed = _time(props.get("time"))
        age = (snapshot - observed).total_seconds() / 60
        if not math.isfinite(value) or value < 0 or age < -5:
            raise NewsParserError("USGS water observation value or age is invalid")
        readings[code] = {
            "value": value,
            "unit": expected_unit,
            "observed_at": observed.isoformat(),
            "age_minutes_at_snapshot": round(max(0, age), 1),
            "stale_at_snapshot": age > 120,
            "approval_status": bounded_text(props.get("approval_status"), max_chars=32),
            "qualifier": bounded_text(props.get("qualifier"), max_chars=80),
        }
    if not readings:
        return []
    latest = max(_time(row["observed_at"]) for row in readings.values())
    stage = readings.get("00065")
    flow = readings.get("00060")
    item = _normalize_item(
        source,
        {
            "title": f"USGS gauge observation: {name}",
            "url": LOCATION_URL,
            "description": (
                "Latest observed stage and streamflow metadata; flood category unavailable."
            ),
            "published_at": latest.isoformat(),
            "tags": ["official", "usgs", "regional", "hydrology", "observation"],
        },
        index=0,
    )
    item["evidence"]["usgs_water"] = {
        "gauge_id": GAUGE_ID,
        "river_name": "Cedar River",
        "station_name": name,
        "county": county,
        "state": "Washington",
        "latitude": point[1],
        "longitude": point[0],
        "huc12": huc12,
        "huc8": HUC8,
        "stage": stage,
        "streamflow": flow,
        "observation_timestamp": latest.isoformat(),
        "snapshot_at": snapshot.isoformat(),
        "stale_at_snapshot": all(row["stale_at_snapshot"] for row in readings.values()),
        "stage_category": None,
        "flood_status": "unknown_no_threshold",
        "source_url": LOCATION_URL,
        "observation_query_url": OBSERVATIONS_URL,
        "filter": {"gauge_ids": gauges, "huc8_allowlist": basins, "matched": True},
        "ranking": {
            "flood_severity_score": 0,
            "hydrology_attention_score": 0,
            "basis": "USGS latest observation has no flood-stage threshold",
        },
    }
    item["evidence"]["regional_identity"] = {
        "river_basin": HUC8,
        "county": county,
    }
    return [item]
