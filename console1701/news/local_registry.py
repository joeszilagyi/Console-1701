from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from console1701.config import (
    LOCAL_ADAPTER_TYPES,
    LOCAL_RETENTION_SENSITIVITIES,
    LOCAL_RISK_LEVELS,
    LOCAL_SOURCE_CLASSES,
    LOCAL_VERIFICATION_STATUSES,
    NEWS_SOURCE_KINDS,
)


@dataclass(frozen=True)
class LocalSourceRegistryEntry:
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
    scope: str = "LOCAL"

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


LOCAL_SOURCE_REGISTRY: tuple[LocalSourceRegistryEntry, ...] = (
    LocalSourceRegistryEntry(
        source_key="sfd_fire_911_dataset",
        source_name="Seattle Real-Time Fire 911 Calls dataset",
        source_family="sfd",
        source_class="official_open_data",
        adapter="socrata_json",
        kind="open_data_json",
        raw_url="https://data.seattle.gov/Public-Safety/Seattle-Real-Time-Fire-911-Calls/kzjm-xkqj",
        homepage_url="https://dev.socrata.com/foundry/data.seattle.gov/kzjm-xkqj",
        parser="sfd_fire_911_socrata",
        priority=90,
        interval_minutes=5,
        official_status="official",
        privacy_risk="high",
        policy_risk="low",
        parser_risk="low",
        retention_sensitivity="high",
        verification_status="candidate_needs_verification",
        future_phase="L6",
        expected_access_kind="Socrata dataset metadata",
        why_it_matters=(
            "Official SFD public call metadata is a strong LOCAL event-correlation source, "
            "subject to privacy redaction rules."
        ),
    ),
    LocalSourceRegistryEntry(
        source_key="alertseattle_feed",
        source_name="AlertSeattle RSS feed candidate",
        source_family="alertseattle",
        source_class="official_alert",
        adapter="rss_atom",
        kind="rss",
        raw_url="https://alert.seattle.gov/feed/",
        homepage_url="https://alert.seattle.gov/",
        parser="alertseattle_rss",
        priority=100,
        interval_minutes=10,
        official_status="official",
        privacy_risk="low",
        policy_risk="medium",
        parser_risk="low",
        retention_sensitivity="medium",
        verification_status="candidate_needs_verification",
        future_phase="L6",
        expected_access_kind="candidate RSS feed",
        why_it_matters="Primary city emergency alert metadata candidate if the feed verifies.",
    ),
    LocalSourceRegistryEntry(
        source_key="metro_service_advisories_rss",
        source_name="King County Metro service advisories RSS",
        source_family="metro",
        source_class="official_transport",
        adapter="rss_atom",
        kind="rss",
        raw_url="https://kingcounty.gov/en/dept/metro/rider-tools/service-advisories/rss",
        homepage_url="https://kingcounty.gov/en/dept/metro/rider-tools/service-advisories",
        parser="metro_rss",
        priority=85,
        interval_minutes=10,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="low",
        retention_sensitivity="medium",
        verification_status="candidate_needs_verification",
        future_phase="L6",
        expected_access_kind="candidate RSS feed",
        why_it_matters="Transit disruptions affect Seattle movement and commute decisions.",
    ),
    LocalSourceRegistryEntry(
        source_key="wsdot_traffic_api",
        source_name="WSDOT traffic API page",
        source_family="wsdot",
        source_class="official_transport",
        adapter="official_api_json",
        kind="api_json",
        raw_url="https://wsdot.wa.gov/traffic/api/",
        parser="wsdot_travel_alerts_json",
        priority=85,
        interval_minutes=10,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="candidate_needs_verification",
        future_phase="L6",
        expected_access_kind="public official API documentation",
        why_it_matters="Official state traveler data can explain Seattle corridor impacts.",
    ),
    LocalSourceRegistryEntry(
        source_key="nws_active_alerts_api",
        source_name="NWS active alerts API",
        source_family="nws",
        source_class="official_weather_hazard",
        adapter="official_api_json",
        kind="api_json",
        raw_url="https://api.weather.gov/alerts/active?area=WA",
        homepage_url="https://www.weather.gov/alerts",
        parser="nws_alerts_json",
        priority=95,
        interval_minutes=10,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="verified",
        future_phase="L6",
        expected_access_kind="documented official Washington GeoJSON alerts API",
        why_it_matters="Official active hazard alerts should rank highly when Seattle is affected.",
    ),
    LocalSourceRegistryEntry(
        source_key="usgs_earthquake_geojson",
        source_name="USGS earthquake GeoJSON feeds",
        source_family="usgs",
        source_class="official_weather_hazard",
        adapter="official_api_json",
        kind="api_json",
        raw_url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php",
        homepage_url="https://earthquake.usgs.gov/",
        priority=90,
        interval_minutes=5,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="low",
        retention_sensitivity="medium",
        verification_status="candidate_needs_verification",
        future_phase="L6",
        expected_access_kind="official GeoJSON feed docs",
        why_it_matters="Nearby or significant earthquakes should elevate in LOCAL hazard state.",
    ),
    LocalSourceRegistryEntry(
        source_key="city_light_outages_home",
        source_name="Seattle City Light outages page",
        source_family="city_light",
        source_class="official_utility",
        adapter="source_health_probe_only",
        kind="reference_only",
        raw_url="https://www.seattle.gov/city-light/outages",
        priority=85,
        interval_minutes=10,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="source_health_probe_only",
        future_phase="L7",
        expected_access_kind="public outage page and map web app",
        why_it_matters=(
            "Power outage context matters locally, the public outage page is verified, and a "
            "stable machine-readable endpoint remains unverified."
        ),
    ),
    LocalSourceRegistryEntry(
        source_key="faa_airport_status_sea",
        source_name="FAA airport status SEA page",
        source_family="faa",
        source_class="official_airport_port",
        adapter="source_health_probe_only",
        kind="reference_only",
        raw_url="https://www.faa.gov/airport-status/SEA",
        priority=90,
        interval_minutes=10,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="source_health_probe_only",
        future_phase="L6",
        expected_access_kind="public airport-status page and NAS Status XML",
        why_it_matters=(
            "SEA operational disruptions have local travel impact, and the FAA NAS Status XML page "
            "provides a machine-readable path for verified status research."
        ),
    ),
    LocalSourceRegistryEntry(
        source_key="west_seattle_blog_feed",
        source_name="West Seattle Blog feed",
        source_family="west_seattle_blog",
        source_class="neighborhood_blog",
        adapter="rss_atom",
        kind="rss",
        raw_url="https://westseattleblog.com/feed/",
        homepage_url="https://westseattleblog.com/",
        parser="local_blog_rss",
        priority=60,
        interval_minutes=15,
        official_status="independent_local",
        privacy_risk="medium",
        policy_risk="medium",
        parser_risk="low",
        retention_sensitivity="medium",
        verification_status="candidate_needs_verification",
        future_phase="L9",
        expected_access_kind="candidate RSS feed",
        why_it_matters="Hyperlocal reporting can corroborate major West Seattle disruptions.",
    ),
    LocalSourceRegistryEntry(
        source_key="reddit_seattle",
        source_name="Reddit r/Seattle",
        source_family="reddit",
        source_class="social_candidate",
        adapter="manual_review_only",
        kind="api_json",
        raw_url="https://www.reddit.com/r/Seattle/",
        priority=20,
        interval_minutes=0,
        official_status="platform",
        privacy_risk="high",
        policy_risk="high",
        parser_risk="high",
        retention_sensitivity="high",
        verification_status="candidate_policy_sensitive",
        future_phase="L10",
        expected_access_kind="platform community page/API candidate",
        why_it_matters="Community signal is policy-sensitive and remains disabled by default.",
    ),
)


_LOCAL_DESIGN_INTERVAL = re.compile(r"^(\d+) (min|h)$")
_LOCAL_OFFICIAL_STATUSES = {
    "independent_local", "local_media", "official", "official_candidate",
    "official_reference_candidate", "platform", "platform_official_account",
    "reference", "unofficial",
}
_LOCAL_FUTURE_PHASES = {"L1", "L2", "L6", "L7", "L8", "L9", "L10"}
_LOCAL_RSS_ADAPTERS = {"rss_atom", "wordpress_feed_candidate"}
_LOCAL_API_ADAPTERS = {
    "airport_status_json_or_xml", "arcgis_feature_service_candidate",
    "gtfs_realtime_alerts", "official_api_json",
}


def _design_interval_minutes(raw: str) -> int:
    if raw in {"manual", "none", "disabled"}:
        return 0
    match = _LOCAL_DESIGN_INTERVAL.fullmatch(raw)
    if match is None:
        raise ValueError(f"Invalid LOCAL design refresh interval: {raw}")
    count = int(match.group(1))
    return count * (60 if match.group(2) == "h" else 1)


def _design_kind(adapter: str) -> str:
    if adapter == "socrata_json":
        return "open_data_json"
    if adapter in _LOCAL_RSS_ADAPTERS:
        return "rss"
    if adapter in _LOCAL_API_ADAPTERS:
        return "api_json"
    if adapter == "static_html_headline_candidate":
        return "homepage_headlines"
    return "reference_only"


def _complete_local_registry(
    core: tuple[LocalSourceRegistryEntry, ...],
) -> tuple[LocalSourceRegistryEntry, ...]:
    raw = json.loads(Path(__file__).with_name("local_registry.json").read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("LOCAL design source inventory must be a list.")
    overrides = {entry.source_key: entry for entry in core}
    entries: list[LocalSourceRegistryEntry] = []
    seen: set[str] = set()
    for row in raw:
        if not isinstance(row, dict):
            raise ValueError("LOCAL design source entry must be an object.")
        key = str(row.get("source_key") or "")
        if not key or key in seen or row.get("scope") != "LOCAL":
            raise ValueError(f"Invalid or duplicate LOCAL design source key: {key}")
        seen.add(key)
        if key in overrides:
            entries.append(overrides[key])
            continue
        adapter = str(row["adapter"])
        entries.append(LocalSourceRegistryEntry(
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
    if not set(overrides).issubset(seen):
        raise ValueError("A verified LOCAL core source is missing from the design inventory.")
    return tuple(entries)


LOCAL_SOURCE_REGISTRY = _complete_local_registry(LOCAL_SOURCE_REGISTRY)


def list_local_source_registry() -> list[dict[str, Any]]:
    return [asdict(entry) for entry in LOCAL_SOURCE_REGISTRY]


def get_local_source_registry_entry(source_key: str) -> dict[str, Any] | None:
    normalized = str(source_key).strip()
    for entry in LOCAL_SOURCE_REGISTRY:
        if entry.source_key == normalized:
            return asdict(entry)
    return None


def local_registry_config_defaults(source_key: str) -> dict[str, Any] | None:
    normalized = str(source_key).strip()
    for entry in LOCAL_SOURCE_REGISTRY:
        if entry.source_key == normalized:
            return entry.to_config_source()
    return None


def local_source_registry_summary() -> dict[str, Any]:
    classes: dict[str, int] = {}
    phases: dict[str, int] = {}
    official_status_counts: dict[str, int] = {}
    verification: dict[str, int] = {}
    for entry in LOCAL_SOURCE_REGISTRY:
        classes[entry.source_class] = classes.get(entry.source_class, 0) + 1
        phases[entry.future_phase] = phases.get(entry.future_phase, 0) + 1
        official_status_counts[entry.official_status] = (
            official_status_counts.get(entry.official_status, 0) + 1
        )
        verification[entry.verification_status] = verification.get(entry.verification_status, 0) + 1
    return {
        "scope": "LOCAL",
        "enabled_by_default": False,
        "source_count": len(LOCAL_SOURCE_REGISTRY),
        "source_class_counts": classes,
        "future_phase_counts": phases,
        "official_status_counts": official_status_counts,
        "verification_status_counts": verification,
    }


def _validate_registry() -> None:
    seen: set[str] = set()
    for entry in LOCAL_SOURCE_REGISTRY:
        if entry.source_key in seen:
            raise RuntimeError(f"Duplicate LOCAL source registry key: {entry.source_key}")
        seen.add(entry.source_key)
        if entry.scope != "LOCAL":
            raise RuntimeError(f"{entry.source_key} must have LOCAL scope.")
        if entry.enabled:
            raise RuntimeError(f"{entry.source_key} must be disabled by default.")
        parts = urlsplit(entry.raw_url)
        if parts.scheme != "https" or not parts.hostname:
            raise RuntimeError(f"{entry.source_key} must have an HTTPS source URL.")
        if not 0 <= entry.priority <= 100 or entry.interval_minutes < 0:
            raise RuntimeError(f"{entry.source_key} has invalid priority or interval.")
        if entry.official_status not in _LOCAL_OFFICIAL_STATUSES:
            raise RuntimeError(f"{entry.source_key} has invalid official_status.")
        if entry.future_phase not in _LOCAL_FUTURE_PHASES:
            raise RuntimeError(f"{entry.source_key} has invalid future_phase.")
        if entry.source_class not in LOCAL_SOURCE_CLASSES:
            raise RuntimeError(f"{entry.source_key} has invalid source_class.")
        if entry.adapter not in LOCAL_ADAPTER_TYPES:
            raise RuntimeError(f"{entry.source_key} has invalid adapter.")
        if entry.kind not in NEWS_SOURCE_KINDS:
            raise RuntimeError(f"{entry.source_key} has invalid source kind.")
        if entry.privacy_risk not in LOCAL_RISK_LEVELS:
            raise RuntimeError(f"{entry.source_key} has invalid privacy_risk.")
        if entry.policy_risk not in LOCAL_RISK_LEVELS:
            raise RuntimeError(f"{entry.source_key} has invalid policy_risk.")
        if entry.parser_risk not in LOCAL_RISK_LEVELS:
            raise RuntimeError(f"{entry.source_key} has invalid parser_risk.")
        if entry.retention_sensitivity not in LOCAL_RETENTION_SENSITIVITIES:
            raise RuntimeError(f"{entry.source_key} has invalid retention_sensitivity.")
        if entry.verification_status not in LOCAL_VERIFICATION_STATUSES:
            raise RuntimeError(f"{entry.source_key} has invalid verification_status.")


_validate_registry()
