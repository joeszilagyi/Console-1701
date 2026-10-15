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


def _route(router, path):
    return next(route.endpoint for route in router.routes if route.path == path)


def _request(path):
    return Request({
        "type": "http", "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": path, "raw_path": path.encode(), "query_string": b"", "headers": [],
        "client": ("127.0.0.1", 12345), "server": ("testserver", 80), "root_path": "",
    })


def _config(tmp_path: Path, monkeypatch, *, science_enabled=False, news_enabled=True):
    state_dir = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state_dir / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state_dir / "handoffs")
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "solar_system_beyond": {"enabled": science_enabled},
        "news": {"enabled": news_enabled},
    }))
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
    return path, config


def test_cosmic_route_is_separate_from_app_health_and_offline(tmp_path, monkeypatch):
    path, config = _config(tmp_path, monkeypatch)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("page load fetched HTTP"))
    ))
    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("page load read fixture"))
    ))
    with connect_db(config["_db_path"]) as conn:
        state = get_news_scope_states(conn, config)["SYSTEM_SOLAR"]
    assert state["state"] == "disabled"
    assert state["label"] == "Cosmic"
    router = build_router(str(path))
    cosmic = _route(router, "/{scope}")(_request("/COSMIC"), "COSMIC").body.decode()
    system = _route(router, "/{scope}")(_request("/SYSTEM"), "SYSTEM").body.decode()
    scope = _route(router, "/api/news/scopes/{scope}")("COSMIC", 8)
    assert "COSMIC recent signal is disabled" in cosmic
    assert "Source ingest status" in system
    assert "Source ingest status" not in cosmic
    assert scope["scope"] == "SYSTEM_SOLAR"
    assert scope["items"] == []


def test_cosmic_enabled_without_sources_is_honestly_not_configured(tmp_path, monkeypatch):
    path, config = _config(tmp_path, monkeypatch, science_enabled=True)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("not-configured page fetched HTTP"))
    ))
    with connect_db(config["_db_path"]) as conn:
        state = get_news_scope_states(conn, config)["SYSTEM_SOLAR"]
    assert state["state"] == "not_configured"
    assert state["configured_source_count"] == 0
    html = _route(build_router(str(path)), "/{scope}")(
        _request("/COSMIC"), "COSMIC"
    ).body.decode()
    assert "No COSMIC sources are configured" in html
    assert "SYSTEM_SOLAR" not in html


def test_cosmic_configured_fixture_cannot_run_with_parent_disabled(tmp_path, monkeypatch):
    path, config = _config(tmp_path, monkeypatch)
    raw = yaml.safe_load(path.read_text())
    raw["news"]["scopes"] = {"SYSTEM_SOLAR": {
        "enabled": True,
        "sources": [{
            "id": "nasa_jpl_science_feed", "name": "Science fixture", "enabled": True,
            "kind": "rss", "parser": "nasa_jpl_science_rss", "fixture_only": True,
            "official_url": "https://www.nasa.gov/centers-and-facilities/jpl/feed/",
            "url": "file:///missing-science.rss",
        }],
    }}
    path.write_text(yaml.safe_dump(raw))
    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("disabled science read a fixture"))
    ))
    result = run_news_scan(path)
    assert result["scanned_sources"] == 0
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        state = get_news_scope_states(conn, config)["SYSTEM_SOLAR"]
    assert state["state"] == "disabled"


def test_cosmic_configured_disabled_and_never_run_sources_are_distinct(tmp_path, monkeypatch):
    path, _ = _config(tmp_path, monkeypatch, science_enabled=True)
    raw = yaml.safe_load(path.read_text())
    raw["news"]["scopes"] = {"SYSTEM_SOLAR": {
        "enabled": True,
        "sources": [{
            "id": "esa_space_science_feed", "name": "ESA Space Science",
            "kind": "rss", "parser": "esa_science_rss", "enabled": False,
            "fixture_only": False,
            "official_url": "https://www.esa.int/rssfeed/Our_Activities/Space_Science",
            "url": "https://www.esa.int/rssfeed/Our_Activities/Space_Science",
        }],
    }}
    path.write_text(yaml.safe_dump(raw))
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert get_news_sources_status(conn, config)[0]["health_state"] == "disabled"
    raw["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0]["enabled"] = True
    path.write_text(yaml.safe_dump(raw))
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert get_news_sources_status(conn, config)[0]["health_state"] == "policy_blocked"
    raw["news"]["fetch_policy"] = {"allow_official_http": True}
    path.write_text(yaml.safe_dump(raw))
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert get_news_sources_status(conn, config)[0]["health_state"] == (
            "configured_never_run"
        )
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("COSMIC state GET fetched HTTP"))
    ))
    html = _route(build_router(str(path)), "/{scope}")(
        _request("/COSMIC"), "COSMIC"
    ).body.decode()
    assert "configured_never_run" in html


def test_cosmic_candidate_summary_and_sqlite_health_render_without_get_fetch(
    tmp_path, monkeypatch
):
    path, _ = _config(tmp_path, monkeypatch, science_enabled=True)
    fixture = Path(__file__).parent / "fixtures/science/nasa_jpl_science.rss"
    raw = yaml.safe_load(path.read_text())
    raw["news"]["scopes"] = {"SYSTEM_SOLAR": {
        "enabled": True, "sources": [{
            "id": "nasa_jpl_science_feed", "name": "Science fixture", "enabled": True,
            "kind": "rss", "parser": "nasa_jpl_science_rss", "fixture_only": True,
            "official_url": "https://www.nasa.gov/centers-and-facilities/jpl/feed/",
            "url": f"file://{fixture}",
        }],
    }}
    path.write_text(yaml.safe_dump(raw))
    assert run_news_scan(path)["item_count"] >= 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        state = get_news_scope_states(conn, config)["SYSTEM_SOLAR"]
    assert state["science_candidates"]["candidate_count"] >= 170
    assert state["science_candidates"]["state_counts"]["heavy_archive_disabled"] >= 10
    assert state["science_candidates"]["state_counts"]["disabled"] == 3
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("COSMIC GET fetched HTTP"))
    ))
    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("COSMIC GET read fixture"))
    ))
    endpoint = _route(build_router(str(path)), "/{scope}")
    for raw_state, stale_after, expected in (
        ("healthy", "2000-01-01T00:00:00+00:00", "stale"),
        ("parser_failed", "2099-01-01T00:00:00+00:00", "parser_failed"),
        ("rate_limited", "2099-01-01T00:00:00+00:00", "rate_limited"),
        ("auth_required", "2099-01-01T00:00:00+00:00", "auth_required"),
        ("policy_blocked", "2099-01-01T00:00:00+00:00", "policy_blocked"),
        ("robots_blocked", "2099-01-01T00:00:00+00:00", "robots_blocked"),
        ("manual_review_only", "2099-01-01T00:00:00+00:00", "manual_review_only"),
        ("needs_scope_filter", "2099-01-01T00:00:00+00:00", "needs_scope_filter"),
        ("needs_terms_review", "2099-01-01T00:00:00+00:00", "needs_terms_review"),
        ("unsupported", "2099-01-01T00:00:00+00:00", "unsupported"),
        ("failed", "2099-01-01T00:00:00+00:00", "failing"),
        ("social_disabled", "2099-01-01T00:00:00+00:00", "social_disabled"),
        ("heavy_archive_disabled", "2099-01-01T00:00:00+00:00",
         "heavy_archive_disabled"),
        ("hype_blocked", "2099-01-01T00:00:00+00:00", "hype_blocked"),
        ("archive_firehose_blocked", "2099-01-01T00:00:00+00:00",
         "archive_firehose_blocked"),
    ):
        with connect_db(config["_db_path"]) as conn:
            conn.execute(
                "UPDATE news_source_health SET state=?, stale_after=?, message=? "
                "WHERE id=(SELECT MAX(id) FROM news_source_health)",
                (raw_state, stale_after, expected),
            )
            source = get_news_sources_status(conn, config)[0]
        assert source["health_state"] == expected
        html = endpoint(_request("/COSMIC"), "COSMIC").body.decode()
        assert expected in html
        assert "Heavy archive candidates gated" in html
        assert "Verified opt-in sources off by default" in html
        assert "SYSTEM_SOLAR" not in html
        assert "naming_collision_unresolved" not in html
