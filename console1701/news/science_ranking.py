"""Explainable science event ranking from source-backed metadata only."""

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


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _signals(member: dict[str, Any]) -> dict[str, Any]:
    evidence = member.get("evidence") or {}
    identity = evidence.get("science_identity") or {}
    gcn = evidence.get("gcn_notice") or {}
    circular = evidence.get("gcn_circular") or {}
    gracedb = evidence.get("gracedb_public_alert") or {}
    rss = evidence.get("science_rss") or {}
    archive = bool(evidence.get("exoplanet_archive") or evidence.get("mast_caom")
                   or evidence.get("pds_collection") or "archive_metadata" in (
                       member.get("tags") or []))
    source = evidence.get("source") or {}
    official = source.get("official_status") == "official" or "official" in (
        member.get("tags") or [])
    significance = min(35, max(0, _int(identity.get("scientific_significance_score"))))
    rarity = min(20, max(0, _int(identity.get("rarity_score"))))
    if gcn.get("status") == "preliminary" and gcn.get("alert_type") == "initial":
        rarity = max(rarity, 8)
    transient = 12 if (
        (gcn and gcn.get("status") == "preliminary")
        or (circular and circular.get("status") == "preliminary_report")
        or (gracedb and gracedb.get("status") in {
            "early_warning", "preliminary", "initial", "update",
        })
    ) else 0
    mission = 10 if identity.get("mission_relevance") is True else (
        5 if rss.get("mission_label") or rss.get("telescope") else 0)
    public = min(20, max(0, _int(identity.get("public_interest_score"))))
    tags = {str(tag).casefold() for tag in identity.get("impact_tags") or []}
    return {
        "source": source, "ingest": evidence.get("ingest") or {},
        "identity": identity, "safety": evidence.get("science_safety") or {},
        "archive": archive, "official": official, "significance": significance,
        "rarity": rarity, "transient": transient, "mission": mission,
        "public": public, "tags": tags, "gcn": gcn, "circular": circular,
        "gracedb": gracedb,
        "published_at": _time(member.get("source_published_at")),
    }


def rank_science_event(
    group: dict[str, Any], members: list[dict[str, Any]], *, now: str
) -> dict[str, Any]:
    """Score science signals without treating archive updates as new discoveries."""
    observed = _time(now)
    signals = [_signals(member) for member in members]
    published = [signal["published_at"] for signal in signals
                 if signal["published_at"] and not signal["archive"]]
    latest = max(published) if published else None
    age_hours = max(0, int((observed - latest).total_seconds() // 3600)) if (
        observed and latest) else None
    recency = max(0, 24 - min(24, age_hours // 3)) if age_hours is not None else 0
    official = 18 if any(signal["official"] and not signal["archive"] for signal in signals) else (
        6 if any(signal["official"] for signal in signals) else 0)
    significance = max((signal["significance"] for signal in signals), default=0)
    rarity = max((signal["rarity"] for signal in signals), default=0)
    transient = max((signal["transient"] for signal in signals), default=0)
    mission = max((signal["mission"] for signal in signals), default=0)
    public = max((signal["public"] for signal in signals), default=0)
    families = list(group.get("families") or [])
    diversity = min(20, len(families) * 4 + (8 if group.get("corroborated") else 0))
    priority = min(10, max((_int(signal["source"].get("priority"))
                            for signal in signals), default=0) // 10)
    cluster = min(8, len({member["id"] for member in members}))
    impact_tags = set().union(*(signal["tags"] for signal in signals)) if signals else set()
    impact = min(16, len(impact_tags & {"local_impact", "regional_impact",
                                         "national_impact", "global_impact"}) * 4)
    family_counts = Counter(str(signal["source"].get("source_family") or "unknown")
                            for signal in signals)
    duplicate = min(24, sum(max(0, count - 1) for count in family_counts.values()) * 3)
    stale = min(24, sum(8 for signal in signals if signal["ingest"].get(
        "source_health_state_at_ingest") in {"stale", "failing", "parser_failed"}))
    low_confidence = 0 if group.get("corroborated") else (
        12 if group.get("identifiers") else 22)
    low_value = 25 if any(signal["identity"].get("public_value_class") in {
        "routine", "background", "opinion", "speculation"} for signal in signals) else 0
    hype = 60 if any(signal["safety"].get("hype_blocked") for signal in signals) else 0
    out_of_scope = 60 if any(signal["identity"].get("out_of_scope") is True
                             for signal in signals) else 0
    archive_firehose = 45 if any(signal["safety"].get("archive_firehose_blocked")
                                 for signal in signals) else (
        15 if signals and all(signal["archive"] for signal in signals) else 0)
    retracted = bool(group.get("withdrawal_retained")) or any(
        signal["gcn"].get("status") == "retracted"
        or signal["circular"].get("status") == "retracted"
        or signal["gracedb"].get("status") == "retracted"
        for signal in signals
    )
    retraction = 50 if retracted else 0
    factors = {
        "recency_score": recency,
        "official_provenance_score": official,
        "scientific_significance_score": significance,
        "source_diversity_score": diversity,
        "mission_relevance_score": mission,
        "rarity_score": rarity,
        "transient_status_score": transient,
        "public_interest_score": public,
        "source_priority_score": priority,
        "cluster_size_score": cluster,
        "local_global_orbital_impact_score": impact,
        "duplicate_family_penalty": duplicate,
        "stale_source_penalty": stale,
        "low_confidence_penalty": low_confidence,
        "low_public_value_penalty": low_value,
        "hype_penalty": hype,
        "out_of_scope_penalty": out_of_scope,
        "archive_firehose_penalty": archive_firehose,
        "retraction_penalty": retraction,
    }
    bonuses = sum(value for key, value in factors.items() if key.endswith("_score"))
    penalties = sum(value for key, value in factors.items() if key.endswith("_penalty"))
    score = 0 if retracted else max(0, bonuses - penalties)
    reasons = [f"{key}={value}" for key, value in factors.items() if value]
    if retracted:
        reasons.append("Source retraction withdraws event elevation regardless of other reports.")
    if any(signal["archive"] for signal in signals):
        reasons.append("Archive update/harvest/observation dates are not discovery dates.")
    if all(signal["archive"] for signal in signals) and signals:
        reasons.append("Archive-only metadata has no release recency bonus.")
    return {
        "score": score, "factors": factors, "reasons": reasons,
        "age_hours": age_hours, "families": families,
        "corroborated": bool(group.get("corroborated")),
        "impact_tags": sorted(impact_tags),
        "recency_basis": "source_publication_or_alert" if latest else "no_release_date",
        "scientific_significance_basis": "explicit_source_metadata_only",
        "hype_basis": "explicit_science_safety_flag_only",
        "retraction_override": retracted,
    }
