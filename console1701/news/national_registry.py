"""Disabled NATIONAL source inventory seeded from the checked-in design table."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

NATIONAL_SOURCE_CLASSES = {
    "local_tv_radio_national",
    "national_news",
    "nonprofit_news",
    "official_air_quality",
    "official_alert",
    "official_aviation",
    "official_court_legal",
    "official_cybersecurity",
    "official_disaster",
    "official_economic",
    "official_emergency",
    "official_energy",
    "official_federal_civic",
    "official_food_safety",
    "official_hurricane",
    "official_public_health",
    "official_rail",
    "official_recall",
    "official_regulatory",
    "official_seismic_volcano",
    "official_transport",
    "official_water_flood",
    "official_weather_hazard",
    "official_wildfire",
    "public_media",
    "social_candidate",
    "source_health_only",
    "unofficial_aggregator",
    "wire_service",
}
NATIONAL_ADAPTER_TYPES = {
    "aviation_status_json_or_xml",
    "cap_alerts",
    "congress_api_candidate",
    "csv_download_candidate",
    "data_gov_catalog_candidate",
    "economic_api_json",
    "federal_register_api",
    "geojson_feed",
    "govinfo_rss",
    "hydrology_api_json",
    "manual_review_only",
    "official_api_json",
    "recall_api_json",
    "rss_atom",
    "source_health_probe_only",
    "static_html_headline_candidate",
}
NATIONAL_OFFICIAL_STATUSES = {
    "national_media",
    "nonprofit_media",
    "official",
    "official_candidate",
    "platform",
    "platform_official_account",
    "public_media",
    "reference",
    "unofficial",
}
NATIONAL_VERIFICATION_STATUSES = {
    "candidate_needs_verification",
    "candidate_policy_sensitive",
    "official_page_seen",
    "unofficial_secondary",
    "user_seeded",
}
NATIONAL_RISK_LEVELS = {"low", "medium", "high"}
NATIONAL_AUTH_REQUIRED_SOURCE_KEYS = {
    "airnow_api_docs",
    "bea_developers",
    "congress_api",
    "fred_api_docs",
}
_RSS_ADAPTERS = {"rss_atom", "govinfo_rss", "cap_alerts"}
_API_ADAPTERS = {
    "aviation_status_json_or_xml",
    "congress_api_candidate",
    "economic_api_json",
    "federal_register_api",
    "geojson_feed",
    "hydrology_api_json",
    "official_api_json",
    "recall_api_json",
}
_INTERVAL_RE = re.compile(r"^(\d+) (min|h)$")


def _interval_minutes(raw: str) -> int:
    if raw in {"manual", "none", "disabled", "scheduled"}:
        return 0
    if raw == "daily":
        return 1440
    match = _INTERVAL_RE.fullmatch(raw)
    if match is None:
        raise ValueError(f"Invalid NATIONAL source refresh interval: {raw}")
    value = int(match.group(1))
    return value * (60 if match.group(2) == "h" else 1)


def _source_kind(adapter: str) -> str:
    if adapter in _RSS_ADAPTERS:
        return "rss"
    if adapter in _API_ADAPTERS:
        return "api_json"
    return "homepage_headlines"


def _load_registry() -> tuple[dict[str, Any], ...]:
    path = Path(__file__).with_name("national_registry.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("NATIONAL source registry must be a list")
    entries: list[dict[str, Any]] = []
    keys: set[str] = set()
    for row in raw:
        if not isinstance(row, dict):
            raise ValueError("NATIONAL source registry entry must be a mapping")
        key = str(row.get("source_key") or "").strip()
        if not key or key in keys or row.get("scope") != "NATIONAL":
            raise ValueError(f"Invalid or duplicate NATIONAL source key: {key}")
        keys.add(key)
        for field, allowed in (
            ("source_class", NATIONAL_SOURCE_CLASSES),
            ("adapter", NATIONAL_ADAPTER_TYPES),
            ("official_status", NATIONAL_OFFICIAL_STATUSES),
            ("verification_status", NATIONAL_VERIFICATION_STATUSES),
            *(
                (field, NATIONAL_RISK_LEVELS)
                for field in ("privacy_risk", "policy_risk", "parser_risk", "retention_sensitivity")
            ),
        ):
            if row.get(field) not in allowed:
                raise ValueError(f"Invalid NATIONAL {field} for {key}: {row.get(field)}")
        phase = str(row.get("future_phase") or "")
        if not re.fullmatch(r"U(?:1|6|7|8|9|10)", phase):
            raise ValueError(f"Invalid NATIONAL future phase for {key}: {phase}")
        url = str(row.get("raw_url") or "")
        if not url.startswith("https://"):
            raise ValueError(f"Invalid NATIONAL source URL for {key}: {url}")
        entry = dict(row)
        entry["priority"] = int(row["priority"])
        entry["interval_minutes"] = _interval_minutes(str(row["refresh_interval"]))
        entry["kind"] = _source_kind(str(row["adapter"]))
        entry["enabled"] = False
        entry["parser"] = {
            "nws_active_alerts_api": "nws_alerts_json",
            "usgs_eq_geojson": "usgs_earthquake_geojson",
        }.get(key)
        entries.append(entry)
    return tuple(entries)


NATIONAL_SOURCE_REGISTRY = _load_registry()


def list_national_source_registry() -> list[dict[str, Any]]:
    return [dict(entry) for entry in NATIONAL_SOURCE_REGISTRY]


def get_national_source_registry_entry(source_key: str) -> dict[str, Any] | None:
    return next(
        (dict(entry) for entry in NATIONAL_SOURCE_REGISTRY if entry["source_key"] == source_key),
        None,
    )


def national_registry_config_defaults(source_key: str) -> dict[str, Any] | None:
    entry = get_national_source_registry_entry(source_key)
    if entry is None:
        return None
    source = {
        "id": entry["source_key"],
        "name": entry["source_name"],
        "scope": "NATIONAL",
        "kind": entry["kind"],
        "enabled": False,
        "url": entry["raw_url"],
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
        "evidence_notes": ["Registry seed only; source is disabled.", entry["why_it_matters"]],
    }
    if entry["parser"]:
        source["parser"] = entry["parser"]
    if source_key in NATIONAL_AUTH_REQUIRED_SOURCE_KEYS:
        source["auth"] = {"api_key": ""}
    return source


def national_source_registry_summary() -> dict[str, Any]:
    counts: dict[str, dict[str, int]] = {
        "source_class_counts": {},
        "future_phase_counts": {},
        "official_status_counts": {},
        "verification_status_counts": {},
    }
    for entry in NATIONAL_SOURCE_REGISTRY:
        for field, key in (
            ("source_class_counts", "source_class"),
            ("future_phase_counts", "future_phase"),
            ("official_status_counts", "official_status"),
            ("verification_status_counts", "verification_status"),
        ):
            value = str(entry[key])
            counts[field][value] = counts[field].get(value, 0) + 1
    return {
        "scope": "NATIONAL",
        "enabled_by_default": False,
        "source_count": len(NATIONAL_SOURCE_REGISTRY),
        **counts,
    }
