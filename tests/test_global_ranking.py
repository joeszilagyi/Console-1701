from __future__ import annotations

from copy import deepcopy

from console1701.news.global_ranking import rank_global_event

NOW = "2026-10-15T20:00:00+00:00"


def _member(item_id: int, family: str = "gdacs") -> dict:
    return {
        "id": item_id,
        "source_published_at": "2026-10-15T12:00:00+00:00",
        "last_seen_at": "2026-10-15T12:00:00+00:00",
        "evidence": {
            "source": {
                "source_family": family,
                "official_status": "official",
                "priority": 70,
            },
            "ingest": {"source_health_state_at_ingest": "healthy"},
            "gdacs": {"alert_level": "Green"},
            "global_identity": {},
        },
    }


def _group(*families: str, corroborated: bool = False) -> dict:
    return {
        "families": list(dict.fromkeys(families)),
        "countries": ["example island"],
        "identifiers": ["gdacs:eq:123"],
        "corroborated": corroborated,
    }


def test_global_rank_elevates_official_alert_and_independent_convergence():
    green = _member(1)
    red = deepcopy(green)
    red["evidence"]["gdacs"]["alert_level"] = "Red"
    green_score = rank_global_event(_group("gdacs"), [green], now=NOW)
    red_score = rank_global_event(_group("gdacs"), [red], now=NOW)
    assert red_score["score"] > green_score["score"]
    assert red_score["factors"]["official_severity_score"] == 50
    assert red_score["factors"]["active_alert_score"] == 20
    assert "GDACS alert level" in red_score["public_impact_basis"]

    duplicate = deepcopy(red)
    duplicate["id"] = 2
    independent = deepcopy(red)
    independent["id"] = 2
    independent["evidence"]["source"]["source_family"] = "reliefweb"
    duplicate_score = rank_global_event(_group("gdacs"), [red, duplicate], now=NOW)
    convergent_score = rank_global_event(
        _group("gdacs", "reliefweb", corroborated=True), [red, independent], now=NOW
    )
    assert duplicate_score["factors"]["duplicate_family_penalty"] == 2
    assert convergent_score["factors"]["source_diversity_score"] > duplicate_score[
        "factors"
    ]["source_diversity_score"]
    assert convergent_score["score"] > duplicate_score["score"]


def test_global_rank_penalizes_stale_low_value_rumor_and_out_of_scope():
    base = _member(1)
    normal = rank_global_event(_group("gdacs"), [base], now=NOW)
    risky = deepcopy(base)
    risky["evidence"]["ingest"]["source_health_state_at_ingest"] = "stale"
    risky["evidence"]["global_identity"] = {
        "public_value_class": "routine",
        "out_of_scope": True,
        "rumor": True,
    }
    reduced = rank_global_event(_group("gdacs"), [risky], now=NOW)
    assert reduced["score"] < normal["score"]
    assert reduced["factors"]["stale_source_penalty"] > 0
    assert reduced["factors"]["low_public_value_penalty"] == 40
    assert reduced["factors"]["out_of_scope_penalty"] == 60
    assert reduced["factors"]["rumor_penalty"] == 70
    assert any("rumor penalty subtracts" in reason for reason in reduced["reasons"])


def test_global_rank_uses_geography_time_and_verified_domestic_tags():
    first = _member(1)
    second = _member(2, family="who")
    second["source_published_at"] = "2026-10-16T00:00:00+00:00"
    second["evidence"]["global_identity"]["impact_tags"] = ["us", "local"]
    near = rank_global_event(
        {**_group("gdacs", "who", corroborated=True), "countries": ["a", "b"]},
        [first, second], now="2026-10-16T02:00:00+00:00"
    )
    far = deepcopy(second)
    far["source_published_at"] = "2026-10-10T00:00:00+00:00"
    far_score = rank_global_event(
        {**_group("gdacs", "who", corroborated=True), "countries": ["a"]},
        [first, far], now="2026-10-16T02:00:00+00:00"
    )
    assert near["factors"]["temporal_proximity_score"] > far_score["factors"][
        "temporal_proximity_score"
    ]
    assert near["factors"]["geographic_reach_score"] > far_score["factors"][
        "geographic_reach_score"
    ]
    assert near["factors"]["us_or_local_impact_score"] == 20
    assert near["impact_tags"] == ["local", "us"]


def test_global_rank_does_not_infer_severity_from_headline_or_unverified_region():
    item = _member(1, family="who")
    item["title"] = "Critical global catastrophe with millions affected"
    item["evidence"].pop("gdacs")
    item["evidence"]["global"] = {
        "affected_regions": ["Africa"],
        "geography_basis": "title_suffix_unverified",
    }
    result = rank_global_event(
        {**_group("who"), "countries": []}, [item], now=NOW
    )
    assert result["factors"]["official_severity_score"] == 0
    assert result["factors"]["public_impact_score"] == 0
    assert result["factors"]["geographic_reach_score"] == 0
    assert result["public_impact_basis"] == []


def test_global_rank_humanitarian_age_priority_cluster_size_and_confidence():
    disaster = _member(1, family="reliefweb")
    disaster["evidence"].pop("gdacs")
    disaster["evidence"]["reliefweb_disaster"] = {"status": "current"}
    fresh = rank_global_event(_group("reliefweb"), [disaster], now=NOW)
    assert fresh["factors"]["humanitarian_impact_score"] == 25
    assert fresh["factors"]["active_alert_score"] == 20
    assert fresh["factors"]["source_priority_score"] == 7
    assert fresh["factors"]["cluster_size_score"] == 1
    assert fresh["factors"]["low_confidence_penalty"] == 15

    old = deepcopy(disaster)
    old["source_published_at"] = "2026-10-01T12:00:00+00:00"
    older_score = rank_global_event(_group("reliefweb"), [old], now=NOW)
    assert older_score["factors"]["recency_score"] < fresh["factors"]["recency_score"]

    second = _member(2, family="unocha")
    second["evidence"].pop("gdacs")
    second["evidence"]["reliefweb_report"] = {"id": "report-1"}
    correlated = rank_global_event(
        _group("reliefweb", "unocha", corroborated=True), [disaster, second], now=NOW
    )
    assert correlated["factors"]["cluster_size_score"] == 2
    assert correlated["factors"]["low_confidence_penalty"] == 0
    assert correlated["factors"]["humanitarian_impact_score"] == 25
