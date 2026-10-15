"""Explainable ORBITAL event ranking from bounded, stored source metadata."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from console1701.news.orbital_events import orbital_independent_family


def _time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _member_signals(member: dict[str, Any], observed: datetime | None) -> dict[str, Any]:
    evidence = member.get("evidence") or {}
    source = evidence.get("source") or {}
    identity = evidence.get("orbital_identity") or {}
    safety = evidence.get("orbital_safety") or {}
    swpc = evidence.get("swpc_alert") or {}
    scale = evidence.get("swpc_noaa_scale") or {}
    kp = evidence.get("swpc_k_index") or {}
    fireball = evidence.get("jpl_fireball") or {}
    event_type = str(identity.get("event_type") or "")
    scale_label = str(scale.get("scale") or swpc.get("noaa_scale") or "").upper()
    level = _int(scale_label[1:]) if len(scale_label) == 2 and scale_label[0] in "GRS" else 0
    official_severity = min(40, level * 8) if level else 0
    if kp.get("source_kind") == "planetary" and isinstance(kp.get("value"), (int, float)):
        official_severity = max(official_severity, min(40, max(0, int(kp["value"]) - 4) * 8))
    if safety.get("official_alert"):
        official_severity = max(official_severity, 18)
    if swpc.get("cancelled"):
        official_severity = 0
    alert_active = bool(safety.get("official_alert"))
    if swpc and observed:
        issued = _time(swpc.get("issued_at"))
        until = _time(swpc.get("valid_until"))
        alert_active = bool(
            alert_active and issued and 0 <= (observed - issued).total_seconds() <= 72 * 3600
            and (until is None or observed <= until)
        )
    operational = min(25, 5 * len(swpc.get("potential_impacts") or []))
    if safety.get("official_alert"):
        operational = max(operational, 10)
    if event_type in {"launch_update", "iss_update", "mission_update"}:
        operational = max(operational, 8)
    public = min(30, max(0, _int(identity.get("public_impact_score"))))
    if scale.get("period_kind") == "current" and level >= 3:
        public = max(public, 12)
    if fireball.get("estimated_impact_energy_kt") is not None:
        public = max(public, 8)  # Reported event, never inferred ground damage.
    operational_basis = [
        "SWPC source-reported potential impacts" if swpc.get("potential_impacts") else None,
        "Official SWPC alert" if safety.get("official_alert") else None,
        "Official agency mission/ISS update" if event_type in {
            "launch_update", "iss_update", "mission_update"
        } else None,
    ]
    public_basis = [
        "Parser-provided public impact score" if identity.get("public_impact_score") else None,
        "Official current NOAA scale G3 or above"
        if scale.get("period_kind") == "current" and level >= 3 else None,
        "JPL reported fireball energy, not ground damage"
        if fireball.get("estimated_impact_energy_kt") is not None else None,
    ]
    return {
        "source": source, "ingest": evidence.get("ingest") or {},
        "identity": identity, "safety": safety,
        "official_severity": official_severity,
        "operational_impact": operational,
        "public_impact": public,
        "operational_impact_basis": [value for value in operational_basis if value],
        "public_impact_basis": [value for value in public_basis if value],
        "active_window": bool(alert_active or
                              safety.get("official_current_scale") or
                              identity.get("active_launch_window")),
    }


def rank_orbital_event(
    group: dict[str, Any], members: list[dict[str, Any]], *, now: str
) -> dict[str, Any]:
    """Score source-backed events without counting repeat records as corroboration."""
    observed = _time(now)
    times = [
        parsed for member in members
        if (parsed := _time(member.get("source_published_at") or member.get("last_seen_at")))
    ]
    latest, earliest = (max(times), min(times)) if times else (None, None)
    age_hours = (
        max(0, int((observed - latest).total_seconds() // 3600))
        if observed and latest else 72
    )
    span_hours = int((latest - earliest).total_seconds() // 3600) if latest and earliest else None
    signals = [_member_signals(member, observed) for member in members]
    families = list(group.get("families") or [])
    family_counts = Counter(
        orbital_independent_family(signal["source"].get("source_family"))
        for signal in signals
    )
    official_families = {
        orbital_independent_family(signal["source"].get("source_family"))
        for signal in signals
        if signal["source"].get("official_status") == "official"
        and signal["source"].get("source_family")
    }
    identities = [signal["identity"] for signal in signals]
    tags = {
        str(tag).lower() for identity in identities for tag in identity.get("impact_tags") or []
    }
    recency = max(0, 24 - min(24, age_hours // 3))
    severity = max((signal["official_severity"] for signal in signals), default=0)
    diversity = min(30, len(families) * 5 + len(official_families) * 5)
    temporal = 8 if len(members) > 1 and span_hours is not None and span_hours <= 24 else (
        4 if len(members) > 1 and span_hours is not None and span_hours <= 72 else 0
    )
    operational = max((signal["operational_impact"] for signal in signals), default=0)
    public = max((signal["public_impact"] for signal in signals), default=0)
    active_window = 15 if any(signal["active_window"] for signal in signals) else 0
    priority = min(10, max(
        (_int(signal["source"].get("priority"), 50) for signal in signals), default=0
    ) // 10)
    cluster_size = min(8, len({member["id"] for member in members}))
    domestic = min(20, 5 * len(tags & {
        "national_impact", "regional_impact", "local_impact",
    }))
    global_impact = 8 if "global_impact" in tags else 0
    duplicate = min(30, sum(max(0, count - 1) for count in family_counts.values()) * 3)
    stale = min(25, sum(
        8 for signal in signals if signal["ingest"].get("source_health_state_at_ingest")
        in {"stale", "failing", "parser_failed"}
    ))
    low_confidence = 0 if group.get("corroborated") else (
        12 if group.get("identifiers") else 24
    )
    low_value = 30 if any(identity.get("public_value_class") in {
        "routine", "background", "opinion", "speculation"
    } for identity in identities) else 0
    out_of_scope = 60 if any(identity.get("out_of_scope") is True for identity in identities) else 0
    rumor = 70 if any(identity.get("rumor") is True for identity in identities) else 0
    sensitive_flags = sorted({
        key for signal in signals for key, value in signal["safety"].items() if value is True
        and key in {
            "tactical_tracking", "restricted_source", "classified_inference",
            "private_operator_monitoring", "object_surveillance", "sensitive_reentry",
            "debris_fear_framing", "social_only_claim", "launch_rumor",
            "neo_panic_language",
        }
    })
    hard_flags = sorted(set(sensitive_flags) & {
        "tactical_tracking", "restricted_source", "classified_inference",
        "private_operator_monitoring", "object_surveillance",
    })
    factors = {
        "recency_score": recency,
        "official_severity_score": severity,
        "source_diversity_score": diversity,
        "temporal_proximity_score": temporal,
        "operational_impact_score": operational,
        "public_impact_score": public,
        "active_alert_or_launch_window_score": active_window,
        "source_priority_score": priority,
        "cluster_size_score": cluster_size,
        "local_or_national_impact_score": domestic,
        "global_impact_score": global_impact,
        "duplicate_family_penalty": duplicate,
        "stale_source_penalty": stale,
        "low_confidence_penalty": low_confidence,
        "low_public_value_penalty": low_value,
        "out_of_scope_penalty": out_of_scope,
        "rumor_penalty": rumor,
    }
    bonuses = sum(value for key, value in factors.items() if key.endswith("_score"))
    penalties = sum(value for key, value in factors.items() if key.endswith("_penalty"))
    score_before_sensitivity = max(0, bonuses - penalties)
    sensitivity_penalty = score_before_sensitivity if hard_flags else (
        min(30, score_before_sensitivity) if sensitive_flags else 0
    )
    factors["sensitivity_penalty"] = sensitivity_penalty
    score = score_before_sensitivity - sensitivity_penalty
    operational_basis = sorted({
        reason for signal in signals for reason in signal["operational_impact_basis"]
    })
    public_basis = sorted({
        reason for signal in signals for reason in signal["public_impact_basis"]
    })
    return {
        "method": "bounded_orbital_metadata_factors_v1",
        "score": score,
        "factors": factors,
        "reasons": [
            f"{key.replace('_', ' ')} "
            f"{'subtracts' if key.endswith('_penalty') else 'adds'} {value}."
            for key, value in factors.items() if value
        ],
        "age_hours": age_hours,
        "span_hours": span_hours,
        "impact_tags": sorted(tags),
        "operational_impact_basis": operational_basis,
        "public_impact_basis": public_basis,
        "source_diversity_basis": (
            f"{len(families)} independent source families"
            if group.get("corroborated") else "not_correlated"
        ),
        "sensitivity": {
            "flags": sensitive_flags,
            "hard_suppression_flags": hard_flags,
            "score_before_sensitivity": score_before_sensitivity,
            "score_after_sensitivity": score,
            "label": "suppressed" if hard_flags else (
                "de_emphasized" if sensitive_flags else "ordinary"
            ),
        },
    }
