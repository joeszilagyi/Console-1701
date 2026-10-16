from __future__ import annotations

import json
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.national_policy import classify_national_item
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_scope_view


def _item(title: str, **evidence: dict) -> dict:
    return {"title": title, "evidence": evidence}


def test_national_policy_suppresses_routine_categories_and_keeps_official_alerts():
    source = {"source_family": "national_news"}
    for title in (
        "Opinion: A columnist assesses policy",
        "Candidate endorsement at campaign rally",
        "Routine press release on agency anniversary",
        "Routine court filing and docket entry",
    ):
        result = classify_national_item(source, _item(title))
        assert result["attention_state"] == "suppressed"
        assert result["retained_for_audit"] is True
    local = _item("Bridge reopens", national_identity={"local_only": True})
    assert classify_national_item(source, local)["suppressed"] is True
    assert classify_national_item(
        {"source_family": "bls"}, _item("Monthly employment report")
    )["suppressed"] is True
    assert classify_national_item(
        {"source_family": "bls", "economic_release_terms": ["employment"]},
        _item("Monthly employment report"),
    )["suppressed"] is False
    assert classify_national_item(
        {"source_family": "reddit"}, _item("Unverified post about outage")
    )["suppressed"] is True
    assert classify_national_item(
        {"source_family": "agency_press"}, _item("Agency announces new office")
    )["suppressed"] is True
    alert = _item("Routine press release on severe storm", nws_alert={
        "status": "Actual", "severity": "Severe", "instruction": "Shelter now."
    })
    assert classify_national_item(source, alert)["attention_state"] == "suppressed"
    nws_source = {"source_family": "nws", "official_status": "official"}
    assert classify_national_item(nws_source, alert)["attention_state"] == "elevated"
    assert classify_national_item(nws_source, alert)["official_impact_score"] == 25


def test_national_policy_elevates_verified_public_safety_signals():
    cases = [
        ("nhtsa", _item("Recall", nhtsa_recall={"park_it": True})),
        ("cisa", _item("KEV", cisa_kev={"cve_id": "CVE-2026-1234"})),
        ("faa", _item("Airport", faa_nas_status={
            "events": [{"event_type": "ground_stop"}]
        })),
        ("fema", _item("Disaster", openfema_declaration={
            "recent_declaration_at_refresh": True
        })),
        ("cisa", _item("Cyber", cisa_advisory={"directive_flag": True})),
        ("fsis", _item("Recall", fsis_recall={
            "current_notice": True, "recall_classification": "Class I"
        })),
    ]
    assert all(classify_national_item(
        {"source_family": family, "official_status": "official"}, item
    )["attention_state"] == "elevated" for family, item in cases)
    unsupported = _item("Claim", national_identity={
        "official_disaster_declaration": True,
        "public_health_action_guidance": True,
        "official_public_alert": True,
    })
    assert classify_national_item(
        {"source_family": "national_news", "official_status": "official"}, unsupported
    )["attention_state"] == "background"
    assert classify_national_item(
        {"source_family": "social", "official_status": "unofficial"},
        _item("Claim", national_identity={"official_disaster_declaration": True}),
    )["suppressed"] is True


def test_national_suppressed_items_are_auditable_but_absent_from_attention(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    fixture = tmp_path / "national.json"
    fixture.write_text(json.dumps({"items": [
        {"title": "Opinion: A columnist assesses policy",
         "url": "https://example.org/opinion", "published_at": "2026-10-15T12:00:00Z"},
        {"title": "National bridge infrastructure repair announced",
         "url": "https://example.org/bridge", "published_at": "2026-10-15T12:00:00Z"},
    ]}))
    config_path = tmp_path / "config.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        national: {{enabled: true}}
        news:
          enabled: true
          scopes:
            NATIONAL:
              enabled: true
              sources:
                - id: national_news_fixture
                  name: National news fixture
                  kind: api_json
                  parser: generic_json_items
                  source_family: national_news
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT title, evidence_json FROM news_items WHERE scope = 'NATIONAL'"
        ).fetchall()
        clusters = conn.execute(
            "SELECT title FROM news_clusters WHERE scope = 'NATIONAL'"
        ).fetchall()
        view = get_news_scope_view(conn, config, "NATIONAL")
    assert len(rows) == 2
    suppressed = next(row for row in rows if row["title"].startswith("Opinion"))
    evidence = json_loads(suppressed["evidence_json"], {})
    assert evidence["national_policy"]["suppressed"] is True
    assert evidence["national_event"]["attention_state"] == "suppressed"
    assert [row["title"] for row in clusters] == ["National bridge infrastructure repair announced"]
    assert [row["title"] for row in view["items"]] == [
        "National bridge infrastructure repair announced"
    ]
