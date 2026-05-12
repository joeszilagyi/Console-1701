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
    "blocked_policy": -20,
    "payload_too_large": -14,
    "failed": -12,
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

    factors = {
        "source_priority": source_priority,
        "recency_bonus": recency_bonus,
        "freshness_bonus": freshness_bonus,
        "scope_priority_boost": scope_boost,
        "official_source_boost": official_boost,
        "tag_bonus": tag_bonus,
        "repeat_observation_bonus": repeat_bonus,
        "source_health_confidence": health_confidence,
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

    return {
        "score": score,
        "factors": factors,
        "age_hours": age_hours,
        "reasons": reasons,
    }


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
