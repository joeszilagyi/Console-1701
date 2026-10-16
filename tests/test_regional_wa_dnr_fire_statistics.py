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
from console1701.news.regional_registry import regional_registry_config_defaults
from console1701.news.regional_wa_dnr import QUERY_URL
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/regional_wa_dnr_fire_statistics.json"
NIFC = Path(__file__).parent / "fixtures/news/regional_nifc_imsr_wa.json"


def _source() -> dict:
    source = regional_registry_config_defaults("wa_dnr_fire_statistics")
    source["official_url"] = source["url"]
    source["url"] = FIXTURE.as_uri()
    return source


def test_dnr_statistics_preserve_identity_county_and_unknown_active_state():
    source = _source()
    assert source["official_url"] == QUERY_URL
    items = parse_fixture_items(source, FIXTURE.read_text())
    assert len(items) == 4
    reports = {item["evidence"]["wa_dnr_fire_statistics"]["fire_name"]: item
               for item in items}
    hatch = reports["HATCH GRADE"]
    data = hatch["evidence"]["wa_dnr_fire_statistics"]
    assert data["fire_event_id"] == 89929
    assert data["county"] == "Walla Walla"
    assert data["reported_acres"] == 9584
    assert data["discovery_date"] == "2026-09-29"
    assert data["date_precision"] == "day"
    assert data["lifecycle_status"] == "unknown"
    assert data["active_fire_claimed"] is False
    assert data["public_impact_inferred"] is False
    assert "active" not in hatch["tags"]
    assert reports["SUTHERLAND"]["evidence"]["wa_dnr_fire_statistics"][
        "lifecycle_status"
    ] == "out_date_reported"
    assert reports["SUTHERLAND"]["evidence"]["wa_dnr_fire_statistics"][
        "fire_out_date"
    ] == "2026-09-28"
    contract = build_regional_event_contract(source, hatch, hashed_url="a" * 64)
    assert contract["matching_basis"] == "official_wa_dnr_fire_event_id"
    assert contract["geography"]["county"] == "Walla Walla"
    assert contract["event_type"] == "wildfire_update"
    assert "active state" in contract["public_impact_basis"]


@pytest.mark.parametrize("change", [
    lambda payload: payload["features"].append(deepcopy(payload["features"][0])),
    lambda payload: payload["features"][0]["attributes"].update(ACRES_BURNED=-1),
    lambda payload: payload["features"][0]["attributes"].update(DSCVR_DT=None),
    lambda payload: payload["features"][0]["attributes"].update(
        FIRE_OUT_DT=1_780_000_000_000
    ),
    lambda payload: payload.update(error={"message": "layer failed"}),
])
def test_dnr_statistics_reject_ambiguous_or_invalid_rows(change):
    payload = json.loads(FIXTURE.read_text())
    change(payload)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(payload))


def test_dnr_statistics_offline_scan_stays_distinct_from_unrelated_nifc(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    path = tmp_path / "regional.yml"
    nifc_url = regional_registry_config_defaults("nifc_imsr_current_wa")["url"]
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - id: wa_dnr_fire_statistics
                  enabled: true
                  url: "{FIXTURE.as_uri()}"
                  official_url: "{QUERY_URL}"
                - id: nifc_imsr_current_wa
                  enabled: true
                  url: "{NIFC.as_uri()}"
                  official_url: "{nifc_url}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 6
    with connect_db(load_config(path)["_db_path"]) as conn:
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='REGIONAL'"
        ).fetchall()
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='REGIONAL'"
        ).fetchall()
    assert len(clusters) == 6
    assert all(len(json_loads(row["evidence_json"], {})["item_ids"]) == 1
               for row in clusters)
    dnr_rows = [json_loads(row["evidence_json"], {}) for row in rows
                if "wa_dnr_fire_statistics" in row["evidence_json"]]
    assert len(dnr_rows) == 4
    assert all(row["ingest"]["fixture_only"] is True for row in dnr_rows)
    assert all(row["regional_event"]["confidence"] == "high" for row in dnr_rows)
    assert all(row["wa_dnr_fire_statistics"]["active_fire_claimed"] is False
               for row in dnr_rows)

    live_path = tmp_path / "live.yml"
    live_path.write_text(dedent("""
        paths: {repo_roots: [], explicit_repos: []}
        news:
          enabled: true
          fetch_policy: {allow_official_http: true}
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - {id: wa_dnr_fire_statistics, enabled: true}
    """).strip() + "\n")
    assert run_news_scan(live_path)["status"] == "partial"
    with connect_db(load_config(live_path)["_db_path"]) as conn:
        live_run = conn.execute(
            "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert live_run["status"] == "policy_blocked"

    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items(regional_registry_config_defaults("wa_dnr_fire_statistics"),
                            FIXTURE.read_text())
