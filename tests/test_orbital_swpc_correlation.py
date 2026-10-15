from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.orbital_events import correlate_orbital_items
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/orbital"


def _parsed_items(scale_payload):
    alerts = parse_fixture_items(
        {"id": "swpc_alerts_json", "scope": "ORBITAL", "kind": "api_json",
         "parser": "swpc_alerts_json"},
        (FIXTURES / "swpc_alerts.json").read_text(),
    )
    scales = parse_fixture_items(
        {"id": "swpc_noaa_scales_json", "scope": "ORBITAL", "kind": "api_json",
         "parser": "swpc_noaa_scales_json"}, scale_payload,
    )
    for index, item in enumerate([*alerts, *scales], 1):
        item["id"] = index
        item["evidence"]["source"] = {
            "source_family": "swpc", "source_key": (
                "swpc_alerts_json" if index <= len(alerts) else "swpc_noaa_scales_json"
            ),
        }
    return alerts, scales


def _aligned_scales():
    return (FIXTURES / "swpc_noaa_scales.json").read_text().replace(
        '"DateStamp": "2026-10-15"', '"DateStamp": "2026-10-10"', 1
    )


def test_swpc_current_scale_matches_warning_only_inside_valid_window():
    alerts, scales = _parsed_items(_aligned_scales())
    assert alerts[0]["evidence"]["orbital_identity"]["noaa_scale"] == "G3"
    assert scales[0]["evidence"]["orbital_identity"]["scale_period"] == "current"
    groups = correlate_orbital_items([*alerts, *scales])
    joined = next(group for group in groups if len(group["item_ids"]) == 2)
    assert joined["item_ids"] == [1, 3]
    assert joined["matches"][0]["basis"] == [
        "same_noaa_scale", "alert_valid_window", "current_scale_observation",
    ]
    assert joined["corroborated"] is False
    assert all(len(group["item_ids"]) == 1 for group in groups if group is not joined)

    outside = _aligned_scales().replace(
        '"TimeStamp": "19:58:00"', '"TimeStamp": "00:01:00"', 1
    )
    alerts, scales = _parsed_items(outside)
    assert all(len(group["item_ids"]) == 1
               for group in correlate_orbital_items([*alerts, *scales]))

    forecast_payload = json.loads(_aligned_scales())
    forecast_payload["0"]["G"]["Scale"] = "0"
    forecast_payload["1"]["DateStamp"] = "2026-10-10"
    forecast_payload["1"]["TimeStamp"] = "20:00:00"
    forecast_payload["1"]["G"]["Scale"] = "3"
    alerts, scales = _parsed_items(json.dumps(forecast_payload))
    assert all(len(group["item_ids"]) == 1
               for group in correlate_orbital_items([*alerts, *scales]))


def test_swpc_window_match_persists_without_claiming_independent_source(tmp_path, monkeypatch):
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("SWPC fixture scan attempted HTTP"))
    ))
    scale_fixture = tmp_path / "scales.json"
    scale_fixture.write_text(_aligned_scales())
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
                  url: "file://{FIXTURES / 'swpc_alerts.json'}"
                - id: swpc_noaa_scales_json
                  enabled: true
                  url: "file://{scale_fixture}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 5
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='ORBITAL'"
        ).fetchall()
    joined = [json_loads(row["evidence_json"], {})["orbital_event"] for row in rows
              if len(json_loads(row["evidence_json"], {})["orbital_event"]["item_ids"]) == 2]
    assert len(joined) == 1
    assert joined[0]["corroborated"] is False
    assert joined[0]["matches"][0]["basis"] == [
        "same_noaa_scale", "alert_valid_window", "current_scale_observation",
    ]
