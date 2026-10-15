"""Bounded NATIONAL event ranking from stored official and configured evidence."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _bounded_int(value: Any, maximum: int) -> int:
    try:
        return min(maximum, max(0, int(value)))
    except (TypeError, ValueError):
        return 0


def _member_signals(member: dict[str, Any], now: datetime | None) -> dict[str, Any]:
    evidence = member.get("evidence") or {}
    identity = evidence.get("national_identity") or {}
    nws = evidence.get("nws_alert") or {}
    usgs = evidence.get("usgs_earthquake") or {}
    nhtsa = evidence.get("nhtsa_recall") or {}
    cisa = evidence.get("cisa_kev") or {}
    advisory = evidence.get("cisa_advisory") or {}
    faa = evidence.get("faa_nas_status") or {}
    federal_register = evidence.get("federal_register") or {}
    govinfo = evidence.get("govinfo_publication") or {}
    source = evidence.get("source") or {}
    usgs_rank = usgs.get("ranking") or {}
    severity = max(
        {"Extreme": 45, "Severe": 32, "Moderate": 15, "Minor": 4}.get(
            str(nws.get("severity") or "").title(), 0
        ),
        35 if usgs.get("tsunami") is True else 0,
        _bounded_int(usgs_rank.get("national_severity_score"), 45),
        _bounded_int((nhtsa.get("ranking") or {}).get("vehicle_safety_score"), 35),
        _bounded_int((cisa.get("ranking") or {}).get("cyber_score"), 22),
        _bounded_int((advisory.get("ranking") or {}).get("cyber_score"), 35),
        _bounded_int((faa.get("ranking") or {}).get("aviation_impact_score"), 45),
        _bounded_int(identity.get("official_severity_score"), 45),
    )
    impact = max(
        30 if nhtsa.get("park_it") or nhtsa.get("park_outside") else
        18 if nhtsa else 0,
        25 if faa.get("events") else 0,
        20 if nws.get("instruction") else 0,
        15 if usgs.get("tsunami") is True else 0,
        _bounded_int(usgs_rank.get("national_felt_impact_score"), 25),
        _bounded_int((federal_register.get("ranking") or {}).get("public_impact_score"), 25),
        _bounded_int(identity.get("public_impact_score"), 35),
    )
    alert_active = False
    expiration = _time(nws.get("expires") or nws.get("ends"))
    if now and expiration and now < expiration and nws.get("status") == "Actual":
        alert_active = True
    if faa.get("events") and faa.get("source_update_at"):
        updated = _time(faa["source_update_at"])
        alert_active = alert_active or bool(
            updated and now and 0 <= (now - updated).total_seconds() <= 6 * 3600
        )
    return {
        "source": source,
        "identity": identity,
        "severity": severity,
        "public_impact": impact,
        "active_alert": alert_active,
        "publication_only": bool(govinfo) and not bool(
            nws or nhtsa or faa or cisa or advisory
        ),
        "health": str((evidence.get("ingest") or {}).get("source_health_state_at_ingest") or ""),
    }


def rank_national_event(
    group: dict[str, Any], members: list[dict[str, Any]], *, now: str
) -> dict[str, Any]:
    observed = _time(now)
    times = [parsed for member in members if (
        parsed := _time(member.get("source_published_at") or member.get("last_seen_at"))
    )]
    latest = max(times) if times else None
    earliest = min(times) if times else None
    age_hours = max(0, int((observed - latest).total_seconds() // 3600)) if (
        observed and latest
    ) else 72
    span_hours = int((latest - earliest).total_seconds() // 3600) if (
        latest and earliest
    ) else None
    signals = [_member_signals(member, observed) for member in members]
    families = list(group.get("families") or [])
    family_counts = Counter(
        str(signal["source"].get("source_family") or "unknown") for signal in signals
    )
    official_families = {
        str(signal["source"].get("source_family")) for signal in signals
        if signal["source"].get("official_status") == "official"
        and signal["source"].get("source_family")
    }
    identities = [signal["identity"] for signal in signals]
    syndicated_only = bool(group.get("matches")) and all(
        match.get("basis") in (["same_article_url"], ["same_syndication_id"])
        for match in group["matches"]
    )
    distinct_article_keys = {
        str((member.get("evidence") or {}).get("national_identity", {}).get(
            "syndication_id"
        ) or member.get("canonical_url") or member.get("url") or member["id"])
        for member in members
    }
    factors = {
        "recency_score": max(0, 20 - min(20, age_hours // 4)),
        "official_severity_score": max((s["severity"] for s in signals), default=0),
        "source_diversity_score": min(30, (
            1 if syndicated_only else len(families)
        ) * 5 + (
            min(1, len(official_families)) if syndicated_only else len(official_families)
        ) * 4),
        "temporal_proximity_score": (
            10 if group.get("corroborated") and span_hours is not None and span_hours <= 24
            else 5 if group.get("corroborated") and span_hours is not None and span_hours <= 72
            else 0
        ),
        "public_impact_score": max((s["public_impact"] for s in signals), default=0),
        "geographic_reach_score": min(30, 5 * (
            len(group.get("affected_states") or [])
            + len(group.get("affected_territories") or [])
        )
                                      + (8 if group.get("national_impact") else 0)
                                      + (5 if group.get("multi_state_impact") else 0)),
        "active_alert_score": 18 if any(s["active_alert"] for s in signals) else 0,
        "source_priority_score": min(10, max((
            _bounded_int(s["source"].get("priority"), 100) for s in signals
        ), default=0) // 10),
        "cluster_size_score": min(8, len(distinct_article_keys)),
        "local_regional_impact_score": min(20, max((
            _bounded_int(identity.get("local_regional_impact_score"), 20)
            for identity in identities
        ), default=0)),
        "duplicate_family_penalty": min(30, 3 * sum(
            max(0, count - 1) for count in family_counts.values()
        )),
        "syndicated_duplicate_penalty": min(24, 6 * (
            len(members) - len(distinct_article_keys)
        )),
        "stale_source_penalty": min(24, sum(
            8 for signal in signals
            if signal["health"] in {"stale", "failing", "failed", "parser_failed"}
        )),
        "low_confidence_penalty": 0 if group.get("corroborated") else (
            12 if group.get("identifiers") else 24
        ),
        "low_public_value_penalty": 35 if any(
            str(identity.get("public_value_class") or "").casefold() in {
                "routine", "opinion", "speculation", "generic_politics"
            } for identity in identities
        ) else 15 if all(s["publication_only"] for s in signals) else 0,
        "out_of_scope_penalty": 60 if any(
            identity.get("out_of_scope") is True for identity in identities
        ) else 0,
    }
    bonuses = sum(value for key, value in factors.items() if key.endswith("_score"))
    penalties = sum(value for key, value in factors.items() if key.endswith("_penalty"))
    score = max(0, bonuses - penalties)
    reasons = [
        f"{key.replace('_', ' ')} "
        f"{'subtracts' if key.endswith('_penalty') else 'adds'} {value}."
        for key, value in factors.items() if value
    ]
    return {
        "method": "bounded_national_stored_metadata_v1",
        "score": score,
        "factors": factors,
        "reasons": reasons,
        "age_hours": age_hours,
        "span_hours": span_hours,
        "public_impact_basis": [name for name, present in (
            ("NWS official instruction", any((m.get("evidence") or {}).get(
                "nws_alert", {}).get("instruction") for m in members)),
            ("NHTSA recall fields", any((m.get("evidence") or {}).get(
                "nhtsa_recall") for m in members)),
            ("FAA NAS active event metadata", any((m.get("evidence") or {}).get(
                "faa_nas_status", {}).get("events") for m in members)),
            ("Federal Register configured impact filter", any((m.get("evidence") or {}).get(
                "federal_register") for m in members)),
            ("explicit national impact evidence", any(identity.get(
                "public_impact_score") for identity in identities)),
        ) if present],
    }
