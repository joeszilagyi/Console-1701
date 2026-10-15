from __future__ import annotations

from textwrap import dedent

from starlette.requests import Request

from console1701 import config as config_module
from console1701.api import build_router
from console1701.config import load_config
from console1701.db import connect_db
from console1701.news.global_registry import (
    GLOBAL_AUTH_REQUIRED_SOURCE_KEYS,
    GLOBAL_HEAVY_ADAPTERS,
    list_global_source_registry,
)
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_scope_states, get_news_sources_status


def _route(router, path: str):
    return next(route.endpoint for route in router.routes if getattr(route, "path", None) == path)


def _request(path: str) -> Request:
    return Request({
        "type": "http", "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": path, "raw_path": path.encode(), "query_string": b"", "headers": [],
        "client": ("127.0.0.1", 12345), "server": ("testserver", 80), "root_path": "",
    })


def test_global_gated_sources_show_health_and_never_access_fixture_or_http(tmp_path, monkeypatch):
    state_dir = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state_dir / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state_dir / "handoffs")

    def unexpected_access(*args, **kwargs):
        raise AssertionError("blocked GLOBAL source attempted file or network access")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)
    config_path = tmp_path / "global.yml"
    config_path.write_text(dedent("""
        paths: {repo_roots: [], explicit_repos: []}
        global: {enabled: true, allow_auth_required_sources: true}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - {id: reddit_worldnews, kind: api_json, enabled: true,
                   url: 'file:///does-not-exist-social.json'}
                - {id: hdx_home, kind: api_json, enabled: true,
                   url: 'file:///does-not-exist-heavy.json'}
                - {id: gdacs_home, enabled: true,
                   url: 'file:///does-not-exist-homepage.html'}
                - {id: reliefweb_api_help, kind: api_json, enabled: true,
                   url: 'file:///does-not-exist-manual.json'}
                - {id: nasa_firms_api, kind: api_json, enabled: true,
                   url: 'file:///does-not-exist-auth.json'}
    """).strip() + "\n")

    result = run_news_scan(config_path)
    assert result["status"] == "partial"
    assert result["item_count"] == 0
    assert result["scanned_sources"] == 5
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        statuses = {row["source_key"]: row for row in get_news_sources_status(conn, config)}
        scope_state = get_news_scope_states(conn, config)["GLOBAL"]
        fetch_states = {
            row["status"] for row in conn.execute("SELECT status FROM news_fetch_runs")
        }
    assert {key: row["health_state"] for key, row in statuses.items()} == {
        "reddit_worldnews": "social_disabled",
        "hdx_home": "heavy_open_data_disabled",
        "gdacs_home": "homepage_extract_disabled",
        "reliefweb_api_help": "manual_review_only",
        "nasa_firms_api": "auth_required",
    }
    assert fetch_states == set(scope_state["source_state_counts"])
    assert scope_state["state"] == "failing"

    router = build_router(str(config_path))
    page = _route(router, "/{scope}")(_request("/GLOBAL"), "GLOBAL")
    body = page.body.decode()
    assert page.status_code == 200
    assert "Heavy data blocked" in body
    assert "GLOBAL homepage blocked" in body
    assert "GLOBAL has failing or policy-blocked sources." in body
    assert "0 shown" in body
    assert _route(router, "/{scope}")(_request("/SYSTEM"), "SYSTEM").status_code == 200
    assert _route(router, "/api/news/scopes/{scope}")("GLOBAL")["items"] == []
    assert _route(router, "/api/news/summary")()["scope_states"]["GLOBAL"]["state"] == "failing"
    assert len(_route(router, "/api/news/sources")()) == 5


def test_all_heavy_global_candidates_block_without_local_gate(tmp_path, monkeypatch):
    def unexpected_access(*args, **kwargs):
        raise AssertionError("heavy GLOBAL candidate attempted file or network access")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)
    keys = [
        entry["source_key"] for entry in list_global_source_registry()
        if entry["source_class"] == "heavy_open_data_candidate"
        or entry["adapter"] in GLOBAL_HEAVY_ADAPTERS
    ]
    assert len(keys) >= 15
    config_path = tmp_path / "heavy.yml"
    sources = "\n".join(
        f"                - {{id: {key}, kind: api_json, enabled: true, "
        f"url: 'file:///missing-{key}.json'}}"
        for key in keys
    )
    config_path.write_text(
        "paths: {repo_roots: [], explicit_repos: []}\n"
        "global: {enabled: true, allow_auth_required_sources: true}\n"
        "news:\n  enabled: true\n  fetch_policy: {allow_homepage_extractors: true}\n"
        "  scopes:\n    GLOBAL:\n      enabled: true\n      sources:\n" + sources + "\n"
    )
    result = run_news_scan(config_path)
    assert result["status"] == "partial"
    assert result["scanned_sources"] == len(keys)
    assert result["item_count"] == 0
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        statuses = get_news_sources_status(conn, config)
    assert len(statuses) == len(keys)
    assert {row["health_state"] for row in statuses} <= {
        "heavy_open_data_disabled", "auth_required"
    }


def test_known_auth_and_social_global_candidates_do_not_run_without_config(
    tmp_path, monkeypatch
):
    def unexpected_access(*args, **kwargs):
        raise AssertionError("account source attempted file or network access")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)
    keys = sorted(GLOBAL_AUTH_REQUIRED_SOURCE_KEYS | {
        "reddit_worldnews", "bluesky_global_breaking", "x_api_docs"
    })
    config_path = tmp_path / "account.yml"
    sources = "\n".join(
        f"                - {{id: {key}, kind: api_json, enabled: true, "
        f"url: 'file:///missing-{key}.json'}}"
        for key in keys
    )
    config_path.write_text(
        "paths: {repo_roots: [], explicit_repos: []}\n"
        "global: {enabled: true, allow_auth_required_sources: true}\n"
        "news:\n  enabled: true\n  scopes:\n    GLOBAL:\n      enabled: true\n"
        "      sources:\n" + sources + "\n"
    )
    result = run_news_scan(config_path)
    assert result["status"] == "partial"
    assert result["scanned_sources"] == len(keys)
    assert result["item_count"] == 0
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        statuses = get_news_sources_status(conn, config)
    assert {row["health_state"] for row in statuses} <= {
        "auth_required", "social_disabled", "heavy_open_data_disabled", "manual_review_only"
    }
