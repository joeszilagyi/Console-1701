from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import (
    SWPC_ALERTS_URL,
    OfficialFetchResult,
    is_supported_official_source,
)
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_scope_view

FIXTURE = Path(__file__).parent / "fixtures/orbital/swpc_alerts.json"


def _config(path: Path, *, parent=True, allow_http=True, source_enabled=True,
            verified=True, url=SWPC_ALERTS_URL):
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: {str(parent).lower()}}}
        news:
          enabled: true
          fetch_policy: {{allow_official_http: {str(allow_http).lower()}}}
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: swpc_alerts_json
                  enabled: {str(source_enabled).lower()}
                  verification_status: {"verified" if verified else "official_page_seen"}
                  url: "{url}"
    """).strip() + "\n")
    return path


def test_swpc_live_allowlist_requires_exact_verified_no_auth_source():
    source = {
        "scope": "ORBITAL", "id": "swpc_alerts_json", "kind": "api_json",
        "parser": "swpc_alerts_json", "url": SWPC_ALERTS_URL,
        "verification_status": "verified",
    }
    assert is_supported_official_source(source)
    for changed in (
        {"scope": "GLOBAL"}, {"id": "swpc_noaa_scales_json"},
        {"url": SWPC_ALERTS_URL + "?format=full"},
        {"url": "https://example.org/products/alerts.json"},
        {"parser": "generic_json_items"},
        {"verification_status": "official_page_seen"},
        {"auth": {"token": "configured"}},
    ):
        assert not is_supported_official_source({**source, **changed})


def test_swpc_live_parent_source_and_http_flags_prevent_access(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked HTTP")),
    )
    for index, settings in enumerate((
        {"parent": False}, {"allow_http": False}, {"source_enabled": False},
        {"verified": False}, {"url": SWPC_ALERTS_URL + "?other=1"},
    )):
        path = _config(tmp_path / f"blocked-{index}.yml", **settings)
        result = run_news_scan(path)
        assert result["item_count"] == 0


def test_explicit_swpc_news_scan_uses_mocked_transport_and_conditional_refresh(
    tmp_path, monkeypatch
):
    path = _config(tmp_path / "live.yml")
    records = json.loads(FIXTURE.read_text())
    recent = (datetime.now(UTC) - timedelta(hours=1)).isoformat(timespec="seconds")
    for record in records:
        if record.get("issue_datetime"):
            record["issue_datetime"] = recent
    fixture = json.dumps(records)
    calls: list[dict] = []

    def fake_fetch(source, **kwargs):
        assert source["url"] == SWPC_ALERTS_URL
        calls.append(kwargs)
        if len(calls) == 1:
            return OfficialFetchResult(fixture, 200, '"swpc-v1"', None, len(fixture))
        return OfficialFetchResult(None, 304, '"swpc-v1"', None, 0)

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    first = run_news_scan(path)
    skipped = run_news_scan(path)
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        runs = conn.execute(
            "SELECT status, http_status, evidence_json FROM news_fetch_runs ORDER BY id"
        ).fetchall()
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='ORBITAL'"
        ).fetchall()
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
        conn.commit()
    unchanged = run_news_scan(path)
    assert first["status"] == "complete" and first["item_count"] == 2
    assert skipped["skipped_sources"] == 1
    assert unchanged["item_count"] == 0
    assert len(calls) == 2 and calls[1]["etag"] == '"swpc-v1"'
    assert runs[0]["status"] == "success" and runs[0]["http_status"] == 200
    assert json_loads(runs[0]["evidence_json"], {})["fixture_only"] is False
    assert len(rows) == 2
    assert all(json_loads(row["evidence_json"], {})["ingest"]["fixture_only"] is False
               for row in rows)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("GET fetched HTTP")),
    )
    with connect_db(config["_db_path"]) as conn:
        view = get_news_scope_view(conn, config, "ORBITAL")
    assert len(view["items"]) == 2


def test_live_swpc_alerts_discard_old_products(tmp_path, monkeypatch):
    path = _config(tmp_path / "old.yml")
    records = json.loads(FIXTURE.read_text())
    old = (datetime.now(UTC) - timedelta(days=10)).isoformat(timespec="seconds")
    for record in records:
        if record.get("issue_datetime"):
            record["issue_datetime"] = old
    payload = json.dumps(records)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda source, **kwargs: OfficialFetchResult(payload, 200, None, None, len(payload)),
    )
    assert run_news_scan(path)["item_count"] == 0
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        count = conn.execute("SELECT COUNT(*) FROM news_items WHERE scope='ORBITAL'").fetchone()[0]
        assert count == 0
