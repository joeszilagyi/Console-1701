from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import (
    SWPC_NOAA_SCALES_URL,
    OfficialFetchResult,
    is_supported_official_source,
)
from console1701.news.orbital_registry import get_orbital_source_registry_entry
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/orbital/swpc_noaa_scales.json"


def _config(path: Path, *, verified=True, allow_http=True):
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: true}}
        news:
          enabled: true
          fetch_policy: {{allow_official_http: {str(allow_http).lower()}}}
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: swpc_noaa_scales_json
                  enabled: true
                  verification_status: {"verified" if verified else "official_page_seen"}
                  url: {SWPC_NOAA_SCALES_URL}
    """).strip() + "\n")
    return path


def _recent_payload() -> str:
    payload = json.loads(FIXTURE.read_text())
    current = datetime.now(UTC) - timedelta(minutes=15)
    tomorrow = current + timedelta(days=1)
    payload["0"]["DateStamp"] = current.date().isoformat()
    payload["0"]["TimeStamp"] = current.strftime("%H:%M:%S")
    payload["1"]["DateStamp"] = tomorrow.date().isoformat()
    payload["1"]["TimeStamp"] = tomorrow.strftime("%H:%M:%S")
    return json.dumps(payload)


def test_swpc_scales_exact_live_allowlist_and_disabled_default(tmp_path, monkeypatch):
    source = {
        "scope": "ORBITAL", "id": "swpc_noaa_scales_json", "kind": "api_json",
        "parser": "swpc_noaa_scales_json", "url": SWPC_NOAA_SCALES_URL,
        "verification_status": "verified",
    }
    assert is_supported_official_source(source)
    for changed in (
        {"url": SWPC_NOAA_SCALES_URL + "?x=1"},
        {"parser": "generic_json_items"}, {"kind": "rss"},
        {"verification_status": "official_page_seen"},
        {"auth": {"token": "x"}},
    ):
        assert not is_supported_official_source({**source, **changed})
    assert get_orbital_source_registry_entry("swpc_noaa_scales_json")["enabled"] is False
    config = load_config(_config(tmp_path / "disabled.yml", verified=False))
    assert config["news"]["scopes"]["ORBITAL"]["sources"][0]["verification_status"] == (
        "official_page_seen"
    )
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked HTTP")),
    )
    assert run_news_scan(tmp_path / "disabled.yml")["item_count"] == 0
    assert run_news_scan(_config(tmp_path / "http-off.yml", allow_http=False))["item_count"] == 0


def test_swpc_scales_live_scan_preserves_period_and_conditional_refresh(tmp_path, monkeypatch):
    path = _config(tmp_path / "live.yml")
    payload = _recent_payload()
    calls: list[dict] = []

    def fake_fetch(source, **kwargs):
        assert source["url"] == SWPC_NOAA_SCALES_URL
        calls.append(kwargs)
        if len(calls) == 1:
            return OfficialFetchResult(payload, 200, '"scales-v1"', None, len(payload))
        return OfficialFetchResult(None, 304, '"scales-v1"', None, 0)

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    first = run_news_scan(path)
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute("SELECT evidence_json FROM news_items WHERE scope='ORBITAL'").fetchall()
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
        conn.commit()
    unchanged = run_news_scan(path)
    assert first["item_count"] == 3 and unchanged["item_count"] == 0
    assert len(calls) == 2 and calls[1]["etag"] == '"scales-v1"'
    periods = {
        json_loads(row["evidence_json"], {})["swpc_noaa_scale"]["period_kind"]
        for row in rows
    }
    assert periods == {"current", "forecast"}
    assert all(json_loads(row["evidence_json"], {})["ingest"]["fixture_only"] is False
               for row in rows)


def test_swpc_scales_live_scan_drops_stale_current_and_distant_forecasts(tmp_path, monkeypatch):
    path = _config(tmp_path / "stale.yml")
    payload = json.loads(_recent_payload())
    old = datetime.now(UTC) - timedelta(days=2)
    distant = datetime.now(UTC) + timedelta(days=10)
    payload["0"]["DateStamp"] = old.date().isoformat()
    payload["0"]["TimeStamp"] = old.strftime("%H:%M:%S")
    payload["1"]["DateStamp"] = distant.date().isoformat()
    payload["1"]["TimeStamp"] = distant.strftime("%H:%M:%S")
    text = json.dumps(payload)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda source, **kwargs: OfficialFetchResult(text, 200, None, None, len(text)),
    )
    assert run_news_scan(path)["item_count"] == 0
