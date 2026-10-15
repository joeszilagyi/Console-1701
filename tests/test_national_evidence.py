from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from jinja2 import Environment, FileSystemLoader

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_item_detail, get_news_scope_view

FIXTURE = Path(__file__).parent / "fixtures/news/national_nhtsa_recalls.json"
TEMPLATES = Path(__file__).resolve().parents[1] / "console1701/templates"


def test_national_evidence_contract_and_drawer_are_offline(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("NATIONAL evidence read must not fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "national.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        national: {{enabled: true}}
        news:
          enabled: true
          scopes:
            NATIONAL:
              enabled: true
              sources:
                - id: nhtsa_evidence_fixture
                  name: NHTSA evidence fixture
                  kind: api_json
                  parser: nhtsa_recalls_json
                  source_family: nhtsa
                  source_class: official_recall
                  official_status: official
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] >= 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        view = get_news_scope_view(conn, config, "NATIONAL")
        row = conn.execute(
            "SELECT id, evidence_json FROM news_items WHERE scope = 'NATIONAL' LIMIT 1"
        ).fetchone()
        detail = get_news_item_detail(conn, int(row["id"]))
        cluster = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope = 'NATIONAL' LIMIT 1"
        ).fetchone()
    assert detail is not None and cluster is not None
    contract = detail["evidence"]["national"]
    assert contract["contract_version"] == 1
    assert contract["source_key"] == "nhtsa_evidence_fixture"
    assert contract["source_name"] == "NHTSA evidence fixture"
    assert contract["source_family"] == "nhtsa"
    assert contract["official_status"] == "official"
    assert contract["item_url"] == detail["url"]
    assert contract["canonical_url"] == detail["canonical_url"]
    assert contract["published_at"] == detail["source_published_at"]
    assert contract["first_seen_at"] == detail["first_seen_at"]
    assert contract["last_seen_at"] == detail["last_seen_at"]
    assert contract["fetch_run_id"] == detail["evidence"]["ingest"]["fetch_run_id"]
    assert contract["parser"] == "nhtsa_recalls_json"
    assert contract["retention_expires_at"] == detail["expires_at"]
    assert contract["geography_basis"] == "not_provided"
    assert contract["event_type"] == "vehicle_recall"
    assert contract["event_confidence"] == "source_reported"
    assert contract["source_diversity_basis"] == "not_correlated"
    assert contract["ranking_features"]["official_severity_score"] > 0
    assert contract["low_public_value_penalty"] == 0
    assert contract["out_of_scope_penalty"] == 0
    assert contract["policy_notes"]
    event = json_loads(cluster["evidence_json"], {})["national_event"]
    assert event["member_evidence"][0]["source_key"] == "nhtsa_evidence_fixture"
    assert event["member_evidence"][0]["parser"] == "nhtsa_recalls_json"
    assert event["member_evidence"][0]["retention_expires_at"] == detail["expires_at"]
    assert event["member_evidence"][0]["policy_notes"]
    assert event["geography_basis"] == ["not_provided"]
    assert event["source_diversity_basis"] == "not_correlated"
    assert "NHTSA recall fields" in event["ranking"]["public_impact_basis"]
    html = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True).get_template(
        "news_panels.html"
    ).module.render_scope_page(view)
    assert "Geography basis" in html
    assert "Low-value / scope penalties" in html
    assert "NHTSA recall fields" in html
    assert "Source nhtsa_evidence_fixture" in html
