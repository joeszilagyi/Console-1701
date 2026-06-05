from __future__ import annotations

from typing import Any

from console1701.config import LOCAL_SOCIAL_SOURCE_FAMILIES, NEWS_HOMEPAGE_SOURCE_KINDS


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
    auth_required = bool(auth_cfg)
    auth_configured = bool(auth_cfg and any(str(value).strip() for value in auth_cfg.values()))
    is_local_fixture = url.startswith("file://")
    uses_homepage = kind in NEWS_HOMEPAGE_SOURCE_KINDS
    homepage_allowed = bool(fetch_policy.get("allow_homepage_extractors"))
    homepage_extractor_blocked = uses_homepage and not homepage_allowed
    local_policy = _local_policy(config, source)

    if is_local_fixture:
        policy_state = "allowed_fixture_only"
        basis = "local_fixture_only"
        robots_state = "not_applicable_local_file"
    else:
        policy_state = "blocked_fixture_phase"
        basis = "future_live_fetch"
        if uses_homepage:
            robots_state = "deferred_until_live_fetch"
        else:
            robots_state = "not_applicable_fixture_phase"

    notes: list[str] = []
    if not scope_cfg.get("enabled"):
        notes.append("Parent scope is disabled.")
    if not source.get("enabled"):
        notes.append("Source is disabled.")
    if auth_required and not auth_configured:
        notes.append("Auth is declared but no credential material is configured.")
    if homepage_extractor_blocked:
        notes.append("Homepage extraction is disabled by config.")
    if not is_local_fixture:
        notes.append("Fixture phase blocks non-file URLs from ingest.")
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
        "robots_state": robots_state,
        "social_source_blocked": bool(local_policy and local_policy.get("social_source_blocked")),
        "local": local_policy,
        "notes": notes,
    }
