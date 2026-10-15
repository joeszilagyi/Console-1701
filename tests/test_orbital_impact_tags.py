from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.orbital_impact import derive_orbital_impact
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/orbital/swpc_alerts.json"
SOURCE = {
    "id": "swpc_alerts_json", "name": "SWPC Alerts", "scope": "ORBITAL",
    "kind": "api_json", "parser": "swpc_alerts_json", "source_family": "swpc",
    "url": f"file://{FIXTURE}",
}


def test_impact_tags_use_official_fields_without_inventing_geographic_reach():
    warning = parse_fixture_items(SOURCE, FIXTURE.read_text())[0]
    impact = derive_orbital_impact(warning)
    assert impact["tags"] == ["AURORA", "RADIO", "SATELLITE"]
    assert impact["basis"]["RADIO"] == ["swpc_alert.potential_impacts.radio"]
    assert not any(tag.endswith("_IMPACT") for tag in impact["tags"])
    assert impact["geography_inferred"] is False


def test_configured_aurora_location_tags_local_or_regional_model_only():
    item = {"evidence": {
        "orbital_identity": {"event_type": "aurora_forecast"},
        "swpc_aurora": {
            "model_only": True, "grid_match_basis": "configured_coordinate_box",
            "model_value": 25, "location_scope": "LOCAL",
        },
    }}
    assert derive_orbital_impact(item)["tags"] == ["AURORA", "LOCAL_IMPACT", "SKY"]
    item["evidence"]["swpc_aurora"]["location_scope"] = "REGIONAL"
    assert derive_orbital_impact(item)["tags"] == ["AURORA", "REGIONAL_IMPACT", "SKY"]
    item["evidence"]["swpc_aurora"]["model_only"] = False
    assert derive_orbital_impact(item)["tags"] == []


def test_impact_type_tags_require_source_records_and_explicit_geography():
    cad = {"evidence": {
        "orbital_identity": {"event_type": "neo_close_approach"},
        "jpl_close_approach": {"designation": "2026 AB"},
    }}
    assert derive_orbital_impact(cad)["tags"] == ["NEO"]
    cad["evidence"]["orbital_identity"]["source_reported_impact_scope"] = "NATIONAL"
    assert derive_orbital_impact(cad)["tags"] == ["NATIONAL_IMPACT", "NEO"]
    cad["evidence"]["orbital_identity"]["source_reported_impact_scope"] = "planetary"
    assert derive_orbital_impact(cad)["tags"] == ["NEO"]


def test_orbital_scan_persists_impact_basis_and_keeps_canonical_scope(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    path = tmp_path / "config.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: true}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: swpc_alerts_json
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute(
            "SELECT scope, tags_json, evidence_json FROM news_items WHERE title LIKE 'WARNING%'"
        ).fetchone()
    assert row["scope"] == "ORBITAL"
    assert {"RADIO", "AURORA", "SATELLITE"} <= set(json_loads(row["tags_json"], []))
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["orbital_identity"]["impact_tags"] == [
        "AURORA", "RADIO", "SATELLITE",
    ]
    assert evidence["orbital_impact"]["basis"]["AURORA"] == [
        "swpc_alert.potential_impacts.aurora",
    ]
