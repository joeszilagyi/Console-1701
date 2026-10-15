from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from starlette.requests import Request

from console1701.api import build_router
from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/global_gdacs.geojson"


def test_global_evidence_contract_persists_facts_and_unassessed_fields(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("unexpected HTTP fetch")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "global.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: gdacs_contract_fixture
                  name: GDACS contract fixture
                  kind: api_json
                  parser: gdacs_geojson
                  source_family: gdacs
                  official_status: official
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute(
            "SELECT scope, url, first_seen_at, last_seen_at, expires_at, evidence_json "
            "FROM news_items WHERE scope = 'GLOBAL'"
        ).fetchone()
    contract = json_loads(row["evidence_json"], {})["global"]
    assert contract["contract_version"] == 1
    assert contract["source_key"] == "gdacs_contract_fixture"
    assert contract["source_name"] == "GDACS contract fixture"
    assert contract["source_family"] == "gdacs"
    assert contract["official_status"] == "official"
    assert contract["item_url"] == row["url"]
    assert contract["first_seen_at"] == row["first_seen_at"]
    assert contract["last_seen_at"] == row["last_seen_at"]
    assert contract["fetch_run_id"] is not None
    assert contract["parser"] == "gdacs_geojson"
    assert contract["affected_countries"] == ["Costa Rica"]
    assert contract["geography_basis"] == "official_source_fields"
    assert contract["event_type"] == "EQ"
    assert contract["event_confidence"] == "source_reported"
    assert contract["source_diversity_basis"] == "not_correlated"
    assert contract["public_impact_basis"] is None
    assert contract["low_public_value_penalty"] is None
    assert contract["out_of_scope_penalty"] is None
    assert contract["matching_tokens"] == []

    router = build_router(str(config_path))
    route = next(
        route.endpoint for route in router.routes
        if getattr(route, "path", None) == "/{scope}"
    )
    request = Request({
        "type": "http", "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": "/GLOBAL", "raw_path": b"/GLOBAL", "query_string": b"", "headers": [],
        "client": ("127.0.0.1", 12345), "server": ("testserver", 80), "root_path": "",
    })
    body = route(request, "GLOBAL").body.decode()
    assert "GDACS contract fixture" in body
    assert "Source diversity" in body
    assert "not_correlated" in body
    assert "Costa Rica" in body
    assert "not assessed" in body
