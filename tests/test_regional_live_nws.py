from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import OfficialFetchResult, RateLimitedError
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "news" / "local_nws_alerts.json"


def _config(
    path: Path, *, local: bool = False, regional: bool = True,
    local_scope_enabled: bool | None = None, local_source_enabled: bool | None = None,
    regional_scope_enabled: bool = True, allow_http: bool = True,
):
    local_scope_enabled = local if local_scope_enabled is None else local_scope_enabled
    local_source_enabled = local if local_source_enabled is None else local_source_enabled
    path.write_text(
        dedent(
            f"""
            paths: {{repo_roots: [], explicit_repos: []}}
            local: {{enabled: {str(local).lower()}}}
            regional: {{enabled: {str(regional).lower()}}}
            news:
              enabled: true
              fetch_policy: {{allow_official_http: {str(allow_http).lower()}}}
              scopes:
                LOCAL:
                  enabled: {str(local_scope_enabled).lower()}
                  sources:
                    - id: nws_active_alerts_api
                      enabled: {str(local_source_enabled).lower()}
                REGIONAL:
                  enabled: {str(regional_scope_enabled).lower()}
                  sources:
                    - id: nws_active_alerts_wa
                      enabled: true
            """
        ).strip() + "\n",
        encoding="utf-8",
    )
    return path


@pytest.mark.parametrize("regional,allow_http", [(False, True), (True, False)])
def test_regional_live_nws_requires_its_policy_gates(
    tmp_path, monkeypatch, regional, allow_http
):
    config_path = _config(
        tmp_path / "config.yml", regional=regional, allow_http=allow_http
    )

    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("REGIONAL NWS must remain blocked")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute("SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1").fetchone()

    assert result["status"] == "partial"
    assert run["status"] == "policy_blocked"


def test_regional_live_nws_ingests_with_own_scope_without_local_policy(tmp_path, monkeypatch):
    config_path = _config(tmp_path / "config.yml")
    fixture = FIXTURE.read_text(encoding="utf-8")
    calls = []

    def fake_fetch(source, **kwargs):
        calls.append((source["id"], kwargs))
        return OfficialFetchResult(fixture, 200, '"regional-v1"', None, len(fixture))

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT scope, evidence_json FROM news_items ORDER BY id"
        ).fetchall()
        run = conn.execute(
            "SELECT status, http_status, evidence_json FROM news_fetch_runs"
        ).fetchone()

    assert result["status"] == "complete"
    assert result["item_count"] == 2
    assert len(calls) == 1
    assert calls[0][0] == "nws_active_alerts_wa"
    assert run["status"] == "success" and run["http_status"] == 200
    assert json_loads(run["evidence_json"], {})["fixture_only"] is False
    assert all(row["scope"] == "REGIONAL" for row in rows)
    assert all(json_loads(row["evidence_json"], {})["regional_event"]["confidence"] == "high"
               for row in rows)


def test_new_regional_source_rejects_unexpected_initial_304(tmp_path, monkeypatch):
    config_path = _config(tmp_path / "config.yml")

    def unexpected_unchanged(source, **kwargs):
        assert kwargs["etag"] is None
        return OfficialFetchResult(None, 304, '"unexpected"', None, 0)

    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text", unexpected_unchanged
    )
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute("SELECT status FROM news_fetch_runs").fetchone()

    assert result["status"] == "partial"
    assert "before every enabled scope had a live snapshot" in result["errors"][0]
    assert run["status"] == "failed"


def test_local_and_regional_share_one_nws_request_with_independent_evidence(
    tmp_path, monkeypatch
):
    config_path = _config(tmp_path / "config.yml", local=True)
    fixture = FIXTURE.read_text(encoding="utf-8")
    calls = []

    def fake_fetch(source, **kwargs):
        calls.append((source["id"], kwargs))
        if len(calls) == 1:
            return OfficialFetchResult(fixture, 200, '"both-v1"', None, len(fixture))
        return OfficialFetchResult(None, 304, '"both-v1"', None, 0)

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    first = run_news_scan(config_path)
    skipped = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        first_runs = conn.execute(
            "SELECT s.scope, r.status, r.evidence_json FROM news_fetch_runs r "
            "JOIN news_sources s ON s.id = r.source_id ORDER BY r.id"
        ).fetchall()
        counts = conn.execute(
            "SELECT scope, COUNT(*) FROM news_items GROUP BY scope ORDER BY scope"
        ).fetchall()
        health = conn.execute(
            "SELECT s.scope, h.state FROM news_source_health h "
            "JOIN news_sources s ON s.id = h.source_id ORDER BY s.scope"
        ).fetchall()
        conn.execute("UPDATE news_fetch_runs SET started_at = '2026-01-01T00:00:00+00:00'")
        conn.commit()

    unchanged = run_news_scan(config_path)
    with connect_db(config["_db_path"]) as conn:
        latest = conn.execute(
            "SELECT s.scope, r.status, r.http_status, r.etag_sent, r.evidence_json "
            "FROM news_fetch_runs r JOIN news_sources s ON s.id = r.source_id "
            "ORDER BY r.id DESC LIMIT 2"
        ).fetchall()

    assert first["item_count"] == 3
    assert first["scanned_sources"] == 2
    assert skipped["skipped_sources"] == 2
    assert len(calls) == 2
    assert calls[0][1]["etag"] is None
    assert calls[1][1]["etag"] == '"both-v1"'
    assert [(row["scope"], row[1]) for row in counts] == [("LOCAL", 1), ("REGIONAL", 2)]
    assert [(row["scope"], row["state"]) for row in health] == [
        ("LOCAL", "healthy"), ("REGIONAL", "healthy")
    ]
    assert [row["status"] for row in first_runs] == ["success", "success"]
    assert json_loads(first_runs[1]["evidence_json"], {})["shared_response"] is True
    assert unchanged["scanned_sources"] == 2
    assert all(row["status"] == "not_modified" and row["http_status"] == 304 for row in latest)
    assert {row["etag_sent"] for row in latest} == {None, '"both-v1"'}


def test_nws_rate_limit_is_shared_across_scopes(tmp_path, monkeypatch):
    config_path = _config(tmp_path / "config.yml", local=True)
    calls = 0

    def limited_fetch(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise RateLimitedError("Official feed returned HTTP 429; backoff applies.")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", limited_fetch)
    first = run_news_scan(config_path)
    second = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        statuses = [row[0] for row in conn.execute("SELECT status FROM news_fetch_runs")]

    assert first["status"] == "partial"
    assert first["scanned_sources"] == 2
    assert second["skipped_sources"] == 2
    assert calls == 1
    assert statuses == ["rate_limited", "rate_limited"]


def test_new_regional_consumer_waits_for_shared_endpoint_interval(tmp_path, monkeypatch):
    config_path = _config(
        tmp_path / "config.yml", local=True, regional=False, regional_scope_enabled=False
    )
    fixture = FIXTURE.read_text(encoding="utf-8")
    calls = []

    def fake_fetch(source, **kwargs):
        calls.append((source["id"], kwargs))
        return OfficialFetchResult(fixture, 200, '"shared-v1"', None, len(fixture))

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    first = run_news_scan(config_path)
    _config(config_path, local=False, regional=True)
    too_soon = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        conn.execute("UPDATE news_fetch_runs SET started_at = '2026-01-01T00:00:00+00:00'")
        conn.commit()
    later = run_news_scan(config_path)

    assert first["scanned_sources"] == 1
    assert too_soon["scanned_sources"] == 0
    assert too_soon["skipped_sources"] == 1
    assert later["scanned_sources"] == 1
    assert [call[0] for call in calls] == ["nws_active_alerts_api", "nws_active_alerts_wa"]
    assert calls[1][1]["etag"] is None


def test_blocked_local_source_does_not_throttle_enabled_regional_source(
    tmp_path, monkeypatch
):
    config_path = _config(
        tmp_path / "config.yml", regional=True,
        local_scope_enabled=True, local_source_enabled=True,
    )
    fixture = FIXTURE.read_text(encoding="utf-8")
    calls = []

    def fake_fetch(source, **kwargs):
        calls.append(source["id"])
        return OfficialFetchResult(fixture, 200, None, None, len(fixture))

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    result = run_news_scan(config_path)

    assert result["status"] == "partial"
    assert result["scanned_sources"] == 2
    assert calls == ["nws_active_alerts_wa"]
