from __future__ import annotations

import json
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_policy import classify_global_item
from console1701.news.scanner import run_news_scan


def _item(title, evidence=None, description=None):
    return {"scope": "GLOBAL", "title": title, "description": description,
            "evidence": evidence or {}}


def test_routine_opinion_domestic_and_social_content_get_explicit_low_value_labels():
    source = {"scope": "GLOBAL", "source_family": "un_press"}
    routine = classify_global_item(source, _item("Routine diplomatic statement on visit"))
    opinion = classify_global_item(source, _item("Opinion: A broad geopolitical view"))
    domestic = classify_global_item(source, _item("Candidate endorsement in domestic election"))
    social = classify_global_item(
        {"scope": "GLOBAL", "source_family": "reddit"}, _item("People discuss a claim"),
    )
    assert routine["evidence"]["global_identity"]["public_value_class"] == "routine"
    assert opinion["evidence"]["global_identity"]["public_value_class"] == "opinion"
    assert domestic["evidence"]["global_identity"]["out_of_scope"] is True
    assert social["evidence"]["global_identity"]["public_value_class"] == "background"
    assert social["evidence"]["global_attention_policy"]["impact_from_headline_inferred"] is False


def test_official_alert_metadata_prevents_routine_suppression():
    item = _item("Routine diplomatic statement on cyclone", {"gdacs": {"alert_level": "Red"}})
    result = classify_global_item(
        {"scope": "GLOBAL", "source_family": "gdacs", "official_status": "official"}, item
    )
    assert result["evidence"]["global_attention_policy"]["official_alert_evidence"] is True
    assert result["evidence"]["global_attention_policy"]["attention_state"] == "eligible"
    assert "public_value_class" not in result["evidence"]["global_identity"]


def test_low_value_descriptions_are_classified_without_overriding_official_alerts():
    source = {"scope": "GLOBAL", "source_family": "un_press"}
    cases = (
        ("This is a routine diplomatic statement about a courtesy call.", "routine"),
        ("Opinion: A commentator reflects on the week.", "opinion"),
        ("This concerns a domestic election campaign rally.", "generic_politics"),
    )
    for description, expected in cases:
        result = classify_global_item(source, _item("World update", description=description))
        assert result["evidence"]["global_identity"]["public_value_class"] == expected
        assert result["evidence"]["global_attention_policy"]["attention_state"] == "background"
    alert = classify_global_item(
        {"scope": "GLOBAL", "source_family": "gdacs", "official_status": "official"},
        _item("Cyclone warning", {"gdacs": {"alert_level": "Red"}},
              description="Routine economic release mentioned in context."),
    )
    assert alert["evidence"]["global_attention_policy"]["attention_state"] == "eligible"


def test_mismatched_or_unverified_source_cannot_claim_official_alert():
    item = _item("Routine diplomatic statement on cyclone", {"gdacs": {"alert_level": "Red"}})
    for family, status in (("un_press", "official"), ("gdacs", "official_candidate")):
        result = classify_global_item(
            {"scope": "GLOBAL", "source_family": family, "official_status": status}, item
        )
        assert result["evidence"]["global_attention_policy"]["official_alert_evidence"] is False
        assert result["evidence"]["global_identity"]["public_value_class"] == "routine"


def test_explicit_rumor_and_graphic_headline_are_labeled_without_impact_inference():
    rumor = classify_global_item(
        {"scope": "GLOBAL", "source_family": "regional_media"},
        _item("Unverified claim about an incident"),
    )
    graphic = classify_global_item(
        {"scope": "GLOBAL", "source_family": "regional_media"},
        _item("Graphic footage of violence"),
    )
    assert rumor["evidence"]["global_identity"]["rumor"] is True
    assert rumor["evidence"]["global_attention_policy"]["attention_state"] == "background"
    assert graphic["evidence"]["sensitivity"]["graphic_violence"] is True
    assert graphic["evidence"]["global_attention_policy"]["attention_state"] == "suppressed"


def test_sensitive_or_unverified_description_is_classified_before_storage():
    source = {"scope": "GLOBAL", "source_family": "regional_media"}
    graphic = classify_global_item(
        source, _item("Incident update", description="The post includes graphic footage."),
    )
    private = classify_global_item(
        source, _item("Incident update", description="Private distress of a named family."),
    )
    rumor = classify_global_item(
        source, _item("Incident update", description="An unverified claim is circulating."),
    )
    assert graphic["evidence"]["sensitivity"]["graphic_violence"] is True
    assert private["evidence"]["sensitivity"]["private_distress"] is True
    assert rumor["evidence"]["global_identity"]["rumor"] is True
    assert graphic["evidence"]["global_attention_policy"]["attention_state"] == "suppressed"
    assert private["evidence"]["global_attention_policy"]["attention_state"] == "suppressed"
    assert rumor["evidence"]["global_attention_policy"]["attention_state"] == "background"


def test_explicit_doxxing_is_redacted_before_global_storage(tmp_path, monkeypatch):
    source = {"scope": "GLOBAL", "source_family": "regional_media"}
    labeled = classify_global_item(
        source, _item("Incident update", description="The post is doxxing a private person."),
    )
    assert labeled["evidence"]["sensitivity"]["doxxing"] is True
    assert labeled["evidence"]["global_attention_policy"]["attention_state"] == "suppressed"
    assert "explicit doxxing description" in labeled["evidence"][
        "global_attention_policy"
    ]["reasons"]
    headline = classify_global_item(source, _item("Doxxed victim named in post"))
    assert headline["evidence"]["sensitivity"]["doxxing"] is True
    assert "explicit doxxing headline" in headline["evidence"][
        "global_attention_policy"
    ]["reasons"]
    assert "doxxing" not in classify_global_item(
        source, _item("Doximity publishes health research")
    )["evidence"]["sensitivity"]

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("unexpected HTTP"))
    ))
    fixture = tmp_path / "doxxing.json"
    fixture.write_text(json.dumps({"items": [{
        "title": "Incident update from region",
        "url": "https://example.test/global/doxxing",
        "description": "The post is doxxing a private person.",
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
                - id: global_doxxing_fixture
                  name: GLOBAL doxxing fixture
                  kind: api_json
                  parser: generic_json_items
                  source_family: unocha
                  source_class: official_conflict_humanitarian
                  official_status: official
                  policy_reviewed: true
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute("SELECT title, description, evidence_json FROM news_items").fetchone()
        cluster_count = conn.execute(
            "SELECT COUNT(*) FROM news_clusters WHERE scope='GLOBAL'"
        ).fetchone()[0]
    assert row["title"] == "Sensitive humanitarian report"
    assert row["description"] is None
    assert cluster_count == 0
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["sensitivity"]["doxxing"] is True
    assert evidence["sensitivity"]["redacted_before_storage"] is True
    assert "explicit doxxing description" in evidence["global"]["policy_notes"]


def test_explicit_person_tracking_is_redacted_before_global_storage(tmp_path, monkeypatch):
    source = {"scope": "GLOBAL", "source_family": "regional_media"}
    headline = classify_global_item(source, _item("Live location of a named journalist"))
    description = classify_global_item(
        source,
        _item("Incident update", description="A post is tracking a private family."),
    )
    neutral = classify_global_item(source, _item("Tracking movements of a tropical storm"))
    assert headline["evidence"]["sensitivity"]["targeted_person_tracking"] is True
    assert description["evidence"]["sensitivity"]["targeted_person_tracking"] is True
    assert "targeted_person_tracking" not in neutral["evidence"]["sensitivity"]
    assert headline["evidence"]["global_attention_policy"]["attention_state"] == "suppressed"

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("unexpected HTTP"))
    ))
    fixture = tmp_path / "tracking.json"
    fixture.write_text(json.dumps({"items": [{
        "title": "Incident update from region",
        "url": "https://example.test/global/tracking",
        "description": "A post is tracking a private family.",
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
                - id: global_tracking_fixture
                  name: GLOBAL tracking fixture
                  kind: api_json
                  parser: generic_json_items
                  source_family: unocha
                  source_class: official_conflict_humanitarian
                  official_status: official
                  policy_reviewed: true
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute("SELECT title, description, evidence_json FROM news_items").fetchone()
        cluster_count = conn.execute(
            "SELECT COUNT(*) FROM news_clusters WHERE scope='GLOBAL'"
        ).fetchone()[0]
    assert row["title"] == "Sensitive humanitarian report"
    assert row["description"] is None
    assert cluster_count == 0
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["sensitivity"]["targeted_person_tracking"] is True
    assert evidence["sensitivity"]["redacted_before_storage"] is True
    assert "explicit person-tracking description" in evidence["global"]["policy_notes"]


def test_scan_suppresses_graphic_title_before_sqlite_storage(tmp_path, monkeypatch):
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("unexpected HTTP"))
    ))
    fixture = tmp_path / "global.json"
    fixture.write_text(json.dumps({"items": [{
        "title": "Graphic footage of violence in public square",
        "url": "https://example.test/global/story-1",
        "description": "Unconfirmed graphic footage",
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
                - id: global_policy_fixture
                  name: GLOBAL policy fixture
                  kind: api_json
                  parser: generic_json_items
                  source_family: unocha
                  source_class: official_conflict_humanitarian
                  official_status: official
                  policy_reviewed: true
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute("SELECT title, description, evidence_json FROM news_items").fetchone()
        clusters = conn.execute(
            "SELECT COUNT(*) FROM news_clusters WHERE scope='GLOBAL'"
        ).fetchone()[0]
    assert row["title"] == "Sensitive humanitarian report"
    assert row["description"] is None
    assert clusters == 0
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["global_attention_policy"]["attention_state"] == "suppressed"
    assert evidence["global"]["attention_state"] == "suppressed"
    assert "graphic_violence" in evidence["global"]["sensitivity_notes"]
    assert "redacted_before_storage" in evidence["global"]["sensitivity_notes"]
    assert "explicit graphic-content headline" in evidence["global"]["policy_notes"]


def test_scan_redacts_graphic_description_with_neutral_title(tmp_path, monkeypatch):
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("unexpected HTTP"))
    ))
    fixture = tmp_path / "global.json"
    fixture.write_text(json.dumps({"items": [{
        "title": "Incident update from region",
        "url": "https://example.test/global/incident-update",
        "description": "Graphic footage of violence includes private distress.",
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
                - id: global_description_fixture
                  name: GLOBAL description fixture
                  kind: api_json
                  parser: generic_json_items
                  source_family: unocha
                  source_class: official_conflict_humanitarian
                  official_status: official
                  policy_reviewed: true
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute("SELECT title, description, evidence_json FROM news_items").fetchone()
        cluster_count = conn.execute(
            "SELECT COUNT(*) FROM news_clusters WHERE scope='GLOBAL'"
        ).fetchone()[0]
    assert row["title"] == "Sensitive humanitarian report"
    assert row["description"] is None
    assert cluster_count == 0
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["sensitivity"]["graphic_violence"] is True
    assert evidence["sensitivity"]["private_distress"] is True
    assert evidence["sensitivity"]["redacted_before_storage"] is True
    assert "explicit graphic-content description" in evidence["global"]["policy_notes"]


def test_scan_keeps_routine_description_out_of_global_attention(tmp_path, monkeypatch):
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("unexpected HTTP"))
    ))
    fixture = tmp_path / "routine.json"
    fixture.write_text(json.dumps({"items": [{
        "title": "World update",
        "url": "https://example.test/global/routine",
        "description": "A routine diplomatic statement about a courtesy call.",
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
                - id: global_routine_fixture
                  name: GLOBAL routine fixture
                  kind: api_json
                  parser: generic_json_items
                  source_family: un_press
                  official_status: official
                  policy_reviewed: true
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute("SELECT evidence_json FROM news_items").fetchone()
        cluster = conn.execute(
            "SELECT score, evidence_json FROM news_clusters WHERE scope='GLOBAL'"
        ).fetchone()
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["global_identity"]["public_value_class"] == "routine"
    assert evidence["global_attention_policy"]["attention_state"] == "background"
    assert evidence["global"]["low_public_value_penalty"] == 40
    assert cluster["score"] == 0
