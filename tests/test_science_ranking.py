from __future__ import annotations

from copy import deepcopy

import pytest

from console1701.news.science_ranking import rank_science_event

NOW = "2026-10-15T20:00:00+00:00"


def _member(item_id, family="nasa_jpl", *, evidence=None, tags=None):
    return {
        "id": item_id, "scope": "SYSTEM_SOLAR", "title": "Science event",
        "source_published_at": "2026-10-15T12:00:00+00:00",
        "tags": tags or ["official"],
        "evidence": {"source": {"source_family": family, "official_status": "official",
                                "priority": 80},
                     "ingest": {"source_health_state_at_ingest": "healthy"},
                     **(evidence or {})},
    }


def _group(*families, corroborated=False, identifiers=None):
    return {"families": list(families), "corroborated": corroborated,
            "identifiers": identifiers or []}


def test_official_release_and_independent_diversity_raise_score():
    first = _member(1, evidence={"science_identity": {
        "scientific_significance_score": 25, "mission_relevance": True,
        "impact_tags": ["global_impact"],
    }})
    second = _member(2, "esa_science")
    alone = rank_science_event(_group("nasa"), [first], now=NOW)
    combined = rank_science_event(
        _group("nasa", "esa", corroborated=True), [first, second], now=NOW,
    )
    assert combined["score"] > alone["score"]
    assert combined["factors"]["source_diversity_score"] > alone["factors"][
        "source_diversity_score"]
    assert combined["factors"]["scientific_significance_score"] == 25
    assert combined["factors"]["local_global_orbital_impact_score"] == 4


def test_archive_only_metadata_is_not_ranked_as_new_discovery():
    archive = _member(1, evidence={"exoplanet_archive": {
        "date_semantics": "parameter_update_not_discovery_date"}})
    ranked = rank_science_event(_group("nasa", identifiers=["planet:x"]), [archive], now=NOW)
    assert ranked["factors"]["recency_score"] == 0
    assert ranked["factors"]["archive_firehose_penalty"] == 15
    assert ranked["recency_basis"] == "no_release_date"
    assert any("not discovery dates" in reason for reason in ranked["reasons"])


def test_preliminary_transient_ranks_above_retraction_and_does_not_claim_confirmation():
    initial = _member(1, "nasa_gcn", evidence={"gcn_notice": {
        "status": "preliminary", "alert_type": "initial"}})
    withdrawn = deepcopy(initial)
    withdrawn["evidence"]["gcn_notice"] = {"status": "retracted", "alert_type": "retraction"}
    first = rank_science_event(_group("nasa"), [initial], now=NOW)
    retracted = rank_science_event(_group("nasa"), [withdrawn], now=NOW)
    assert first["score"] > retracted["score"]
    assert first["factors"]["transient_status_score"] == 12
    assert retracted["factors"]["retraction_penalty"] == 50


@pytest.mark.parametrize("withdrawal", [
    {"gcn_notice": {"status": "retracted"}},
    {"gcn_circular": {"status": "retracted"}},
    {"gracedb_public_alert": {"status": "retracted"}},
])
def test_retraction_withdraws_cross_source_elevation_even_with_other_high_signals(withdrawal):
    high = _member(1, "nasa_gcn", evidence={"science_identity": {
        "scientific_significance_score": 35,
        "rarity_score": 20, "public_interest_score": 20,
        "mission_relevance": True, "impact_tags": ["global_impact"],
    }})
    other = _member(2, "esa_science", evidence=withdrawal)
    group = _group("nasa", "esa", corroborated=True, identifiers=["gcn_event:grb"])
    before = rank_science_event(group, [high], now=NOW)
    after = rank_science_event(group, [high, other], now=NOW)
    assert before["score"] > 50
    assert after["score"] == 0
    assert after["retraction_override"] is True
    assert after["factors"]["retraction_penalty"] == 50
    assert any("withdraws event elevation" in reason for reason in after["reasons"])


def test_hype_stale_duplicate_and_out_of_scope_penalties_are_explicit():
    first = _member(1, evidence={"science_safety": {"hype_blocked": True},
                                    "science_identity": {"out_of_scope": True}})
    first["evidence"]["ingest"]["source_health_state_at_ingest"] = "stale"
    second = deepcopy(first)
    second["id"] = 2
    ranked = rank_science_event(_group("nasa"), [first, second], now=NOW)
    assert ranked["factors"]["hype_penalty"] == 60
    assert ranked["factors"]["out_of_scope_penalty"] == 60
    assert ranked["factors"]["duplicate_family_penalty"] == 3
    assert ranked["factors"]["stale_source_penalty"] == 16
    assert ranked["score"] == 0


def test_headline_alone_does_not_create_scientific_significance():
    item = _member(1, evidence={})
    item["title"] = "Unprecedented discovery of life changes everything"
    ranked = rank_science_event(_group("nasa"), [item], now=NOW)
    assert ranked["factors"]["scientific_significance_score"] == 0
    assert ranked["factors"]["public_interest_score"] == 0
    assert ranked["scientific_significance_basis"] == "explicit_source_metadata_only"
