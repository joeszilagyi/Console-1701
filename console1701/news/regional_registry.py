from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


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
        raw_url="https://api.weather.gov/alerts/active",
        homepage_url="https://www.weather.gov/alerts",
        parser="nws_alerts_json",
        priority=100,
        interval_minutes=10,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="medium",
        retention_sensitivity="medium",
        verification_status="official_page_seen",
        future_phase="R1",
        expected_access_kind="official JSON API",
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
        expected_access_kind="public official API documentation",
        why_it_matters=(
            "Regional corridor, pass, and border-crossing impacts need transport context."
        ),
    ),
    RegionalSourceRegistryEntry(
        source_key="usgs_eq_geojson",
        source_name="USGS earthquake GeoJSON",
        source_family="usgs",
        source_class="official_seismic_volcano",
        adapter="official_api_json",
        kind="api_json",
        raw_url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php",
        homepage_url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php",
        priority=90,
        interval_minutes=5,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="low",
        retention_sensitivity="medium",
        verification_status="official_page_seen",
        future_phase="R1",
        expected_access_kind="public GeoJSON feed docs",
        why_it_matters="Washington seismic and Cascadia hazard coverage needs earthquake context.",
    ),
    RegionalSourceRegistryEntry(
        source_key="king_county_emergency_news",
        source_name="King County emergency news",
        source_family="county_emergency",
        source_class="county_emergency",
        adapter="rss_atom",
        kind="rss",
        raw_url="https://kingcounty.gov/en/dept/council/news/2025/05/04-emergency.aspx",
        homepage_url="https://kingcounty.gov/",
        parser="regional_news_rss",
        priority=90,
        interval_minutes=10,
        official_status="official",
        privacy_risk="low",
        policy_risk="low",
        parser_risk="low",
        retention_sensitivity="medium",
        verification_status="official_page_seen",
        future_phase="R2",
        expected_access_kind="candidate RSS/feed metadata",
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
