"""Deterministic REGIONAL event identity for currently verified fixture parsers."""

from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

_ZONE_RE = re.compile(r"\b[A-Z]{2}[A-Z]\d{3}\b")
_COUNTY_LABEL_RE = re.compile(r"[A-Za-z][A-Za-z .'-]{0,80} County\Z", re.I)


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
    water = evidence.get("usgs_water")
    wsf = evidence.get("wsf_alert")
    aqi = evidence.get("ecology_aqi")
    pierce = evidence.get("pierce_road_alert")
    nifc = evidence.get("nifc_imsr")
    wfigs = evidence.get("nifc_wfigs")
    nwcc_fire = evidence.get("nwcc_large_fire")
    dnr_fire = evidence.get("wa_dnr_fire_statistics")
    county_news = evidence.get("king_county_emergency")
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
    elif (source.get("id") == "nifc_wfigs_current_wa"
          and source.get("source_family") == "wildfire_federal"
          and source.get("official_status") == "official"
          and isinstance(wfigs, dict) and wfigs.get("unique_fire_identifier")):
        identity = f"nifc-imsr:{wfigs['unique_fire_identifier']}"
        event_type = "wildfire_update"
        matching_basis = "official_nifc_wfigs_unique_fire_identifier"
        confidence = "high"
        geography = {
            "basis": "official_WA_point_of_origin_state_and_county",
            "matched": True,
            "county": wfigs.get("county"),
            "fire_incident": wfigs.get("fire_name"),
        }
        match_tokens = [str(wfigs["unique_fire_identifier"])[:120],
                        str(wfigs.get("fire_name") or "")[:100]]
        public_impact_basis = (
            "NIFC WFIGS current/recent record; ActiveFireCandidate does not prove active "
            "fire or public impact"
        )
    elif isinstance(nifc, dict) and nifc.get("unique_fire_identifier"):
        identity = f"nifc-imsr:{nifc['unique_fire_identifier']}"
        event_type = "wildfire_update"
        matching_basis = "official_nifc_unique_fire_identifier"
        confidence = "high"
        geography = {
            "basis": "official_incident_prefix_and_point_bounds",
            "matched": True,
            "fire_incident": nifc.get("fire_name"),
            "latitude": nifc.get("latitude"),
            "longitude": nifc.get("longitude"),
        }
        match_tokens = [str(nifc["unique_fire_identifier"])[:120],
                        str(nifc.get("fire_name") or "")[:100]]
        public_impact_basis = (
            "Current IMSR listing and reported acres; active status and public impact unverified"
        )
    elif isinstance(nwcc_fire, dict) and nwcc_fire.get("normalized_fire_key"):
        identity = f"nifc-imsr:{nwcc_fire['normalized_fire_key']}"
        event_type = "wildfire_update"
        matching_basis = "official_nwcc_unit_number_start_year"
        confidence = "high"
        geography = {
            "basis": "official_WA_management_unit_not_fire_point",
            "matched": True,
            "fire_incident": nwcc_fire.get("fire_name"),
            "management_unit": nwcc_fire.get("unit_id"),
        }
        match_tokens = [str(nwcc_fire["normalized_fire_key"])[:120],
                        str(nwcc_fire.get("fire_name") or "")[:100]]
        public_impact_basis = (
            "NWCC large-fire record; edit time and containment do not prove current activity "
            "or public impact"
        )
    elif isinstance(dnr_fire, dict) and dnr_fire.get("fire_event_id"):
        identity = f"wa-dnr-fire:{dnr_fire['fire_event_id']}"
        event_type = "wildfire_update"
        matching_basis = "official_wa_dnr_fire_event_id"
        confidence = "high"
        geography = {
            "basis": "official_WA_DNR_county_label",
            "matched": True,
            "county": dnr_fire.get("county"),
            "fire_incident": dnr_fire.get("fire_name"),
        }
        match_tokens = [str(dnr_fire["fire_event_id"]),
                        str(dnr_fire.get("fire_name") or "")[:100]]
        public_impact_basis = (
            "WA DNR fire statistics; active state, update time and public impact unverified"
        )
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
        county_labels = [
            part.strip() for part in str(nws.get("area_desc") or "").split(";")
            if _COUNTY_LABEL_RE.fullmatch(part.strip())
        ][:8]
        geography = {
            "basis": "official_affected_zones",
            "matched": bool(zone_ids or nws.get("area_desc")),
            "zone_ids": zone_ids[:8],
            "county": county_labels,
            "area_desc": nws.get("area_desc"),
        }
        match_tokens = [str(nws["id"])[:120], *zone_ids[:8]]
        public_impact_basis = "NWS severity, urgency, and active-alert state"
    elif (source.get("id") == "king_county_emergency_news"
          and source.get("source_family") == "county_emergency"
          and source.get("official_status") == "official"
          and isinstance(county_news, dict)
          and county_news.get("classification") == "emergency_alert"
          and county_news.get("county") == "King County"
          and "flood" in {
              str(category).casefold() for category in county_news.get("categories") or []
          }
          and re.search(r"\bKing County\b", str(item.get("title") or ""), re.I)
          and re.search(r"\bflood\b", str(item.get("title") or ""), re.I)):
        identity = f"king-county-emergency:{item['url']}"
        event_type = "weather_alert"
        matching_basis = "official_county_flood_warning_title_and_category"
        confidence = "high"
        geography = {
            "basis": "official_county_publisher_and_explicit_title",
            "matched": True,
            "county": "King County",
        }
        match_tokens = ["King County", "Flood"]
        public_impact_basis = "County source warning title and Flood category"
    elif isinstance(water, dict) and water.get("gauge_id"):
        identity = f"usgs-water:{water['gauge_id']}:{water.get('observation_timestamp')}"
        event_type = "hydrology_observation"
        matching_basis = "official_gauge_id_and_observation_time"
        confidence = "high"
        geography = {
            "basis": "official_station_huc_and_county",
            "matched": bool((water.get("filter") or {}).get("matched")),
            "county": water.get("county"),
            "river_basin": water.get("huc8"),
        }
        match_tokens = [str(water["gauge_id"])[:120], str(water.get("huc8") or "")]
        public_impact_basis = "Observation only; no USGS flood-stage threshold in fixture"
    elif isinstance(aqi, dict) and aqi.get("site_id"):
        identity = f"ecology-aqi:{aqi['site_id']}:{aqi.get('sample_at')}"
        event_type = "air_quality_observation"
        matching_basis = "official_station_id_and_sample_time"
        confidence = "high"
        geography = {
            "basis": "official_site_name_allowlist",
            "matched": True,
            "city": "Seattle",
            "aqi_station": f"ecology:{aqi['site_id']}",
        }
        match_tokens = [str(aqi["site_id"]), str(aqi.get("aqi_category") or "")]
        public_impact_basis = "Ecology source-provided AQI category and value"
    elif isinstance(wsf, dict) and wsf.get("bulletin_id"):
        identity = f"wsf-bulletin:{wsf['bulletin_id']}"
        event_type = "ferry_alert"
        matching_basis = "official_wsf_bulletin_id"
        confidence = "high"
        routes = [str(value) for value in wsf.get("affected_route_ids") or []][:30]
        geography = {
            "basis": "official_affected_route_ids",
            "matched": bool(routes or wsf.get("all_routes")),
            "ferry_route_ids": routes,
            "all_routes": bool(wsf.get("all_routes")),
        }
        match_tokens = [str(wsf["bulletin_id"]), *routes]
        public_impact_basis = "WSF bulletin cancellation or delay text; no vessel inference"
    elif isinstance(pierce, dict) and str(pierce.get("alert_id") or "").isdigit():
        identity = f"pierce-road-alert:{pierce['alert_id']}"
        event_type = "traveler_alert"
        matching_basis = "official_pierce_road_alert_id"
        confidence = "high"
        geography = {
            "basis": "official_publisher_jurisdiction",
            "matched": True,
            "county": "Pierce",
        }
        match_tokens = [str(pierce["alert_id"])]
        public_impact_basis = "Pierce County road alert classification"
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
