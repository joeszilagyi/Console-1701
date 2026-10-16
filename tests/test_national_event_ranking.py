from __future__ import annotations

from copy import deepcopy

from console1701.news.national_ranking import rank_national_event

NOW = "2026-10-15T20:00:00+00:00"


def _member(item_id: int, family: str = "nws") -> dict:
    return {
        "id": item_id,
        "title": "Severe weather alert",
        "source_published_at": "2026-10-15T12:00:00+00:00",
        "last_seen_at": "2026-10-15T12:00:00+00:00",
        "evidence": {
            "source": {"source_family": family, "official_status": "official", "priority": 70},
            "ingest": {"source_health_state_at_ingest": "healthy"},
            "nws_alert": {
                "severity": "Severe", "status": "Actual",
                "expires": "2026-10-16T00:00:00+00:00",
                "instruction": "Take shelter.",
            },
            "national_identity": {},
        },
    }


def _group(*families: str, corroborated: bool = False) -> dict:
    return {
        "families": list(dict.fromkeys(families)),
        "identifiers": ["nws:alert-1"],
        "affected_states": ["wa"],
        "corroborated": corroborated,
    }


def test_national_rank_uses_official_severity_alert_and_impact():
    severe = _member(1)
    mild = deepcopy(severe)
    mild["evidence"]["nws_alert"]["severity"] = "Minor"
    mild["evidence"]["nws_alert"]["instruction"] = None
    mild["evidence"]["nws_alert"]["expires"] = "2026-10-15T10:00:00+00:00"
    high = rank_national_event(_group("nws"), [severe], now=NOW)
    low = rank_national_event(_group("nws"), [mild], now=NOW)
    assert high["score"] > low["score"]
    assert high["factors"]["official_severity_score"] == 32
    assert high["factors"]["active_alert_score"] == 18
    assert high["factors"]["public_impact_score"] == 20
    assert "NWS official instruction" in high["public_impact_basis"]


def test_national_rank_rewards_independent_sources_and_penalizes_duplicate_family():
    first = _member(1)
    duplicate = _member(2)
    independent = _member(2, family="public_media")
    repeated = rank_national_event(_group("nws"), [first, duplicate], now=NOW)
    convergent = rank_national_event(
        _group("nws", "public_media", corroborated=True), [first, independent], now=NOW
    )
    assert repeated["factors"]["duplicate_family_penalty"] == 3
    assert convergent["factors"]["source_diversity_score"] > repeated[
        "factors"
    ]["source_diversity_score"]
    assert convergent["score"] > repeated["score"]


def test_national_rank_covers_age_geography_local_impact_and_penalties():
    member = _member(1)
    near = rank_national_event({**_group("nws"), "affected_states": ["wa", "or"]},
                               [member], now=NOW)
    risky = deepcopy(member)
    risky["source_published_at"] = "2026-10-01T12:00:00+00:00"
    risky["evidence"]["ingest"]["source_health_state_at_ingest"] = "stale"
    risky["evidence"]["national_identity"] = {
        "public_value_class": "routine", "out_of_scope": True,
        "local_regional_impact_score": 12,
    }
    reduced = rank_national_event(_group("nws"), [risky], now=NOW)
    assert near["factors"]["geographic_reach_score"] > reduced[
        "factors"
    ]["geographic_reach_score"]
    assert near["factors"]["recency_score"] > reduced["factors"]["recency_score"]
    assert reduced["factors"]["stale_source_penalty"] == 8
    assert reduced["factors"]["low_public_value_penalty"] == 35
    assert reduced["factors"]["out_of_scope_penalty"] == 60
    assert reduced["factors"]["local_regional_impact_score"] == 0
    usgs = _member(2, family="usgs")
    usgs["evidence"]["usgs_earthquake"] = {
        "ranking": {"magnitude_weight": 24, "felt_weight": 4}
    }
    assert rank_national_event(_group("usgs"), [usgs], now=NOW)["factors"][
        "local_regional_impact_score"
    ] == 12
    assert any("out of scope penalty subtracts" in reason for reason in reduced["reasons"])


def test_national_rank_does_not_infer_impact_from_headline():
    member = _member(1)
    member["title"] = "Catastrophic nationwide disaster millions affected"
    member["evidence"].pop("nws_alert")
    score = rank_national_event({**_group("news"), "identifiers": [],
                                 "affected_states": []}, [member], now=NOW)
    assert score["factors"]["official_severity_score"] == 0
    assert score["factors"]["public_impact_score"] == 0
    assert score["factors"]["geographic_reach_score"] == 0
    assert score["public_impact_basis"] == []


def test_national_rank_rejects_unqualified_identity_scores_and_foreign_fields():
    member = _member(1, family="public_media")
    member["evidence"]["national_identity"] = {
        "official_severity_score": 45,
        "public_impact_score": 35,
        "local_regional_impact_score": 20,
    }
    member["evidence"]["national_policy"] = {"official_impact_score": 35}
    member["evidence"]["openfema_declaration"] = {
        "recent_declaration_at_refresh": True
    }
    score = rank_national_event(_group("public_media"), [member], now=NOW)
    assert score["factors"]["official_severity_score"] == 0
    assert score["factors"]["public_impact_score"] == 0
    assert score["factors"]["local_regional_impact_score"] == 0
    assert score["public_impact_basis"] == []


def test_national_rank_keeps_qualified_fema_and_fsis_signals():
    fema = _member(1, family="fema")
    fema["evidence"]["openfema_declaration"] = {
        "recent_declaration_at_refresh": True
    }
    fema_score = rank_national_event(_group("fema"), [fema], now=NOW)
    assert fema_score["factors"]["public_impact_score"] == 22
    assert fema_score["public_impact_basis"] == ["FEMA recent declaration"]
    fsis = _member(2, family="fsis")
    fsis["evidence"]["fsis_recall"] = {
        "current_notice": True,
        "recall_classification": "Class I",
        "recall_type": "Recall",
    }
    fsis_score = rank_national_event(_group("fsis"), [fsis], now=NOW)
    assert fsis_score["factors"]["official_severity_score"] == 25
    assert fsis_score["factors"]["public_impact_score"] == 25


def test_national_rank_accounts_for_time_priority_cluster_size_and_confidence():
    first = _member(1)
    second = _member(2, family="public_media")
    near = rank_national_event(
        _group("nws", "public_media", corroborated=True), [first, second], now=NOW
    )
    far = deepcopy(second)
    far["source_published_at"] = "2026-10-01T12:00:00+00:00"
    distant = rank_national_event(
        _group("nws", "public_media", corroborated=True), [first, far], now=NOW
    )
    assert near["factors"]["temporal_proximity_score"] == 10
    assert distant["factors"]["temporal_proximity_score"] == 0
    assert near["factors"]["source_priority_score"] == 7
    assert near["factors"]["cluster_size_score"] == 2
    assert near["factors"]["low_confidence_penalty"] == 0
    assert rank_national_event(
        {**_group("nws"), "identifiers": []}, [first], now=NOW
    )["factors"]["low_confidence_penalty"] == 24


def test_national_rank_does_not_reward_syndicated_duplicate_as_convergence():
    first = _member(1, family="publisher_one")
    second = _member(2, family="publisher_two")
    first["canonical_url"] = second["canonical_url"] = "https://wire.example/story/123"
    group = {
        **_group("publisher_one", "publisher_two"),
        "corroborated": False,
        "matches": [{"item_ids": [1, 2], "basis": ["same_article_url"]}],
    }
    ranking = rank_national_event(group, [first, second], now=NOW)
    assert ranking["factors"]["source_diversity_score"] == 9
    assert ranking["factors"]["temporal_proximity_score"] == 0
    assert ranking["factors"]["cluster_size_score"] == 1
    assert ranking["factors"]["syndicated_duplicate_penalty"] == 6
