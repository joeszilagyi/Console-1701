from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import is_supported_official_source
from console1701.news.orbital_flares import FLARES_URL
from console1701.news.orbital_registry import get_orbital_source_registry_entry
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import list_orbital_items_by_facet

FIXTURE = Path(__file__).parent / "fixtures/news/orbital_swpc_xray_flares.json"
SOURCE = {
    "id": "swpc_xray_flux_summary", "name": "SWPC GOES flare list",
    "scope": "ORBITAL", "kind": "api_json", "parser": "swpc_xray_flares_json",
    "source_family": "swpc", "official_url": FLARES_URL,
    "url": f"file://{FIXTURE}",
}


def test_swpc_flare_fixture_keeps_m_class_observations_without_alert_claims():
    entry = get_orbital_source_registry_entry("swpc_xray_flux_summary")
    assert entry["raw_url"] == FLARES_URL
    assert entry["parser"] == "swpc_xray_flares_json"
    assert entry["enabled"] is False
    assert not is_supported_official_source({**SOURCE, "url": FLARES_URL,
                                             "verification_status": "verified"})
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 2
    first, stronger = items
    assert first["evidence"]["swpc_xray_flare"]["max_class"] == "M1.3"
    assert stronger["evidence"]["swpc_xray_flare"]["max_class"] == "M6.4"
    assert stronger["source_published_at"] == "2026-10-10T15:10:00+00:00"
    assert stronger["evidence"]["orbital_identity"]["event_type"] == "solar_flare"
    assert stronger["evidence"]["orbital_safety"]["official_alert"] is False
    assert stronger["evidence"]["swpc_xray_flare"]["earth_impact_inferred"] is False
    assert "description" not in stronger["evidence"]["swpc_xray_flare"]
    assert first["url"] != stronger["url"]


def test_swpc_flare_rejects_bad_scope_identity_time_and_overflow():
    payload = json.loads(FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="exact ORBITAL"):
        parse_fixture_items({**SOURCE, "official_url": "https://example.test/x.json"},
                            FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="duplicate"):
        parse_fixture_items(SOURCE, json.dumps([payload[0], payload[0]]))
    bad = dict(payload[0], max_time="2026-10-09T12:00:00Z")
    with pytest.raises(NewsParserError, match="invalid event metadata"):
        parse_fixture_items(SOURCE, json.dumps([bad]))
    with pytest.raises(NewsParserError, match="bounded array"):
        parse_fixture_items(SOURCE, json.dumps([payload[2]] * 201))


def test_swpc_flare_offline_scan_stores_observation_not_operational_impact(
    tmp_path, monkeypatch
):
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("unexpected HTTP"))
    ))
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
                - id: swpc_xray_flux_summary
                  enabled: true
                  official_url: "{FLARES_URL}"
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    result = run_news_scan(path)
    assert result["status"] == "complete" and result["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        items = list_orbital_items_by_facet(conn, "event_type", "solar_flare")
        assert len(items) == 2
        rows = conn.execute("SELECT evidence_json FROM news_items ORDER BY id").fetchall()
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert all(item["orbital_impact"]["tags"] == [] for item in evidence)
    assert all(item["orbital_safety"]["official_alert"] is False for item in evidence)
    assert sorted(item["orbital_event"]["ranking"]["factors"][
        "official_severity_score"
    ] for item in evidence) == [12, 20]
