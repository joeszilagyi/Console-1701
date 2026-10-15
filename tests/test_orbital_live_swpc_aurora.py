from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import (
    SWPC_OVATION_AURORA_URL,
    OfficialFetchResult,
    is_supported_official_source,
)
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_scope_view, get_news_sources_status

FIXTURE = Path(__file__).parent / "fixtures/orbital/swpc_aurora.json"
LOCATION = {
    "name": "Seattle", "scope": "LOCAL", "latitude": 47.6, "longitude": -122.3,
    "radius_degrees": 2.0, "min_intensity": 50.0,
}


def _config(path: Path, *, location=True, verified=True, allow_http=True, minimum=50):
    orbital = {
        "enabled": True,
        "aurora_locations": [{**LOCATION, "min_intensity": minimum}] if location else [],
    }
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "orbital": orbital,
        "news": {
            "enabled": True,
            "fetch_policy": {"allow_official_http": allow_http},
            "scopes": {"ORBITAL": {"enabled": True, "sources": [{
                "id": "swpc_aurora_json", "enabled": True,
                "verification_status": "verified" if verified else "official_page_seen",
                "url": SWPC_OVATION_AURORA_URL,
            }]}}
        },
    }))
    return path


def _payload(*, observation_age=10, forecast_ahead=50) -> str:
    raw = json.loads(FIXTURE.read_text())
    now = datetime.now(UTC)
    raw["Observation Time"] = (
        now - timedelta(minutes=observation_age)
    ).isoformat(timespec="seconds")
    raw["Forecast Time"] = (
        now + timedelta(minutes=forecast_ahead)
    ).isoformat(timespec="seconds")
    return json.dumps(raw)


def test_aurora_live_allowlist_requires_configured_bounded_location():
    source = {
        "scope": "ORBITAL", "id": "swpc_aurora_json", "kind": "api_json",
        "parser": "swpc_aurora_json", "url": SWPC_OVATION_AURORA_URL,
        "verification_status": "verified", "aurora_locations": [LOCATION],
    }
    assert is_supported_official_source(source)
    for changed in (
        {"url": SWPC_OVATION_AURORA_URL + "?x=1"},
        {"parser": "generic_json_items"}, {"aurora_locations": []},
        {"aurora_locations": [{**LOCATION, "min_intensity": 0}]},
        {"verification_status": "official_page_seen"},
    ):
        assert not is_supported_official_source({**source, **changed})


def test_aurora_location_and_http_gates_stop_before_access(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked HTTP")),
    )
    path = _config(tmp_path / "no-location.yml", location=False)
    assert run_news_scan(path)["item_count"] == 0
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        status = get_news_sources_status(conn, config)[0]
    assert status["health_state"] == "needs_scope_filter"
    for index, settings in enumerate((
        {"verified": False}, {"allow_http": False}, {"minimum": 0},
    )):
        assert run_news_scan(_config(tmp_path / f"blocked-{index}.yml", **settings))[
            "item_count"
        ] == 0


def test_aurora_live_scan_retains_only_local_model_summary(tmp_path, monkeypatch):
    path = _config(tmp_path / "live.yml")
    payload = _payload()
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda source, **kwargs: OfficialFetchResult(payload, 200, '"aurora-v1"', None,
                                                     len(payload)),
    )
    assert run_news_scan(path)["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute("SELECT evidence_json, tags_json FROM news_items WHERE scope='ORBITAL'")
        row = row.fetchone()
        assert len(get_news_scope_view(conn, config, "ORBITAL")["items"]) == 1
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["swpc_aurora"]["model_only"] is True
    assert evidence["swpc_aurora"]["sample_count"] <= 5
    assert "coordinates" not in evidence["swpc_aurora"]
    assert evidence["orbital_impact"]["tags"] == ["AURORA", "LOCAL_IMPACT", "SKY"]
    assert evidence["ingest"]["fixture_only"] is False


def test_aurora_live_scan_drops_stale_model(tmp_path, monkeypatch):
    path = _config(tmp_path / "old.yml")
    payload = _payload(observation_age=180, forecast_ahead=50)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda source, **kwargs: OfficialFetchResult(payload, 200, None, None, len(payload)),
    )
    assert run_news_scan(path)["item_count"] == 0
