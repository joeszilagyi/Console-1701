"""Disabled ORBITAL source inventory from the checked-in design table."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from console1701.config import NEWS_SOURCE_KINDS

ORBITAL_SOURCE_CLASSES = set("""
astronomy_news commercial_launch_provider launch_event_api manual_review_only
 official_astronomy_data official_aurora official_conjunction_awareness
 official_crewed_spaceflight official_fireball official_iss official_launch
 official_minor_planet official_mission_news official_neo official_orbital_debris
 official_reentry official_satellite_catalog official_science_release
 official_solar_data official_space_agency_news official_space_safety
 official_space_weather official_space_weather_json official_transient_astronomy
 public_media_space restricted_auth_candidate social_candidate source_health_only
 space_news spaceflight_news_api unofficial_aggregator
""".split())
ORBITAL_ADAPTER_TYPES = set("""
arcgis_feature_service_candidate astronomy_tap_api_candidate celestrak_gp_json
 celestrak_satcat_csv_json celestrak_socrates_candidate cneos_api
 esa_reentry_page_candidate jpl_ssd_api launch_library_api local_file_fixture
 manual_review_only mpc_api nasa_api_json official_api_json rss_atom
 source_health_probe_only space_track_api_candidate spaceflight_news_api
 static_html_headline_candidate swpc_alerts_json swpc_json swpc_product_text
""".split())
ORBITAL_OFFICIAL_STATUSES = set("""
commercial_provider fixture nonprofit official official_candidate platform
 platform_official_account public_api public_media publisher reference unknown unofficial
""".split())
ORBITAL_VERIFICATION_STATUSES = set("""
assistant_seeded candidate_needs_verification candidate_policy_sensitive
 official_page_seen official_feed_seen reject_for_now restricted_auth_required
 unofficial_secondary user_seeded verified
""".split())
ORBITAL_RISK_LEVELS = {"low", "medium", "high"}
ORBITAL_FUTURE_PHASES = {"O1", "O2", "O6", "O7", "O8", "O9", "O10", "O11"}
ORBITAL_AUTH_REQUIRED_SOURCE_KEYS = {
    "space_track_home", "space_track_docs", "nasa_open_apis", "esa_reentry",
}
_API_ADAPTERS = {
    "astronomy_tap_api_candidate", "celestrak_gp_json", "celestrak_satcat_csv_json",
    "celestrak_socrates_candidate", "cneos_api", "jpl_ssd_api", "launch_library_api",
    "mpc_api", "nasa_api_json", "official_api_json", "space_track_api_candidate",
    "spaceflight_news_api", "swpc_alerts_json", "swpc_json",
}
_INTERVAL_RE = re.compile(r"^(\d+) (min|h)$")
_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _interval_minutes(raw: str) -> int:
    if raw in {"manual", "none", "disabled"}:
        return 0
    match = _INTERVAL_RE.fullmatch(raw)
    if match is None:
        raise ValueError(f"Invalid ORBITAL source refresh interval: {raw}")
    value = int(match.group(1))
    return value * (60 if match.group(2) == "h" else 1)


def _source_kind(adapter: str) -> str:
    if adapter == "local_file_fixture":
        return "local_file_json"
    if adapter == "rss_atom":
        return "rss"
    if adapter in _API_ADAPTERS:
        return "api_json"
    return "reference_only"


def _load_registry() -> tuple[dict[str, Any], ...]:
    path = Path(__file__).with_name("orbital_registry.json")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("ORBITAL source registry must be a list")
    entries: list[dict[str, Any]] = []
    keys: set[str] = set()
    for row in raw:
        if not isinstance(row, dict):
            raise ValueError("ORBITAL source registry entry must be a mapping")
        key = str(row.get("source_key") or "")
        family = str(row.get("source_family") or "")
        if (
            not _KEY_RE.fullmatch(key) or key in keys or row.get("scope") != "ORBITAL"
            or not _KEY_RE.fullmatch(family)
        ):
            raise ValueError(f"Invalid or duplicate ORBITAL source key/family: {key}")
        keys.add(key)
        for field, allowed in (
            ("source_class", ORBITAL_SOURCE_CLASSES),
            ("adapter", ORBITAL_ADAPTER_TYPES),
            ("official_status", ORBITAL_OFFICIAL_STATUSES),
            ("verification_status", ORBITAL_VERIFICATION_STATUSES),
            ("future_phase", ORBITAL_FUTURE_PHASES),
            *((name, ORBITAL_RISK_LEVELS) for name in (
                "privacy_risk", "policy_risk", "parser_risk", "retention_sensitivity"
            )),
        ):
            if row.get(field) not in allowed:
                raise ValueError(f"Invalid ORBITAL {field} for {key}: {row.get(field)}")
        url = str(row.get("raw_url") or "")
        if key == "orbital_fixture_pack":
            valid_url = url == "tests/fixtures/orbital/"
        elif key == "orbital_arcgis_reentry_candidate":
            valid_url = url == "docs/project/ORBITAL_ARCGIS_REENTRY_CANDIDATE_TBD"
        else:
            parts = urlsplit(url)
            valid_url = (
                parts.scheme == "https" and bool(parts.hostname) and not parts.username
                and not parts.password and not parts.fragment
            )
        if not valid_url:
            raise ValueError(f"Invalid ORBITAL source URL for {key}: {url}")
        try:
            priority = int(row["priority"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid ORBITAL priority for {key}") from exc
        if not 0 <= priority <= 100:
            raise ValueError(f"Invalid ORBITAL priority for {key}")
        adapter = str(row["adapter"])
        kind = _source_kind(adapter)
        if kind not in NEWS_SOURCE_KINDS:
            raise ValueError(f"Invalid ORBITAL kind for {key}: {kind}")
        entry = dict(row)
        entry["priority"] = priority
        entry["interval_minutes"] = _interval_minutes(str(row["refresh_interval"]))
        entry["kind"] = kind
        entry["enabled"] = False
        entry["parser"] = {
            "swpc_alerts_json": "swpc_alerts_json",
            "swpc_noaa_scales_json": "swpc_noaa_scales_json",
            "swpc_kp_summary_json": "swpc_kp_json",
            "swpc_kp_1m_json": "swpc_kp_json",
            "swpc_boulder_k_json": "swpc_kp_json",
            "swpc_aurora_json": "swpc_aurora_json",
            "swpc_xray_flux_summary": "swpc_xray_flares_json",
            "jpl_cad_api": "jpl_cad_json",
            "jpl_fireball_api": "jpl_fireball_json",
            "jpl_scout_api": "jpl_scout_json",
            "launch_library_upcoming": "launch_library_json",
            "launch_library_events": "launch_library_json",
            "spaceflight_news_articles": "spaceflight_news_json",
            "celestrak_iss_gp": "celestrak_iss_gp_json",
            "mpc_mpecs_api": "mpc_mpec_json",
            "nasa_rss_feeds": "nasa_orbital_rss",
            "nasa_iss_page": "nasa_orbital_rss",
            "nasa_spacestation_blog": "nasa_orbital_rss",
            "nasa_artemis": "nasa_orbital_rss",
            "nasa_artemis_blog": "nasa_orbital_rss",
            "nasa_kennedy_blog": "nasa_orbital_rss",
            "jpl_rss": "nasa_orbital_rss",
            "nasa_science_news": "nasa_orbital_rss",
            "esa_rss": "esa_orbital_rss",
            "esa_iss": "esa_orbital_rss",
        }.get(key)
        entry["source_health_behavior"] = (
            "unsupported" if row["verification_status"] == "reject_for_now" else
            "auth_required" if row["verification_status"] == "restricted_auth_required" else
            "policy_blocked" if row["verification_status"] == "candidate_policy_sensitive" else
            "manual_review_only" if adapter == "manual_review_only" else
            "disabled_until_verified"
        )
        entry["evidence_notes"] = [
            f"Expected source health: {entry['source_health_behavior']}.",
            str(row["why_it_matters"]),
        ]
        entries.append(entry)
    return tuple(entries)


ORBITAL_SOURCE_REGISTRY = _load_registry()
ORBITAL_SOURCE_FAMILIES = {str(entry["source_family"]) for entry in ORBITAL_SOURCE_REGISTRY}


def list_orbital_source_registry() -> list[dict[str, Any]]:
    return [dict(entry) for entry in ORBITAL_SOURCE_REGISTRY]


def get_orbital_source_registry_entry(source_key: str) -> dict[str, Any] | None:
    normalized = str(source_key).strip()
    return next(
        (dict(entry) for entry in ORBITAL_SOURCE_REGISTRY if entry["source_key"] == normalized),
        None,
    )


def orbital_registry_config_defaults(source_key: str) -> dict[str, Any] | None:
    entry = get_orbital_source_registry_entry(source_key)
    if entry is None:
        return None
    url = str(entry["raw_url"])
    if source_key == "orbital_fixture_pack":
        url = f"file://{url}"
    source = {
        "id": entry["source_key"],
        "name": entry["source_name"],
        "scope": "ORBITAL",
        "kind": entry["kind"],
        "enabled": False,
        "url": url,
        "official_status": entry["official_status"],
        "priority": entry["priority"],
        "interval_minutes": entry["interval_minutes"],
        "source_family": entry["source_family"],
        "source_class": entry["source_class"],
        "adapter": entry["adapter"],
        "parser": entry["parser"],
        "privacy_risk": entry["privacy_risk"],
        "policy_risk": entry["policy_risk"],
        "parser_risk": entry["parser_risk"],
        "retention_sensitivity": entry["retention_sensitivity"],
        "verification_status": entry["verification_status"],
        "future_phase": entry["future_phase"],
        "expected_access_kind": entry["expected_access_kind"],
        "evidence_notes": ["Registry seed only; source is disabled.", *entry["evidence_notes"]],
    }
    if source_key in ORBITAL_AUTH_REQUIRED_SOURCE_KEYS:
        source["auth"] = {"api_key": ""}
    return source


def orbital_source_registry_summary() -> dict[str, Any]:
    counts: dict[str, dict[str, int]] = {
        "source_class_counts": {},
        "future_phase_counts": {},
        "official_status_counts": {},
        "verification_status_counts": {},
    }
    for entry in ORBITAL_SOURCE_REGISTRY:
        for field, key in (
            ("source_class_counts", "source_class"),
            ("future_phase_counts", "future_phase"),
            ("official_status_counts", "official_status"),
            ("verification_status_counts", "verification_status"),
        ):
            value = str(entry[key])
            counts[field][value] = counts[field].get(value, 0) + 1
    return {
        "scope": "ORBITAL", "enabled_by_default": False,
        "source_count": len(ORBITAL_SOURCE_REGISTRY), **counts,
    }
