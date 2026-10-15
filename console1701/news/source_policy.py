from __future__ import annotations

from typing import Any

from console1701.config import LOCAL_SOCIAL_SOURCE_FAMILIES, NEWS_HOMEPAGE_SOURCE_KINDS
from console1701.news.global_registry import (
    GLOBAL_AUTH_REQUIRED_SOURCE_KEYS,
    GLOBAL_HEAVY_ADAPTERS,
)
from console1701.news.national_registry import NATIONAL_AUTH_REQUIRED_SOURCE_KEYS
from console1701.news.official_http import is_supported_official_source
from console1701.news.orbital_registry import ORBITAL_AUTH_REQUIRED_SOURCE_KEYS

_ORBITAL_RESTRICTED_CLASSES = {
    "restricted_auth_candidate", "official_satellite_catalog",
    "official_conjunction_awareness",
}
_ORBITAL_MANUAL_ADAPTERS = {
    "manual_review_only", "source_health_probe_only", "static_html_headline_candidate",
    "swpc_product_text", "esa_reentry_page_candidate",
    "arcgis_feature_service_candidate", "astronomy_tap_api_candidate",
}
_ORBITAL_TOPIC_FLAGS = {
    "official_space_weather": "include_space_weather",
    "official_space_weather_json": "include_space_weather",
    "official_solar_data": "include_space_weather",
    "official_aurora": "include_aurora",
    "official_neo": "include_neo_close_approaches",
    "official_fireball": "include_fireballs",
    "official_launch": "include_launches",
    "commercial_launch_provider": "include_launches",
    "launch_event_api": "include_launches",
    "official_crewed_spaceflight": "include_crewed_spaceflight",
    "official_iss": "include_iss",
    "official_reentry": "include_reentries",
    "official_orbital_debris": "include_debris",
    "official_satellite_catalog": "include_satellite_catalog",
    "official_conjunction_awareness": "include_conjunction_awareness",
    "official_space_agency_news": "include_space_agency_news",
    "official_mission_news": "include_space_agency_news",
    "space_news": "include_spaceflight_news",
    "public_media_space": "include_spaceflight_news",
    "spaceflight_news_api": "include_spaceflight_news",
    "official_transient_astronomy": "include_astronomy_transients",
    "official_astronomy_data": "include_astronomy_transients",
}


def _local_policy(config: dict[str, Any], source: dict[str, Any]) -> dict[str, Any] | None:
    if str(source.get("scope") or "").upper() != "LOCAL":
        return None
    local_cfg = config.get("local") or {}
    source_family = str(source.get("source_family") or "").strip().lower() or None
    source_class = str(source.get("source_class") or "").strip().lower() or None
    is_social = source_class == "social_candidate" or source_family in LOCAL_SOCIAL_SOURCE_FAMILIES
    is_neighborhood_blog = source_class == "neighborhood_blog"
    return {
        "enabled": bool(local_cfg.get("enabled")),
        "default_place_label": str(local_cfg.get("default_place_label") or "Seattle"),
        "include_airport": bool(local_cfg.get("include_airport", True)),
        "include_port": bool(local_cfg.get("include_port", True)),
        "include_king_county_transit": bool(
            local_cfg.get("include_king_county_transit", True)
        ),
        "include_wsdot_seattle_corridors": bool(
            local_cfg.get("include_wsdot_seattle_corridors", True)
        ),
        "include_ferries": bool(local_cfg.get("include_ferries", True)),
        "hazard_radius_miles": int(local_cfg.get("hazard_radius_miles", 75)),
        "earthquake_min_magnitude": float(local_cfg.get("earthquake_min_magnitude", 3.0)),
        "allow_neighborhood_blogs": bool(local_cfg.get("allow_neighborhood_blogs")),
        "allow_social_sources": bool(local_cfg.get("allow_social_sources")),
        "source_family": source_family,
        "source_class": source_class,
        "adapter": source.get("adapter") or source.get("parser"),
        "verification_status": source.get("verification_status"),
        "official_status": source.get("official_status"),
        "future_phase": source.get("future_phase"),
        "expected_access_kind": source.get("expected_access_kind"),
        "policy_risk": source.get("policy_risk"),
        "parser_risk": source.get("parser_risk"),
        "retention_sensitivity": source.get("retention_sensitivity"),
        "is_social_source": is_social,
        "social_source_blocked": is_social and not bool(local_cfg.get("allow_social_sources")),
        "is_neighborhood_blog": is_neighborhood_blog,
    }


def evaluate_source_policy(config: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    news_cfg = config.get("news") or {}
    scope_cfg = ((news_cfg.get("scopes") or {}).get(source.get("scope")) or {})
    fetch_policy = news_cfg.get("fetch_policy") or {}
    url = str(source.get("url") or "").strip()
    kind = str(source.get("kind") or "").strip()
    auth_cfg = source.get("auth") if isinstance(source.get("auth"), dict) else None
    scope = str(source.get("scope") or "").upper()
    auth_required = bool(auth_cfg) or (
        scope == "NATIONAL" and str(source.get("id") or "") in NATIONAL_AUTH_REQUIRED_SOURCE_KEYS
    ) or (
        scope == "GLOBAL" and str(source.get("id") or "") in GLOBAL_AUTH_REQUIRED_SOURCE_KEYS
    ) or (
        scope == "ORBITAL" and str(source.get("id") or "") in ORBITAL_AUTH_REQUIRED_SOURCE_KEYS
    )
    auth_configured = bool(auth_cfg and any(str(value).strip() for value in auth_cfg.values()))
    is_local_fixture = url.startswith("file://")
    scope_policy_enabled = (
        bool((config.get("local") or {}).get("enabled"))
        if source.get("scope") == "LOCAL"
        else bool((config.get("regional") or {}).get("enabled"))
        if source.get("scope") == "REGIONAL"
        else bool((config.get("national") or {}).get("enabled"))
        if source.get("scope") == "NATIONAL"
        else bool((config.get("global") or {}).get("enabled"))
        if source.get("scope") == "GLOBAL"
        else bool((config.get("orbital") or {}).get("enabled"))
        if source.get("scope") == "ORBITAL"
        else False
    )
    is_allowed_official_http = (
        bool(fetch_policy.get("allow_official_http"))
        and scope_policy_enabled
        and is_supported_official_source(source)
    )
    uses_homepage = kind in NEWS_HOMEPAGE_SOURCE_KINDS
    homepage_allowed = bool(fetch_policy.get("allow_homepage_extractors"))
    global_cfg = config.get("global") or {}
    orbital_cfg = config.get("orbital") or {}
    homepage_extractor_blocked = uses_homepage and (
        not homepage_allowed
        or (scope == "GLOBAL" and not bool(global_cfg.get("allow_homepage_extractors")))
    )
    local_policy = _local_policy(config, source)
    source_family = str(source.get("source_family") or "").strip().lower()
    source_class = str(source.get("source_class") or "").strip().lower()
    is_social = source_class == "social_candidate" or source_family in LOCAL_SOCIAL_SOURCE_FAMILIES
    national_social_blocked = (
        scope == "NATIONAL"
        and is_social
        and not bool((config.get("national") or {}).get("include_social_sources"))
    )
    regional_social_blocked = (
        scope == "REGIONAL"
        and is_social
        and not bool((config.get("regional") or {}).get("allow_social_sources"))
    )
    global_social_blocked = (
        scope == "GLOBAL"
        and is_social
        and not bool(global_cfg.get("include_social_sources"))
    )
    global_heavy_source = scope == "GLOBAL" and (
        source_class == "heavy_open_data_candidate"
        or str(source.get("adapter") or "").strip().lower() in GLOBAL_HEAVY_ADAPTERS
    )
    global_heavy_source_blocked = global_heavy_source and not bool(
        global_cfg.get("allow_heavy_open_data_sources")
    )
    global_manual_review = scope == "GLOBAL" and str(
        source.get("adapter") or ""
    ).strip().lower() == "manual_review_only"
    global_reference_only = scope == "GLOBAL" and str(
        source.get("adapter") or ""
    ).strip().lower() == "source_health_probe_only"
    orbital_adapter = str(source.get("adapter") or "").strip().lower()
    orbital_class = str(source.get("source_class") or "").strip().lower()
    orbital_social_blocked = scope == "ORBITAL" and is_social and not bool(
        orbital_cfg.get("include_social_sources")
    )
    orbital_auth_policy_blocked = scope == "ORBITAL" and auth_required and not bool(
        orbital_cfg.get("allow_auth_required_sources")
    )
    orbital_restricted_blocked = scope == "ORBITAL" and (
        orbital_class in _ORBITAL_RESTRICTED_CLASSES
        or orbital_adapter in {"space_track_api_candidate", "celestrak_satcat_csv_json",
                               "celestrak_socrates_candidate"}
    ) and not bool(orbital_cfg.get("allow_restricted_sources"))
    orbital_tactical_blocked = scope == "ORBITAL" and orbital_class in {
        "official_satellite_catalog", "official_conjunction_awareness",
    } and not bool(orbital_cfg.get("allow_tactical_sources"))
    orbital_topic_flag = _ORBITAL_TOPIC_FLAGS.get(orbital_class)
    orbital_topic_blocked = scope == "ORBITAL" and bool(orbital_topic_flag) and not bool(
        orbital_cfg.get(orbital_topic_flag)
    )
    orbital_homepage_blocked = scope == "ORBITAL" and uses_homepage and not bool(
        orbital_cfg.get("allow_homepage_extractors")
    )
    orbital_manual = scope == "ORBITAL" and (
        orbital_adapter in _ORBITAL_MANUAL_ADAPTERS
        or orbital_class in _ORBITAL_RESTRICTED_CLASSES
        or (orbital_adapter and not source.get("parser")
            and orbital_adapter != "local_file_fixture")
    )
    reference_only = kind == "reference_only"
    gate_state = None
    if global_social_blocked:
        gate_state = "social_disabled"
    elif global_heavy_source_blocked:
        gate_state = "heavy_open_data_disabled"
    elif scope == "GLOBAL" and homepage_extractor_blocked:
        gate_state = "homepage_extract_disabled"
    elif global_manual_review:
        gate_state = "manual_review_only"
    elif reference_only or global_reference_only:
        gate_state = "unsupported"
    if scope == "ORBITAL":
        if not orbital_cfg.get("enabled"):
            gate_state = "policy_blocked"
        elif orbital_social_blocked:
            gate_state = "social_disabled"
        elif orbital_tactical_blocked:
            gate_state = "sensitivity_blocked"
        elif orbital_restricted_blocked:
            gate_state = "restricted_source_disabled"
        elif orbital_auth_policy_blocked or orbital_topic_blocked:
            gate_state = "policy_blocked"
        elif orbital_homepage_blocked:
            gate_state = "homepage_disabled"
        elif orbital_class in {
            "official_satellite_catalog", "official_conjunction_awareness",
        }:
            gate_state = "needs_scope_filter"
        elif orbital_class == "restricted_auth_candidate":
            gate_state = "needs_terms_review"
        elif reference_only and orbital_adapter == "source_health_probe_only":
            gate_state = "source_health_only"
        elif reference_only and orbital_adapter != "manual_review_only":
            gate_state = "unsupported"
        elif orbital_manual:
            gate_state = "manual_review_only"

    if is_local_fixture:
        policy_state = "allowed_fixture_only"
        basis = "local_fixture_only"
        robots_state = "not_applicable_local_file"
    elif is_allowed_official_http:
        policy_state = "allowed_official_http"
        basis = "explicit_official_https"
        robots_state = (
            "not_applicable_official_feed" if kind == "rss" else "not_applicable_official_api"
        )
    else:
        policy_state = "blocked_fixture_phase"
        basis = "future_live_fetch"
        if uses_homepage:
            robots_state = "deferred_until_live_fetch"
        else:
            robots_state = "not_applicable_fixture_phase"
    if gate_state:
        policy_state = gate_state
        basis = "source_gate"

    notes: list[str] = []
    if not scope_cfg.get("enabled"):
        notes.append("Parent scope is disabled.")
    if not source.get("enabled"):
        notes.append("Source is disabled.")
    if auth_required and not auth_configured:
        notes.append("Auth is declared but no credential material is configured.")
    if homepage_extractor_blocked:
        notes.append("Homepage extraction is disabled by config.")
    if not is_local_fixture and not is_allowed_official_http:
        notes.append("Official HTTP opt-in or endpoint allowlist blocks this URL from ingest.")
    if is_allowed_official_http:
        notes.append("Explicit news-scan only; no page-load or host-scan fetch.")
    if uses_homepage and is_local_fixture:
        notes.append("Homepage selectors are being tested against a local fixture only.")
    if local_policy:
        if not local_policy["enabled"]:
            notes.append("LOCAL Seattle policy layer is disabled by config.")
        if local_policy["is_social_source"] and not local_policy["allow_social_sources"]:
            notes.append("LOCAL social source allowance is disabled.")
        if (
            local_policy["is_neighborhood_blog"]
            and not local_policy["allow_neighborhood_blogs"]
        ):
            notes.append("LOCAL neighborhood blog allowance is disabled.")
    if national_social_blocked:
        notes.append("NATIONAL social source allowance is disabled.")
    if regional_social_blocked:
        notes.append("REGIONAL social source allowance is disabled.")
    if global_social_blocked:
        notes.append("GLOBAL social source allowance is disabled.")
    if global_heavy_source_blocked:
        notes.append("GLOBAL heavy open-data source allowance is disabled.")
    if scope == "GLOBAL" and homepage_extractor_blocked:
        notes.append("GLOBAL homepage extraction allowance is disabled.")
    if global_manual_review:
        notes.append("GLOBAL source requires manual review and has no ingest adapter.")
    if scope == "ORBITAL":
        if not orbital_cfg.get("enabled"):
            notes.append("ORBITAL parent policy is disabled.")
        if orbital_social_blocked:
            notes.append("ORBITAL social source allowance is disabled.")
        if orbital_auth_policy_blocked:
            notes.append("ORBITAL auth-required source allowance is disabled.")
        if orbital_restricted_blocked:
            notes.append("ORBITAL restricted source allowance is disabled.")
        if orbital_tactical_blocked:
            notes.append("ORBITAL tactical satellite source allowance is disabled.")
        if orbital_topic_blocked:
            notes.append(f"ORBITAL {orbital_topic_flag} topic is disabled.")
        if orbital_homepage_blocked:
            notes.append("ORBITAL homepage extraction allowance is disabled.")
        if orbital_manual:
            notes.append("ORBITAL source requires an explicit verified parser or manual review.")
    if reference_only or global_reference_only:
        notes.append(f"{scope} registry reference is for source health only.")
    for note in source.get("evidence_notes") or []:
        if note not in notes:
            notes.append(str(note))

    return {
        "basis": basis,
        "policy_state": policy_state,
        "kind": kind,
        "scope": source.get("scope"),
        "source_family": source.get("source_family"),
        "source_class": source.get("source_class"),
        "adapter": source.get("adapter") or source.get("parser"),
        "verification_status": source.get("verification_status"),
        "official_status": source.get("official_status"),
        "future_phase": source.get("future_phase"),
        "expected_access_kind": source.get("expected_access_kind"),
        "policy_risk": source.get("policy_risk"),
        "retention_sensitivity": source.get("retention_sensitivity"),
        "parser_risk": source.get("parser_risk"),
        "enabled": bool(source.get("enabled")),
        "scope_enabled": bool(scope_cfg.get("enabled")),
        "auth_required": auth_required,
        "auth_configured": auth_configured,
        "homepage_extractor_allowed": homepage_allowed,
        "uses_homepage_extractor": uses_homepage,
        "homepage_extractor_blocked": homepage_extractor_blocked,
        "global_heavy_source": global_heavy_source,
        "global_heavy_source_blocked": global_heavy_source_blocked,
        "gate_state": gate_state,
        "robots_state": robots_state,
        "social_source_blocked": bool(
            (local_policy and local_policy.get("social_source_blocked"))
            or national_social_blocked
            or regional_social_blocked
            or global_social_blocked
            or orbital_social_blocked
        ),
        "local": local_policy,
        "notes": notes,
    }
