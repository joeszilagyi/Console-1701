from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import OfficialFetchResult
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "news" / "regional_usgs_earthquakes.json"


def _config(path: Path, *, regional: bool = True, allow_http: bool = True, threshold: float = 3.0):
    path.write_text(
        dedent(
            f"""
            paths: {{repo_roots: [], explicit_repos: []}}
            regional: {{enabled: {str(regional).lower()}}}
            news:
              enabled: true
              fetch_policy: {{allow_official_http: {str(allow_http).lower()}}}
              scopes:
                REGIONAL:
                  enabled: true
                  sources:
                    - id: usgs_eq_geojson
                      enabled: true
                      min_magnitude: {threshold}
            """
        ).strip() + "\n",
        encoding="utf-8",
    )
    return path


def test_usgs_live_feed_requires_regional_http_and_threshold_gates(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("USGS live request must remain blocked")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    for index, settings in enumerate(
        (
            {"regional": False},
            {"allow_http": False},
            {"threshold": 2.0},
        )
    ):
        config_path = _config(tmp_path / f"blocked-{index}.yml", **settings)
        result = run_news_scan(config_path)
        config = load_config(config_path)
        with connect_db(config["_db_path"]) as conn:
            run = conn.execute(
                "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
        assert result["status"] == "partial"
        assert run["status"] == "policy_blocked"


def test_usgs_live_feed_stores_regional_events_and_uses_conditional_refresh(
    tmp_path, monkeypatch
):
    config_path = _config(tmp_path / "live.yml")
    fixture = FIXTURE.read_text(encoding="utf-8")
    calls = []

    def fake_fetch(source, **kwargs):
        calls.append((source["id"], kwargs))
        if len(calls) == 1:
            return OfficialFetchResult(
                fixture, 200, None, "Thu, 08 Oct 2026 18:00:00 GMT", len(fixture)
            )
        return OfficialFetchResult(None, 304, None, "Thu, 08 Oct 2026 18:00:00 GMT", 0)

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    first = run_news_scan(config_path)
    skipped = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        runs = conn.execute(
            "SELECT status, http_status, item_count, last_modified_received, "
            "evidence_json FROM news_fetch_runs ORDER BY id"
        ).fetchall()
        items = conn.execute(
            "SELECT scope, rank_score, evidence_json FROM news_items ORDER BY id"
        ).fetchall()
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='REGIONAL'"
        ).fetchall()
        source = conn.execute(
            "SELECT policy_json FROM news_sources WHERE source_key='usgs_eq_geojson'"
        ).fetchone()
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
        conn.commit()
    unchanged = run_news_scan(config_path)
    with connect_db(config["_db_path"]) as conn:
        latest = conn.execute(
            "SELECT status, http_status, last_modified_sent FROM news_fetch_runs "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert first["status"] == "complete"
    assert first["item_count"] == 2
    assert skipped["skipped_sources"] == 1
    assert len(calls) == 2
    assert calls[0][0] == "usgs_eq_geojson"
    assert calls[0][1]["last_modified"] is None
    assert calls[1][1]["last_modified"] == "Thu, 08 Oct 2026 18:00:00 GMT"
    assert runs[0]["status"] == "success" and runs[0]["http_status"] == 200
    assert runs[0]["item_count"] == 2
    assert json_loads(runs[0]["evidence_json"], {})["fixture_only"] is False
    assert "earthquake near" not in runs[0]["evidence_json"]
    assert json_loads(source["policy_json"], {})["policy_state"] == "allowed_official_http"
    assert len(items) == len(clusters) == 2
    assert all(item["scope"] == "REGIONAL" for item in items)
    assert all(
        json_loads(item["evidence_json"], {})["regional_event"]["matching_basis"]
        == "official_usgs_event_id" for item in items
    )
    assert all(
        item["rank_score"] == sum(
            json_loads(item["evidence_json"], {})["ranking"]["factors"].values()
        )
        for item in items
    )
    assert unchanged["item_count"] == 0
    assert latest["status"] == "not_modified" and latest["http_status"] == 304
    assert latest["last_modified_sent"] == "Thu, 08 Oct 2026 18:00:00 GMT"
