from __future__ import annotations

import json
from pathlib import Path

import yaml

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_events import correlate_global_items
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/news"


def _matched_payloads() -> tuple[str, str, str]:
    gdacs = (FIXTURES / "global_gdacs.rss").read_text()
    gdacs = gdacs.replace(
        "<gdacs:eventid>1001338</gdacs:eventid>",
        "<gdacs:eventid>1001338</gdacs:eventid>"
        "<gdacs:glide>TC-2026-000001-GUM</gdacs:glide>",
    )
    reliefweb = json.loads((FIXTURES / "global_reliefweb_disasters.json").read_text())
    fields = reliefweb["data"][0]["fields"]
    fields["glide"] = "TC-2026-000001-GUM"
    fields["name"] = "Guam: Tropical Cyclone CHAMPI-26 - Oct 2026"
    fields["country"] = [{"name": "Guam", "iso3": "GUM"}]
    fields["primary_country"] = {"name": "Guam", "iso3": "GUM"}
    fields["url"] = "https://reliefweb.int/disaster/tc-2026-000001-gum"
    report = json.loads((FIXTURES / "global_reliefweb_reports.json").read_text())
    report_fields = report["data"][0]["fields"]
    report_fields["title"] = "Guam: Cyclone CHAMPI-26 Situation Report"
    report_fields["disaster"][0] = {
        "id": 51000, "name": fields["name"], "glide": "TC-2026-000001-GUM",
    }
    report_fields["country"] = [{"name": "Guam"}]
    return gdacs, json.dumps(reliefweb), json.dumps(report)


def test_gdacs_and_reliefweb_parsers_retain_shared_glide():
    gdacs, reliefweb, report = _matched_payloads()
    gdacs_item = parse_fixture_items(
        {"scope": "GLOBAL", "kind": "rss", "parser": "gdacs_rss"}, gdacs,
    )[0]
    reliefweb_item = parse_fixture_items(
        {"scope": "GLOBAL", "kind": "api_json", "parser": "reliefweb_disasters_json"},
        reliefweb,
    )[0]
    assert gdacs_item["evidence"]["gdacs"]["glide"] == "TC-2026-000001-GUM"
    assert reliefweb_item["evidence"]["reliefweb_disaster"]["glide"] == (
        "TC-2026-000001-GUM"
    )
    report_item = parse_fixture_items({
        "scope": "GLOBAL", "kind": "api_json", "parser": "reliefweb_reports_json",
        "active_disaster_ids": [51000], "retention_days": 3, "max_items": 1,
        "official_source_names": ["UN Office for the Coordination of Humanitarian Affairs"],
        "humanitarian_theme_names": ["Shelter and Non-Food Items"],
    }, report)[0]
    assert report_item["evidence"]["reliefweb_report"]["disaster_glides"] == [
        "TC-2026-000001-GUM"
    ]


def test_glide_matching_requires_valid_identifier():
    def item(item_id: int, family: str, glide: str) -> dict:
        key = "gdacs" if family == "gdacs" else "reliefweb_disaster"
        return {
            "id": item_id, "scope": "GLOBAL", "title": "Different story",
            "source_published_at": "2026-10-15T12:00:00+00:00",
            "evidence": {
                key: {"glide": glide},
                "source": {"source_family": family, "official_status": "official"},
                "global": {"event_type": "tropical_cyclone",
                           "affected_countries": ["Guam" if item_id == 1 else "Palau"],
                           "geography_basis": "official_source_fields"},
            },
        }

    valid = correlate_global_items([
        item(1, "gdacs", "TC-2026-000001-GUM"),
        item(2, "reliefweb", "tc-2026-000001-gum"),
    ])
    assert valid[0]["item_ids"] == [1, 2]
    assert valid[0]["matches"][0]["basis"] == ["shared_event_id"]
    assert valid[0]["identifiers"] == ["glide:tc-2026-000001-gum"]
    invalid = correlate_global_items([
        item(1, "gdacs", "TC-2026-1-GUM"),
        item(2, "reliefweb", "TC-2026-1-GUM"),
    ])
    assert [group["item_ids"] for group in invalid] == [[1], [2]]
    conflicting = [
        item(1, "gdacs", "TC-2026-000001-GUM"),
        item(2, "reliefweb", "TC-2026-000002-GUM"),
    ]
    conflicting[1]["evidence"]["global"]["affected_countries"] = ["Guam"]
    assert [group["item_ids"] for group in correlate_global_items(conflicting)] == [
        [1], [2]
    ]


def test_shared_glide_offline_scan_creates_corroborated_global_event(tmp_path, monkeypatch):
    gdacs, reliefweb, report = _matched_payloads()
    gdacs_path = tmp_path / "gdacs.rss"
    reliefweb_path = tmp_path / "reliefweb.json"
    report_path = tmp_path / "report.json"
    gdacs_path.write_text(gdacs)
    reliefweb_path.write_text(reliefweb)
    report_path.write_text(report)
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "global": {"enabled": True},
        "news": {"enabled": True, "scopes": {"GLOBAL": {"enabled": True,
                 "sources": [
                     {"id": "gdacs_glide_fixture", "name": "GDACS GLIDE fixture",
                      "kind": "rss", "parser": "gdacs_rss", "source_family": "gdacs",
                      "official_status": "official", "enabled": True,
                      "url": f"file://{gdacs_path}"},
                     {"id": "reliefweb_glide_fixture", "name": "ReliefWeb GLIDE fixture",
                      "kind": "api_json", "parser": "reliefweb_disasters_json",
                      "source_family": "reliefweb", "official_status": "official",
                      "enabled": True, "url": f"file://{reliefweb_path}"},
                     {"id": "reliefweb_report_glide_fixture", "name": "ReliefWeb report fixture",
                      "kind": "api_json", "parser": "reliefweb_reports_json",
                      "source_family": "reliefweb", "official_status": "official",
                      "enabled": True, "url": f"file://{report_path}",
                      "active_disaster_ids": [51000], "retention_days": 3, "max_items": 1,
                      "official_source_names": [
                          "UN Office for the Coordination of Humanitarian Affairs"],
                      "humanitarian_theme_names": ["Shelter and Non-Food Items"]},
                 ]}}},
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("GLIDE fixture attempted HTTP"))
    ))
    result = run_news_scan(path)
    assert result["status"] == "complete" and result["item_count"] == 3
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        clusters = conn.execute(
            "SELECT item_count,evidence_json FROM news_clusters WHERE scope='GLOBAL'"
        ).fetchall()
    assert len(clusters) == 1 and clusters[0]["item_count"] == 3
    event = json_loads(clusters[0]["evidence_json"], {})["global_event"]
    assert event["confidence"] == "corroborated"
    assert event["families"] == ["gdacs", "reliefweb"]
    assert all(match["basis"] == ["shared_event_id"] for match in event["matches"])
