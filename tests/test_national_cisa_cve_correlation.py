"""CISA advisory and KEV joins require an official, nearby CVE match."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml

from console1701 import config as config_module
from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.cisa_advisories import CISA_ADVISORIES_RSS_URL
from console1701.news.national_events import correlate_national_items
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/news"


def _sources(advisory_path: Path) -> tuple[dict, dict]:
    advisory = {
        "id": "cisa_advisories", "name": "CISA advisories", "scope": "NATIONAL",
        "kind": "rss", "parser": "cisa_advisories_rss", "source_family": "cisa",
        "official_status": "official", "official_url": CISA_ADVISORIES_RSS_URL,
        "url": advisory_path.resolve().as_uri(), "enabled": True,
    }
    kev_path = FIXTURES / "national_cisa_kev.json"
    kev = {
        "id": "cisa_kev", "name": "CISA KEV", "scope": "NATIONAL",
        "kind": "api_json", "parser": "cisa_kev_json", "source_family": "cisa",
        "official_status": "official", "url": kev_path.resolve().as_uri(),
        "enabled": True,
    }
    return advisory, kev


def _nearby_feed(tmp_path: Path) -> Path:
    feed = (FIXTURES / "national_cisa_advisories.rss").read_text()
    feed = feed.replace(
        "Thu, 08 Oct 26 12:00:00 +0000",
        "Wed, 14 Oct 26 12:00:00 +0000",
        1,
    )
    path = tmp_path / "nearby_cisa_advisories.rss"
    path.write_text(feed)
    return path


def _parsed(source: dict, path: Path) -> list[dict]:
    items = parse_fixture_items(source, path.read_text())
    for index, item in enumerate(items, 1):
        item["id"] = index
        item["evidence"]["source"] = {
            "source_family": source["source_family"],
            "official_status": source["official_status"],
            "source_key": source["id"],
        }
    return items


def test_cisa_cve_join_uses_official_authority_and_72_hour_window(tmp_path):
    feed = _nearby_feed(tmp_path)
    advisory_source, kev_source = _sources(feed)
    advisories = _parsed(advisory_source, feed)
    kev = _parsed(kev_source, FIXTURES / "national_cisa_kev.json")
    for index, item in enumerate(kev, len(advisories) + 1):
        item["id"] = index
    groups = correlate_national_items([*advisories, *kev])
    paired = [group for group in groups if len(group["item_ids"]) == 2]
    assert len(paired) == 1
    assert paired[0]["identifiers"] == [
        "cisa_advisory:aa26-281a", "cisa_node:25593", "cve:cve-2026-12345"
    ]
    assert paired[0]["matches"][0]["basis"] == [
        "shared_cve", "same_authority", "time_window"
    ]
    assert paired[0]["families"] == ["cisa"]
    assert paired[0]["corroborated"] is False

    old = deepcopy(advisories[0])
    old["source_published_at"] = "2026-10-08T12:00:00+00:00"
    assert all(len(group["item_ids"]) == 1 for group in correlate_national_items([old, kev[0]]))
    unofficial = deepcopy(advisories[0])
    unofficial["evidence"]["source"]["official_status"] = "unverified"
    assert all(len(group["item_ids"]) == 1 for group in correlate_national_items([
        unofficial, kev[0]
    ]))


def test_cisa_cve_offline_scan_persists_one_same_family_pair(tmp_path, monkeypatch):
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    advisory, kev = _sources(_nearby_feed(tmp_path))
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {"enabled": True, "scopes": {"NATIONAL": {
            "enabled": True, "sources": [advisory, kev],
        }}},
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("CISA fixtures attempted HTTP"))
    ))
    assert run_news_scan(path)["item_count"] == 8
    with connect_db(load_config(path)["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT item_count, evidence_json FROM news_clusters WHERE scope='NATIONAL'"
        ).fetchall()
    events = [json_loads(row["evidence_json"], {})["national_event"] for row in rows]
    paired = [event for event in events if len(event["item_ids"]) == 2]
    assert len(events) == 7
    assert len(paired) == 1
    assert paired[0]["matches"][0]["basis"] == [
        "shared_cve", "same_authority", "time_window"
    ]
    assert paired[0]["corroborated"] is False
