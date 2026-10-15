from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import (
    USGS_REGIONAL_EARTHQUAKES_URL,
    OfficialFetchResult,
    is_supported_official_source,
)
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/national_usgs_earthquakes.json"


def _config(path: Path, *, national: bool = True, allow_http: bool = True,
            threshold: float = 5.0) -> Path:
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        national: {{enabled: {str(national).lower()}}}
        news:
          enabled: true
          fetch_policy: {{allow_official_http: {str(allow_http).lower()}}}
          scopes:
            NATIONAL:
              enabled: true
              sources:
                - id: usgs_eq_geojson
                  enabled: true
                  min_magnitude: {threshold}
    """).strip() + "\n")
    return path


def test_national_usgs_exact_source_and_parent_gates(tmp_path, monkeypatch):
    source = {
        "scope": "NATIONAL", "id": "usgs_eq_geojson", "kind": "api_json",
        "parser": "usgs_earthquake_geojson", "url": USGS_REGIONAL_EARTHQUAKES_URL,
        "verification_status": "verified", "min_magnitude": 5.0,
    }
    assert is_supported_official_source(source)
    assert not is_supported_official_source({**source, "url": source["url"] + "?x=1"})
    assert not is_supported_official_source({**source, "min_magnitude": 2.0})
    assert not is_supported_official_source({**source, "verification_status": "official_page_seen"})
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked HTTP")),
    )
    for index, settings in enumerate((
        {"national": False}, {"allow_http": False}, {"threshold": 2.0},
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


def test_national_usgs_explicit_scan_and_conditional_refresh(tmp_path, monkeypatch):
    path = _config(tmp_path / "live.yml")
    fixture = FIXTURE.read_text()
    calls: list[dict] = []

    def fake_fetch(source, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return OfficialFetchResult(fixture, 200, None, "Thu, 15 Oct 2026 19:46:00 GMT",
                                       len(fixture))
        return OfficialFetchResult(None, 304, None, "Thu, 15 Oct 2026 19:46:00 GMT", 0)

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
            "SELECT evidence_json FROM news_items WHERE scope = 'NATIONAL'"
        ).fetchall()
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope = 'NATIONAL'"
        ).fetchall()
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
        conn.commit()
    unchanged = run_news_scan(path)
    assert first["status"] == "complete" and first["item_count"] == 3
    assert skipped["skipped_sources"] == 1
    assert len(calls) == 2
    assert calls[0]["last_modified"] is None
    assert calls[1]["last_modified"] == "Thu, 15 Oct 2026 19:46:00 GMT"
    assert runs[0]["status"] == "success" and runs[0]["http_status"] == 200
    assert runs[0]["item_count"] == 3
    assert json_loads(runs[0]["evidence_json"], {})["fixture_only"] is False
    assert len(items) == len(clusters) == 3
    assert all(json_loads(row["evidence_json"], {})["national_event"]["confidence"]
               == "source_reported" for row in items)
    assert unchanged["item_count"] == 0
