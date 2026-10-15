from __future__ import annotations

from pathlib import Path

import yaml
from starlette.requests import Request

from console1701 import config as config_module
from console1701.api import build_router
from console1701.config import load_config
from console1701.db import connect_db, init_db
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_sources_status


def _path(tmp_path: Path, monkeypatch, sources: list[dict], *, flags: dict | None = None):
    state_dir = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state_dir / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state_dir / "handoffs")
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "orbital": {"enabled": True, **(flags or {})},
        "news": {"enabled": True, "scopes": {
            "ORBITAL": {"enabled": True, "sources": sources}
        }},
    }))
    return path


def _source(key: str, *, url: str | None = None, **extra) -> dict:
    return {
        "id": key, "name": key, "enabled": True,
        "url": url or f"file:///missing-{key}.json", **extra,
    }


def _route(router, path: str):
    return next(route.endpoint for route in router.routes if getattr(route, "path", None) == path)


def _request(path: str) -> Request:
    return Request({
        "type": "http", "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": path, "raw_path": path.encode(), "query_string": b"", "headers": [],
        "client": ("127.0.0.1", 12345), "server": ("testserver", 80), "root_path": "",
    })


def _no_access(monkeypatch):
    def unexpected(*args, **kwargs):
        raise AssertionError("ORBITAL gate must not read a fixture or fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected)
    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected)


def test_orbital_and_system_get_routes_do_not_run_ingest(tmp_path, monkeypatch):
    path = _path(tmp_path, monkeypatch, [
        _source("nasa_rss_feeds"),
        _source("space_track_home"),
        _source("celestrak_elements", parser="generic_json_items"),
        _source("reddit_space"),
    ])
    _no_access(monkeypatch)
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
    router = build_router(str(path))
    orbital_page = _route(router, "/{scope}")(_request("/ORBITAL"), "ORBITAL")
    system_page = _route(router, "/{scope}")(_request("/SYSTEM"), "SYSTEM")
    scope = _route(router, "/api/news/scopes/{scope}")("ORBITAL", 8)
    summary = _route(router, "/api/news/summary")()
    sources = _route(router, "/api/news/sources")()
    assert orbital_page.status_code == system_page.status_code == 200
    assert scope["items"] == []
    assert summary["scope_states"]["ORBITAL"]["state"] == "failing"
    assert {row["source_key"] for row in sources if row["scope"] == "ORBITAL"} == {
        "nasa_rss_feeds", "space_track_home", "celestrak_elements", "reddit_space",
    }


def test_restricted_and_policy_sensitive_candidates_stop_before_access(tmp_path, monkeypatch):
    keys = [
        "space_track_home", "space_track_docs", "celestrak_elements",
        "celestrak_satcat", "celestrak_socrates", "nasa_conjunction_assessment",
        "nasa_orbital_debris_news", "esa_reentry", "orbital_arcgis_reentry_candidate",
    ]
    path = _path(tmp_path, monkeypatch, [_source(key) for key in keys])
    _no_access(monkeypatch)
    assert run_news_scan(path)["item_count"] == 0
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        status = {row["source_key"]: row for row in get_news_sources_status(conn, config)}
        count = conn.execute("SELECT COUNT(*) FROM news_items WHERE scope='ORBITAL'").fetchone()[0]
        assert count == 0
    assert status["space_track_home"]["health_state"] == "auth_required"
    assert status["space_track_docs"]["health_state"] == "auth_required"
    for key in ("celestrak_elements", "celestrak_satcat", "celestrak_socrates"):
        assert status[key]["health_state"] == "sensitivity_blocked"
    assert status["nasa_orbital_debris_news"]["health_state"] == "policy_blocked"
    assert status["esa_reentry"]["health_state"] == "auth_required"
    assert status["orbital_arcgis_reentry_candidate"]["health_state"] == "unsupported"


def test_missing_api_keys_stop_nasa_space_track_and_future_api(tmp_path, monkeypatch):
    path = _path(tmp_path, monkeypatch, [
        _source("nasa_open_apis"),
        _source("space_track_home"),
        _source("future_keyed", kind="api_json", parser="generic_json_items",
                auth={"api_key": ""}),
        _source("x_swpc", kind="api_json", auth={"token": ""}),
    ])
    _no_access(monkeypatch)
    assert run_news_scan(path)["item_count"] == 0
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        states = {row["source_key"]: row["health_state"]
                  for row in get_news_sources_status(conn, config)}
    assert states == {
        "nasa_open_apis": "auth_required",
        "space_track_home": "auth_required",
        "future_keyed": "auth_required",
        "x_swpc": "auth_required",
    }


def test_tactical_catalogs_do_not_render_even_with_topic_flags(tmp_path, monkeypatch):
    keys = ["celestrak_elements", "celestrak_satcat", "celestrak_socrates"]
    path = _path(tmp_path, monkeypatch, [
        _source(key, parser="generic_json_items") for key in keys
    ], flags={
        "include_satellite_catalog": True,
        "include_conjunction_awareness": True,
        "allow_restricted_sources": True,
        "allow_tactical_sources": True,
    })
    _no_access(monkeypatch)
    assert run_news_scan(path)["item_count"] == 0
    router = build_router(str(path))
    scope = _route(router, "/api/news/scopes/{scope}")("ORBITAL", 8)
    page = _route(router, "/{scope}")(_request("/ORBITAL"), "ORBITAL")
    assert scope["items"] == []
    assert "Tactical object 12345" not in page.body.decode()
    assert all(source["health_state"] == "needs_scope_filter"
               for source in scope["sources"] if source["source_key"] in keys)
