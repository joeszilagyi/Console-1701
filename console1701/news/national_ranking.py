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
    source = evidence.get("source") or {}
    family = str(source.get("source_family") or "").casefold()
    nws = (evidence.get("nws_alert") or {}) if family == "nws" else {}
    usgs = (evidence.get("usgs_earthquake") or {}) if family == "usgs" else {}
    nhtsa = (evidence.get("nhtsa_recall") or {}) if family == "nhtsa" else {}
    cpsc = (evidence.get("cpsc_recall") or {}) if family == "cpsc" else {}
    cisa = (evidence.get("cisa_kev") or {}) if family == "cisa" else {}
    advisory = (evidence.get("cisa_advisory") or {}) if family == "cisa" else {}
    faa = (evidence.get("faa_nas_status") or {}) if family == "faa" else {}
    federal_register = (
        (evidence.get("federal_register") or {}) if family == "federal_register" else {}
    )
    nhc = (evidence.get("nhc_rss") or {}) if family == "noaa_nhc" else {}
    fsis = (evidence.get("fsis_recall") or {}) if family == "fsis" else {}
    fema = (evidence.get("openfema_declaration") or {}) if family == "fema" else {}
    govinfo = evidence.get("govinfo_publication") or {}
    usgs_rank = usgs.get("ranking") or {}
    nhc_type = str(nhc.get("storm_type") or "").casefold()
    fsis_class_i = (fsis.get("current_notice") is True
                    and fsis.get("recall_classification") == "Class I")
    fsis_public_alert = (fsis.get("current_notice") is True
                         and fsis.get("recall_type") == "Public Health Alert")
    cpsc_risk = set(cpsc.get("risk_indicators") or [])
    impact_basis: list[str] = []
    if nws.get("instruction"):
        impact_basis.append("NWS official instruction")
    if nhtsa:
        impact_basis.append("NHTSA recall fields")
    if faa.get("events"):
        impact_basis.append("FAA NAS event metadata")
    if usgs.get("tsunami") is True or _bounded_int(
        usgs_rank.get("national_felt_impact_score"), 25
    ):
        impact_basis.append("USGS earthquake fields")
    if _bounded_int((federal_register.get("ranking") or {}).get("public_impact_score"), 25):
        impact_basis.append("Federal Register configured impact filter")
    if cpsc:
        impact_basis.append("CPSC source-stated recall risk")
    if cisa:
        impact_basis.append("CISA known-exploited vulnerability")
    if advisory.get("directive_flag") is True or advisory.get("kind") == "cyber_alert":
        impact_basis.append("CISA official alert or directive")
    if fsis_class_i or fsis_public_alert:
        impact_basis.append("FSIS current high-risk recall or public health alert")
    if fema.get("recent_declaration_at_refresh") is True:
        impact_basis.append("FEMA recent declaration")
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
        25 if nhc_type == "hurricane" else 15 if nhc_type == "tropical storm" else 0,
        25 if fsis_class_i else 0,
    )
    impact = max(
        30 if nhtsa.get("park_it") or nhtsa.get("park_outside") else
        18 if nhtsa else 0,
        25 if faa.get("events") else 0,
        20 if nws.get("instruction") else 0,
        15 if usgs.get("tsunami") is True else 0,
        _bounded_int(usgs_rank.get("national_felt_impact_score"), 25),
        _bounded_int((federal_register.get("ranking") or {}).get("public_impact_score"), 25),
        25 if "death_risk" in cpsc_risk else 18 if "injury_risk" in cpsc_risk else
        10 if cpsc else 0,
        12 if cisa else 0,
        25 if advisory.get("directive_flag") is True
        or advisory.get("kind") == "cyber_alert" else 0,
        25 if fsis_class_i or fsis_public_alert else 0,
        22 if fema.get("recent_declaration_at_refresh") is True else 0,
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
        "public_impact_basis": impact_basis,
        "local_regional_impact": min(20, max(
            _bounded_int(usgs_rank.get("magnitude_weight"), 40) // 2,
            _bounded_int(usgs_rank.get("felt_weight"), 10) * 2,
        )) if usgs else 0,
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
            signal["local_regional_impact"] for signal in signals
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
        "public_impact_basis": list(dict.fromkeys(
            basis for signal in signals for basis in signal["public_impact_basis"]
        )),
    }
