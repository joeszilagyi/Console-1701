"""Deterministic REGIONAL event identity for currently verified fixture parsers."""

from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

_ZONE_RE = re.compile(r"\b[A-Z]{2}[A-Z]\d{3}\b")


def _texts(values: Any, *, limit: int = 8) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text and text not in result:
            result.append(text[:120])
        if len(result) >= limit:
            break
    return result


def build_regional_event_contract(
    source: dict[str, Any], item: dict[str, Any], *, hashed_url: str
) -> dict[str, Any]:
    evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
    usgs = evidence.get("usgs_earthquake")
    nws = evidence.get("nws_alert")
    wsdot = evidence.get("wsdot_alert")
    identity = f"isolated:{source.get('id')}:{hashed_url}"
    event_type = "regional_headline"
    matching_basis = "isolated_url"
    confidence = "low"
    geography: dict[str, Any] = {"basis": "unverified_headline", "matched": False}
    match_tokens: list[str] = []
    public_impact_basis: str | None = None

    if isinstance(usgs, dict) and usgs.get("id"):
        identity = f"usgs-earthquake:{usgs['id']}"
        event_type = "earthquake"
        matching_basis = "official_usgs_event_id"
        confidence = "high"
        geography = {
            "basis": "official_point_with_configured_bounds",
            "matched": bool((usgs.get("filter") or {}).get("matched")),
            "place": usgs.get("place"),
            "latitude": usgs.get("latitude"),
            "longitude": usgs.get("longitude"),
            "filter": usgs.get("filter"),
        }
        match_tokens = [str(usgs["id"])[:120]]
        public_impact_basis = "USGS magnitude, felt reports, and alert level"
    elif isinstance(nws, dict) and nws.get("id"):
        identity = f"nws-alert:{nws['id']}"
        event_type = "weather_alert"
        matching_basis = "official_nws_alert_id"
        confidence = "high"
        zones = _texts(nws.get("affected_zones"))
        geocode = nws.get("geocode") if isinstance(nws.get("geocode"), dict) else {}
        zone_ids = _texts(geocode.get("UGC"))
        zone_ids.extend(
            zone for value in zones for zone in _ZONE_RE.findall(value) if zone not in zone_ids
        )
        geography = {
            "basis": "official_affected_zones",
            "matched": bool(zone_ids or nws.get("area_desc")),
            "zone_ids": zone_ids[:8],
            "area_desc": nws.get("area_desc"),
        }
        match_tokens = [str(nws["id"])[:120], *zone_ids[:8]]
        public_impact_basis = "NWS severity, urgency, and active-alert state"
    elif isinstance(wsdot, dict) and wsdot.get("alert_id"):
        identity = f"wsdot-alert:{wsdot['alert_id']}"
        event_type = "traveler_alert"
        matching_basis = "official_wsdot_alert_id"
        confidence = "high"
        routes = _texts(wsdot.get("route_tokens"))
        facilities = _texts(wsdot.get("facility_tokens"))
        geography = {
            "basis": "official_route_county_facility",
            "matched": bool(routes or facilities or wsdot.get("county")),
            "routes": routes,
            "facilities": facilities,
            "county": wsdot.get("county"),
            "region": wsdot.get("region"),
        }
        match_tokens = [str(wsdot["alert_id"])[:120], *routes, *facilities]
        public_impact_basis = "WSDOT route and travel-impact classification"
    else:
        local_news = evidence.get("local_news")
        if isinstance(local_news, dict):
            geography = {
                "basis": "headline_service_area_only",
                "matched": False,
                "service_areas": _texts(local_news.get("service_areas")),
            }

    event_key = "regional-" + sha256(identity.encode("utf-8")).hexdigest()[:24]
    return {
        "event_key": event_key,
        "event_type": event_type,
        "matching_basis": matching_basis,
        "confidence": confidence,
        "matching_tokens": match_tokens,
        "geography": geography,
        "public_impact_basis": public_impact_basis,
        "privacy_basis": "No article body stored; no inferred private location.",
        "source_family": str(source.get("source_family") or "").strip().lower() or None,
    }
