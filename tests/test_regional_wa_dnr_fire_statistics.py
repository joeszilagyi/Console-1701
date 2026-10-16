from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.regional_contract import build_regional_event_contract
from console1701.news.regional_events import correlate_regional_items
from console1701.news.regional_registry import regional_registry_config_defaults
from console1701.news.regional_wa_dnr import QUERY_URL, SMALL_QUERY_URL
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/regional_wa_dnr_fire_statistics.json"
SMALL_FIXTURE = Path(__file__).parent / "fixtures/news/regional_wa_dnr_fire_statistics_small.json"
NWCC = Path(__file__).parent / "fixtures/news/regional_nwcc_large_fire_wa.json"


def _source() -> dict:
    source = regional_registry_config_defaults("wa_dnr_fire_statistics")
    source["official_url"] = source["url"]
    source["url"] = FIXTURE.as_uri()
    return source


def test_dnr_statistics_preserve_identity_county_and_unknown_active_state():
    source = _source()
    assert source["official_url"] == QUERY_URL
    items = parse_fixture_items(source, FIXTURE.read_text())
    assert len(items) == 31
    reports = {item["evidence"]["wa_dnr_fire_statistics"]["fire_name"]: item
               for item in items}
    hatch = reports["HATCH GRADE"]
    data = hatch["evidence"]["wa_dnr_fire_statistics"]
    assert data["fire_event_id"] == 89929
    assert data["county"] == "Walla Walla"
    assert data["reported_acres"] == 9584
    assert data["discovery_date"] == "2026-09-29"
    assert data["date_precision"] == "day"
    assert data["source_date_zone"] == "America/Los_Angeles"
    assert data["lifecycle_status"] == "unknown"
    assert data["active_fire_claimed"] is False
    assert data["public_impact_inferred"] is False
    assert "active" not in hatch["tags"]
    assert reports["COLWASH"]["evidence"]["wa_dnr_fire_statistics"][
        "lifecycle_status"
    ] == "out_date_reported"
    assert reports["COLWASH"]["evidence"]["wa_dnr_fire_statistics"][
        "fire_out_date"
    ] == "2026-08-28"
    assert reports["PEARL HILL"]["evidence"]["wa_dnr_fire_statistics"][
        "control_date"
    ] == "2026-08-01"  # 2026-08-02 02:08 UTC is August 1 in Washington.
    assert {reports[name]["evidence"]["wa_dnr_fire_statistics"]["discovery_date"]
            for name in ("SISI", "LITTLE GIANT", "SINLAHEKIN")} == {
        "2026-08-14", "2026-07-15", "2026-07-26",
    }
    contract = build_regional_event_contract(source, hatch, hashed_url="a" * 64)
    assert contract["matching_basis"] == "official_wa_dnr_fire_event_id"
    assert contract["geography"]["county"] == "Walla Walla"
    assert contract["event_type"] == "wildfire_update"
    assert "active state" in contract["public_impact_basis"]


def test_dnr_source_date_uses_pacific_day_at_utc_boundary():
    payload = json.loads(FIXTURE.read_text())
    payload["features"] = payload["features"][:1]
    payload["features"][0]["attributes"]["DSCVR_DT"] = int(
        datetime.fromisoformat("2026-10-16T06:30:00+00:00").timestamp() * 1000
    )
    item, = parse_fixture_items(_source(), json.dumps(payload))
    assert item["evidence"]["wa_dnr_fire_statistics"]["discovery_date"] == "2026-10-15"
    assert item["evidence"]["wa_dnr_fire_statistics"]["source_date_zone"] == (
        "America/Los_Angeles"
    )


def test_dnr_smaller_fire_query_fixture_keeps_its_exact_source_contract():
    source = _source()
    source["url"] = SMALL_FIXTURE.as_uri()
    source["official_url"] = SMALL_QUERY_URL
    items = parse_fixture_items(source, SMALL_FIXTURE.read_text())
    assert len(items) == 4
    reports = {item["evidence"]["wa_dnr_fire_statistics"]["fire_name"]: item
               for item in items}
    assert reports["WHISKEY CREEK"]["evidence"]["wa_dnr_fire_statistics"][
        "reported_acres"
    ] == 120
    assert reports["SUTHERLAND"]["evidence"]["wa_dnr_fire_statistics"][
        "fire_out_date"
    ] == "2026-09-28"
    assert all(item["evidence"]["wa_dnr_fire_statistics"]["query_url"] == SMALL_QUERY_URL
               for item in items)


@pytest.mark.parametrize("change", [
    lambda payload: payload["features"].append(deepcopy(payload["features"][0])),
    lambda payload: payload["features"][0]["attributes"].update(ACRES_BURNED=-1),
    lambda payload: payload["features"][0]["attributes"].update(DSCVR_DT=None),
    lambda payload: payload["features"][0]["attributes"].update(
        FIRE_OUT_DT=1_780_000_000_000
    ),
    lambda payload: payload.update(error={"message": "layer failed"}),
    lambda payload: payload.update(exceededTransferLimit=True),
])
def test_dnr_statistics_reject_ambiguous_or_invalid_rows(change):
    payload = json.loads(FIXTURE.read_text())
    change(payload)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(payload))


def test_dnr_statistics_offline_scan_preserves_unknown_active_state(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    path = tmp_path / "regional.yml"
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
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 31
    with connect_db(load_config(path)["_db_path"]) as conn:
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='REGIONAL'"
        ).fetchall()
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='REGIONAL'"
        ).fetchall()
    assert len(clusters) == 31
    assert all(len(json_loads(row["evidence_json"], {})["item_ids"]) == 1
               for row in clusters)
    dnr_rows = [json_loads(row["evidence_json"], {}) for row in rows
                if "wa_dnr_fire_statistics" in row["evidence_json"]]
    assert len(dnr_rows) == 31
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


def test_dnr_and_nwcc_offline_scan_joins_source_backed_fire_starts(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    nwcc_url = regional_registry_config_defaults("nwcc_large_fire_wa")["url"]
    path = tmp_path / "regional-pair.yml"
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
                - id: nwcc_large_fire_wa
                  enabled: true
                  url: "{NWCC.as_uri()}"
                  official_url: "{nwcc_url}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 35
    with connect_db(load_config(path)["_db_path"]) as conn:
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='REGIONAL'"
        ).fetchall()
        items = conn.execute(
            "SELECT id, evidence_json FROM news_items WHERE scope='REGIONAL'"
        ).fetchall()
    by_id = {row["id"]: json_loads(row["evidence_json"], {}) for row in items}
    events = [json_loads(row["evidence_json"], {}) for row in clusters]
    assert len(events) == 32
    paired = [event for event in events if len(event["item_ids"]) == 2]
    assert len(paired) == 3
    names = set()
    for event in paired:
        assert event["corroborated"] is True
        assert event["families"] == ["wildfire_federal", "wa_dnr"]
        assert event["correlation"]["matches"][0]["basis"] == [
            "event_type", "fire_incident", "source_start_date", "independent_family",
        ]
        dnr = next(by_id[item_id]["wa_dnr_fire_statistics"] for item_id in event["item_ids"]
                   if "wa_dnr_fire_statistics" in by_id[item_id])
        names.add(dnr["fire_name"])
        assert dnr["active_fire_claimed"] is False
        assert dnr["public_impact_inferred"] is False
        for item_id in event["item_ids"]:
            factors = by_id[item_id]["ranking"]["factors"]
            assert factors["regional_active_alert_bonus"] == 0
            assert factors["regional_public_impact_bonus"] == 0
    assert names == {"SISI", "LITTLE GIANT", "SINLAHEKIN"}


def test_dnr_nwcc_fire_name_alone_cannot_bridge_different_start_dates():
    dnr_source = _source()
    nwcc_source = regional_registry_config_defaults("nwcc_large_fire_wa")
    nwcc_source["official_url"] = nwcc_source["url"]
    nwcc_source["url"] = NWCC.as_uri()
    dnr = next(item for item in parse_fixture_items(dnr_source, FIXTURE.read_text())
               if item["evidence"]["wa_dnr_fire_statistics"]["fire_name"] == "SISI")
    nwcc = next(item for item in parse_fixture_items(nwcc_source, NWCC.read_text())
                if item["evidence"]["nwcc_large_fire"]["fire_name"] == "Sisi")
    for item_id, item, source in ((1, dnr, dnr_source), (2, nwcc, nwcc_source)):
        item["id"] = item_id
        item["evidence"]["source"] = {
            "source_key": source["id"], "source_family": source["source_family"],
            "official_status": source["official_status"],
        }
        item["evidence"]["regional_event"] = build_regional_event_contract(
            source, item, hashed_url="a" * 64,
        )
    assert correlate_regional_items([dnr, nwcc])[0]["item_ids"] == [1, 2]
    nwcc["evidence"]["nwcc_large_fire"]["start_date"] = "2026-08-15"
    assert [group["item_ids"] for group in correlate_regional_items([dnr, nwcc])] == [
        [1], [2],
    ]
