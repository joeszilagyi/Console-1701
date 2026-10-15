"""Fixture-only WA Ecology hourly AQI metadata for three verified Seattle sites."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from console1701.news.normalize import bounded_text
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

QUERY_URL = (
    "https://gis.ecology.wa.gov/serverext/rest/services/AQ/"
    "AirQualityMonitoringHourlyResults/MapServer/0/query"
    "?where=HourPriorToLatest%3D1+AND+SiteId+IN+%2842%2C46%2C76%29"
    "&outFields=%2A&returnGeometry=false&resultRecordCount=3&f=json"
)
LAYER_URL = (
    "https://gis.ecology.wa.gov/serverext/rest/services/AQ/"
    "AirQualityMonitoringHourlyResults/MapServer/0"
)
SITES = {42: "Seattle-Beacon Hill", 46: "Seattle-South Park", 76: "Seattle-Duwamish"}
CATEGORIES = {
    "Good": (0, 50, 0),
    "Moderate": (51, 100, 0),
    "Unhealthy for Sensitive Groups": (101, 150, 12),
    "Unhealthy": (151, 200, 20),
    "Very Unhealthy": (201, 300, 30),
    "Hazardous": (301, 500, 40),
}
MAX_BYTES = 65_536


def _aqi(value: Any, *, field: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not 0 <= value <= 500:
        raise NewsParserError(f"Ecology {field} is not a valid AQI integer")
    return value


def parse_ecology_aqi_fixture(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if source.get("scope") != "REGIONAL" or source.get("id") != "wa_ecology_aqi":
        raise NewsParserError("Ecology AQI fixture requires its REGIONAL registry source")
    if not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("Ecology AQI parser is fixture-only")
    if source.get("official_url") != QUERY_URL:
        raise NewsParserError("Ecology AQI fixture requires the exact verified query URL")
    if len(payload_text.encode("utf-8")) > MAX_BYTES:
        raise PayloadTooLargeError("Ecology AQI fixture exceeds 64 KiB")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError("Malformed Ecology AQI JSON fixture") from exc
    if not isinstance(payload, dict) or payload.get("error") is not None:
        raise NewsParserError("Ecology AQI response contains an ArcGIS error")
    features = payload.get("features")
    if not isinstance(features, list) or len(features) > 3:
        raise NewsParserError("Ecology AQI fixture must have at most three features")
    seen: set[int] = set()
    items: list[dict[str, Any]] = []
    for index, feature in enumerate(features):
        attrs = feature.get("attributes") if isinstance(feature, dict) else None
        if not isinstance(attrs, dict):
            raise NewsParserError(f"Ecology AQI feature {index} has no attributes")
        site_id = attrs.get("SiteId")
        if type(site_id) is not int or site_id not in SITES or site_id in seen:
            raise NewsParserError(f"Ecology AQI feature {index} has invalid site identity")
        seen.add(site_id)
        if attrs.get("SiteName") != SITES[site_id] or attrs.get("HourPriorToLatest") != 1:
            raise NewsParserError(f"Ecology AQI feature {index} mismatches the latest site query")
        stamp = attrs.get("DateTime_PST")
        if type(stamp) is not int or not 1_600_000_000_000 <= stamp <= 2_200_000_000_000:
            raise NewsParserError(f"Ecology AQI feature {index} has invalid sample time")
        observed = datetime.fromtimestamp(stamp / 1000, tz=UTC).isoformat(timespec="seconds")
        value = _aqi(attrs.get("AQIValue"), field="AQIValue")
        category = bounded_text(attrs.get("AQICategory"), max_chars=40)
        if value is None or category not in CATEGORIES:
            raise NewsParserError(f"Ecology AQI feature {index} has invalid category/value")
        minimum, maximum, impact_score = CATEGORIES[category]
        if not minimum <= value <= maximum:
            raise NewsParserError(f"Ecology AQI feature {index} mismatches category band")
        pm25_aqi = _aqi(attrs.get("AQI_PM25"), field="AQI_PM25")
        pm25_cat = bounded_text(attrs.get("AQI_PM25_Cat"), max_chars=40)
        if pm25_cat is not None and pm25_cat not in CATEGORIES:
            raise NewsParserError(f"Ecology AQI feature {index} has invalid PM2.5 category")
        pm25_value = attrs.get("PM25_Value")
        if pm25_value is not None:
            if type(pm25_value) not in {int, float} or not 0 <= pm25_value <= 1000:
                raise NewsParserError(f"Ecology AQI feature {index} has invalid PM2.5 value")
        item = _normalize_item(source, {
            "title": f"{SITES[site_id]} air quality: {category} (AQI {value})",
            "url": LAYER_URL,
            "canonical_url": f"{LAYER_URL}?site_id={site_id}&sample_ms={stamp}",
            "description": "Hourly WA Ecology station AQI observation.",
            "published_at": observed,
            "tags": ["official", "regional", "air-quality", "aqi", category.lower()],
        }, index=index)
        item["evidence"]["ecology_aqi"] = {
            "site_id": site_id,
            "site_name": SITES[site_id],
            "city": "Seattle",
            "sample_at": observed,
            "hour_prior_to_latest": 1,
            "aqi_value": value,
            "aqi_category": category,
            "pm25_aqi": pm25_aqi,
            "pm25_category": pm25_cat,
            "pm25_concentration": pm25_value,
            "source_url": LAYER_URL,
            "query_url": QUERY_URL,
            "street_address_stored": False,
            "ranking": {"public_impact_score": impact_score,
                        "basis": "Ecology source-provided AQI category"},
        }
        item["evidence"]["regional_identity"] = {
            "aqi_station": f"ecology:{site_id}", "city": "Seattle",
        }
        items.append(item)
    return items
