from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from starlette.requests import Request

from console1701 import config as config_module
from console1701.api import build_router
from console1701.config import load_config
from console1701.db import connect_db, init_db
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
    system_page = _route(router, "/{scope}")(_request("/SYSTEM"), "SYSTEM")
    assert system_page.status_code == 200
    assert "heavy open data disabled 1" in system_page.body.decode()
    assert "homepage extract disabled 1" in system_page.body.decode()
    assert _route(router, "/api/news/scopes/{scope}")("GLOBAL")["items"] == []
    assert _route(router, "/api/news/summary")()["scope_states"]["GLOBAL"]["state"] == "failing"
    assert len(_route(router, "/api/news/sources")()) == 5


def test_global_parser_failure_from_fixture_reaches_stored_health_and_ui(tmp_path, monkeypatch):
    state_dir = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state_dir / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state_dir / "handoffs")
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    fixture = tmp_path / "gdacs.rss"
    fixture.write_text((Path(__file__).parent / "fixtures/news/global_gdacs.rss").read_text())
    config_path = tmp_path / "global-parser-failure.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - {{id: gdacs_failure_fixture, name: GDACS malformed fixture,
                   kind: rss, parser: gdacs_rss, source_family: gdacs,
                   official_status: official, enabled: true,
                   url: '{fixture.as_uri()}'}}
    """).strip() + "\n")
    first = run_news_scan(config_path)
    assert first["status"] == "complete"
    assert first["item_count"] == 1
    fixture.write_text("<rss><channel><item>")
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
        conn.commit()
    result = run_news_scan(config_path)
    assert result["status"] == "partial"
    assert result["item_count"] == 0
    with connect_db(config["_db_path"]) as conn:
        runs = conn.execute(
            "SELECT status FROM news_fetch_runs ORDER BY id"
        ).fetchall()
        items = conn.execute(
            "SELECT id FROM news_items WHERE scope='GLOBAL'"
        ).fetchall()
        states = get_news_sources_status(conn, config)
        scope_state = get_news_scope_states(conn, config)["GLOBAL"]
    assert runs[-1]["status"] == "parser_failed"
    assert len(items) == 1  # Last good snapshot survives the failed refresh.
    assert states[0]["health_state"] == "parser_failed"
    assert scope_state["state"] == "failing"

    router = build_router(str(config_path))
    page = _route(router, "/{scope}")(_request("/GLOBAL"), "GLOBAL")
    assert page.status_code == 200
    assert "parser_failed" in page.body.decode()
    assert _route(router, "/api/news/scopes/{scope}")("GLOBAL")["sources"][0][
        "health_state"
    ] == "parser_failed"


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


@pytest.mark.parametrize(
    "news_enabled,source_line,expected",
    [
        (False, "", "disabled"),
        (True, "", "not_configured"),
        (True, "- {id: waiting, name: Waiting, kind: api_json, enabled: false, "
         "url: 'file:///missing.json'}", "configured_disabled"),
        (True, "- {id: waiting, name: Waiting, kind: api_json, enabled: true, "
         "url: 'file:///missing.json'}", "configured_never_run"),
    ],
)
def test_global_get_routes_never_ingest_for_unstarted_states(
    tmp_path, monkeypatch, news_enabled, source_line, expected
):
    def unexpected_access(*args, **kwargs):
        raise AssertionError("GET route attempted ingest")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)
    config_path = tmp_path / "state.yml"
    source_config = (
        f"      sources:\n        {source_line}\n" if source_line else
        "      sources: []\n"
    )
    config_path.write_text(
        "paths: {repo_roots: [], explicit_repos: []}\n"
        "global: {enabled: true}\n"
        f"news:\n  enabled: {str(news_enabled).lower()}\n"
        "  scopes:\n    GLOBAL:\n      enabled: true\n" + source_config
    )
    router = build_router(str(config_path))
    page = _route(router, "/{scope}")(_request("/GLOBAL"), "GLOBAL")
    assert page.status_code == 200
    assert expected in page.body.decode()
    assert expected in _route(
        router, "/{scope}")(_request("/SYSTEM"), "SYSTEM"
    ).body.decode()
    assert _route(router, "/api/news/scopes/{scope}")("GLOBAL")["state"]["state"] == expected
    assert _route(router, "/api/news/summary")()["scope_states"]["GLOBAL"]["state"] == expected


@pytest.mark.parametrize(
    "stored_state,expected,stale",
    [
        ("healthy", "healthy", False),
        ("healthy", "stale", True),
        ("failing", "failing", False),
        ("parser_failed", "parser_failed", False),
        ("policy_blocked", "policy_blocked", False),
        ("rate_limited", "rate_limited", False),
        ("robots_blocked", "robots_blocked", False),
        ("unsupported", "unsupported", False),
    ],
)
def test_global_get_routes_never_ingest_for_stored_health_states(
    tmp_path, monkeypatch, stored_state, expected, stale
):
    state_dir = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state_dir / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state_dir / "handoffs")
    config_path = tmp_path / "health.yml"
    config_path.write_text(dedent("""
        paths: {repo_roots: [], explicit_repos: []}
        global: {enabled: true}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - {id: health_fixture, name: Health fixture, kind: api_json,
                   enabled: true, url: 'file:///missing-health.json'}
    """).strip() + "\n")
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        source_id = conn.execute(
            "INSERT INTO news_sources (source_key, scope, name, kind, url, enabled, "
            "config_hash, created_at, updated_at) VALUES (?, 'GLOBAL', ?, 'api_json', ?, "
            "1, 'test', ?, ?)",
            ("health_fixture", "Health fixture", "file:///missing-health.json",
             "2026-10-15T00:00:00+00:00", "2026-10-15T00:00:00+00:00"),
        ).lastrowid
        conn.execute(
            "INSERT INTO news_source_health (source_id, observed_at, state, stale_after) "
            "VALUES (?, ?, ?, ?)",
            (source_id, "2026-10-15T00:00:00+00:00", stored_state,
             "2020-01-01T00:00:00+00:00" if stale else None),
        )
        conn.commit()

    def unexpected_access(*args, **kwargs):
        raise AssertionError("GET route attempted ingest")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)
    router = build_router(str(config_path))
    page = _route(router, "/{scope}")(_request("/GLOBAL"), "GLOBAL")
    assert page.status_code == 200
    assert expected in page.body.decode()
    system_page = _route(router, "/{scope}")(_request("/SYSTEM"), "SYSTEM")
    assert system_page.status_code == 200
    assert expected.replace("_", " ") in system_page.body.decode()
    sources = _route(router, "/api/news/sources")()
    assert sources[0]["health_state"] == expected
    assert _route(router, "/api/news/scopes/{scope}")("GLOBAL")["sources"][0][
        "health_state"
    ] == expected


def test_global_page_exposes_overflow_source_states(tmp_path):
    source_rows = "\n".join(
        f"                - {{id: source_{index}, name: Source {index}, kind: api_json, "
        f"enabled: false, url: 'file:///missing-{index}.json'}}"
        for index in range(8)
    )
    config_path = tmp_path / "overflow.yml"
    config_path.write_text(
        "paths: {repo_roots: [], explicit_repos: []}\n"
        "global: {enabled: true}\nnews:\n  enabled: true\n"
        "  scopes:\n    GLOBAL:\n      enabled: true\n      sources:\n"
        + source_rows + "\n"
    )
    router = build_router(str(config_path))
    view = _route(router, "/api/news/scopes/{scope}")("GLOBAL")
    assert view["source_total_count"] == 8
    assert view["source_omitted_count"] == 2
    assert len(view["source_overflow"]) == 2
    page = _route(router, "/{scope}")(_request("/GLOBAL"), "GLOBAL")
    body = page.body.decode()
    assert "6 of 8 sources shown" in body
    assert "2 more configured sources" in body
    assert "Source 7" in body


def test_global_get_hides_expired_items_before_next_scan(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures/news/global_gdacs.geojson"
    config_path = tmp_path / "expiry.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: gdacs_fixture
                  name: GDACS fixture
                  kind: api_json
                  parser: gdacs_geojson
                  source_family: gdacs
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        conn.execute("UPDATE news_items SET expires_at = '2020-01-01T00:00:00+00:00'")
        conn.commit()

    def unexpected_access(*args, **kwargs):
        raise AssertionError("GET route attempted ingest")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)
    router = build_router(str(config_path))
    scope_view = _route(router, "/api/news/scopes/{scope}")("GLOBAL")
    assert scope_view["items"] == []
    assert scope_view["clusters"] == []
    assert _route(router, "/api/news/summary")()["scope_states"]["GLOBAL"][
        "active_item_count"
    ] == 0
    page = _route(router, "/{scope}")(_request("/GLOBAL"), "GLOBAL")
    assert "0 shown" in page.body.decode()
