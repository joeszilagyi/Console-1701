from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.regional_contract import build_regional_event_contract
from console1701.news.regional_nwcc_large_fire import QUERY_URL
from console1701.news.regional_registry import regional_registry_config_defaults
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/regional_nwcc_large_fire_wa.json"
NIFC = Path(__file__).parent / "fixtures/news/regional_nifc_imsr_wa.json"


def _source(key: str, path: Path) -> dict:
    source = regional_registry_config_defaults(key)
    source["official_url"] = source["url"]
    source["url"] = path.as_uri()
    return source


def test_nwcc_large_fire_fixture_preserves_report_without_activity_claim():
    source = _source("nwcc_large_fire_wa", FIXTURE)
    assert source["official_url"] == QUERY_URL
    items = parse_fixture_items(source, FIXTURE.read_text())
    assert len(items) == 4
    by_name = {item["evidence"]["nwcc_large_fire"]["fire_name"]: item for item in items}
    little = by_name["Little Giant"]
    report = little["evidence"]["nwcc_large_fire"]
    assert report["normalized_fire_key"] == "2026-WAOWF-260406"
    assert report["percent_contained"] == 95
    assert report["reported_acres"] == 172912
    assert report["edit_at"] == "2026-10-15T20:15:34.682000+00:00"
    assert report["active_fire_claimed"] is False
    assert report["public_impact_inferred"] is False
    assert little["title"].endswith("(WAOWF unit)")
    assert by_name["Sinlahekin"]["source_published_at"] < little["source_published_at"]

    nifc_source = _source("nifc_imsr_current_wa", NIFC)
    nifc = parse_fixture_items(nifc_source, NIFC.read_text())
    nifc_little = next(item for item in nifc if item["evidence"]["nifc_imsr"]["fire_name"]
                       == "Little Giant")
    nwcc_event = build_regional_event_contract(source, little, hashed_url="a" * 64)
    nifc_event = build_regional_event_contract(nifc_source, nifc_little, hashed_url="b" * 64)
    assert nwcc_event["event_key"] == nifc_event["event_key"]
    assert nwcc_event["matching_basis"] == "official_nwcc_unit_number_start_year"
    assert nwcc_event["geography"]["basis"] == "official_WA_management_unit_not_fire_point"


@pytest.mark.parametrize("change", [
    lambda payload: payload.update(exceededTransferLimit=True),
    lambda payload: payload["features"][0]["attributes"].update(UNIT_ID="ORMHF"),
    lambda payload: payload["features"][0]["attributes"].update(START_DATE="bad"),
    lambda payload: payload["features"][0]["attributes"].update(Percent_Contained=101),
    lambda payload: payload["features"][0]["attributes"].update(
        INCIWEB="https://example.test/incident-information/waowf-little-giant-fire"
    ),
    lambda payload: payload["features"].append(deepcopy(payload["features"][0])),
])
def test_nwcc_large_fire_rejects_invalid_or_ambiguous_rows(change):
    payload = json.loads(FIXTURE.read_text())
    change(payload)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source("nwcc_large_fire_wa", FIXTURE), json.dumps(payload))


def test_nwcc_and_nifc_offline_scan_joins_same_incidents_without_corroboration(
    tmp_path, monkeypatch,
):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    config_path = tmp_path / "regional.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - id: nwcc_large_fire_wa
                  enabled: true
                  url: "{FIXTURE.as_uri()}"
                  official_url: "{QUERY_URL}"
                - id: nifc_imsr_current_wa
                  enabled: true
                  url: "{NIFC.as_uri()}"
                  official_url: "{regional_registry_config_defaults('nifc_imsr_current_wa')['url']}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 6
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='REGIONAL'"
        ).fetchall()
    evidence = [json_loads(row["evidence_json"], {}) for row in clusters]
    assert len(evidence) == 4
    paired = [row for row in evidence if len(row["item_ids"]) == 2]
    assert len(paired) == 2
    assert all(row["corroborated"] is False for row in paired)
    assert all(row["families"] == ["wildfire_federal"] for row in paired)
    assert all(row["correlation"]["matches"][0]["basis"] == ["shared_official_event_id"]
               for row in paired)

    live_config = tmp_path / "live.yml"
    live_config.write_text(dedent("""
        paths: {repo_roots: [], explicit_repos: []}
        news:
          enabled: true
          fetch_policy: {allow_official_http: true}
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - {id: nwcc_large_fire_wa, enabled: true}
    """).strip() + "\n")
    assert run_news_scan(live_config)["status"] == "partial"
    live = load_config(live_config)
    with connect_db(live["_db_path"]) as conn:
        run = conn.execute(
            "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert run["status"] == "policy_blocked"

    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items(regional_registry_config_defaults("nwcc_large_fire_wa"),
                            FIXTURE.read_text())
