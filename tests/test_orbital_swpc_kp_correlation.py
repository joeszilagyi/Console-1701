from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.orbital_events import correlate_orbital_items
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/orbital"


def _kp_payload(value: float, stamp: str = "2026-10-10T19:00:00") -> str:
    return json.dumps([{"time_tag": stamp, "Kp": value, "station_count": 8}])


def _parsed_pair(value: float, stamp: str = "2026-10-10T19:00:00") -> list[dict]:
    alerts = parse_fixture_items({
        "id": "swpc_alerts_json", "scope": "ORBITAL", "kind": "api_json",
        "parser": "swpc_alerts_json",
    }, (FIXTURES / "swpc_alerts.json").read_text())
    kp = parse_fixture_items({
        "id": "swpc_kp_summary_json", "scope": "ORBITAL", "kind": "api_json",
        "parser": "swpc_kp_json",
    }, _kp_payload(value, stamp))
    for index, item in enumerate([*alerts, *kp], 1):
        item["id"] = index
        item["evidence"]["source"] = {
            "source_family": "swpc",
            "source_key": "swpc_alerts_json" if index <= len(alerts) else "swpc_kp_summary_json",
        }
    return [*alerts, *kp]


@pytest.mark.parametrize("value,expected", [
    (5.0, "G1"), (5.67, "G1"), (6.0, "G2"), (7.0, "G3"),
    (8.9, "G4"), (9.0, "G5"),
])
def test_observed_planetary_kp_uses_noaa_scale_thresholds(value, expected):
    item = _parsed_pair(value)[-1]
    assert item["evidence"]["swpc_k_index"]["noaa_scale"] == expected
    assert item["evidence"]["orbital_identity"]["noaa_scale"] == expected


def test_planetary_kp_matches_same_level_warning_inside_valid_window():
    items = _parsed_pair(7.0)
    assert items[-1]["evidence"]["orbital_identity"]["noaa_scale"] == "G3"
    groups = correlate_orbital_items(items)
    joined = next(group for group in groups if len(group["item_ids"]) == 2)
    assert joined["item_ids"] == [1, 3]
    assert joined["matches"][0]["basis"] == [
        "same_noaa_geomagnetic_scale", "alert_valid_window",
        "planetary_kp_observation",
    ]
    assert joined["corroborated"] is False
    assert all(len(group["item_ids"]) == 1 for group in groups if group is not joined)


def test_kp_requires_same_level_valid_time_and_planetary_measurement():
    for items in (
        _parsed_pair(6.0),
        _parsed_pair(7.0, "2026-10-11T01:00:00"),
    ):
        assert all(len(group["item_ids"]) == 1 for group in correlate_orbital_items(items))
    boulder = parse_fixture_items({
        "id": "swpc_boulder_k_json", "scope": "ORBITAL", "kind": "api_json",
        "parser": "swpc_kp_json",
    }, json.dumps([{"time_tag": "2026-10-10T19:00:00", "k_index": 7.0}]))[0]
    boulder["id"] = 3
    boulder["evidence"]["source"] = {
        "source_family": "swpc", "source_key": "swpc_boulder_k_json",
    }
    assert boulder["evidence"]["orbital_identity"]["noaa_scale"] is None
    assert all(len(group["item_ids"]) == 1
               for group in correlate_orbital_items([*_parsed_pair(7.0)[:2], boulder]))
    estimated = parse_fixture_items({
        "id": "swpc_kp_1m_json", "scope": "ORBITAL", "kind": "api_json",
        "parser": "swpc_kp_json",
    }, json.dumps([{"time_tag": "2026-10-10T19:00:00", "estimated_kp": 7.0}]))[0]
    estimated["id"] = 3
    estimated["evidence"]["source"] = {
        "source_family": "swpc", "source_key": "swpc_kp_1m_json",
    }
    assert estimated["evidence"]["swpc_k_index"]["observation_type"] == "estimated_1m"
    assert estimated["evidence"]["orbital_identity"]["noaa_scale"] is None
    assert all(len(group["item_ids"]) == 1
               for group in correlate_orbital_items([*_parsed_pair(7.0)[:2], estimated]))


def test_kp_alert_join_persists_offline_without_extra_family_credit(tmp_path, monkeypatch):
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("SWPC fixture attempted HTTP"))
    ))
    kp_path = tmp_path / "kp.json"
    kp_path.write_text(_kp_payload(7.0))
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "orbital": {"enabled": True},
        "news": {"enabled": True, "scopes": {"ORBITAL": {"enabled": True,
            "sources": [
                {"id": "swpc_alerts_json", "enabled": True,
                 "url": f"file://{FIXTURES / 'swpc_alerts.json'}"},
                {"id": "swpc_kp_summary_json", "enabled": True,
                 "url": f"file://{kp_path}"},
            ],
        }}},
    }))
    assert run_news_scan(path)["item_count"] == 3
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='ORBITAL'"
        ).fetchall()
    events = [json_loads(row["evidence_json"], {})["orbital_event"] for row in rows]
    joined = next(event for event in events if len(event["item_ids"]) == 2)
    assert joined["families"] == ["swpc"] and joined["corroborated"] is False
    assert joined["matches"][0]["basis"][-1] == "planetary_kp_observation"
