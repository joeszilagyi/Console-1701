from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from urllib.error import HTTPError

import pytest
import yaml

from console1701.config import ConfigError, load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import (
    USGS_GEOSERVE_ADMIN_URL,
    USGS_REGIONAL_EARTHQUAKES_URL,
    OfficialFetchResult,
    RateLimitedError,
    fetch_national_usgs_geoserve_admin,
)
from console1701.news.parsers import NewsIngestError, PayloadTooLargeError, UnsupportedSourceError
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/news"
ADMIN = json.loads((FIXTURES / "national_usgs_geoserve_admin.json").read_text())


def _source() -> dict:
    return {
        "scope": "NATIONAL", "id": "usgs_eq_geojson", "kind": "api_json",
        "parser": "usgs_earthquake_geojson", "url": USGS_REGIONAL_EARTHQUAKES_URL,
        "verification_status": "verified", "min_magnitude": 5.0,
        "geoserve_admin_enrichment": True, "interval_minutes": 30,
    }


def _feed(count: int = 2) -> str:
    payload = json.loads((FIXTURES / "national_usgs_earthquakes.json").read_text())
    original = payload["features"][0]
    features = []
    for index in range(count):
        row = deepcopy(original)
        event_id = f"live-border-{index}"
        row["id"] = event_id
        row["properties"]["url"] = (
            f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}"
        )
        row["properties"]["place"] = "Near the border"
        row["geometry"]["coordinates"] = (
            [-122.3, 48.5, 12.7] if index % 2 == 0 else [-122.9, 49.25, 12.7]
        )
        features.append(row)
    payload["features"] = features
    return json.dumps(payload)


def _config(path: Path, *, interval: int = 30) -> Path:
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {
            "enabled": True,
            "fetch_policy": {"allow_official_http": True},
            "scopes": {"NATIONAL": {"enabled": True, "sources": [{
                "id": "usgs_eq_geojson", "enabled": True,
                "interval_minutes": interval,
                "geoserve_admin_enrichment": True,
            }]}},
        },
    }))
    return path


def test_geoserve_opt_in_requires_thirty_minute_live_source(tmp_path):
    with pytest.raises(ConfigError, match="interval_minutes"):
        load_config(_config(tmp_path / "too-often.yml", interval=5))
    configured = load_config(_config(tmp_path / "allowed.yml"))
    source = configured["news"]["scopes"]["NATIONAL"]["sources"][0]
    assert source["geoserve_admin_enrichment"] is True
    assert source["interval_minutes"] == 30


def test_geoserve_transport_rejects_wrong_source_and_caps_response(monkeypatch):
    source = _source()
    observed = {}

    class Response:
        status = 200
        headers = {"Content-Type": "application/json"}

        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, limit):
            return self.body[:limit]

    class Opener:
        def __init__(self, body):
            self.body = body

        def open(self, request, *, timeout):
            observed["url"] = request.full_url
            observed["accept"] = request.get_header("Accept")
            observed["timeout"] = timeout
            return Response(self.body)

    body = json.dumps(ADMIN["border-wa"]).encode()
    monkeypatch.setattr(
        "console1701.news.official_http.build_opener", lambda *handlers: Opener(body)
    )
    response, size = fetch_national_usgs_geoserve_admin(
        source, latitude=48.5, longitude=-122.3,
        user_agent="console-1701 test", timeout_seconds=100,
    )
    assert response["admin"]["features"][0]["properties"]["iso"] == "USA"
    assert size == len(body)
    assert observed == {
        "url": (USGS_GEOSERVE_ADMIN_URL
                + "?latitude=48.500000&longitude=-122.300000&type=admin"),
        "accept": "application/json", "timeout": 5,
    }
    with pytest.raises(UnsupportedSourceError):
        fetch_national_usgs_geoserve_admin(
            {**source, "url": "https://example.org/earthquakes"},
            latitude=48.5, longitude=-122.3,
            user_agent="console-1701 test", timeout_seconds=5,
        )
    with pytest.raises(UnsupportedSourceError):
        fetch_national_usgs_geoserve_admin(
            {**source, "interval_minutes": 5},
            latitude=48.5, longitude=-122.3,
            user_agent="console-1701 test", timeout_seconds=5,
        )
    monkeypatch.setattr(
        "console1701.news.official_http.build_opener",
        lambda *handlers: Opener(b"x" * 2049),
    )
    with pytest.raises(PayloadTooLargeError):
        fetch_national_usgs_geoserve_admin(
            source, latitude=48.5, longitude=-122.3,
            user_agent="console-1701 test", timeout_seconds=5,
        )

    class RateLimitedOpener:
        def open(self, request, *, timeout):
            raise HTTPError(request.full_url, 429, "rate limited", {}, None)

    monkeypatch.setattr(
        "console1701.news.official_http.build_opener",
        lambda *handlers: RateLimitedOpener(),
    )
    with pytest.raises(RateLimitedError):
        fetch_national_usgs_geoserve_admin(
            source, latitude=48.5, longitude=-122.3,
            user_agent="console-1701 test", timeout_seconds=5,
        )


def test_opted_in_live_scan_excludes_verified_foreign_epicenter(tmp_path, monkeypatch):
    feed = _feed()
    calls = []
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: OfficialFetchResult(feed, 200, None, None, len(feed)),
    )

    def fake_admin(source, *, latitude, longitude, **kwargs):
        calls.append((latitude, longitude))
        result = ADMIN["border-wa" if latitude == 48.5 else "border-bc"]
        return result, len(json.dumps(result))

    monkeypatch.setattr("console1701.news.scanner.fetch_national_usgs_geoserve_admin", fake_admin)
    path = _config(tmp_path / "live.yml")
    result = run_news_scan(path)
    assert result["status"] == "complete" and result["item_count"] == 1
    assert calls == [(48.5, -122.3), (49.25, -122.9)]
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        items = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchall()
        run = conn.execute(
            "SELECT evidence_json FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert len(items) == 1
    item = json_loads(items[0]["evidence_json"], {})
    assert item["usgs_earthquake"]["filter"]["geoserve_admin"]["iso"] == "USA"
    assert item["usgs_earthquake"]["filter"]["geography_basis"] == (
        "usgs_geoserve_admin_live"
    )
    assert item["national_identity"]["multi_state_impact"] is False
    assert json_loads(run["evidence_json"], {})["geoserve_admin"]["lookups_applied"] == 2


def test_geoserve_failure_keeps_coarse_feed(tmp_path, monkeypatch):
    feed = _feed(6)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: OfficialFetchResult(feed, 200, None, None, len(feed)),
    )
    calls = []

    def fake_admin(source, *, latitude, longitude, **kwargs):
        calls.append((latitude, longitude))
        if len(calls) == 2:
            raise NewsIngestError("GeoServe unavailable")
        result = ADMIN["border-wa"]
        return result, len(json.dumps(result))

    monkeypatch.setattr("console1701.news.scanner.fetch_national_usgs_geoserve_admin", fake_admin)
    path = _config(tmp_path / "failure.yml")
    assert run_news_scan(path)["item_count"] == 6
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute(
            "SELECT evidence_json FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    evidence = json_loads(run["evidence_json"], {})["geoserve_admin"]
    assert evidence["state"] == "unavailable"
    assert evidence["lookups_attempted"] == 2
    assert evidence["lookups_applied"] == 1


def test_malformed_geoserve_response_discards_all_enrichment(tmp_path, monkeypatch):
    feed = _feed()
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: OfficialFetchResult(feed, 200, None, None, len(feed)),
    )
    wrong = deepcopy(ADMIN["border-bc"])
    wrong["metadata"]["request"] = ADMIN["border-wa"]["metadata"]["request"]
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_national_usgs_geoserve_admin",
        lambda source, *, latitude, longitude, **kwargs: (
            ADMIN["border-wa"] if latitude == 48.5 else wrong, 400,
        ),
    )
    path = _config(tmp_path / "malformed.yml")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        items = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchall()
        run = conn.execute(
            "SELECT evidence_json FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert all(
        json_loads(row["evidence_json"], {})["usgs_earthquake"]["filter"]
        .get("geoserve_admin") is None for row in items
    )
    assert json_loads(run["evidence_json"], {})["geoserve_admin"]["state"] == (
        "invalid_response"
    )


def test_geoserve_rate_limit_backs_off_two_hours(tmp_path, monkeypatch):
    feed = _feed()
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: OfficialFetchResult(feed, 200, None, None, len(feed)),
    )
    calls = []

    def rate_limited(*args, **kwargs):
        calls.append(1)
        raise RateLimitedError("GeoServe returned HTTP 429")

    monkeypatch.setattr("console1701.news.scanner.fetch_national_usgs_geoserve_admin", rate_limited)
    path = _config(tmp_path / "rate.yml")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        conn.execute(
            "UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'"
        )
        conn.commit()
    run_news_scan(path)
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute(
            "SELECT evidence_json FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    evidence = json_loads(run["evidence_json"], {})["geoserve_admin"]
    assert evidence["state"] == "rate_backoff"
    assert evidence["lookups_attempted"] == 0
    assert len(calls) == 1


def test_geoserve_lookups_are_capped_at_five(tmp_path, monkeypatch):
    feed = _feed(6)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: OfficialFetchResult(feed, 200, None, None, len(feed)),
    )
    calls = []
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_national_usgs_geoserve_admin",
        lambda source, *, latitude, longitude, **kwargs: (
            calls.append((latitude, longitude)) or ADMIN[
                "border-wa" if latitude == 48.5 else "border-bc"
            ], 400,
        ),
    )
    path = _config(tmp_path / "cap.yml")
    capped = run_news_scan(path)
    assert capped["item_count"] >= 1, capped
    assert len(calls) == 5
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute(
            "SELECT evidence_json FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    evidence = json_loads(run["evidence_json"], {})["geoserve_admin"]
    assert evidence["state"] == "bounded_partial"
    assert evidence["candidate_count"] == 6
    assert evidence["lookups_applied"] == 5
