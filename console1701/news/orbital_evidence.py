"""Bounded, auditable ORBITAL item evidence for the local detail view."""

from __future__ import annotations

from typing import Any


def build_orbital_evidence_contract(
    member: dict[str, Any], group: dict[str, Any], ranking: dict[str, Any],
    confidence: str,
) -> dict[str, Any]:
    evidence = member.get("evidence") or {}
    source = evidence.get("source") or {}
    identity = evidence.get("orbital_identity") or {}
    impact = evidence.get("orbital_impact") or {}
    basis = impact.get("basis") or {}
    ingest = evidence.get("ingest") or {}
    retention = evidence.get("retention") or {}
    policy = evidence.get("policy") or {}
    storage = evidence.get("storage") or {}
    penalties = {
        key: value for key, value in (ranking.get("factors") or {}).items()
        if key.endswith("_penalty")
    }
    return {
        "source_id": source.get("source_key"),
        "source_name": source.get("source_name"),
        "source_family": source.get("source_family"),
        "source_class": source.get("source_class"),
        "official_status": source.get("official_status"),
        "item_url": storage.get("url"),
        "canonical_url": storage.get("canonical_url"),
        "published_at": member.get("source_published_at"),
        "first_seen_at": member.get("first_seen_at"),
        "last_seen_at": member.get("last_seen_at"),
        "fetch_run_id": ingest.get("fetch_run_id"),
        "parser": source.get("parser"),
        "source_health_at_ingest": ingest.get("source_health_state_at_ingest"),
        "event_type": identity.get("event_type"),
        "event_confidence": confidence,
        "mission_label": identity.get("mission_name") or identity.get("mission_id"),
        "object_label": identity.get("object_id"),
        "safe_satellite_id": identity.get("safe_satellite_id"),
        "reentry_object_id": identity.get("reentry_object_id"),
        "source_keys": group.get("source_keys") or [],
        "source_families": group.get("families") or [],
        "source_diversity_basis": ranking.get("source_diversity_basis"),
        "matching_tokens": sorted({
            token for match in group.get("matches") or []
            for token in match.get("shared_tokens") or []
        }),
        "match_basis": [match.get("basis") or [] for match in group.get("matches") or []],
        "ranking_features": ranking.get("factors") or {},
        "ranking_reasons": ranking.get("reasons") or [],
        "operational_impact_basis": ranking.get("operational_impact_basis") or [],
        "public_impact_basis": ranking.get("public_impact_basis") or [],
        "impact_tags": impact.get("tags") or [],
        "impact_basis": basis,
        "geographic_impact_basis": {
            tag: reasons for tag, reasons in basis.items() if tag.endswith("_IMPACT")
        },
        "sensitivity_decision": ranking.get("sensitivity") or {},
        "penalties": penalties,
        "policy_state": policy.get("policy_state"),
        "policy_notes": policy.get("notes") or [],
        "retention_expires_at": retention.get("expires_at") or member.get("expires_at"),
    }
