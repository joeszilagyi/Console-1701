from __future__ import annotations

from console1701.news.ranking import (
    apply_local_event_ranking_adjustments,
    apply_regional_cluster_ranking_adjustments,
    build_rank_result,
)


def test_local_active_nws_alert_stays_elevated_after_recency_fades() -> None:
    source = {"scope": "LOCAL", "priority": 80}
    item = {
        "source_published_at": "2026-10-13T12:00:00+00:00",
        "evidence": {"nws_alert": {
            "ranking": {"active_alert": True},
            "effective": "2026-10-13T12:00:00+00:00",
            "expires": "2026-10-16T12:00:00+00:00",
        }},
    }
    seen_at = "2026-10-15T12:00:00+00:00"
    active = build_rank_result(
        source, item, seen_at=seen_at, combined_tags=["official"],
        latest_health_state="healthy", repeat_count=0,
    )
    expired_item = {**item, "evidence": {"nws_alert": {
        **item["evidence"]["nws_alert"],
        "expires": "2026-10-14T12:00:00+00:00",
    }}}
    expired = build_rank_result(
        source, expired_item, seen_at=seen_at, combined_tags=["official"],
        latest_health_state="healthy", repeat_count=0,
    )

    assert active["local_recency_state"] == "active_but_older"
    assert active["factors"]["local_active_alert_bonus"] == 20
    assert active["score"] == sum(active["factors"].values())
    assert any("remains active" in reason for reason in active["reasons"])
    adjusted = apply_local_event_ranking_adjustments(
        active, source_family="nws", local_event={"families": ["nws"], "item_count": 1}
    )
    assert adjusted["local_recency_state"] == "active_but_older"
    assert adjusted["health_state"] == "healthy"
    assert expired["local_recency_state"] == "older"
    assert expired["factors"]["local_active_alert_bonus"] == 0
    assert active["score"] - expired["score"] == 20


def test_regional_cluster_ranking_uses_independent_families_without_accumulating() -> None:
    base = {
        "score": 100,
        "factors": {"source_priority": 100},
        "age_hours": 0,
        "reasons": ["Source priority contributes 100."],
    }
    first = apply_regional_cluster_ranking_adjustments(
        base, family_count=2, same_family_count=1, item_count=3
    )
    again = apply_regional_cluster_ranking_adjustments(
        first, family_count=2, same_family_count=1, item_count=3
    )

    assert first["factors"]["regional_source_diversity_bonus"] == 5
    assert first["factors"]["regional_cluster_size_bonus"] == 4
    assert first["factors"]["regional_duplicate_family_penalty"] == 0
    assert first["score"] == again["score"] == sum(again["factors"].values())
    assert first["reasons"] == again["reasons"]


def test_regional_ranking_records_alert_stale_geography_and_event_timing() -> None:
    source = {"scope": "REGIONAL", "priority": 80}
    item = {
        "source_published_at": "2026-10-15T06:00:00+00:00",
        "evidence": {
            "regional_event": {"confidence": "high", "geography": {"matched": True}},
            "nws_alert": {
                "ranking": {"active_alert": True, "total_alert_weight": 40},
                "expires": "2026-10-16T12:00:00+00:00",
            },
        },
    }
    seen_at = "2026-10-15T12:00:00+00:00"
    active = build_rank_result(
        source, item, seen_at=seen_at, combined_tags=["official"],
        latest_health_state="stale", repeat_count=0,
    )
    expired = build_rank_result(
        source, {**item, "evidence": {**item["evidence"], "nws_alert": {
            **item["evidence"]["nws_alert"], "expires": "2026-10-14T12:00:00+00:00",
        }}}, seen_at=seen_at, combined_tags=["official"],
        latest_health_state="healthy", repeat_count=0,
    )
    rejected = build_rank_result(
        source, {**item, "evidence": {**item["evidence"], "usgs_earthquake": {
            "filter": {"matched": False},
        }}}, seen_at=seen_at, combined_tags=["official"],
        latest_health_state="healthy", repeat_count=0,
    )
    assert active["factors"]["regional_active_alert_bonus"] == 10
    assert active["factors"]["regional_stale_source_penalty"] == -6
    assert expired["factors"]["regional_active_alert_bonus"] == 0
    assert rejected["factors"]["regional_out_of_region_penalty"] == -30
    assert active["score"] == sum(active["factors"].values())
    near = apply_regional_cluster_ranking_adjustments(
        active, family_count=2, same_family_count=1, item_count=2,
        temporal_proximity_hours=4,
    )
    far = apply_regional_cluster_ranking_adjustments(
        near, family_count=2, same_family_count=1, item_count=2,
        temporal_proximity_hours=36,
    )
    assert near["factors"]["regional_temporal_proximity_bonus"] == 6
    assert far["factors"]["regional_temporal_proximity_bonus"] == 0
    assert far["score"] == sum(far["factors"].values())


def test_apply_local_event_ranking_adjustments_keeps_score_equal_to_factor_sum() -> None:
    ranking = {
        "score": -40,
        "factors": {
            "local_privacy_penalty": -40,
        },
        "age_hours": 0,
        "reasons": [],
        "health_state": "healthy",
    }

    adjusted = apply_local_event_ranking_adjustments(
        ranking,
        source_family=None,
        local_event={
            "families": ["spd", "local_news"],
            "matched": True,
            "item_count": 2,
            "match_score": 30,
            "topic_repetition_score": 6,
            "topic_repetition_tokens": ["outage", "capitol"],
        },
    )

    assert adjusted["factors"]["local_privacy_penalty"] == -20
    assert adjusted["factors"]["local_source_diversity_score"] == 2
    assert adjusted["factors"]["local_source_diversity_bonus"] == 3
    assert adjusted["factors"]["local_source_family_boost"] == 9
    assert adjusted["factors"]["local_cluster_size_bonus"] == 4
    assert adjusted["factors"]["local_topic_repetition_bonus"] == 6
    assert adjusted["score"] == sum(int(value) for value in adjusted["factors"].values())
    assert (
        "Independent cross-source confirmation partially offsets privacy suppression."
        in adjusted["reasons"]
    )
    assert "LOCAL source family weighting adds 9 across spd, local_news." in adjusted["reasons"]
    assert "LOCAL topic repetition adds 6 across 2 repeated tokens." in adjusted["reasons"]


def test_apply_local_event_ranking_adjustments_penalizes_social_only_private_reports() -> None:
    ranking = {
        "score": -40,
        "factors": {
            "local_privacy_penalty": -40,
        },
        "age_hours": 0,
        "reasons": [],
        "health_state": "healthy",
    }

    adjusted = apply_local_event_ranking_adjustments(
        ranking,
        source_family="reddit",
        local_event={
            "families": ["reddit"],
            "matched": False,
            "item_count": 1,
            "match_score": 0,
        },
    )

    assert adjusted["factors"]["local_privacy_penalty"] == -60
    assert adjusted["score"] == sum(int(value) for value in adjusted["factors"].values())
    assert (
        "Social-only private/sensitive reports stay in the background unless corroborated."
        in adjusted["reasons"]
    )
