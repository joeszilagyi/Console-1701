"""Disabled GLOBAL source inventory seeded from the checked-in design table."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from console1701.config import NEWS_SOURCE_KINDS

GLOBAL_SOURCE_CLASSES = set(
    """global_news heavy_open_data_candidate manual_review_only nonprofit_news
    official_air_quality official_aviation official_conflict_humanitarian
    official_cybersecurity official_development official_diplomacy official_disaster
    official_economic official_environment official_global_alert official_human_rights
    official_humanitarian official_maritime official_nuclear_safety official_public_health
    official_seismic_volcano official_transport official_tropical_cyclone official_tsunami
    official_water_flood official_weather_hazard official_wildfire public_media
    regional_global_news social_candidate source_health_only unofficial_aggregator
    wire_service""".split()
)
GLOBAL_ADAPTER_TYPES = set(
    """acled_api_candidate arcgis_feature_service_candidate cap_alerts
    csv_download_candidate data_catalog_candidate disaster_api_json ecdc_rss gdacs_api
    gdacs_feed gdelt_api_candidate geojson_feed hdx_hapi_json humanitarian_api_json
    imf_api_candidate local_file_fixture manual_review_only nasa_firms_api_candidate
    official_api_json reliefweb_api rss_atom source_health_probe_only
    static_html_headline_candidate who_api_json worldbank_api_json""".split()
)
GLOBAL_OFFICIAL_STATUSES = set(
    """NGO academic_data commercial fixture industry_association media nonprofit
    nonprofit_data official official_candidate open_data platform platform_media_account
    platform_official_account public_media publisher reference unofficial""".split()
)
GLOBAL_OFFICIAL_STATUSES.add("ngo")
GLOBAL_VERIFICATION_STATUSES = set(
    """assistant_seeded candidate_needs_verification candidate_policy_sensitive
    official_feed_seen official_page_seen reject_for_now unofficial_secondary user_seeded
    verified""".split()
)
GLOBAL_RISK_LEVELS = {"low", "medium", "high"}
GLOBAL_FUTURE_PHASES = {"G1", "G2", "G6", "G7", "G8", "G9", "G10"}
GLOBAL_AUTH_REQUIRED_SOURCE_KEYS = {
    "nasa_firms_api", "nasa_firms_web_services", "acled_home", "acled_api_docs",
    "marinetraffic_api", "reliefweb_disasters", "reliefweb_updates",
}
GLOBAL_HEAVY_ADAPTERS = {
    "acled_api_candidate", "arcgis_feature_service_candidate", "csv_download_candidate",
    "data_catalog_candidate", "gdelt_api_candidate", "hdx_hapi_json",
    "imf_api_candidate", "nasa_firms_api_candidate", "worldbank_api_json",
}
_RSS_ADAPTERS = {"cap_alerts", "ecdc_rss", "gdacs_feed", "rss_atom"}
_API_ADAPTERS = {
    "acled_api_candidate", "arcgis_feature_service_candidate", "disaster_api_json",
    "gdacs_api", "gdelt_api_candidate", "geojson_feed", "hdx_hapi_json",
    "humanitarian_api_json", "imf_api_candidate", "nasa_firms_api_candidate",
    "official_api_json", "reliefweb_api", "who_api_json", "worldbank_api_json",
}
_INTERVAL_RE = re.compile(r"^(\d+) (min|h)$")


def _interval_minutes(raw: str) -> int:
    if raw in {"manual", "none", "disabled", "scheduled"}:
        return 0
    if raw == "weekly":
        return 10080
    if raw == "monthly":
        return 43200
    match = _INTERVAL_RE.fullmatch(raw)
    if match is None:
        raise ValueError(f"Invalid GLOBAL source refresh interval: {raw}")
    value = int(match.group(1))
    return value * (60 if match.group(2) == "h" else 1)


def _source_kind(adapter: str) -> str:
    if adapter == "local_file_fixture":
        return "local_file_json"
    if adapter in _RSS_ADAPTERS:
        return "rss"
    if adapter in _API_ADAPTERS:
        return "api_json"
    return "homepage_headlines"


def _load_registry() -> tuple[dict[str, Any], ...]:
    path = Path(__file__).with_name("global_registry.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("GLOBAL source registry must be a list")
    entries: list[dict[str, Any]] = []
    keys: set[str] = set()
    for row in raw:
        if not isinstance(row, dict):
            raise ValueError("GLOBAL source registry entry must be a mapping")
        key = str(row.get("source_key") or "").strip()
        if not key or key in keys or row.get("scope") != "GLOBAL":
            raise ValueError(f"Invalid or duplicate GLOBAL source key: {key}")
        keys.add(key)
        for field, allowed in (
            ("source_class", GLOBAL_SOURCE_CLASSES),
            ("adapter", GLOBAL_ADAPTER_TYPES),
            ("official_status", GLOBAL_OFFICIAL_STATUSES),
            ("verification_status", GLOBAL_VERIFICATION_STATUSES),
            ("future_phase", GLOBAL_FUTURE_PHASES),
            *(
                (field, GLOBAL_RISK_LEVELS)
                for field in ("privacy_risk", "policy_risk", "parser_risk", "retention_sensitivity")
            ),
        ):
            if row.get(field) not in allowed:
                raise ValueError(f"Invalid GLOBAL {field} for {key}: {row.get(field)}")
        url = str(row.get("raw_url") or "")
        if not url.startswith("https://") and not (
            key == "global_fixture_pack_local" and url == "tests/fixtures/global/"
        ):
            raise ValueError(f"Invalid GLOBAL source URL for {key}: {url}")
        entry = dict(row)
        entry["priority"] = int(row["priority"])
        entry["interval_minutes"] = _interval_minutes(str(row["refresh_interval"]))
        kind = str(row.get("kind") or _source_kind(str(row["adapter"])))
        if kind not in NEWS_SOURCE_KINDS:
            raise ValueError(f"Invalid GLOBAL kind for {key}: {kind}")
        entry["kind"] = kind
        entry["enabled"] = False
        entry["parser"] = None
        entry["source_health_behavior"] = (
            "unsupported" if row["verification_status"] == "reject_for_now"
            else "policy_blocked" if row["verification_status"] == "candidate_policy_sensitive"
            else "disabled_until_verified"
        )
        entry["evidence_notes"] = [
            f"Expected source health: {entry['source_health_behavior']}.",
            str(row["why_it_matters"]),
        ]
        entries.append(entry)
    return tuple(entries)


GLOBAL_SOURCE_REGISTRY = _load_registry()
GLOBAL_SOURCE_FAMILIES = {str(entry["source_family"]) for entry in GLOBAL_SOURCE_REGISTRY}


def list_global_source_registry() -> list[dict[str, Any]]:
    return [dict(entry) for entry in GLOBAL_SOURCE_REGISTRY]


def get_global_source_registry_entry(source_key: str) -> dict[str, Any] | None:
    normalized = str(source_key).strip()
    return next(
        (dict(entry) for entry in GLOBAL_SOURCE_REGISTRY if entry["source_key"] == normalized),
        None,
    )


def global_registry_config_defaults(source_key: str) -> dict[str, Any] | None:
    entry = get_global_source_registry_entry(source_key)
    if entry is None:
        return None
    url = str(entry["raw_url"])
    if source_key == "global_fixture_pack_local":
        url = f"file://{url}"
    source = {
        "id": entry["source_key"],
        "name": entry["source_name"],
        "scope": "GLOBAL",
        "kind": entry["kind"],
        "enabled": False,
        "url": url,
        "official_status": entry["official_status"],
        "priority": entry["priority"],
        "interval_minutes": entry["interval_minutes"],
        "source_family": entry["source_family"],
        "source_class": entry["source_class"],
        "adapter": entry["adapter"],
        "privacy_risk": entry["privacy_risk"],
        "policy_risk": entry["policy_risk"],
        "parser_risk": entry["parser_risk"],
        "retention_sensitivity": entry["retention_sensitivity"],
        "verification_status": entry["verification_status"],
        "future_phase": entry["future_phase"],
        "expected_access_kind": entry["expected_access_kind"],
        "evidence_notes": [
            "Registry seed only; source is disabled.",
            *entry["evidence_notes"],
        ],
    }
    if source_key in GLOBAL_AUTH_REQUIRED_SOURCE_KEYS:
        source["auth"] = (
            {"appname": ""} if source_key.startswith("reliefweb_") else {"api_key": ""}
        )
    return source


def global_source_registry_summary() -> dict[str, Any]:
    counts: dict[str, dict[str, int]] = {
        "source_class_counts": {},
        "future_phase_counts": {},
        "official_status_counts": {},
        "verification_status_counts": {},
    }
    for entry in GLOBAL_SOURCE_REGISTRY:
        for field, key in (
            ("source_class_counts", "source_class"),
            ("future_phase_counts", "future_phase"),
            ("official_status_counts", "official_status"),
            ("verification_status_counts", "verification_status"),
        ):
            value = str(entry[key])
            counts[field][value] = counts[field].get(value, 0) + 1
    return {
        "scope": "GLOBAL",
        "enabled_by_default": False,
        "source_count": len(GLOBAL_SOURCE_REGISTRY),
        **counts,
    }
