from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from console1701 import config as config_module
from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/science/gracedb_public_alerts.json"
ENDPOINT = "https://gracedb.ligo.org/api/v2/superevents/"


def _source():
    return {
        "id": "gracedb_public_alerts", "scope": "SYSTEM_SOLAR", "kind": "api_json",
        "parser": "gracedb_public_alert_fixture", "fixture_only": True,
        "official_url": ENDPOINT, "url": f"file://{FIXTURE}",
    }


def test_gracedb_fixture_tracks_retraction_and_update_without_sky_maps():
    withdrawn, active = parse_fixture_items(_source(), FIXTURE.read_text())
    retraction = withdrawn["evidence"]["gracedb_public_alert"]
    update = active["evidence"]["gracedb_public_alert"]
    assert retraction["status"] == "retracted"
    assert retraction["revision_types"] == ["EW", "RE"]
    assert retraction["latest_revision"] == 2
    assert retraction["notice_at"] == "2025-10-17T21:19:22+00:00"
    assert withdrawn["evidence"]["science_identity"]["gracedb_superevent_id"] == "S251017di"
    assert update["status"] == "update"
    assert update["revision_types"] == ["PR", "PR", "IN", "UP"]
    assert update["event_time_gps"] != update["notice_at"]
    assert retraction["sky_map_downloaded"] is False
    assert update["earth_impact_inferred"] is False
    assert "confirmed" not in active["title"].lower()


@pytest.mark.parametrize(("mutation", "value"), [
    ("query", {"category": "Test", "is_public": True, "count": 2}),
    ("category", "Test"),
    ("self_link", "https://example.test/fake"),
    ("voevent_type", "UNKNOWN"),
    ("duplicate_revision", 1),
])
def test_gracedb_fixture_rejects_nonpublic_or_bad_metadata(mutation, value):
    payload = json.loads(FIXTURE.read_text())
    record = payload["records"][0]
    if mutation == "query":
        payload["query"] = value
    elif mutation == "category":
        record["superevent"]["category"] = value
    elif mutation == "self_link":
        record["superevent"]["links"]["self"] = value
    elif mutation == "voevent_type":
        record["voevents"]["voevents"][0]["voevent_type"] = value
    else:
        record["voevents"]["voevents"][1]["N"] = value
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(payload))


def test_gracedb_fixture_requires_exact_source_and_bounded_payload():
    for change in ({"fixture_only": False}, {"official_url": "https://example.test/"},
                   {"id": "gracedb_private"}):
        with pytest.raises(NewsParserError):
            parse_fixture_items({**_source(), **change}, FIXTURE.read_text())
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "{")
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 65_537)


def test_gracedb_offline_scan_preserves_withdrawal_without_http(tmp_path, monkeypatch):
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "solar_system_beyond": {"enabled": True},
        "news": {"enabled": True, "scopes": {"SYSTEM_SOLAR": {
            "enabled": True, "sources": [{**_source(), "name": "GraceDB fixture",
                                             "enabled": True}],
        }}},
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("GraceDB fixture scan attempted HTTP"))
    ))
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute("SELECT title, evidence_json FROM news_items ORDER BY title").fetchall()
        events = conn.execute(
            "SELECT status, score, ranking_explanation_json FROM science_events ORDER BY title"
        ).fetchall()
    assert len(events) == 2
    assert {event["status"] for event in events} == {"retracted", "active"}
    assert any(event["score"] == 0 for event in events if event["status"] == "retracted")
    assert all(json_loads(row["evidence_json"], {})["ingest"]["fixture_only"] for row in rows)
    assert all("gracedb_public_alert" in json_loads(row["evidence_json"], {}) for row in rows)
