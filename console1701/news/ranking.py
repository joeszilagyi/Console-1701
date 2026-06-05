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

LOCAL_SOCIAL_SOURCE_FAMILIES = {
    "neighborhood_blog",
    "reddit",
    "bluesky",
    "x_api",
}


def _local_event_families(local_event: dict[str, Any] | None) -> list[str]:
    raw_families = local_event.get("families") if isinstance(local_event, dict) else []
    if not isinstance(raw_families, list):
        raw_families = []
    families = [str(value).lower().strip() for value in raw_families if str(value).strip()]
    return _dedupe_in_order(families)


def _apply_local_privacy_ranking_adjustments(
    factors: dict[str, int],
    reasons: list[str],
    local_event: dict[str, Any],
    source_family: str | None,
) -> None:
    privacy_penalty = int(factors.get("local_privacy_penalty") or 0)
    if privacy_penalty >= 0:
        return

    families = _local_event_families(local_event)
    family_count = len(families)
    matched = bool(local_event.get("matched"))
    item_count = int(local_event.get("item_count") or 1)
    normalized_source_family = str(source_family or "").strip().lower() if source_family else ""
    if normalized_source_family and not families:
        families = [normalized_source_family]
        family_count = len(families)

    family_set = set(families)
    is_social_only = bool(family_set) and family_set.issubset(LOCAL_SOCIAL_SOURCE_FAMILIES)

    if is_social_only:
        privacy_penalty -= 20
        reasons.append(
            "Social-only private/sensitive reports stay in the background unless corroborated."
        )
    elif family_count <= 1 and item_count == 1 and not matched:
        privacy_penalty -= 12
        reasons.append(
            "Single-family private/public-safety reports remain low-priority without convergence."
        )

    if family_count >= 2:
        privacy_penalty = int(privacy_penalty / 2)
        reasons.append(
            "Independent cross-source confirmation partially offsets privacy suppression."
        )

    if is_social_only and family_count >= 2:
        # Multiple social-only confirmations still stay suppressed, but the harsher
        # single-source social penalty should soften once there is corroboration.
        privacy_penalty = int(privacy_penalty / 2)

    factors["local_privacy_penalty"] = privacy_penalty


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
        "health_state": latest_health_state,
    }


def apply_local_event_ranking_adjustments(
    ranking: dict[str, Any],
    *,
    source_family: str | None,
    local_event: dict[str, Any] | None,
) -> dict[str, Any]:
    ranking = dict(ranking)
    factors = dict(ranking.get("factors") or {})
    reasons = list(ranking.get("reasons") or [])
    health_state = str(ranking.get("health_state") or "").lower().strip()

    if not local_event:
        return {
            "score": int(ranking.get("score", 0)),
            "factors": factors,
            "age_hours": int(ranking.get("age_hours", 0)),
            "reasons": reasons,
        }

    families = _local_event_families(local_event)
    source_diversity_score = len(families)

    duplicate_family = bool(local_event.get("is_duplicate_family"))
    if not duplicate_family and source_family:
        normalized_source_family = str(source_family).lower().strip()
        duplicate_family = bool(local_event.get("matched")) and normalized_source_family in set(
            families
        )

    match_score = int(local_event.get("match_score") or 0)
    item_count = int(local_event.get("item_count") or 1)

    source_diversity_bonus = 0
    if source_diversity_score > 1:
        source_diversity_bonus = min(12, (source_diversity_score - 1) * 3)

    cluster_size_bonus = 0
    if item_count > 1:
        cluster_size_bonus = min(12, item_count * 2)

    duplicate_family_penalty = -8 if duplicate_family else 0
    low_confidence_penalty = -6 if local_event.get("matched") and match_score < 25 else 0
    stale_source_penalty = 0
    if health_state == "stale":
        stale_source_penalty = int(factors.get("source_health_confidence") or 0)
        factors["local_stale_source_penalty"] = stale_source_penalty

    factors["local_source_diversity_score"] = source_diversity_score
    factors["local_source_diversity_bonus"] = source_diversity_bonus
    factors["local_cluster_size_bonus"] = cluster_size_bonus
    factors["local_duplicate_family_penalty"] = duplicate_family_penalty
    factors["local_low_confidence_penalty"] = low_confidence_penalty
    if stale_source_penalty:
        factors["source_health_confidence"] = stale_source_penalty

    _apply_local_privacy_ranking_adjustments(
        factors=factors,
        reasons=reasons,
        local_event=local_event,
        source_family=source_family,
    )

    score = sum(int(value) for value in factors.values())

    if source_diversity_bonus:
        reasons.append(
            f"LOCAL event source diversity adds {source_diversity_bonus} "
            f"across {source_diversity_score} families."
        )
    if cluster_size_bonus:
        reasons.append(
            f"LOCAL event size adds {cluster_size_bonus} from {item_count} matched items."
        )
    if duplicate_family_penalty:
        reasons.append(
            "LOCAL duplicate family match subtracts 8 due same source family convergence."
        )
    if low_confidence_penalty:
        reasons.append(
            f"LOCAL event match confidence is low; subtracts {abs(low_confidence_penalty)} "
            "to reduce over-weight."
        )
    if stale_source_penalty:
        reasons.append("LOCAL source health is stale and reduces confidence.")

    return {
        "score": score,
        "factors": factors,
        "age_hours": int(ranking.get("age_hours", 0)),
        "reasons": reasons,
    }


def _dedupe_in_order(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = str(value).lower().strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def _local_signal_factors(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
    factors: dict[str, int] = {
        "local_official_alert_boost": 0,
        "local_public_impact_boost": 0,
        "local_transit_impact_boost": 0,
        "local_utility_impact_boost": 0,
        "local_airport_port_boost": 0,
        "local_blog_signal_boost": 0,
        "local_privacy_penalty": 0,
    }
    reasons: list[str] = []

    alertseattle = evidence.get("alertseattle")
    if isinstance(alertseattle, dict):
        ranking = (
            alertseattle.get("ranking") if isinstance(alertseattle.get("ranking"), dict) else {}
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

    city_light = evidence.get("city_light_outage")
    if isinstance(city_light, dict):
        ranking = city_light.get("ranking") if isinstance(city_light.get("ranking"), dict) else {}
        boost = min(45, _int_value(ranking.get("utility_impact_score")))
        factors["local_utility_impact_boost"] = boost
        if boost:
            reasons.append(f"City Light utility-impact evidence adds {boost}.")

    faa = evidence.get("faa_airport_status")
    if isinstance(faa, dict):
        ranking = faa.get("ranking") if isinstance(faa.get("ranking"), dict) else {}
        boost = min(45, _int_value(ranking.get("airport_impact_score")))
        factors["local_airport_port_boost"] = boost
        if boost:
            reasons.append(f"FAA airport-impact evidence adds {boost}.")

    local_blog = evidence.get("local_blog")
    if isinstance(local_blog, dict):
        ranking = local_blog.get("ranking") if isinstance(local_blog.get("ranking"), dict) else {}
        boost = min(20, _int_value(ranking.get("local_blog_score")))
        factors["local_blog_signal_boost"] = boost
        if boost:
            reasons.append(f"Neighborhood-blog local signal evidence adds {boost}.")

    spd_blotter = evidence.get("spd_blotter")
    if isinstance(spd_blotter, dict):
        ranking = spd_blotter.get("ranking") if isinstance(spd_blotter.get("ranking"), dict) else {}
        boost = min(45, _int_value(ranking.get("incident_score")))
        factors["local_public_impact_boost"] = max(
            factors["local_public_impact_boost"],
            boost,
        )
        if boost:
            reasons.append(f"SPD blotter incident evidence adds {boost}.")
        if bool(spd_blotter.get("preliminary_report")):
            reasons.append("SPD feed marks this as preliminary report context.")
        spd_privacy = spd_blotter.get("privacy")
        if isinstance(spd_privacy, dict) and bool(spd_privacy.get("low_acuity_private")):
            if factors["local_privacy_penalty"] == 0:
                factors["local_privacy_penalty"] = -40
                reasons.append(
                    "SPD privacy rules subtract 40 for low-acuity private-call evidence."
                )
            else:
                reasons.append("SPD evidence also includes low-acuity privacy suppression.")

    sdot_blog = evidence.get("sdot_blog")
    if isinstance(sdot_blog, dict):
        ranking = sdot_blog.get("ranking") if isinstance(sdot_blog.get("ranking"), dict) else {}
        boost = min(36, _int_value(ranking.get("traffic_impact_score")))
        factors["local_transit_impact_boost"] = max(
            factors["local_transit_impact_boost"],
            boost,
        )
        if boost:
            reasons.append(f"SDOT blog transit-impact evidence adds {boost}.")

    local_news = evidence.get("local_news")
    if isinstance(local_news, dict):
        ranking = local_news.get("ranking") if isinstance(local_news.get("ranking"), dict) else {}
        boost = min(25, _int_value(ranking.get("local_news_score")))
        if local_news.get("traffic_related"):
            factors["local_transit_impact_boost"] = max(
                factors["local_transit_impact_boost"],
                boost,
            )
            if boost:
                reasons.append(f"Local traffic news adds {boost}.")
        elif boost:
            factors["local_blog_signal_boost"] = max(
                factors["local_blog_signal_boost"],
                boost,
            )
            reasons.append(f"Local-news signal adds {boost}.")

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
