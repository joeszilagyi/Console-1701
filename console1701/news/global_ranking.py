"""Explainable GLOBAL event ranking from stored source metadata only."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

_US_ISO3 = {"USA", "PRI", "GUM", "VIR", "ASM", "MNP"}
_US_COUNTRY_NAMES = {
    "united states", "united states of america", "puerto rico", "guam",
    "u s virgin islands", "us virgin islands", "american samoa",
    "northern mariana islands",
}


def _us_country(value: Any) -> bool:
    return isinstance(value, str) and value.strip().casefold() in _US_COUNTRY_NAMES


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


def _source_signals(member: dict[str, Any], *, observed: datetime | None) -> dict[str, Any]:
    evidence = member.get("evidence") or {}
    source = evidence.get("source") or {}
    family = source.get("source_family")
    official = source.get("official_status") == "official"
    gdacs = (evidence.get("gdacs") or {}) if official and family == "gdacs" else {}
    reliefweb = (
        evidence.get("reliefweb_disaster") or {}
    ) if official and family == "reliefweb" else {}
    report = (
        evidence.get("reliefweb_report") or {}
    ) if official and family == "reliefweb" else {}
    who = evidence.get("who_don") or {}
    usgs = (evidence.get("usgs_earthquake") or {}) if official and family == "usgs" else {}
    nhc = evidence.get("nhc_rss") or {}
    iaea = evidence.get("iaea") or {}
    cap = evidence.get("wmo_bom_cap") or {}
    identity = evidence.get("global_identity") or {}
    cap_level = 0
    if (observed and source.get("source_family") == "wmo"
            and source.get("official_status") == "official"
            and cap.get("issuer_verified") is True and cap.get("status") == "Actual"
            and cap.get("scope") == "Public"
            and cap.get("message_type") in {"Alert", "Update"}):
        for info in cap.get("infos") or []:
            if not isinstance(info, dict) or info.get("cancelled") is True:
                continue
            effective = _time(info.get("effective_at"))
            expires = _time(info.get("expires_at"))
            if (effective and expires and effective <= observed < expires
                    and info.get("areas")
                    and info.get("urgency") in {"Immediate", "Expected"}
                    and info.get("certainty") in {"Observed", "Likely"}):
                cap_level = max(cap_level, {"Severe": 25, "Extreme": 40}.get(
                    str(info.get("severity")), 0
                ))
    iaea_urgent = bool(
        source.get("source_family") == "iaea"
        and source.get("official_status") == "official"
        and (iaea.get("ranking") or {}).get("official_nuclear_safety_source") is True
        and iaea.get("urgent_title_phrase") is True
        and iaea.get("severity_confirmed") is False
    )
    who_don_context = bool(
        source.get("source_family") == "who"
        and source.get("official_status") == "official"
        and (who.get("ranking") or {}).get("who_don") is True
        and (who.get("ranking") or {}).get("official_public_health") is True
    )
    level = str(gdacs.get("alert_level") or "").lower()
    gdacs_us = bool(
        level in {"red", "orange"}
        and (str(gdacs.get("iso3") or "").upper() in _US_ISO3
             or _us_country(gdacs.get("country"))
             or any(_us_country(value) for value in gdacs.get("affected_countries") or []))
    )
    reliefweb_us = bool(
        reliefweb.get("status") in {"current", "alert"}
        and any(_us_country(value) for value in reliefweb.get("countries") or [])
    )
    domestic_impact_basis = (
        "GDACS alert for source-reported U.S. jurisdiction" if gdacs_us else
        "ReliefWeb active disaster in source-reported U.S. jurisdiction"
        if reliefweb_us else None
    )
    official_severity = {"red": 50, "orange": 35, "green": 12}.get(level, 0)
    official_severity = max(official_severity, cap_level)
    if reliefweb.get("status") in {"current", "alert"}:
        official_severity = max(official_severity, 20)
    magnitude = usgs.get("magnitude")
    if isinstance(magnitude, (int, float)):
        official_severity = max(
            official_severity,
            45 if magnitude >= 7 else 35 if magnitude >= 6 else 20 if magnitude >= 5 else 0,
        )
    nhc_official = (
        source.get("source_family") == "noaa_nhc"
        and source.get("official_status") == "official"
    )
    storm_type = str(nhc.get("storm_type") or "").lower() if nhc_official else ""
    if storm_type == "hurricane":
        official_severity = max(official_severity, 30)
    elif storm_type == "tropical storm":
        official_severity = max(official_severity, 18)
    advisory_at = _time(member.get("source_published_at"))
    nhc_watch = bool(
        observed and advisory_at and timedelta(0) <= observed - advisory_at <= timedelta(hours=12)
        and nhc_official
        and nhc.get("advisory_type") == "public_advisory"
        and nhc.get("watch_warning_terms")
    )
    public_impact = max(
        30 if level == "red" else 18 if level == "orange" else 0,
        25 if isinstance(magnitude, (int, float)) and magnitude >= 7 else 0,
        18 if usgs.get("tsunami") is True else 0,
        15 if reliefweb.get("status") in {"current", "alert"} else 0,
        12 if nhc_watch else 0,
    )
    humanitarian = max(
        25 if reliefweb.get("status") in {"current", "alert"} else 0,
        12 if report else 0,
    )
    alert = bool(nhc_watch or level in {"red", "orange"} or usgs.get("tsunami") is True or
                 reliefweb.get("status") in {"current", "alert"} or cap_level)
    return {
        "official_severity": official_severity,
        "public_impact": public_impact,
        "humanitarian": humanitarian,
        "active_alert": alert,
        "source": source,
        "ingest": evidence.get("ingest") or {},
        "identity": identity,
        "iaea_urgent": iaea_urgent,
        "who_don_context": who_don_context,
        "cap_level": cap_level,
        "nhc_watch_current": nhc_watch,
        "gdacs_impact": level in {"red", "orange"},
        "usgs_impact": bool(
            isinstance(magnitude, (int, float)) and magnitude >= 7
            or usgs.get("tsunami") is True
        ),
        "reliefweb_impact": reliefweb.get("status") in {"current", "alert"},
        "domestic_impact_basis": domestic_impact_basis,
        "impact_tags": ["us"] if domestic_impact_basis else [],
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
    signals = [_source_signals(member, observed=observed) for member in members]
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
        tag for signal in signals for tag in signal["impact_tags"]
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
    nuclear_safety_context = 8 if any(signal["iaea_urgent"] for signal in signals) else 0
    public_health_context = 8 if any(signal["who_don_context"] for signal in signals) else 0
    humanitarian = max((signal["humanitarian"] for signal in signals), default=0)
    domestic_impact = min(20, 10 * len(impact_tags & {
        "us", "national", "regional", "local"
    }))
    priority = min(10, max(
        (_int(signal["source"].get("priority"), 50) for signal in signals), default=0
    ) // 10)
    cluster_size = min(10, max(
        0, len({member["id"] for member in members})
        - int(group.get("dependent_duplicate_count") or 0),
    ))
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
        "nuclear_safety_context_score": nuclear_safety_context,
        "public_health_context_score": public_health_context,
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
            signal["gdacs_impact"] for signal in signals
        ) else None,
        "USGS magnitude or tsunami flag" if any(
            signal["usgs_impact"] for signal in signals
        ) else None,
        "ReliefWeb active disaster" if any(
            signal["reliefweb_impact"] for signal in signals
        ) else None,
        *(signal["domestic_impact_basis"] for signal in signals
          if signal["domestic_impact_basis"]),
        "NHC advisory watch/warning terms (geography unverified)" if any(
            signal["nhc_watch_current"] for signal in signals
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
        "public_impact_basis": list(dict.fromkeys(value for value in impact_basis if value)),
        "official_alert_basis": [
            "BoM CAP Actual/Public high-severity area warning within effective window"
        ] if any(signal["cap_level"] for signal in signals) else [],
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
