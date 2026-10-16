from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.regional_contract import build_regional_event_contract
from console1701.news.regional_nifc_wfigs import QUERY_URL
from console1701.news.regional_registry import regional_registry_config_defaults
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/news"
WFIGS = FIXTURES / "regional_nifc_wfigs_current_wa.json"
IMSR = FIXTURES / "regional_nifc_imsr_wa.json"
NWCC = FIXTURES / "regional_nwcc_large_fire_wa.json"


def _source(key: str, path: Path) -> dict:
    source = regional_registry_config_defaults(key)
    source["official_url"] = source["url"]
    source["url"] = path.resolve().as_uri()
    return source


def test_wfigs_observed_fixture_keeps_current_candidate_distinct_from_active_fire():
    source = _source("nifc_wfigs_current_wa", WFIGS)
    assert source["official_url"] == QUERY_URL
    items = parse_fixture_items(source, WFIGS.read_text())
    assert len(items) == 15
    by_name = {item["evidence"]["nifc_wfigs"]["fire_name"]: item for item in items}
    sisi = by_name["SISI"]["evidence"]["nifc_wfigs"]
    assert sisi["unique_fire_identifier"] == "2026-WAOWF-260664"
    assert sisi["county"] == "Chelan"
    assert sisi["reported_acres"] == 4615
    assert sisi["percent_contained"] == 34
    assert sisi["active_fire_candidate"] is True
    assert sisi["active_fire_claimed"] is False
    assert sisi["public_impact_inferred"] is False
    assert sisi["evacuation_claimed"] is False
    assert sisi["query_url"] == QUERY_URL
    assert by_name["SINLAHEKIN"]["evidence"]["nifc_wfigs"]["percent_contained"] == 100
    assert all(item["evidence"]["nifc_wfigs"]["active_fire_claimed"] is False
               for item in items)

    imsr = parse_fixture_items(_source("nifc_imsr_current_wa", IMSR), IMSR.read_text())
    imsr_sisi = next(item for item in imsr
                     if item["evidence"]["nifc_imsr"]["fire_name"] == "Sisi")
    wfigs_event = build_regional_event_contract(source, by_name["SISI"], hashed_url="a" * 64)
    imsr_event = build_regional_event_contract(
        _source("nifc_imsr_current_wa", IMSR), imsr_sisi, hashed_url="b" * 64
    )
    assert wfigs_event["event_key"] == imsr_event["event_key"]
    assert wfigs_event["matching_basis"] == "official_nifc_wfigs_unique_fire_identifier"
    assert wfigs_event["geography"]["county"] == "Chelan"
    spoofed = build_regional_event_contract(
        {**source, "source_family": "regional_news"}, by_name["SISI"], hashed_url="c" * 64
    )
    assert spoofed["matching_basis"] == "isolated_url"


@pytest.mark.parametrize("change", [
    lambda payload: payload.update(exceededTransferLimit=True),
    lambda payload: payload["features"][0]["attributes"].update(POOState="US-OR"),
    lambda payload: payload["features"][0]["attributes"].update(
        ActiveFireCandidate=0
    ),
    lambda payload: payload["features"][0]["attributes"].update(PercentContained=101),
    lambda payload: payload["features"][0]["attributes"].update(
        ModifiedOnDateTime_dt=0
    ),
    lambda payload: payload["features"].append(deepcopy(payload["features"][0])),
])
def test_wfigs_rejects_invalid_or_ambiguous_rows(change):
    payload = json.loads(WFIGS.read_text())
    change(payload)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source("nifc_wfigs_current_wa", WFIGS), json.dumps(payload))


def test_wfigs_rejects_wrong_source_and_unbounded_payload():
    raw = WFIGS.read_text()
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items(regional_registry_config_defaults("nifc_wfigs_current_wa"), raw)
    source = _source("nifc_wfigs_current_wa", WFIGS)
    with pytest.raises(NewsParserError, match="exact official query"):
        parse_fixture_items({**source, "official_url": "https://example.test/query"}, raw)
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(source, " " * 32_769)


def test_wfigs_imsr_nwcc_scan_dedupes_same_fire_without_active_claim(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected HTTP")),
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
                - id: nifc_wfigs_current_wa
                  enabled: true
                  url: "{WFIGS.resolve().as_uri()}"
                  official_url: "{QUERY_URL}"
                - id: nifc_imsr_current_wa
                  enabled: true
                  url: "{IMSR.resolve().as_uri()}"
                  official_url: "{regional_registry_config_defaults('nifc_imsr_current_wa')['url']}"
                - id: nwcc_large_fire_wa
                  enabled: true
                  url: "{NWCC.resolve().as_uri()}"
                  official_url: "{regional_registry_config_defaults('nwcc_large_fire_wa')['url']}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 21
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        clusters = conn.execute(
            "SELECT cluster_key, evidence_json FROM news_clusters WHERE scope='REGIONAL'"
        ).fetchall()
        items = conn.execute(
            "SELECT id, evidence_json FROM news_items WHERE scope='REGIONAL'"
        ).fetchall()
    events = [json_loads(row["evidence_json"], {}) for row in clusters]
    evidence = {row["id"]: json_loads(row["evidence_json"], {}) for row in items}
    wfigs = [row for row in evidence.values() if "nifc_wfigs" in row]
    assert len(wfigs) == 15
    for fire_id, expected_count in (
        ("2026-WAOWF-260664", 3),
        ("2026-WAOWF-260406", 3),
    ):
        item_id = next(item_id for item_id, row in evidence.items()
                       if (row.get("nifc_wfigs") or {}).get("unique_fire_identifier") == fire_id)
        event = next(row for row in events if item_id in row["item_ids"])
        assert len(event["item_ids"]) == expected_count
        assert event["families"] == ["wildfire_federal"]
        assert event["corroborated"] is False
    assert all(row["nifc_wfigs"]["active_fire_claimed"] is False for row in wfigs)
    assert all(row["ranking"]["factors"]["regional_active_alert_bonus"] == 0
               for row in wfigs)

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
                - {id: nifc_wfigs_current_wa, enabled: true}
    """).strip() + "\n")
    assert run_news_scan(live_config)["status"] == "partial"
    live = load_config(live_config)
    with connect_db(live["_db_path"]) as conn:
        run = conn.execute(
            "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert run["status"] == "policy_blocked"
