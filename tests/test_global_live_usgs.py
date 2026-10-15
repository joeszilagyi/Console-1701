from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from console1701.config import ConfigError, load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import (
    USGS_GLOBAL_EARTHQUAKES_URL,
    OfficialFetchResult,
    is_supported_official_source,
)
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/global_usgs_earthquakes.json"


def _config(tmp_path, *, allow_http=True, source_override=None):
    source = {
        "id": "usgs_eq_geojson_global", "kind": "api_json",
        "parser": "usgs_earthquake_geojson", "enabled": True,
        "max_age_hours": 168,
    }
    source.update(source_override or {})
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "global": {"enabled": True},
        "news": {"enabled": True, "fetch_policy": {"allow_official_http": allow_http},
                 "scopes": {"GLOBAL": {"enabled": True, "sources": [source]}}},
    }))
    return path


def test_global_usgs_exact_allowlist_and_opt_in_scan(tmp_path, monkeypatch):
    path = _config(tmp_path)
    config = load_config(path)
    source = config["news"]["scopes"]["GLOBAL"]["sources"][0]
    assert source["url"] == USGS_GLOBAL_EARTHQUAKES_URL
    assert source["verification_status"] == "verified"
    assert is_supported_official_source(source)
    for override in (
        {"url": USGS_GLOBAL_EARTHQUAKES_URL + "?x=1"},
        {"parser": "generic_json"}, {"verification_status": "official_page_seen"},
        {"min_magnitude": 4.0}, {"auth": {"token": "x"}},
    ):
        assert not is_supported_official_source({**source, **override})
    fixture = FIXTURE.read_text()
    calls = []

    def fake_fetch(source, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return OfficialFetchResult(fixture, 200, None, "Thu, 15 Oct 2026 19:46:00 GMT",
                                       len(fixture))
        return OfficialFetchResult(None, 304, None, "Thu, 15 Oct 2026 19:46:00 GMT", 0)

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    first = run_news_scan(path)
    second = run_news_scan(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute("SELECT evidence_json FROM news_items WHERE scope='GLOBAL'").fetchall()
        runs = conn.execute(
            "SELECT status, http_status FROM news_fetch_runs ORDER BY id"
        ).fetchall()
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
        conn.commit()
    third = run_news_scan(path)
    assert first["status"] == "complete" and first["item_count"] == 4
    assert second["skipped_sources"] == 1
    assert third["item_count"] == 0 and len(calls) == 2
    assert calls[1]["last_modified"] == "Thu, 15 Oct 2026 19:46:00 GMT"
    assert [(row["status"], row["http_status"]) for row in runs] == [("success", 200)]
    assert len(rows) == 4
    for row in rows:
        evidence = json_loads(row["evidence_json"], {})
        assert evidence["ingest"]["fixture_only"] is False
        assert evidence["source"]["verification_status"] == "verified"
        assert evidence["global"]["affected_countries"] == []
        assert evidence["global"]["geography_basis"] == "source_place_unverified"


@pytest.mark.parametrize("override", [
    {"url": USGS_GLOBAL_EARTHQUAKES_URL + "?x=1"},
    {"parser": "generic_json"}, {"verification_status": "official_page_seen"},
    {"interval_minutes": 5}, {"kind": "rss"},
])
def test_global_usgs_live_config_rejects_nonexact_source(tmp_path, override):
    with pytest.raises(ConfigError):
        load_config(_config(tmp_path, source_override=override))


def test_global_usgs_http_disabled_blocks_fetch(tmp_path, monkeypatch):
    path = _config(tmp_path, allow_http=False)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *args, **kwargs: (
        (_ for _ in ()).throw(AssertionError("GLOBAL GET attempted unapproved HTTP"))
    ))
    assert run_news_scan(path)["item_count"] == 0
