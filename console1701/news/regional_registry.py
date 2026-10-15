from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from console1701.config import (
    NEWS_SOURCE_KINDS,
    REGIONAL_ADAPTER_TYPES,
    REGIONAL_RISK_LEVELS,
    REGIONAL_SOURCE_CLASSES,
    REGIONAL_VERIFICATION_STATUSES,
)


@dataclass(frozen=True)
class RegionalSourceRegistryEntry:
    source_key: str
    source_name: str
    source_family: str
    source_class: str
    adapter: str
    kind: str
    raw_url: str
    priority: int
    interval_minutes: int
    official_status: str
    privacy_risk: str
    policy_risk: str
    parser_risk: str
    retention_sensitivity: str
    verification_status: str
    future_phase: str
    why_it_matters: str
    expected_access_kind: str
    homepage_url: str | None = None
    parser: str | None = None
    enabled: bool = False
    scope: str = "REGIONAL"

    def to_config_source(self) -> dict[str, Any]:
        source = {
            "id": self.source_key,
            "name": self.source_name,
            "scope": self.scope,
            "kind": self.kind,
            "enabled": False,
            "url": self.raw_url,
            "official_status": self.official_status,
            "priority": self.priority,
            "interval_minutes": self.interval_minutes,
            "source_family": self.source_family,
            "source_class": self.source_class,
            "adapter": self.adapter,
            "privacy_risk": self.privacy_risk,
            "policy_risk": self.policy_risk,
            "parser_risk": self.parser_risk,
            "retention_sensitivity": self.retention_sensitivity,
            "verification_status": self.verification_status,
            "future_phase": self.future_phase,
            "expected_access_kind": self.expected_access_kind,
            "evidence_notes": [
                f"Registry seed only; future_phase={self.future_phase}.",
                self.why_it_matters,
            ],
        }
        if self.homepage_url:
            source["homepage_url"] = self.homepage_url
        if self.parser:
            source["parser"] = self.parser
        return source


REGIONAL_SOURCE_REGISTRY: tuple[RegionalSourceRegistryEntry, ...] = (
    RegionalSourceRegistryEntry(
        source_key="nws_active_alerts_wa",
        source_name="NWS active alerts for Washington",
        source_family="nws",
        source_class="official_weather_hazard",
        adapter="official_api_json",
        kind="api_json",
        raw_url="https://api.weather.gov/alerts/active?area=WA",
        homepage_url="https://www.weather.gov/alerts",
        parser="nws_alerts_json",
        priority=100,
        interval_minutes=10,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="verified",
        future_phase="R1",
        expected_access_kind="documented official Washington GeoJSON alerts API",
        why_it_matters="Primary Washington weather-hazard source for regional alerting.",
    ),
    RegionalSourceRegistryEntry(
        source_key="wsdot_traveler_api",
        source_name="WSDOT traveler information API",
        source_family="wsdot",
        source_class="official_transport",
        adapter="official_api_json",
        kind="api_json",
        raw_url="https://wsdot.wa.gov/traffic/api/",
        homepage_url="https://wsdot.wa.gov/traffic/api/",
        parser="wsdot_travel_alerts_json",
        priority=95,
        interval_minutes=5,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="official_page_seen",
        future_phase="R1",
        expected_access_kind="documented JSON REST; assigned access code required",
        why_it_matters=(
            "Regional corridor, pass, and border-crossing impacts need transport context."
        ),
    ),
    RegionalSourceRegistryEntry(
        source_key="wsdot_highway_alerts_rss",
        source_name="WSDOT active highway alerts RSS",
        source_family="wsdot",
        source_class="official_transport",
        adapter="official_rss",
        kind="rss",
        raw_url="https://www.wsdot.wa.gov/traffic/api/HighwayAlerts/rss.aspx",
        homepage_url="https://www.wsdot.wa.gov/traffic/api/",
        parser="wsdot_highway_alerts_rss",
        priority=95,
        interval_minutes=30,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="verified",
        future_phase="R1",
        expected_access_kind="public official Highway Alerts RSS",
        why_it_matters="Public statewide current highway alerts without an API access code.",
    ),
    RegionalSourceRegistryEntry(
        source_key="usgs_eq_geojson",
        source_name="USGS earthquake GeoJSON",
        source_family="usgs",
        source_class="official_seismic_volcano",
        adapter="official_api_json",
        kind="api_json",
        raw_url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson",
        homepage_url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php",
        parser="usgs_earthquake_geojson",
        priority=90,
        interval_minutes=5,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="low",
        retention_sensitivity="medium",
        verification_status="verified",
        future_phase="R1",
        expected_access_kind="documented official M2.5+ past-day GeoJSON summary feed",
        why_it_matters="Washington seismic and Cascadia hazard coverage needs earthquake context.",
    ),
    RegionalSourceRegistryEntry(
        source_key="wa_ecology_aqi",
        source_name="WA Ecology AQI",
        source_family="ecology",
        source_class="official_air_quality",
        adapter="official_api_json",
        kind="api_json",
        raw_url=(
            "https://gis.ecology.wa.gov/serverext/rest/services/AQ/"
            "AirQualityMonitoringHourlyResults/MapServer/0/query"
            "?where=HourPriorToLatest%3D1+AND+SiteId+IN+%2842%2C46%2C76%29"
            "&outFields=%2A&returnGeometry=false&resultRecordCount=3&f=json"
        ),
        homepage_url="https://ecology.wa.gov/research-data/monitoring-assessment/air-quality-index",
        parser="ecology_aqi_fixture",
        priority=75,
        interval_minutes=30,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="verified",
        future_phase="R7",
        expected_access_kind="observed bounded ArcGIS hourly AQI JSON; fixture only",
        why_it_matters="Official Seattle station AQI without storing street addresses.",
    ),
    RegionalSourceRegistryEntry(
        source_key="nwcc_blog",
        source_name="NWCC Info blog",
        source_family="nwcc",
        source_class="official_wildfire",
        adapter="rss_atom",
        kind="rss",
        raw_url="https://nwccinfo.blogspot.com/feeds/posts/default",
        homepage_url="https://nwccinfo.blogspot.com/p/who-we-are.html",
        parser="nwcc_atom_fixture",
        priority=85,
        interval_minutes=30,
        official_status="official_candidate",
        privacy_risk="low",
        policy_risk="medium",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="verified",
        future_phase="R7",
        expected_access_kind="linked public Atom feed; fixture parsing only",
        why_it_matters="Interagency wildfire updates without inferred Washington impact.",
    ),
    RegionalSourceRegistryEntry(
        source_key="wsf_bulletins",
        source_name="WSF schedule bulletins",
        source_family="wsf",
        source_class="official_ferry",
        adapter="official_api_json",
        kind="api_json",
        raw_url="https://www.wsdot.wa.gov/ferries/api/schedule/rest/alerts",
        homepage_url="https://www.wsdot.com/ferries/schedule/bulletin.aspx",
        parser="wsf_alerts_fixture",
        priority=90,
        interval_minutes=10,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="official_page_seen",
        future_phase="R6",
        expected_access_kind="documented JSON alerts operation; API access code required",
        why_it_matters="Ferry cancellations and delays are core Puget Sound signals.",
    ),
    RegionalSourceRegistryEntry(
        source_key="usgs_water_api",
        source_name="USGS Water Data APIs",
        source_family="usgs_water",
        source_class="official_water_flood",
        adapter="hydrology_api_json",
        kind="api_json",
        raw_url=(
            "https://api.waterdata.usgs.gov/ogcapi/v1/collections/latest-continuous/items"
            "?f=json&monitoring_location_id=USGS-12119000&parameter_code=00060,00065&limit=5"
        ),
        homepage_url="https://api.waterdata.usgs.gov/docs/ogcapi/",
        parser="usgs_water_latest_fixture",
        priority=85,
        interval_minutes=15,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="verified",
        future_phase="R7",
        expected_access_kind="observed OGC JSON; fixture assembly only, no live join",
        why_it_matters="Source-backed Cedar River gauge observations without inferred flood stage.",
    ),
    RegionalSourceRegistryEntry(
        source_key="king_county_emergency_news",
        source_name="King County emergency news",
        source_family="county_emergency",
        source_class="county_emergency",
        adapter="rss_atom",
        kind="rss",
        raw_url="https://kcemergency.com/feed/",
        homepage_url="https://kcemergency.com/",
        parser="king_county_emergency_rss",
        priority=90,
        interval_minutes=30,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="low",
        retention_sensitivity="medium",
        verification_status="verified",
        future_phase="R2",
        expected_access_kind="verified official WordPress RSS feed; live ingest disabled",
        why_it_matters=(
            "County emergency communications are useful for regional public-impact alerts."
        ),
    ),
    RegionalSourceRegistryEntry(
        source_key="regional_news_rss",
        source_name="Regional news RSS",
        source_family="regional_news",
        source_class="regional_news",
        adapter="rss_atom",
        kind="rss",
        raw_url="https://example.invalid/regional-news.rss",
        homepage_url="https://example.invalid/",
        parser="regional_news_rss",
        priority=50,
        interval_minutes=15,
        official_status="independent_local",
        privacy_risk="medium",
        policy_risk="medium",
        parser_risk="low",
        retention_sensitivity="medium",
        verification_status="candidate_needs_verification",
        future_phase="R3",
        expected_access_kind="verified RSS feed",
        why_it_matters=(
            "Regional reporting can corroborate official alerts and public-impact events."
        ),
    ),
)


_REGIONAL_DESIGN_INTERVAL = re.compile(r"^(\d+) (min|h)$")
_REGIONAL_RSS_ADAPTERS = {"cap_alerts", "official_rss", "rss_atom", "wordpress_feed_candidate"}
_REGIONAL_API_ADAPTERS = {
    "airport_status_json_or_xml", "arcgis_feature_service_candidate", "geojson_feed",
    "gtfs_realtime_alerts", "hydrology_api_json", "official_api_json", "open511_json",
}
_REGIONAL_OFFICIAL_STATUSES = {
    "independent_local", "local_tv", "nonprofit_community", "nonprofit_media",
    "official", "official_candidate", "official_reference_candidate", "platform",
    "platform_official_account", "public_media", "reference", "regional_media",
}
_REGIONAL_FUTURE_PHASES = {"R1", "R2", "R3", "R6", "R7", "R8", "R9", "R10"}


def _design_interval_minutes(raw: str) -> int:
    if raw in {"manual", "none", "disabled"}:
        return 0
    match = _REGIONAL_DESIGN_INTERVAL.fullmatch(raw)
    if match is None:
        raise ValueError(f"Invalid REGIONAL design refresh interval: {raw}")
    count = int(match.group(1))
    return count * (60 if match.group(2) == "h" else 1)


def _design_kind(adapter: str) -> str:
    if adapter == "socrata_json":
        return "open_data_json"
    if adapter in _REGIONAL_RSS_ADAPTERS:
        return "rss"
    if adapter in _REGIONAL_API_ADAPTERS:
        return "api_json"
    if adapter == "static_html_headline_candidate":
        return "homepage_headlines"
    return "reference_only"


def _complete_regional_registry(
    core: tuple[RegionalSourceRegistryEntry, ...],
) -> tuple[RegionalSourceRegistryEntry, ...]:
    raw = json.loads(
        Path(__file__).with_name("regional_registry.json").read_text(encoding="utf-8")
    )
    if not isinstance(raw, list):
        raise ValueError("REGIONAL design source inventory must be a list.")
    overrides = {entry.source_key: entry for entry in core}
    entries: list[RegionalSourceRegistryEntry] = []
    seen: set[str] = set()
    for row in raw:
        if not isinstance(row, dict):
            raise ValueError("REGIONAL design source entry must be an object.")
        key = str(row.get("source_key") or "")
        if not key or key in seen or row.get("scope") != "REGIONAL":
            raise ValueError(f"Invalid or duplicate REGIONAL design source key: {key}")
        seen.add(key)
        if key in overrides:
            entries.append(overrides.pop(key))
            continue
        adapter = str(row["adapter"])
        entries.append(RegionalSourceRegistryEntry(
            source_key=key,
            source_name=str(row["source_name"]),
            source_family=str(row["source_family"]),
            source_class=str(row["source_class"]),
            adapter=adapter,
            kind=_design_kind(adapter),
            raw_url=str(row["raw_url"]),
            priority=int(row["priority"]),
            interval_minutes=_design_interval_minutes(str(row["refresh_interval"])),
            official_status=str(row["official_status"]),
            privacy_risk=str(row["privacy_risk"]),
            policy_risk=str(row["policy_risk"]),
            parser_risk=str(row["parser_risk"]),
            retention_sensitivity=str(row["retention_sensitivity"]),
            verification_status=str(row["verification_status"]),
            future_phase=str(row["future_phase"]),
            why_it_matters=str(row["why_it_matters"]),
            expected_access_kind=str(row["expected_access_kind"]),
        ))
    entries.extend(overrides.values())
    return tuple(entries)


REGIONAL_SOURCE_REGISTRY = _complete_regional_registry(REGIONAL_SOURCE_REGISTRY)


def _validate_registry() -> None:
    seen: set[str] = set()
    for entry in REGIONAL_SOURCE_REGISTRY:
        if entry.source_key in seen:
            raise RuntimeError(f"Duplicate REGIONAL source registry key: {entry.source_key}")
        seen.add(entry.source_key)
        if entry.scope != "REGIONAL" or entry.enabled:
            raise RuntimeError(f"{entry.source_key} must be disabled REGIONAL source.")
        parts = urlsplit(entry.raw_url)
        if parts.scheme != "https" or not parts.hostname:
            raise RuntimeError(f"{entry.source_key} must have an HTTPS source URL.")
        if not 0 <= entry.priority <= 100 or entry.interval_minutes < 0:
            raise RuntimeError(f"{entry.source_key} has invalid priority or interval.")
        for field, allowed in (
            ("source_class", REGIONAL_SOURCE_CLASSES),
            ("adapter", REGIONAL_ADAPTER_TYPES),
            ("kind", NEWS_SOURCE_KINDS),
            ("official_status", _REGIONAL_OFFICIAL_STATUSES),
            ("privacy_risk", REGIONAL_RISK_LEVELS),
            ("policy_risk", REGIONAL_RISK_LEVELS),
            ("parser_risk", REGIONAL_RISK_LEVELS),
            ("retention_sensitivity", REGIONAL_RISK_LEVELS),
            ("verification_status", REGIONAL_VERIFICATION_STATUSES),
            ("future_phase", _REGIONAL_FUTURE_PHASES),
        ):
            if getattr(entry, field) not in allowed:
                raise RuntimeError(f"{entry.source_key} has invalid {field}.")


_validate_registry()


def list_regional_source_registry() -> list[dict[str, Any]]:
    return [asdict(entry) for entry in REGIONAL_SOURCE_REGISTRY]


def get_regional_source_registry_entry(source_key: str) -> dict[str, Any] | None:
    normalized = str(source_key).strip()
    for entry in REGIONAL_SOURCE_REGISTRY:
        if entry.source_key == normalized:
            return asdict(entry)
    return None


def regional_registry_config_defaults(source_key: str) -> dict[str, Any] | None:
    normalized = str(source_key).strip()
    for entry in REGIONAL_SOURCE_REGISTRY:
        if entry.source_key == normalized:
            return entry.to_config_source()
    return None


def regional_source_registry_summary() -> dict[str, Any]:
    classes: dict[str, int] = {}
    phases: dict[str, int] = {}
    official_status_counts: dict[str, int] = {}
    verification: dict[str, int] = {}
    for entry in REGIONAL_SOURCE_REGISTRY:
        classes[entry.source_class] = classes.get(entry.source_class, 0) + 1
        phases[entry.future_phase] = phases.get(entry.future_phase, 0) + 1
        official_status_counts[entry.official_status] = (
            official_status_counts.get(entry.official_status, 0) + 1
        )
        verification[entry.verification_status] = verification.get(entry.verification_status, 0) + 1
    return {
        "scope": "REGIONAL",
        "enabled_by_default": False,
        "source_count": len(REGIONAL_SOURCE_REGISTRY),
        "source_class_counts": classes,
        "future_phase_counts": phases,
        "official_status_counts": official_status_counts,
        "verification_status_counts": verification,
    }
