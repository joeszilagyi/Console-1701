from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/national_usgs_redwood_dyfi.json"


def _source() -> dict:
    return {
        "id": "usgs_eq_geojson", "scope": "NATIONAL", "kind": "api_json",
        "parser": "usgs_earthquake_geojson", "url": FIXTURE.resolve().as_uri(),
        "min_magnitude": 5.0,
    }


def test_usgs_dyfi_aggregates_observed_felt_states_without_zip_storage():
    item, = parse_fixture_items(_source(), FIXTURE.read_text())
    quake = item["evidence"]["usgs_earthquake"]
    assert quake["id"] == "nc75382936"
    dyfi = quake["dyfi_state_evidence"]
    assert dyfi["state_summary"] == [
        {"state": "CA", "response_count": 1704, "max_cdi": 6.3745},
        {"state": "NV", "response_count": 11, "max_cdi": 2.2372},
        {"state": "OR", "response_count": 6, "max_cdi": 2.0},
    ]
    assert dyfi["reported_states_at_threshold"] == ["CA", "NV"]
    assert dyfi["zip_locations_stored"] is False
    identity = item["evidence"]["national_identity"]
    assert identity["affected_states"] == ["CA", "NV"]
    assert identity["multi_state_impact"] is True
    assert "not observed damage" in identity["impact_scope_basis"]
    stored = json.dumps(item["evidence"])
    assert '"location"' not in stored and '"zip_code"' not in stored
    assert "<location" not in stored and len(stored) < 5000


def test_usgs_dyfi_rejects_wrong_event_product_and_markup():
    payload = json.loads(FIXTURE.read_text())
    payload["fixture_dyfi"]["product_url"] = payload["fixture_dyfi"][
        "product_url"
    ].replace("nc75382936", "other-event")
    with pytest.raises(NewsParserError, match="exact official product URL"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(FIXTURE.read_text())
    payload["fixture_dyfi"]["xml"] = "<!DOCTYPE foo><cdidata/>"
    with pytest.raises(NewsParserError, match="invalid bounded product metadata"):
        parse_fixture_items(_source(), json.dumps(payload))
    with pytest.raises(NewsParserError, match="NATIONAL local fixture"):
        parse_fixture_items(_source() | {"url": "https://earthquake.usgs.gov/feed"},
                            FIXTURE.read_text())


def test_usgs_dyfi_offline_scan_persists_multi_state_basis(tmp_path, monkeypatch):
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {"enabled": True, "scopes": {"NATIONAL": {"enabled": True,
                 "sources": [{"id": "usgs_eq_geojson", "enabled": True,
                              "url": FIXTURE.resolve().as_uri()}]}}},
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("DYFI fixture attempted HTTP"))
    ))
    result = run_news_scan(path)
    assert result["status"] == "complete" and result["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        item = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchone()
        cluster = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='NATIONAL'"
        ).fetchone()
    assert item is not None and cluster is not None
    item_evidence = json_loads(item["evidence_json"], {})
    cluster_evidence = json_loads(cluster["evidence_json"], {})["national_event"]
    assert "<location" not in item["evidence_json"]
    assert item_evidence["national_identity"]["multi_state_impact"] is True
    assert cluster_evidence["affected_states"] == ["ca", "nv"]
    assert cluster_evidence["ranking"]["factors"]["geographic_reach_score"] == 15
