from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

SCOPE_PRIORITY_BOOST = {
    "LOCAL": 18,
    "REGIONAL": 14,
    "NATIONAL": 10,
    "GLOBAL": 8,
    "ORBITAL": 6,
}

HEALTH_CONFIDENCE_BOOST = {
    "healthy": 6,
    "stale": -6,
    "parser_failed": -16,
    "policy_blocked": -20,
    "blocked_policy": -20,
    "payload_too_large": -14,
    "failed": -12,
    "failing": -12,
}


def build_rank_result(
    source: dict[str, Any],
    item: dict[str, Any],
    *,
    seen_at: str,
    combined_tags: list[str],
    latest_health_state: str | None,
    repeat_count: int,
) -> dict[str, Any]:
    source_priority = int(source.get("priority", 50))
    published = _parse_time(item.get("source_published_at")) or _parse_time(seen_at)
    seen = _parse_time(seen_at) or published
    age_hours = max(0, int((seen - published).total_seconds() // 3600)) if seen and published else 0
    recency_bonus = max(0, 72 - min(age_hours, 72))
    freshness_bonus = 6 if age_hours <= 6 else 0
    scope_boost = SCOPE_PRIORITY_BOOST.get(str(source.get("scope") or "").upper(), 0)
    official_boost = 12 if "official" in {tag.lower() for tag in combined_tags} else 0
    tag_bonus = min(len(combined_tags), 10)
    repeat_bonus = min(max(0, repeat_count), 5)
    health_confidence = HEALTH_CONFIDENCE_BOOST.get(str(latest_health_state or "").lower(), 0)
    local_signal = _local_signal_factors(item)

    factors = {
        "source_priority": source_priority,
        "recency_bonus": recency_bonus,
        "freshness_bonus": freshness_bonus,
        "scope_priority_boost": scope_boost,
        "official_source_boost": official_boost,
        "tag_bonus": tag_bonus,
        "repeat_observation_bonus": repeat_bonus,
        "source_health_confidence": health_confidence,
        **local_signal["factors"],
    }
    score = sum(factors.values())
    reasons = [
        f"Source priority contributes {source_priority}.",
        f"Recency contributes {recency_bonus} from age_hours={age_hours}.",
        f"Scope boost contributes {scope_boost} for {source.get('scope')}.",
    ]
    if freshness_bonus:
        reasons.append(f"Freshness adds {freshness_bonus} because the item is <= 6 hours old.")
    if official_boost:
        reasons.append(f"Official tagging adds {official_boost}.")
    if tag_bonus:
        reasons.append(f"Tag density adds {tag_bonus} across {len(combined_tags)} tags.")
    if repeat_bonus:
        reasons.append(f"Repeat observations add {repeat_bonus}.")
    if health_confidence:
        reasons.append(
            f"Source health contributes {health_confidence} from state {latest_health_state}."
        )
    reasons.extend(local_signal["reasons"])

    return {
        "score": score,
        "factors": factors,
        "age_hours": age_hours,
        "reasons": reasons,
    }


def _local_signal_factors(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
    factors: dict[str, int] = {
        "local_official_alert_boost": 0,
        "local_public_impact_boost": 0,
        "local_transit_impact_boost": 0,
        "local_blog_signal_boost": 0,
        "local_privacy_penalty": 0,
    }
    reasons: list[str] = []

    alertseattle = evidence.get("alertseattle")
    if isinstance(alertseattle, dict):
        ranking = (
            alertseattle.get("ranking")
            if isinstance(alertseattle.get("ranking"), dict)
            else {}
        )
        boost = min(45, _int_value(ranking.get("city_alert_score")))
        factors["local_official_alert_boost"] = max(factors["local_official_alert_boost"], boost)
        if boost:
            reasons.append(f"AlertSeattle city-alert evidence adds {boost}.")

    nws_alert = evidence.get("nws_alert")
    if isinstance(nws_alert, dict):
        ranking = nws_alert.get("ranking") if isinstance(nws_alert.get("ranking"), dict) else {}
        boost = min(45, _int_value(ranking.get("total_alert_weight")))
        factors["local_official_alert_boost"] = max(factors["local_official_alert_boost"], boost)
        if boost:
            reasons.append(f"NWS active-alert severity evidence adds {boost}.")

    sfd = evidence.get("sfd_fire_911")
    if isinstance(sfd, dict):
        public_impact = (
            sfd.get("public_impact") if isinstance(sfd.get("public_impact"), dict) else {}
        )
        boost = min(40, _int_value(public_impact.get("public_impact_score")))
        factors["local_public_impact_boost"] = max(
            factors["local_public_impact_boost"],
            boost,
        )
        if boost:
            reasons.append(f"SFD public-impact evidence adds {boost}.")

    wsdot = evidence.get("wsdot_alert")
    if isinstance(wsdot, dict):
        ranking = wsdot.get("ranking") if isinstance(wsdot.get("ranking"), dict) else {}
        boost = min(40, _int_value(ranking.get("public_impact_score")))
        factors["local_public_impact_boost"] = max(
            factors["local_public_impact_boost"],
            boost,
        )
        if boost:
            reasons.append(f"WSDOT public-impact evidence adds {boost}.")

    metro = evidence.get("metro_advisory")
    if isinstance(metro, dict):
        ranking = metro.get("ranking") if isinstance(metro.get("ranking"), dict) else {}
        boost = min(40, _int_value(ranking.get("transit_impact_score")))
        factors["local_transit_impact_boost"] = boost
        if boost:
            reasons.append(f"Metro transit-impact evidence adds {boost}.")

    local_blog = evidence.get("local_blog")
    if isinstance(local_blog, dict):
        ranking = local_blog.get("ranking") if isinstance(local_blog.get("ranking"), dict) else {}
        boost = min(20, _int_value(ranking.get("local_blog_score")))
        factors["local_blog_signal_boost"] = boost
        if boost:
            reasons.append(f"Neighborhood-blog local signal evidence adds {boost}.")

    privacy = evidence.get("privacy")
    if isinstance(privacy, dict) and privacy.get("low_acuity_private"):
        factors["local_privacy_penalty"] = -40
        reasons.append("LOCAL privacy rules subtract 40 for low-acuity private-call evidence.")

    return {"factors": factors, "reasons": reasons}


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
