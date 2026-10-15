from __future__ import annotations

from pathlib import Path

import yaml
from starlette.requests import Request

from console1701 import config as config_module
from console1701.api import build_router
from console1701.config import load_config
from console1701.db import connect_db, init_db
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_scope_states, get_news_sources_status


def _config(tmp_path: Path, monkeypatch, sources: list[dict], *, flags: dict | None = None,
            news_enabled=True, fetch_policy: dict | None = None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    state_dir = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state_dir / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state_dir / "handoffs")
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "orbital": {"enabled": True, **(flags or {})},
        "news": {"enabled": news_enabled, "fetch_policy": fetch_policy or {}, "scopes": {
            "ORBITAL": {"enabled": True, "sources": sources},
        }},
    }))
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
    return path, config


def _source(key: str, *, enabled=True, **extra):
    return {"id": key, "enabled": enabled,
            "url": f"file:///missing-{key}.json", **extra}


def _request() -> Request:
    return Request({
        "type": "http", "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": "/ORBITAL", "raw_path": b"/ORBITAL", "query_string": b"", "headers": [],
        "client": ("127.0.0.1", 12345), "server": ("testserver", 80), "root_path": "",
    })


def test_orbital_source_health_distinguishes_disabled_social_and_restricted(tmp_path, monkeypatch):
    path, config = _config(tmp_path, monkeypatch, [
        _source("swpc_alerts_json", enabled=False),
        _source("reddit_space"),
        _source("space_track_home", auth={"api_key": "configured-test-key"}),
        _source("celestrak_elements"),
        _source("swpc_home"),
        _source("nasa_news"),
        _source("nasa_open_apis"),
    ])
    with connect_db(config["_db_path"]) as conn:
        states = {row["source_key"]: row["health_state"]
                  for row in get_news_sources_status(conn, config)}
        scope = get_news_scope_states(conn, config)["ORBITAL"]
    assert states == {
        "swpc_alerts_json": "disabled",
        "reddit_space": "social_disabled",
        "space_track_home": "restricted_source_disabled",
        "celestrak_elements": "sensitivity_blocked",
        "swpc_home": "source_health_only",
        "nasa_news": "manual_review_only",
        "nasa_open_apis": "auth_required",
    }
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP on GET")),
    )
    monkeypatch.setattr(
        "console1701.news.scanner.load_fixture_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no fixture on GET")),
    )
    assert scope["state"] == "failing"
    router = build_router(str(path))
    endpoint = next(route.endpoint for route in router.routes if route.path == "/{scope}")
    html = endpoint(_request(), "ORBITAL").body.decode()
    assert "Restricted disabled" in html
    assert "Sensitivity blocked" in html
    assert "Health only" in html
    assert "auth_required" in html
    assert "manual_review_only" in html
    assert "No" in html and "stored" in html


def test_orbital_disabled_and_empty_states_are_distinct(tmp_path, monkeypatch):
    for label, sources, news_enabled, expected in (
        ("news_off", [], False, "disabled"),
        ("empty", [], True, "not_configured"),
        ("all_off", [_source("swpc_alerts_json", enabled=False)], True,
         "configured_disabled"),
    ):
        path, config = _config(
            tmp_path / label, monkeypatch, sources, news_enabled=news_enabled
        )
        with connect_db(config["_db_path"]) as conn:
            assert get_news_scope_states(conn, config)["ORBITAL"]["state"] == expected
        router = build_router(str(path))
        endpoint = next(route.endpoint for route in router.routes if route.path == "/{scope}")
        assert expected in endpoint(_request(), "ORBITAL").body.decode()


def test_orbital_homepage_and_topic_policy_states_are_distinct(tmp_path, monkeypatch):
    path, config = _config(
        tmp_path, monkeypatch, [
            _source("custom_page", name="Candidate page", kind="homepage_headlines"),
            _source("swpc_alerts_json"),
        ],
        flags={"include_space_weather": False},
        fetch_policy={"allow_homepage_extractors": True},
    )
    with connect_db(config["_db_path"]) as conn:
        states = {row["source_key"]: row["health_state"]
                  for row in get_news_sources_status(conn, config)}
    assert states == {"custom_page": "homepage_disabled", "swpc_alerts_json": "policy_blocked"}
    router = build_router(str(path))
    endpoint = next(route.endpoint for route in router.routes if route.path == "/{scope}")
    html = endpoint(_request(), "ORBITAL").body.decode()
    assert "homepage_disabled" in html and "policy_blocked" in html


def test_orbital_terms_and_scope_filter_remain_closed_with_allowance_flags(tmp_path, monkeypatch):
    path, config = _config(tmp_path, monkeypatch, [
        _source("space_track_home", auth={"api_key": "configured-test-key"}),
        _source("celestrak_elements", parser="generic_json_items"),
    ], flags={
        "allow_auth_required_sources": True,
        "allow_restricted_sources": True,
        "allow_tactical_sources": True,
        "include_satellite_catalog": True,
    })
    with connect_db(config["_db_path"]) as conn:
        states = {row["source_key"]: row["health_state"]
                  for row in get_news_sources_status(conn, config)}
    assert states == {
        "space_track_home": "needs_terms_review",
        "celestrak_elements": "needs_scope_filter",
    }
    monkeypatch.setattr(
        "console1701.news.scanner.load_fixture_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked fixture read")),
    )
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked HTTP")),
    )
    assert run_news_scan(path)["item_count"] == 0


def test_orbital_stale_parser_and_rate_states_render_from_sqlite(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures/orbital/swpc_alerts.json"
    path, config = _config(tmp_path, monkeypatch, [
        _source("swpc_alerts_json", url=f"file://{fixture}"),
    ])
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    assert run_news_scan(path)["item_count"] == 2
    monkeypatch.setattr(
        "console1701.news.scanner.load_fixture_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no fixture on GET")),
    )
    router = build_router(str(path))
    endpoint = next(route.endpoint for route in router.routes if route.path == "/{scope}")
    for raw_state, stale_after, expected in (
        ("healthy", "2000-01-01T00:00:00+00:00", "stale"),
        ("parser_failed", "2099-01-01T00:00:00+00:00", "parser_failed"),
        ("rate_limited", "2099-01-01T00:00:00+00:00", "rate_limited"),
        ("failed", "2099-01-01T00:00:00+00:00", "failing"),
    ):
        with connect_db(config["_db_path"]) as conn:
            conn.execute(
                "UPDATE news_source_health SET state=?, stale_after=?, message=? "
                "WHERE id=(SELECT MAX(id) FROM news_source_health)",
                (raw_state, stale_after, expected),
            )
            states = {row["source_key"]: row["health_state"]
                      for row in get_news_sources_status(conn, config)}
        assert states["swpc_alerts_json"] == expected
        assert expected in endpoint(_request(), "ORBITAL").body.decode()
        assert expected in endpoint(_request(), "SYSTEM").body.decode()
