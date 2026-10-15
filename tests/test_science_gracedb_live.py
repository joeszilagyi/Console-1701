from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

from console1701 import config as config_module
from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news import official_http
from console1701.news.official_http import is_supported_official_source
from console1701.news.parsers import NewsIngestError, parse_fixture_items
from console1701.news.scanner import purge_news_retention, run_news_scan

ENDPOINT = "https://gracedb.ligo.org/api/v2/superevents/"
FIXTURE = Path(__file__).parent / "fixtures/science/gracedb_public_alerts.json"


def _live_source():
    return {
        "id": "gracedb_public_alerts", "name": "GraceDB public alerts",
        "scope": "SYSTEM_SOLAR", "kind": "api_json",
        "parser": "gracedb_public_alert_fixture", "enabled": True,
        "fixture_only": False, "verification_status": "verified",
        "official_url": ENDPOINT, "url": ENDPOINT,
    }


def _record():
    record = deepcopy(json.loads(FIXTURE.read_text())["records"][1])
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    record["superevent"]["created"] = now
    record["voevents"] = {
        "numRows": 1,
        "voevents": [{"N": 1, "voevent_type": "PR", "created": now}],
    }
    return record


def test_gracedb_live_query_uses_only_public_list_and_bounded_voevent_url(monkeypatch):
    record = _record()
    urls = []

    def fake_get(url, **kwargs):
        urls.append(url)
        assert kwargs["limit"] <= 65_536
        if "?" in url:
            query = parse_qs(urlsplit(url).query)
            assert query["count"] == ["10"]
            assert "category: Production" in query["query"][0]
            assert "is_public: True" in query["query"][0]
            assert "created:" in query["query"][0]
            return {"numRows": 1, "superevents": [record["superevent"]]}, 200
        assert url == record["superevent"]["links"]["voevents"]
        return record["voevents"], 100

    monkeypatch.setattr(official_http, "_gracedb_json_get", fake_get)
    source = _live_source()
    assert is_supported_official_source(source)
    result = official_http.fetch_official_text(
        source, user_agent="test", timeout_seconds=5, max_bytes=65_536,
    )
    assert result.status_code == 200 and result.response_bytes == 300
    assert len(urls) == 2
    assert all("/files/" not in url and "/logs/" not in url for url in urls)
    item = parse_fixture_items(source, result.text)[0]
    assert item["evidence"]["gracedb_public_alert"]["fixture_only"] is False
    assert item["evidence"]["gracedb_public_alert"]["sky_map_downloaded"] is False


@pytest.mark.parametrize("problem", ["overflow", "foreign_link", "nonproduction"])
def test_gracedb_live_rejects_incomplete_or_untrusted_list_before_joins(monkeypatch, problem):
    record = _record()
    row = record["superevent"]
    if problem == "foreign_link":
        row["links"]["voevents"] = "https://example.test/voevents/"
    if problem == "nonproduction":
        row["category"] = "Test"
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        assert "?" in url
        return {"numRows": 11 if problem == "overflow" else 1,
                "superevents": [row]}, 200

    monkeypatch.setattr(official_http, "_gracedb_json_get", fake_get)
    with pytest.raises(NewsIngestError):
        official_http.fetch_official_text(
            _live_source(), user_agent="test", timeout_seconds=5, max_bytes=65_536,
        )
    assert len(calls) == 1


def test_gracedb_live_scan_updates_a_candidate_to_retracted_without_network(
    tmp_path, monkeypatch
):
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    path = tmp_path / "config.yml"
    source = {key: value for key, value in _live_source().items() if key != "scope"}
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "solar_system_beyond": {"enabled": True},
        "news": {"enabled": True, "fetch_policy": {"allow_official_http": True},
                 "scopes": {"SYSTEM_SOLAR": {"enabled": True, "sources": [source]}}},
    }))
    config = load_config(path)
    configured = config["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0]
    assert configured["interval_minutes"] >= 60
    record = _record()
    active_records = [record]

    def fake_get(url, **kwargs):
        if "?" in url:
            return {"numRows": len(active_records),
                    "superevents": [item["superevent"] for item in active_records]}, 200
        assert url == record["superevent"]["links"]["voevents"]
        return record["voevents"], 100

    monkeypatch.setattr(official_http, "_gracedb_json_get", fake_get)
    first = run_news_scan(path)
    assert first["status"] == "complete" and first["item_count"] == 1
    with connect_db(config["_db_path"]) as conn:
        assert conn.execute("SELECT COUNT(*) FROM news_items").fetchone()[0] == 1
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
    record["voevents"]["voevents"].append({
        "N": 2, "voevent_type": "RE", "created": datetime.now(UTC).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        ),
    })
    record["voevents"]["numRows"] = 2
    second = run_news_scan(path)
    assert second["status"] == "complete" and second["item_count"] == 1
    with connect_db(config["_db_path"]) as conn:
        assert conn.execute("SELECT COUNT(*) FROM news_items").fetchone()[0] == 1
        row = conn.execute("SELECT evidence_json FROM news_items").fetchone()
        event = conn.execute("SELECT status, score FROM science_events").fetchone()
    evidence = json_loads(row["evidence_json"], {})["gracedb_public_alert"]
    assert evidence["status"] == "retracted"
    assert event["status"] == "retracted" and event["score"] == 0

    active_records.clear()
    with connect_db(config["_db_path"]) as conn:
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
    empty = run_news_scan(path)
    assert empty["status"] == "complete" and empty["item_count"] == 0
    with connect_db(config["_db_path"]) as conn:
        assert conn.execute("SELECT status FROM news_items").fetchone()[0] == "active"
        assert conn.execute("SELECT status FROM science_events").fetchone()[0] == "retracted"
        purged = purge_news_retention(
            conn, config, now=(datetime.now(UTC) + timedelta(days=8)).isoformat()
        )
        assert conn.execute("SELECT COUNT(*) FROM news_items").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM science_events").fetchone()[0] == 0
    assert purged["items"] == 1 and purged["science_events"] == 1
