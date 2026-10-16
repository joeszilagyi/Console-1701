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
from console1701.news.regional_events import correlate_regional_items
from console1701.news.regional_nifc_wfigs import QUERY_URL
from console1701.news.regional_registry import regional_registry_config_defaults
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/news"
WFIGS = FIXTURES / "regional_nifc_wfigs_current_wa.json"
IMSR = FIXTURES / "regional_nifc_imsr_wa.json"
NWCC = FIXTURES / "regional_nwcc_large_fire_wa.json"
DNR = FIXTURES / "regional_wa_dnr_fire_statistics.json"


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


def _correlation_row(item: dict, source: dict, item_id: int) -> dict:
    item = deepcopy(item)
    item["id"] = item_id
    item["evidence"]["source"] = {
        "source_key": source["id"], "source_family": source["source_family"],
        "official_status": source["official_status"],
    }
    item["evidence"]["regional_event"] = build_regional_event_contract(
        source, item, hashed_url=f"{item_id:064d}"
    )
    return item


def test_wfigs_dnr_matches_only_name_county_and_exact_discovery_day():
    wfigs_source = _source("nifc_wfigs_current_wa", WFIGS)
    dnr_source = _source("wa_dnr_fire_statistics", DNR)
    wfigs = parse_fixture_items(wfigs_source, WFIGS.read_text())
    dnr = parse_fixture_items(dnr_source, DNR.read_text())
    wfigs_by_name = {item["evidence"]["nifc_wfigs"]["fire_name"].casefold(): item
                     for item in wfigs}
    dnr_by_name = {item["evidence"]["wa_dnr_fire_statistics"]["fire_name"].casefold(): item
                   for item in dnr}
    left = _correlation_row(wfigs_by_name["sisi"], wfigs_source, 1)
    right = _correlation_row(dnr_by_name["sisi"], dnr_source, 2)
    group = correlate_regional_items([left, right])[0]
    assert group["item_ids"] == [1, 2]
    assert group["matches"][0]["basis"] == [
        "event_type", "fire_incident", "county", "source_start_date",
        "independent_family",
    ]
    assert group["corroborated"] is True

    wrong_county = deepcopy(right)
    wrong_county["evidence"]["regional_identity"]["county"] = "Pierce"
    wrong_county["evidence"]["regional_event"]["geography"]["county"] = "Pierce"
    assert [group["item_ids"] for group in correlate_regional_items([
        left, wrong_county
    ])] == [[1], [2]]
    wrong_date = deepcopy(right)
    wrong_date["evidence"]["wa_dnr_fire_statistics"]["discovery_date"] = "2026-08-15"
    assert [group["item_ids"] for group in correlate_regional_items([
        left, wrong_date
    ])] == [[1], [2]]
    little = _correlation_row(wfigs_by_name["little giant"], wfigs_source, 3)
    dnr_little = _correlation_row(dnr_by_name["little giant"], dnr_source, 4)
    assert [group["item_ids"] for group in correlate_regional_items([
        little, dnr_little
    ])] == [[3], [4]]  # Source dates differ by one UTC day.


def test_wfigs_dnr_offline_scan_persists_only_verified_cross_family_pairs(
    tmp_path, monkeypatch,
):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected HTTP")),
    )
    wfigs_url = regional_registry_config_defaults("nifc_wfigs_current_wa")["url"]
    dnr_url = regional_registry_config_defaults("wa_dnr_fire_statistics")["url"]
    config_path = tmp_path / "wfigs-dnr.yml"
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
                  official_url: "{wfigs_url}"
                - id: wa_dnr_fire_statistics
                  enabled: true
                  url: "{DNR.resolve().as_uri()}"
                  official_url: "{dnr_url}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 46
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='REGIONAL'"
        ).fetchall()
        items = conn.execute(
            "SELECT id, evidence_json FROM news_items WHERE scope='REGIONAL'"
        ).fetchall()
    by_id = {row["id"]: json_loads(row["evidence_json"], {}) for row in items}
    events = [json_loads(row["evidence_json"], {}) for row in clusters]
    paired = [event for event in events if len(event["item_ids"]) == 2]
    assert len(paired) == 9
    assert len(events) == 37
    names = set()
    for event in paired:
        assert set(event["families"]) == {"wa_dnr", "wildfire_federal"}
        assert event["corroborated"] is True
        assert event["correlation"]["matches"][0]["basis"] == [
            "event_type", "fire_incident", "county", "source_start_date",
            "independent_family",
        ]
        dnr = next(by_id[item_id]["wa_dnr_fire_statistics"] for item_id in event["item_ids"]
                   if "wa_dnr_fire_statistics" in by_id[item_id])
        names.add(dnr["fire_name"])
        for item_id in event["item_ids"]:
            factors = by_id[item_id]["ranking"]["factors"]
            assert factors["regional_active_alert_bonus"] == 0
            assert factors["regional_public_impact_bonus"] == 0
    assert "SISI" in names
    assert "LITTLE GIANT" not in names
    assert "THREE QUEENS" not in names


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
