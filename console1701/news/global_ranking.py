"""Explainable GLOBAL event ranking from stored source metadata only."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any


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


def _source_signals(member: dict[str, Any]) -> dict[str, Any]:
    evidence = member.get("evidence") or {}
    gdacs = evidence.get("gdacs") or {}
    reliefweb = evidence.get("reliefweb_disaster") or {}
    report = evidence.get("reliefweb_report") or {}
    who = evidence.get("who_don") or {}
    usgs = evidence.get("usgs_earthquake") or {}
    nhc = evidence.get("nhc_rss") or {}
    identity = evidence.get("global_identity") or {}
    level = str(gdacs.get("alert_level") or "").lower()
    official_severity = {"red": 50, "orange": 35, "green": 12}.get(level, 0)
    if who:
        official_severity = max(official_severity, 20)
    if reliefweb.get("status") in {"current", "alert"}:
        official_severity = max(official_severity, 20)
    magnitude = usgs.get("magnitude")
    if isinstance(magnitude, (int, float)):
        official_severity = max(
            official_severity,
            45 if magnitude >= 7 else 35 if magnitude >= 6 else 20 if magnitude >= 5 else 0,
        )
    storm_type = str(nhc.get("storm_type") or "").lower()
    if storm_type == "hurricane":
        official_severity = max(official_severity, 30)
    elif storm_type == "tropical storm":
        official_severity = max(official_severity, 18)
    nhc_watch = bool(nhc.get("watch_warning_terms"))
    public_impact = max(
        30 if level == "red" else 18 if level == "orange" else 0,
        25 if isinstance(magnitude, (int, float)) and magnitude >= 7 else 0,
        18 if usgs.get("tsunami") is True else 0,
        15 if reliefweb.get("status") in {"current", "alert"} else 0,
        12 if nhc_watch else 0,
        min(35, max(0, _int(identity.get("public_impact_score")))),
    )
    humanitarian = max(
        25 if reliefweb.get("status") in {"current", "alert"} else 0,
        12 if report else 0,
        min(35, max(0, _int(identity.get("humanitarian_impact_score")))),
    )
    alert = bool(nhc_watch or level in {"red", "orange"} or usgs.get("tsunami") is True or
                 reliefweb.get("status") in {"current", "alert"})
    return {
        "official_severity": official_severity,
        "public_impact": public_impact,
        "humanitarian": humanitarian,
        "active_alert": alert,
        "source": evidence.get("source") or {},
        "ingest": evidence.get("ingest") or {},
        "identity": identity,
    }


def rank_global_event(
    group: dict[str, Any],
    members: list[dict[str, Any]],
    *,
    now: str,
) -> dict[str, Any]:
    """Score one matched event without counting duplicate family mentions as convergence."""
    observed = _time(now)
    times = [
        parsed for member in members
        if (parsed := _time(member.get("source_published_at") or member.get("last_seen_at")))
    ]
    latest = max(times) if times else None
    earliest = min(times) if times else None
    age_hours = (
        max(0, int((observed - latest).total_seconds() // 3600))
        if observed and latest else 72
    )
    span_hours = int((latest - earliest).total_seconds() // 3600) if latest and earliest else None
    signals = [_source_signals(member) for member in members]
    families = list(group.get("credited_families") or group.get("families") or [])
    family_counts = Counter(
        str(signal["source"].get("source_family") or "unknown") for signal in signals
    )
    official_families = (
        set(group["credited_official_families"])
        if "credited_official_families" in group else {
            str(signal["source"].get("source_family"))
            for signal in signals if signal["source"].get("official_status") == "official"
            and signal["source"].get("source_family")
        }
    )
    identities = [signal["identity"] for signal in signals]
    impact_tags = {
        str(tag).lower() for identity in identities
        for tag in identity.get("impact_tags") or []
    }
    recency = max(0, 20 - min(20, age_hours // 4))
    severity = max((signal["official_severity"] for signal in signals), default=0)
    diversity = min(40, len(families) * 6 + len(official_families) * 5)
    temporal = (
        10 if group.get("corroborated") and span_hours is not None
        and span_hours <= 24 else
        5 if group.get("corroborated") and span_hours is not None
        and span_hours <= 72 else 0
    )
    public_impact = max((signal["public_impact"] for signal in signals), default=0)
    geography = min(
        30,
        len(group.get("countries") or []) * 6 + len({
            str(region).lower() for member in members
            for region in (member.get("evidence") or {}).get("global", {}).get(
                "affected_regions", []
            )
            if (member.get("evidence") or {}).get("global", {}).get(
                "geography_basis"
            ) == "official_source_fields"
        }) * 3,
    )
    active_alert = 20 if any(signal["active_alert"] for signal in signals) else 0
    humanitarian = max((signal["humanitarian"] for signal in signals), default=0)
    domestic_impact = min(20, 10 * len(impact_tags & {
        "us", "national", "regional", "local"
    }))
    priority = min(10, max(
        (_int(signal["source"].get("priority"), 50) for signal in signals), default=0
    ) // 10)
    cluster_size = min(10, len({member["id"] for member in members}))
    duplicate_family = min(30, sum(max(0, count - 1) for count in family_counts.values()) * 2)
    duplicate_syndication = min(30, int(group.get("syndicated_duplicate_count") or 0) * 5)
    stale_source = min(25, sum(
        8 for signal in signals
        if signal["ingest"].get("source_health_state_at_ingest") in {
            "stale", "failing", "parser_failed"
        }
    ))
    low_confidence = 0 if group.get("corroborated") else (
        15 if group.get("identifiers") else 30
    )
    low_value_classes = {
        str(identity.get("public_value_class") or "").lower() for identity in identities
    }
    low_public_value = 40 if low_value_classes & {
        "routine", "opinion", "speculation", "generic_politics"
    } else 20 if "background" in low_value_classes else 0
    out_of_scope = 60 if any(identity.get("out_of_scope") is True for identity in identities) else 0
    rumor = 70 if any(identity.get("rumor") is True for identity in identities) else 0
    sensitivity_flags = sorted({
        key for member in members
        for key, value in (
            (member.get("evidence") or {}).get("sensitivity")
            if isinstance((member.get("evidence") or {}).get("sensitivity"), dict) else {}
        ).items() if value is True
    })
    conflict_adjacent = (
        "conflict_adjacent" in sensitivity_flags
        or any(((member.get("evidence") or {}).get("source") or {}).get(
            "conflict_sensitive"
        ) is True for member in members)
    )
    hard_suppression_flags = {
        "war_ticker", "graphic_violence", "casualty_speculation",
        "targeted_person_tracking", "private_distress", "doxxing", "source_laundering",
    }
    hard_flags = sorted(hard_suppression_flags & set(sensitivity_flags))
    independent_confirmed = bool(group.get("corroborated")) and len(families) >= 2
    official_confirmed = bool(official_families)
    elevation_allowed = official_confirmed or independent_confirmed
    factors = {
        "recency_score": recency,
        "official_severity_score": severity,
        "source_diversity_score": diversity,
        "temporal_proximity_score": temporal,
        "public_impact_score": public_impact,
        "geographic_reach_score": geography,
        "active_alert_score": active_alert,
        "humanitarian_impact_score": humanitarian,
        "us_or_local_impact_score": domestic_impact,
        "source_priority_score": priority,
        "cluster_size_score": cluster_size,
        "duplicate_family_penalty": duplicate_family,
        "duplicate_syndication_penalty": duplicate_syndication,
        "stale_source_penalty": stale_source,
        "low_confidence_penalty": low_confidence,
        "low_public_value_penalty": low_public_value,
        "out_of_scope_penalty": out_of_scope,
        "rumor_penalty": rumor,
    }
    bonuses = sum(value for key, value in factors.items() if key.endswith("_score"))
    penalties = sum(value for key, value in factors.items() if key.endswith("_penalty"))
    score_before_sensitivity = max(0, bonuses - penalties)
    sensitivity_penalty = (
        score_before_sensitivity if hard_flags else
        max(0, score_before_sensitivity - 20)
        if (conflict_adjacent or rumor) and not elevation_allowed else 0
    )
    factors["sensitivity_penalty"] = sensitivity_penalty
    score = score_before_sensitivity - sensitivity_penalty
    impact_basis = [
        "GDACS alert level" if any(
            str(((member.get("evidence") or {}).get("gdacs") or {}).get("alert_level") or "")
            .lower() in {"red", "orange"} for member in members
        ) else None,
        "USGS magnitude or tsunami flag" if any(
            signal["public_impact"] > 0 and
            (member.get("evidence") or {}).get("usgs_earthquake")
            for member, signal in zip(members, signals, strict=True)
        ) else None,
        "ReliefWeb active disaster" if any(
            ((member.get("evidence") or {}).get("reliefweb_disaster") or {}).get(
                "status"
            ) in {"current", "alert"} for member in members
        ) else None,
        "NHC advisory watch/warning terms (geography unverified)" if any(
            ((member.get("evidence") or {}).get("nhc_rss") or {}).get(
                "watch_warning_terms"
            ) for member in members
        ) else None,
        "parser-provided impact score" if any(
            identity.get("public_impact_score") for identity in identities
        ) else None,
    ]
    reasons = [
        f"{key.replace('_', ' ')} "
        f"{'subtracts' if key.endswith('_penalty') else 'adds'} {value}."
        for key, value in factors.items() if value
    ]
    return {
        "method": "bounded_stored_metadata_factors_v1",
        "score": score,
        "factors": factors,
        "reasons": reasons,
        "age_hours": age_hours,
        "span_hours": span_hours,
        "public_impact_basis": [value for value in impact_basis if value],
        "impact_tags": sorted(impact_tags),
        "sensitivity": {
            "score_before_sensitivity": score_before_sensitivity,
            "score_after_sensitivity": score,
            "conflict_adjacent": conflict_adjacent,
            "flags": sensitivity_flags,
            "hard_suppression_flags": hard_flags,
            "official_confirmed": official_confirmed,
            "independent_confirmed": independent_confirmed,
            "elevation_allowed": elevation_allowed and not hard_flags,
            "label": (
                "suppressed_sensitive_content" if hard_flags else
                "unconfirmed_conflict_or_rumor" if sensitivity_penalty else
                "confirmed_conflict_context" if conflict_adjacent else "ordinary"
            ),
        },
    }
