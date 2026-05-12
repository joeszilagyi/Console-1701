from __future__ import annotations

from typing import Any

from console1701.config import NEWS_HOMEPAGE_SOURCE_KINDS


def evaluate_source_policy(config: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    news_cfg = config.get("news") or {}
    scope_cfg = ((news_cfg.get("scopes") or {}).get(source.get("scope")) or {})
    fetch_policy = news_cfg.get("fetch_policy") or {}
    url = str(source.get("url") or "").strip()
    kind = str(source.get("kind") or "").strip()
    auth_cfg = source.get("auth") if isinstance(source.get("auth"), dict) else None
    auth_required = bool(auth_cfg)
    auth_configured = bool(auth_cfg and any(str(value).strip() for value in auth_cfg.values()))
    homepage_allowed = bool(fetch_policy.get("allow_homepage_extractors"))
    is_local_fixture = url.startswith("file://")
    uses_homepage = kind in NEWS_HOMEPAGE_SOURCE_KINDS

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
    if uses_homepage and not homepage_allowed:
        notes.append("Homepage extraction is disabled by config.")
    if not is_local_fixture:
        notes.append("Fixture phase blocks non-file URLs from ingest.")
    if uses_homepage and is_local_fixture:
        notes.append("Homepage selectors are being tested against a local fixture only.")
    for note in source.get("evidence_notes") or []:
        if note not in notes:
            notes.append(str(note))

    return {
        "basis": basis,
        "policy_state": policy_state,
        "kind": kind,
        "scope": source.get("scope"),
        "enabled": bool(source.get("enabled")),
        "scope_enabled": bool(scope_cfg.get("enabled")),
        "auth_required": auth_required,
        "auth_configured": auth_configured,
        "homepage_extractor_allowed": homepage_allowed,
        "uses_homepage_extractor": uses_homepage,
        "robots_state": robots_state,
        "notes": notes,
    }
