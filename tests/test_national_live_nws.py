from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from starlette.requests import Request

from console1701 import config as config_module
from console1701.api import build_router
from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.national_registry import national_registry_config_defaults
from console1701.news.official_http import OfficialFetchResult, is_supported_official_source
from console1701.news.parsers import (
    NWS_NATIONAL_SEVERE_ALERTS_URL,
    NewsParserError,
    parse_fixture_items,
)
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/national_nws_alerts.json"


def _config(path: Path, *, national=True, allow_http=True, interval=5):
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": national},
        "news": {"enabled": True, "fetch_policy": {"allow_official_http": allow_http},
                 "scopes": {"NATIONAL": {"enabled": True, "sources": [{
                     "id": "nws_active_alerts_api", "enabled": True,
                     "interval_minutes": interval,
                 }]}}},
    }))
    return path


def _severe_payload():
    payload = json.loads(FIXTURE.read_text())
    payload["features"] = [payload["features"][0]]
    return json.dumps(payload)


def test_national_nws_live_contract_and_policy_gates(tmp_path, monkeypatch):
    source = national_registry_config_defaults("nws_active_alerts_api")
    assert source is not None
    assert source["url"] == NWS_NATIONAL_SEVERE_ALERTS_URL
    assert source["enabled"] is False
    assert is_supported_official_source(source)
    for change in (
        {"url": "https://api.weather.gov/alerts/active"},
        {"url": source["url"] + "&area=WA"},
        {"parser": "generic_json_items"},
        {"verification_status": "official_page_seen"},
        {"interval_minutes": 0},
        {"interval_minutes": True},
    ):
        assert not is_supported_official_source({**source, **change})
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("blocked NATIONAL NWS HTTP"))
    ))
    for index, settings in enumerate((
        {"national": False}, {"allow_http": False}, {"interval": 0},
    )):
        path = _config(tmp_path / f"blocked-{index}.yml", **settings)
        result = run_news_scan(path)
        config = load_config(path)
        with connect_db(config["_db_path"]) as conn:
            row = conn.execute(
                "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
        assert result["status"] == "partial"
        assert row["status"] == "policy_blocked"


def test_national_nws_live_parser_rejects_out_of_contract_rows():
    source = national_registry_config_defaults("nws_active_alerts_api")
    assert source is not None
    assert len(parse_fixture_items(source, _severe_payload())) == 1
    with pytest.raises(NewsParserError, match="severity/status filter"):
        parse_fixture_items(source, FIXTURE.read_text())
    payload = json.loads(_severe_payload())
    payload["features"][0]["properties"]["status"] = "Test"
    with pytest.raises(NewsParserError, match="severity/status filter"):
        parse_fixture_items(source, json.dumps(payload))
    payload = json.loads(_severe_payload())
    payload["features"] *= 1001
    with pytest.raises(NewsParserError, match="1000-feature cap"):
        parse_fixture_items(source, json.dumps(payload))


def test_national_nws_explicit_live_scan_and_conditional_refresh(tmp_path, monkeypatch):
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    path = _config(tmp_path / "live.yml")
    calls = []

    def fake_fetch(source, **kwargs):
        calls.append((source["url"], kwargs))
        if len(calls) == 1:
            payload = _severe_payload()
            return OfficialFetchResult(payload, 200, 'W/"severe-sample"', None, len(payload))
        return OfficialFetchResult(None, 304, 'W/"severe-sample"', None, 0)

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    first = run_news_scan(path)
    skipped = run_news_scan(path)
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        runs = conn.execute(
            "SELECT status, http_status, item_count, evidence_json FROM news_fetch_runs "
            "ORDER BY id"
        ).fetchall()
        items = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchall()
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
        conn.commit()
    unchanged = run_news_scan(path)
    assert first["status"] == "complete" and first["item_count"] == 1
    assert skipped["skipped_sources"] == 1
    assert len(calls) == 2
    assert all(url == NWS_NATIONAL_SEVERE_ALERTS_URL for url, _ in calls)
    assert calls[0][1]["etag"] is None
    assert calls[1][1]["etag"] == 'W/"severe-sample"'
    assert unchanged["item_count"] == 0
    assert runs[0]["status"] == "success" and runs[0]["http_status"] == 200
    assert json_loads(runs[0]["evidence_json"], {})["fixture_only"] is False
    assert len(items) == 1
    evidence = json_loads(items[0]["evidence_json"], {})
    assert evidence["nws_alert"]["severity"] == "Severe"
    assert evidence["nws_alert"]["affected_states"] == ["WA"]
    assert evidence["national"]["attention_state"] == "elevated"
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("NATIONAL page attempted HTTP"))
    ))
    router = build_router(str(path))
    page = next(route.endpoint for route in router.routes
                if getattr(route, "path", None) == "/{scope}")
    request = Request({
        "type": "http", "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": "/NATIONAL", "raw_path": b"/NATIONAL", "query_string": b"",
        "headers": [], "client": ("127.0.0.1", 12345), "server": ("testserver", 80),
        "root_path": "",
    })
    assert page(request, "NATIONAL").status_code == 200
    api = next(route.endpoint for route in router.routes
               if getattr(route, "path", None) == "/api/news/scopes/{scope}")
    assert api("NATIONAL")["state"]["state"] == "healthy"
