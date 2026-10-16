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
from console1701.news.regional_nwcc_point_daily import QUERY_URL
from console1701.news.regional_registry import regional_registry_config_defaults
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/regional_nwcc_point_daily_wa.json"
NWCC_LARGE = Path(__file__).parent / "fixtures/news/regional_nwcc_large_fire_wa.json"


def _source(key: str, path: Path) -> dict:
    source = regional_registry_config_defaults(key)
    source["official_url"] = source["url"]
    source["url"] = path.as_uri()
    return source


def test_nwcc_daily_snapshot_preserves_dated_status_and_shared_identity():
    source = _source("nwcc_point_daily_wa", FIXTURE)
    assert source["official_url"] == QUERY_URL
    items = parse_fixture_items(source, FIXTURE.read_text())
    assert len(items) == 4
    by_name = {item["evidence"]["nwcc_point_daily"]["fire_name"]: item
               for item in items}
    assert set(by_name) == {"SISI", "SINLAHEKIN", "LITTLE GIANT", "Luna"}
    sisi = by_name["SISI"]
    report = sisi["evidence"]["nwcc_point_daily"]
    assert report["normalized_fire_key"] == "2026-WAOWF-260664"
    assert report["status_at_source_snapshot"] == "Active"
    assert report["source_data_last_edit_at"] == "2026-10-07T13:48:16.887000+00:00"
    assert report["active_now_verified"] is False
    assert report["public_impact_inferred"] is False
    assert "Current activity and public impact are unverified" in sisi["description"]
    large_source = _source("nwcc_large_fire_wa", NWCC_LARGE)
    large = parse_fixture_items(large_source, NWCC_LARGE.read_text())
    large_sisi = next(item for item in large
                      if item["evidence"]["nwcc_large_fire"]["fire_name"] == "Sisi")
    assert (build_regional_event_contract(source, sisi, hashed_url="a" * 64)["event_key"]
            == build_regional_event_contract(large_source, large_sisi,
                                             hashed_url="b" * 64)["event_key"])


@pytest.mark.parametrize("change", [
    lambda payload: payload.update(data_last_edit_ms=None),
    lambda payload: payload["query"].update(exceededTransferLimit=True),
    lambda payload: payload["query"]["features"][0]["attributes"].update(STATUS="Contained"),
    lambda payload: payload["query"]["features"][0]["geometry"].update(y=40),
    lambda payload: payload["query"]["features"][0]["attributes"].update(
        INCIWEB="https://example.test/incident-information/waowf-sisi-fire"
    ),
    lambda payload: payload["query"]["features"].append(
        deepcopy(payload["query"]["features"][0])),
])
def test_nwcc_daily_rejects_ambiguous_wa_rows(change):
    payload = json.loads(FIXTURE.read_text())
    change(payload)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source("nwcc_point_daily_wa", FIXTURE), json.dumps(payload))


def test_nwcc_daily_offline_scan_dedupes_same_family_and_blocks_live(tmp_path, monkeypatch):
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
                - id: nwcc_point_daily_wa
                  enabled: true
                  url: "{FIXTURE.as_uri()}"
                  official_url: "{QUERY_URL}"
                - id: nwcc_large_fire_wa
                  enabled: true
                  url: "{NWCC_LARGE.as_uri()}"
                  official_url: "{regional_registry_config_defaults('nwcc_large_fire_wa')['url']}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 8
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='REGIONAL'"
        ).fetchall()
    evidence = [json_loads(row["evidence_json"], {}) for row in clusters]
    assert len(evidence) == 4
    paired = [row for row in evidence if len(row["item_ids"]) == 2]
    assert len(paired) == 4
    assert all(row["corroborated"] is False for row in paired)
    assert all(row["families"] == ["wildfire_federal"] for row in paired)

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
                - {id: nwcc_point_daily_wa, enabled: true}
    """).strip() + "\n")
    assert run_news_scan(live_config)["status"] == "partial"
    with connect_db(load_config(live_config)["_db_path"]) as conn:
        run = conn.execute(
            "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert run["status"] == "policy_blocked"
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items(regional_registry_config_defaults("nwcc_point_daily_wa"),
                            FIXTURE.read_text())
