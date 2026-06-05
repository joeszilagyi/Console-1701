from __future__ import annotations

from console1701.news.ranking import apply_local_event_ranking_adjustments


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
        },
    )

    assert adjusted["factors"]["local_privacy_penalty"] == -20
    assert adjusted["factors"]["local_source_diversity_score"] == 2
    assert adjusted["factors"]["local_source_diversity_bonus"] == 3
    assert adjusted["factors"]["local_cluster_size_bonus"] == 4
    assert adjusted["score"] == sum(int(value) for value in adjusted["factors"].values())
    assert (
        "Independent cross-source confirmation partially offsets privacy suppression."
        in adjusted["reasons"]
    )


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
