"""Disabled COSMIC source candidates under the internal SYSTEM_SOLAR scope key."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SCIENCE_SOURCE_CLASSES = set(
    """astronomy_catalog_candidate astronomy_news auth_required_candidate
    heavy_archive_candidate literature_metadata_candidate manual_review_only
    official_astronomy_archive official_exoplanet official_exoplanet_archive
    official_gravitational_wave official_high_energy_astrophysics
    official_minor_body_science official_neutrino_candidate official_observatory_news
    official_planetary_data_archive official_planetary_science official_science_release
    official_solar_science official_solar_system_mission official_space_telescope
    official_supernova_transient official_transient_alert public_media_science
    science_news social_candidate source_health_only""".split()
)
SCIENCE_ADAPTERS = set(
    """ads_api_candidate astronomers_telegram_rss astroquery_candidate
    exoplanet_archive_api gaia_tap_candidate gcn_circular_candidate
    gcn_notice_candidate gracedb_api_candidate heasarc_api_candidate jpl_ssd_api
    local_file_fixture manual_review_only mast_api_candidate mpc_api nasa_api_json
    official_api_json pds_api_candidate rss_atom simbad_tap_candidate
    source_health_probe_only static_html_headline_candidate tap_adql_candidate
    tns_api_candidate vizier_tap_candidate""".split()
)
SCIENCE_OFFICIAL_STATUSES = set(
    """fixture nonprofit official official_candidate platform
    platform_official_account public_media publisher reference third_party_docs""".split()
)
SCIENCE_VERIFICATION_STATUSES = set(
    """assistant_seeded auth_required candidate_needs_verification
    candidate_policy_sensitive heavy_archive_risk official_page_seen reject_for_now
    unofficial_secondary user_seeded""".split()
)
SCIENCE_FUTURE_PHASES = {f"S{n}" for n in (2, 3, 7, 8, 9, 10, 11, 12)}
SCIENCE_RISK_LEVELS = {"low", "medium", "high"}
SCIENCE_HEAVY_ADAPTERS = {
    "ads_api_candidate", "astroquery_candidate", "exoplanet_archive_api",
    "gaia_tap_candidate", "heasarc_api_candidate", "mast_api_candidate",
    "pds_api_candidate", "simbad_tap_candidate", "tap_adql_candidate",
    "vizier_tap_candidate",
}
_RSS_ADAPTERS = {"astronomers_telegram_rss", "rss_atom"}
_API_ADAPTERS = {
    "exoplanet_archive_api", "gcn_circular_candidate", "gcn_notice_candidate",
    "gracedb_api_candidate", "heasarc_api_candidate", "jpl_ssd_api",
    "mast_api_candidate", "mpc_api", "nasa_api_json", "official_api_json",
    "pds_api_candidate", "tns_api_candidate",
}
_INTERVAL_RE = re.compile(r"^(\d+) (min|h)$")
_REQUIRED_TEXT = {
    "source_key", "source_name", "source_family", "source_class", "scope", "raw_url",
    "expected_access_kind", "adapter", "refresh_interval", "official_status",
    "verification_status", "why_it_matters", "future_phase",
}


def _interval_minutes(value: str) -> int:
    if value in {"disabled", "manual", "none"}:
        return 0
    match = _INTERVAL_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"Invalid science refresh interval: {value}")
    minutes = int(match.group(1)) * (60 if match.group(2) == "h" else 1)
    if minutes <= 0:
        raise ValueError(f"Invalid science refresh interval: {value}")
    return minutes


def _source_health_behavior(row: dict[str, Any]) -> str:
    if row["verification_status"] == "reject_for_now":
        return "unsupported"
    if row["source_class"] == "social_candidate":
        return "social_disabled"
    if row["verification_status"] == "auth_required" or row[
        "source_class"
    ] == "auth_required_candidate":
        return "auth_required"
    if row["source_class"] in {"heavy_archive_candidate", "astronomy_catalog_candidate"} or row[
        "adapter"
    ] in SCIENCE_HEAVY_ADAPTERS:
        return "heavy_archive_disabled"
    if row["adapter"] == "manual_review_only":
        return "manual_review_only"
    if row["adapter"] == "source_health_probe_only":
        return "source_health_only"
    if row["verification_status"] == "candidate_policy_sensitive":
        return "policy_blocked"
    return "disabled_until_verified"


def _source_kind(adapter: str) -> str:
    if adapter == "local_file_fixture":
        return "local_file_json"
    if adapter in _RSS_ADAPTERS:
        return "rss"
    if adapter in _API_ADAPTERS:
        return "api_json"
    return "reference_only"


def validate_science_registry(raw: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(raw, list):
        raise ValueError("Science source registry must be a list")
    seen: set[str] = set()
    entries: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict) or any(
            not isinstance(row.get(field), str) or not row[field].strip()
            for field in _REQUIRED_TEXT
        ):
            raise ValueError("Science source registry entry lacks required text")
        key = row["source_key"].strip()
        if key in seen or row["scope"] != "SYSTEM_SOLAR":
            raise ValueError(f"Invalid or duplicate science source key: {key}")
        seen.add(key)
        for field, choices in (
            ("source_class", SCIENCE_SOURCE_CLASSES),
            ("adapter", SCIENCE_ADAPTERS),
            ("official_status", SCIENCE_OFFICIAL_STATUSES),
            ("verification_status", SCIENCE_VERIFICATION_STATUSES),
            ("future_phase", SCIENCE_FUTURE_PHASES),
            *((field, SCIENCE_RISK_LEVELS) for field in (
                "privacy_risk", "policy_risk", "parser_risk", "retention_sensitivity"
            )),
        ):
            if row.get(field) not in choices:
                raise ValueError(f"Invalid science {field} for {key}: {row.get(field)}")
        url = row["raw_url"]
        parsed = urlsplit(url)
        if key == "system_solar_fixture_pack":
            if url != "tests/fixtures/system_solar/" or row["adapter"] != "local_file_fixture":
                raise ValueError("Invalid science fixture pack")
        elif parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError(f"Invalid science URL for {key}: {url}")
        try:
            priority = int(row["priority"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid science priority for {key}") from exc
        if not 0 <= priority <= 100:
            raise ValueError(f"Invalid science priority for {key}")
        entry = dict(row)
        entry["priority"] = priority
        entry["interval_minutes"] = _interval_minutes(row["refresh_interval"])
        entry["kind"] = _source_kind(row["adapter"])
        entry["enabled"] = False
        entry["parser"] = None
        entry["source_health_behavior"] = _source_health_behavior(row)
        entry["evidence_notes"] = [
            f"Expected source health: {entry['source_health_behavior']}.",
            str(row["why_it_matters"]),
        ]
        entries.append(entry)
    return tuple(entries)


SCIENCE_SOURCE_REGISTRY = validate_science_registry(
    json.loads(Path(__file__).with_name("science_registry.json").read_text(encoding="utf-8"))
)


def list_science_source_registry() -> list[dict[str, Any]]:
    return deepcopy(SCIENCE_SOURCE_REGISTRY)


def get_science_source_registry_entry(source_key: str) -> dict[str, Any] | None:
    return next(
        (deepcopy(row) for row in SCIENCE_SOURCE_REGISTRY if row["source_key"] == source_key),
        None,
    )


def science_candidate_health_summary() -> dict[str, Any]:
    """Describe disabled registry candidates separately from configured source health."""
    counts: dict[str, int] = {}
    for entry in SCIENCE_SOURCE_REGISTRY:
        state = str(entry["source_health_behavior"])
        counts[state] = counts.get(state, 0) + 1
    return {"candidate_count": len(SCIENCE_SOURCE_REGISTRY), "state_counts": counts}
