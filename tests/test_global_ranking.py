from __future__ import annotations

import json
from copy import deepcopy
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_ranking import rank_global_event
from console1701.news.scanner import _redact_global_sensitive_item, run_news_scan

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


def test_global_rank_ignores_impact_fields_on_wrong_or_unverified_source():
    cases = (
        ("gdacs", {"alert_level": "Red"}, "GDACS alert level"),
        ("reliefweb_disaster", {"status": "current"}, "ReliefWeb active disaster"),
        ("usgs_earthquake", {"magnitude": 7.2, "tsunami": True},
         "USGS magnitude or tsunami flag"),
    )
    for key, value, basis in cases:
        member = _member(1, family="un_press")
        member["evidence"].pop("gdacs")
        member["evidence"][key] = value
        wrong_family = rank_global_event(_group("un_press"), [member], now=NOW)
        assert wrong_family["factors"]["official_severity_score"] == 0
        assert wrong_family["factors"]["public_impact_score"] == 0
        assert wrong_family["factors"]["active_alert_score"] == 0
        assert basis not in wrong_family["public_impact_basis"]

        member["evidence"]["source"]["source_family"] = {
            "gdacs": "gdacs", "reliefweb_disaster": "reliefweb",
            "usgs_earthquake": "usgs",
        }[key]
        member["evidence"]["source"]["official_status"] = "official_candidate"
        unverified = rank_global_event(_group("un_press"), [member], now=NOW)
        assert unverified["factors"]["official_severity_score"] == 0
        assert unverified["factors"]["public_impact_score"] == 0
        assert basis not in unverified["public_impact_basis"]

        member["evidence"]["source"]["official_status"] = "official"
        verified = rank_global_event(_group("un_press"), [member], now=NOW)
        assert verified["factors"]["official_severity_score"] > 0
        assert verified["factors"]["public_impact_score"] > 0
        assert basis in verified["public_impact_basis"]


def test_global_rank_requires_source_specific_evidence_for_impact_scores():
    article = _member(1, family="pbs_world")
    article["evidence"].pop("gdacs")
    article["evidence"]["global_identity"] = {
        "public_value_class": "background",
        "public_impact_score": 35,
        "humanitarian_impact_score": 35,
    }
    unsupported = rank_global_event(_group("pbs_world"), [article], now=NOW)
    assert unsupported["factors"]["public_impact_score"] == 0
    assert unsupported["factors"]["humanitarian_impact_score"] == 0
    assert unsupported["public_impact_basis"] == []

    article["evidence"]["source"].update(
        {"source_family": "reliefweb", "official_status": "official"}
    )
    article["evidence"]["reliefweb_disaster"] = {"status": "current"}
    supported = rank_global_event(_group("reliefweb"), [article], now=NOW)
    assert supported["factors"]["public_impact_score"] == 15
    assert supported["factors"]["humanitarian_impact_score"] == 25
    assert supported["public_impact_basis"] == ["ReliefWeb active disaster"]


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


def test_who_don_source_context_does_not_infer_outbreak_severity_or_impact():
    item = _member(1, family="who")
    item["evidence"].pop("gdacs")
    item["evidence"]["who_don"] = {
        "ranking": {"who_don": True, "official_public_health": True},
    }
    ranked = rank_global_event(
        {**_group("who"), "countries": []}, [item], now=NOW
    )
    assert ranked["factors"]["public_health_context_score"] == 8
    assert ranked["factors"]["official_severity_score"] == 0
    assert ranked["factors"]["public_impact_score"] == 0
    assert ranked["factors"]["active_alert_score"] == 0
    assert ranked["public_impact_basis"] == []

    unverified = deepcopy(item)
    unverified["evidence"]["source"]["official_status"] = "candidate"
    assert rank_global_event(
        {**_group("who"), "countries": []}, [unverified], now=NOW
    )["factors"]["public_health_context_score"] == 0


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


def test_conflict_context_needs_official_or_independent_confirmation():
    unconfirmed = _member(1, family="community")
    unconfirmed["evidence"]["source"]["official_status"] = "candidate"
    unconfirmed["evidence"]["source"]["conflict_sensitive"] = True
    unconfirmed["evidence"]["gdacs"]["alert_level"] = "Red"
    isolated = rank_global_event(_group("community"), [unconfirmed], now=NOW)
    assert isolated["score"] <= 20
    assert isolated["factors"]["sensitivity_penalty"] > 0
    assert isolated["sensitivity"]["label"] == "unconfirmed_conflict_or_rumor"

    official = deepcopy(unconfirmed)
    official["evidence"]["source"]["official_status"] = "official"
    confirmed = rank_global_event(_group("community"), [official], now=NOW)
    assert confirmed["sensitivity"]["elevation_allowed"] is True
    assert confirmed["score"] > isolated["score"]

    independent = deepcopy(unconfirmed)
    independent["id"] = 2
    independent["evidence"]["source"]["source_family"] = "humanitarian"
    corroborated = rank_global_event(
        _group("community", "humanitarian", corroborated=True),
        [unconfirmed, independent], now=NOW,
    )
    assert corroborated["sensitivity"]["independent_confirmed"] is True
    assert corroborated["score"] > isolated["score"]


def test_sensitive_content_is_suppressed_and_redacted_before_storage():
    member = _member(1)
    member["evidence"]["sensitivity"] = {
        "graphic_violence": True, "targeted_person_tracking": True,
    }
    member["evidence"]["gdacs"]["alert_level"] = "Red"
    result = rank_global_event(_group("gdacs"), [member], now=NOW)
    assert result["score"] == 0
    assert result["sensitivity"]["label"] == "suppressed_sensitive_content"
    assert result["sensitivity"]["hard_suppression_flags"] == [
        "graphic_violence", "targeted_person_tracking"
    ]
    original = {
        "title": "Graphic detail about a private person",
        "description": "Private identifying detail",
        "evidence": {"sensitivity": {"targeted_person_tracking": True}},
    }
    redacted = _redact_global_sensitive_item(original)
    assert redacted["title"] == "Sensitive humanitarian report"
    assert redacted["description"] is None
    assert redacted["evidence"]["sensitivity"]["redacted_before_storage"] is True
    assert original["title"] == "Graphic detail about a private person"


def test_global_sensitive_fixture_scan_redacts_and_suppresses(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected HTTP")),
    )
    fixture = tmp_path / "sensitive.json"
    fixture.write_text(json.dumps({"items": [{
        "title": "Private identifying headline",
        "url": "https://example.test/report/one",
        "description": "Private identifying description",
        "published_at": "2026-10-15T12:00:00Z",
    }]}))
    config_path = tmp_path / "config.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: sensitive_fixture
                  name: Sensitive fixture
                  kind: api_json
                  parser: generic_json_items
                  source_family: unocha
                  source_class: official_conflict_humanitarian
                  official_status: official
                  policy_reviewed: true
                  sensitivity_flags: [conflict_adjacent, targeted_person_tracking]
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute(
            "SELECT title, description, evidence_json FROM news_items WHERE scope = 'GLOBAL'"
        ).fetchone()
        cluster = conn.execute(
            "SELECT title, score, evidence_json FROM news_clusters WHERE scope = 'GLOBAL'"
        ).fetchone()
    assert result["status"] == "complete"
    assert row["title"] == "Sensitive humanitarian report"
    assert row["description"] is None
    assert cluster is None
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["sensitivity"]["redacted_before_storage"] is True
    assert evidence["global_event"]["ranking"]["sensitivity"]["label"] == (
        "suppressed_sensitive_content"
    )
    assert "Private identifying" not in str(dict(row))
