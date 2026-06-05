from __future__ import annotations

from pathlib import Path

from starlette.requests import Request

from console1701 import api as api_module
from console1701 import config as config_module
from console1701.api import build_router
from console1701.config import load_config
from console1701.db import connect_db, init_db, utc_now
from console1701.news.scanner import run_news_scan
from console1701.scanner import insert_host_snapshot

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "news"


def _write_test_config(path: Path) -> None:
    path.write_text(
        """
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _use_temp_state(monkeypatch, tmp_path: Path) -> Path:
    state_dir = tmp_path / "state"
    db_path = state_dir / "console.sqlite"
    handoff_dir = state_dir / "handoffs"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", db_path)
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", handoff_dir)
    return db_path


def _request(path: str) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "root_path": "",
        }
    )


def _route_endpoint(router, path: str):
    route = next(route for route in router.routes if getattr(route, "path", None) == path)
    return route.endpoint


def _insert_news_source(
    conn,
    source_key: str,
    *,
    scope: str,
    name: str,
    kind: str = "local_file_json",
    url: str | None = None,
    enabled: bool = True,
) -> int:
    row = conn.execute(
        """
        INSERT INTO news_sources (
          source_key, scope, name, kind, url, homepage_url, enabled, config_hash,
          priority, tags_json, policy_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_key,
            scope,
            name,
            kind,
            url,
            None,
            1 if enabled else 0,
            "manual-test",
            50,
            "[]",
            "{}",
            "2026-06-01T12:00:00+00:00",
            "2026-06-01T12:00:00+00:00",
        ),
    )
    conn.commit()
    return int(row.lastrowid)


def _insert_news_source_health(
    conn,
    source_id: int,
    *,
    observed_at: str,
    state: str,
    stale_after: str | None = None,
    last_success_at: str | None = None,
    last_failure_at: str | None = None,
    message: str | None = None,
    consecutive_failures: int = 0,
) -> None:
    conn.execute(
        """
        INSERT INTO news_source_health (
          source_id, observed_at, state, last_success_at, last_failure_at,
          consecutive_failures, stale_after, message, evidence_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}')
        """,
        (
            source_id,
            observed_at,
            state,
            last_success_at,
            last_failure_at,
            consecutive_failures,
            stale_after,
            message,
        ),
    )
    conn.commit()


def test_root_page_renders_html(tmp_path, monkeypatch):
    db_path = _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    _write_test_config(config_path)
    router = build_router(str(config_path))
    with connect_db(db_path) as conn:
        init_db(conn)
        insert_host_snapshot(
            conn,
            "2026-05-01T12:00:00-07:00",
            {
                "identity": {"hostname": "demo-host"},
                "os": {"pretty_name": "Debian GNU/Linux 13"},
                "kernel": {"release": "6.12.0", "architecture": "x86_64"},
                "session": {"uptime_seconds": 123.0, "uptime_human": "2m"},
                "debian": {
                    "debian_version": "13.0",
                    "dpkg": {"installed_packages": 100, "audit_issue_count": 0},
                    "apt": {
                        "held_package_count": 0,
                        "history": {"last_command": "apt upgrade"},
                        "source_files": [],
                    },
                    "reboot": {"required": False},
                },
                "memory": {"available_percent": 50.0, "human_total": "8.0 GiB"},
                "storage": {"root": {"use_percent": 42.0}},
                "filesystems": {"items": []},
                "network": {"default_route": {"dev": "eth0"}},
                "services": {},
                "processes": {},
                "dev_tools": {},
                "logs": {},
                "health": {
                    "state": "OK",
                    "score": 100,
                    "severity": "green",
                    "headline": "No host issues",
                    "summary": "Host is OK.",
                    "next_sane_action": "No action needed.",
                    "penalties": [],
                    "checks": {},
                },
                "evidence": {},
                "probe_errors": [],
            },
        )
        conn.commit()

    response = _route_endpoint(router, "/")(_request("/"))
    body = response.body.decode()

    assert response.status_code == 200
    assert response.media_type == "text/html"
    assert "console-1701" in body
    assert "/static/app.js?v=machine-console-13" in body
    assert "/static/app.css?v=machine-console-17" in body
    assert 'id="news-scan-button"' in body
    assert 'data-active-scope="OVERVIEW"' in body
    assert 'data-scope-nav="OVERVIEW"' in body
    assert 'href="/"' in body
    assert 'data-scope-nav="INTERNAL"' in body
    assert 'href="/INTERNAL"' in body
    assert 'data-scope-nav="ORBITAL"' in body
    assert "Attention now" in body
    assert "Local and regional pulse" in body
    assert "Orbital and source health" in body
    assert "Recent-signal ingest is disabled by config." in body
    assert "Machine readout" not in body
    assert "demo-host" in body
    assert str(db_path) in body

    internal_response = _route_endpoint(router, "/{scope}")(_request("/INTERNAL"), "INTERNAL")
    internal_body = internal_response.body.decode()

    assert internal_response.status_code == 200
    assert "Machine readout" in internal_body
    assert "B2 Services / systems" in internal_body
    assert "B3 Debian" in internal_body
    assert "B4 Hardware" in internal_body
    assert 'data-sparkline="cpu"' in internal_body
    assert 'data-live="poll-policy"' in internal_body
    assert internal_body.index("Machine readout") < internal_body.index("Local work")


def test_scoped_root_page_marks_active_scope(tmp_path, monkeypatch):
    db_path = _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    _write_test_config(config_path)
    router = build_router(str(config_path))

    response = _route_endpoint(router, "/{scope}")(_request("/ORBITAL"), "ORBITAL")
    body = response.body.decode()

    assert response.status_code == 200
    assert 'data-active-scope="ORBITAL"' in body
    assert 'data-scope-nav="ORBITAL"' in body
    assert 'aria-current="page"' in body
    assert "Latest items" in body
    assert "Source health" in body
    assert "External news ingest is disabled by config." in body
    assert "Machine readout" not in body
    assert str(db_path) in body


def test_news_scope_page_and_api_render_fixture_backed_state(tmp_path, monkeypatch):
    db_path = _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    fixture = Path(__file__).resolve().parent / "fixtures" / "news" / "local_items.json"
    config_path.write_text(
        f"""
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
news:
  enabled: true
  scopes:
    LOCAL:
      enabled: true
      sources:
        - id: local_fixture
          name: Local fixture
          kind: local_file_json
          enabled: true
          url: "file://{fixture.resolve()}"
          parser: generic_json_items
          tags: [fixture]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    router = build_router(str(config_path))
    run_news_scan(str(config_path))

    scope_response = _route_endpoint(router, "/{scope}")(_request("/LOCAL"), "LOCAL")
    scope_body = scope_response.body.decode()

    assert scope_response.status_code == 200
    assert "Seattle ferry delay at Colman Dock" in scope_body
    assert "Source health" in scope_body
    assert "Local fixture" in scope_body
    assert "Audit trail" in scope_body
    assert "Family" in scope_body
    assert "Verification" in scope_body
    assert "Access" in scope_body
    assert "Retention expiry" in scope_body
    assert "Fetch run" in scope_body
    assert "Policy" in scope_body
    assert "Fetch 1" in scope_body
    assert "Health 1" in scope_body

    summary = _route_endpoint(router, "/api/news/summary")()
    scope_payload = _route_endpoint(router, "/api/news/scopes/{scope}")("LOCAL", 8)
    sources = _route_endpoint(router, "/api/news/sources")()

    with connect_db(db_path) as conn:
        init_db(conn)
        item_id = conn.execute("SELECT id FROM news_items ORDER BY id LIMIT 1").fetchone()["id"]

    item = _route_endpoint(router, "/api/news/items/{item_id}")(item_id)

    assert summary["enabled"] is True
    assert summary["active_item_count"] == 2
    assert summary["last_scan_result"]["status"] == "complete"
    assert summary["last_purge"]["before_counts"]["news_items"] == 2
    assert summary["source_state_counts"]["healthy"] == 1
    assert scope_payload["state"]["state"] == "healthy"
    assert scope_payload["state"]["source_state_counts"]["healthy"] == 1
    assert len(scope_payload["items"]) == 2
    assert sources[0]["policy"]["basis"] == "local_fixture_only"
    assert sources[0]["health_state"] == "healthy"
    assert sources[0]["recent_fetch_runs"][0]["status"] == "success"
    assert sources[0]["recent_health_rows"][0]["state"] == "healthy"
    assert item["title"] == "Seattle ferry delay at Colman Dock"
    assert item["source"]["source_key"] == "local_fixture"
    assert item["evidence"]["source"]["source_key"] == "local_fixture"
    assert item["evidence"]["policy"]["policy_state"] == "allowed_fixture_only"
    assert item["evidence"]["source_health"]["state"] == "healthy"
    assert item["evidence"]["privacy"]["article_body_stored"] is False
    assert summary["last_purge"]["summary"]["items"] == 0


def test_news_local_event_api_returns_event_summary(tmp_path, monkeypatch):
    db_path = _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    fixture = FIXTURE_DIR / "local_city_light_outages.json"
    config_path.write_text(
        f"""
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
news:
  enabled: true
  scopes:
    LOCAL:
      enabled: true
      sources:
        - id: city_light_outage_fixture_a
          name: City Light outage fixture A
          kind: local_file_json
          enabled: true
          url: "file://{fixture.resolve()}"
          parser: city_light_outages_json
          source_family: city_light
          source_class: official_utility
          adapter: source_health_probe_only
        - id: city_light_outage_fixture_b
          name: City Light outage fixture B
          kind: local_file_json
          enabled: true
          url: "file://{fixture.resolve()}"
          parser: city_light_outages_json
          source_family: city_light
          source_class: official_utility
          adapter: source_health_probe_only
""".strip()
        + "\n",
        encoding="utf-8",
    )
    router = build_router(str(config_path))
    run_news_scan(str(config_path))
    with connect_db(db_path) as conn:
        init_db(conn)
        row = conn.execute(
            "SELECT id, local_event_id FROM news_items ORDER BY id LIMIT 1"
        ).fetchone()
        event_id = int(row["local_event_id"]) if row and row["local_event_id"] else None
        item_id = int(row["id"]) if row else None

    if not event_id:
        raise AssertionError("No local event was linked during scan")

    local_event = _route_endpoint(router, "/api/news/local-events/{event_id}")(event_id)
    item = _route_endpoint(router, "/api/news/items/{item_id}")(item_id)

    assert local_event["id"] == event_id
    assert int(local_event["source_count"]) == 2
    assert int(local_event["item_count"]) == 2
    assert int(local_event["matching_contract"]["topic_repetition_score"]) > 0
    assert int(local_event["matching_contract"]["source_severity_score"]) == 0
    assert any(payload["id"] == item_id for payload in local_event["items"])
    assert item["local_event"]["id"] == event_id
    assert item["evidence"]["local_event"]["event"]["id"] == event_id


def test_news_scan_api_returns_disabled_and_started_states(tmp_path, monkeypatch):
    _use_temp_state(monkeypatch, tmp_path)
    disabled_config = tmp_path / "disabled.yml"
    _write_test_config(disabled_config)
    disabled_router = build_router(str(disabled_config))

    disabled = _route_endpoint(disabled_router, "/api/news/scan")(api_module.BackgroundTasks())

    assert disabled["status"] == "disabled"

    enabled_config = tmp_path / "enabled.yml"
    fixture = Path(__file__).resolve().parent / "fixtures" / "news" / "local_items.json"
    enabled_config.write_text(
        f"""
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
news:
  enabled: true
  scopes:
    LOCAL:
      enabled: true
      sources:
        - id: local_fixture
          name: Local fixture
          kind: local_file_json
          enabled: true
          url: "file://{fixture.resolve()}"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    enabled_router = build_router(str(enabled_config))

    started = _route_endpoint(enabled_router, "/api/news/scan")(api_module.BackgroundTasks())

    assert started["status"] == "started"


def test_system_scope_renders_recent_signal_config_warnings(tmp_path, monkeypatch):
    _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        """
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
news:
  enabled: true
  scopes:
    LOCAL:
      enabled: true
    REGIONAL:
      sources:
        - id: blocked_remote
          name: Blocked remote
          kind: rss
          enabled: true
          url: "https://example.invalid/feed.xml"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    router = build_router(str(config_path))

    response = _route_endpoint(router, "/{scope}")(_request("/SYSTEM"), "SYSTEM")
    body = response.body.decode()
    summary = _route_endpoint(router, "/api/news/summary")()

    assert response.status_code == 200
    assert "Config warnings" in body
    assert "LOCAL is enabled, but no sources are configured for it." in body
    assert "blocked_remote is enabled but blocked in the current fixture-only ingest phase." in body
    assert "LOCAL is enabled, but no sources are configured for it." in summary["config_warnings"]


def test_news_summary_surfaces_source_state_counts(tmp_path, monkeypatch):
    _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        """
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
news:
  enabled: true
  scopes:
    LOCAL:
      enabled: true
      sources:
        - id: waiting_fixture
          name: Waiting fixture
          kind: local_file_json
          enabled: true
          url: "file:///tmp/waiting.json"
        - id: disabled_fixture
          name: Disabled fixture
          kind: local_file_json
          enabled: false
          url: "file:///tmp/disabled.json"
    REGIONAL:
      enabled: false
      sources:
        - id: blocked_remote
          name: Blocked remote
          kind: rss
          enabled: true
          url: "https://example.invalid/feed.xml"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    router = build_router(str(config_path))

    summary = _route_endpoint(router, "/api/news/summary")()
    sources = _route_endpoint(router, "/api/news/sources")()

    assert summary["source_state_counts"]["configured_never_run"] == 1
    assert summary["source_state_counts"]["disabled"] == 1
    assert summary["source_state_counts"]["policy_blocked"] == 1
    assert any(source["health_message"] for source in sources)


def test_local_scope_ui_shows_disabled_source_states_without_fake_headlines(tmp_path, monkeypatch):
    _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        """
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
news:
  enabled: true
  scopes:
    LOCAL:
      enabled: true
      sources:
        - id: disabled_fixture
          name: Disabled fixture
          kind: local_file_json
          enabled: false
          url: "file:///tmp/disabled.json"
    REGIONAL:
      enabled: false
      sources: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    router = build_router(str(config_path))
    response = _route_endpoint(router, "/{scope}")(_request("/LOCAL"), "LOCAL")
    body = response.body.decode()

    assert response.status_code == 200
    assert "configured but disabled" in body
    assert "Source health" in body
    assert "No sources are configured for this scope." not in body
    assert "Seattle ferry delay at Colman Dock" not in body


def test_local_scope_ui_shows_not_configured_and_never_run_states(tmp_path, monkeypatch):
    _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        """
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
news:
  enabled: true
  scopes:
    LOCAL:
      enabled: true
    REGIONAL:
      enabled: true
      sources:
        - id: regional_stub
          name: Regional stub
          kind: local_file_json
          enabled: false
          url: "file:///tmp/regional.json"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    router = build_router(str(config_path))
    not_configured_page = _route_endpoint(router, "/{scope}")(_request("/LOCAL"), "LOCAL")
    not_configured_body = not_configured_page.body.decode()

    assert "No LOCAL sources are configured." in not_configured_body
    assert "No sources are configured for this scope." in not_configured_body

    _use_temp_state(monkeypatch, tmp_path)
    config_path.write_text(
        """
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
news:
  enabled: true
  scopes:
    LOCAL:
      enabled: true
      sources:
        - id: waiting_fixture
          name: Waiting fixture
          kind: local_file_json
          enabled: true
          url: "file:///tmp/waiting.json"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    never_run_router = build_router(str(config_path))
    never_run_page = _route_endpoint(never_run_router, "/{scope}")(_request("/LOCAL"), "LOCAL")
    never_run_body = never_run_page.body.decode()

    assert "have not been ingested yet" in never_run_body
    assert "No LOCAL sources are configured." not in never_run_body


def test_local_scope_ui_shows_stale_and_failing_states(tmp_path, monkeypatch):
    db_path = _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        """
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
news:
  enabled: true
  scopes:
    LOCAL:
      enabled: true
      sources:
        - id: stale_local_fixture
          name: Stale fixture
          kind: local_file_json
          enabled: true
          url: "file:///tmp/stale.json"
        - id: failed_local_fixture
          name: Failed fixture
          kind: local_file_json
          enabled: true
          url: "file:///tmp/fail.json"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    with connect_db(db_path) as conn:
        init_db(conn)
        stale_source_id = _insert_news_source(
            conn,
            "stale_local_fixture",
            scope="LOCAL",
            name="Stale fixture",
            url="file:///tmp/stale.json",
            enabled=True,
        )
        fail_source_id = _insert_news_source(
            conn,
            "failed_local_fixture",
            scope="LOCAL",
            name="Failed fixture",
            url="file:///tmp/fail.json",
            enabled=True,
        )
        _insert_news_source_health(
            conn,
            stale_source_id,
            observed_at="2020-01-01T00:00:00+00:00",
            state="healthy",
            stale_after="2020-01-01T00:00:00+00:00",
            last_success_at="2020-01-01T00:00:00+00:00",
            message="stale fixture",
        )
        _insert_news_source_health(
            conn,
            fail_source_id,
            observed_at="2026-05-01T00:00:00+00:00",
            state="parser_failed",
            last_failure_at="2026-05-01T00:00:00+00:00",
            message="forced parser failure",
            consecutive_failures=2,
        )

    router = build_router(str(config_path))
    stale_or_fail_page = _route_endpoint(router, "/{scope}")(_request("/LOCAL"), "LOCAL")
    body = stale_or_fail_page.body.decode()

    assert stale_or_fail_page.status_code == 200
    assert "stale" in body.lower()
    assert "failing" in body.lower()
    assert "parser failed" in body.lower()
    assert "forced parser failure" in body.lower()


def test_local_scope_ui_shows_social_and_homepage_disabled_states(tmp_path, monkeypatch):
    _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    _write_test_config(config_path)
    config = load_config(str(config_path))
    config["news"]["enabled"] = True
    config["news"]["scopes"]["LOCAL"]["enabled"] = True
    config["news"]["scopes"]["LOCAL"]["sources"] = [
        {
            "id": "social_candidate_fixture",
            "name": "Blocked social source",
            "scope": "LOCAL",
            "kind": "local_file_json",
            "enabled": True,
            "url": "file:///tmp/social-source.json",
            "source_family": "bluesky",
            "source_class": "social_candidate",
        },
        {
            "id": "homepage_headline_fixture",
            "name": "Blocked homepage extractor",
            "scope": "LOCAL",
            "kind": "homepage_headlines",
            "enabled": True,
            "url": "file:///tmp/homepage-source.html",
            "source_family": "official_seattle",
            "source_class": "official_local",
            "selectors": {
                "item_selector": ".item",
                "link_selector": "a",
            },
        },
    ]
    config["local"]["allow_social_sources"] = False
    config["news"]["fetch_policy"]["allow_homepage_extractors"] = False

    def fake_config(_path=None):
        return config

    monkeypatch.setattr(api_module, "_config", fake_config)
    router = build_router(str(config_path))

    scope_response = _route_endpoint(router, "/{scope}")(_request("/LOCAL"), "LOCAL")
    _route_endpoint(router, "/api/news/sources")()
    summary = _route_endpoint(router, "/api/news/summary")()
    body = scope_response.body.decode()

    assert scope_response.status_code == 200
    assert summary["source_state_counts"]["social_disabled"] == 1
    assert summary["source_state_counts"]["homepage_disabled"] == 1
    assert summary["scope_states"]["LOCAL"]["source_state_counts"]["social_disabled"] == 1
    assert summary["scope_states"]["LOCAL"]["source_state_counts"]["homepage_disabled"] == 1
    assert "Homepage extraction is disabled by config." in body
    assert (
        "LOCAL social source is blocked until local.allow_social_sources is enabled."
        in body
    )
    assert "Blocked social source" in body
    assert "Blocked homepage extractor" in body


def test_news_get_routes_do_not_trigger_ingest_or_fixture_reads(tmp_path, monkeypatch):
    _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        """
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
news:
  enabled: true
  scopes:
    LOCAL:
      enabled: true
      sources:
        - id: missing_fixture
          name: Missing fixture
          kind: local_file_json
          enabled: true
          url: "file:///tmp/console-1701-missing-news-fixture.json"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    router = build_router(str(config_path))

    def fail_if_scan_runs(_config_path=None):
        raise AssertionError("GET route triggered news ingest")

    monkeypatch.setattr(api_module, "run_news_scan", fail_if_scan_runs)

    root = _route_endpoint(router, "/")(_request("/"))
    local_page = _route_endpoint(router, "/{scope}")(_request("/LOCAL"), "LOCAL")
    system_page = _route_endpoint(router, "/{scope}")(_request("/SYSTEM"), "SYSTEM")
    summary = _route_endpoint(router, "/api/news/summary")()
    scope = _route_endpoint(router, "/api/news/scopes/{scope}")("LOCAL", 8)
    sources = _route_endpoint(router, "/api/news/sources")()

    assert root.status_code == 200
    assert local_page.status_code == 200
    assert system_page.status_code == 200
    assert summary["source_state_counts"]["configured_never_run"] == 1
    assert scope["state"]["state"] == "configured_never_run"
    assert sources[0]["source_key"] == "missing_fixture"
    assert sources[0]["latest_fetch_run"] is None


def test_root_page_renders_codex_terminal_action_for_host_penalty(tmp_path, monkeypatch):
    db_path = _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    _write_test_config(config_path)
    router = build_router(str(config_path))
    with connect_db(db_path) as conn:
        init_db(conn)
        insert_host_snapshot(
            conn,
            "2026-05-01T12:00:00-07:00",
            {
                "identity": {"hostname": "demo-host"},
                "os": {"pretty_name": "Debian GNU/Linux 13"},
                "kernel": {"release": "6.12.0", "architecture": "x86_64"},
                "session": {"uptime_seconds": 123.0, "uptime_human": "2m"},
                "memory": {"available_percent": 50.0, "human_total": "8.0 GiB"},
                "storage": {"root": {"use_percent": 42.0}},
                "filesystems": {"items": []},
                "network": {"default_route": {"dev": "eth0"}},
                "services": {},
                "processes": {},
                "dev_tools": {},
                "logs": {},
                "health": {
                    "state": "CAUTION",
                    "score": 85,
                    "severity": "amber",
                    "headline": "Failed system service: x11vnc.service.",
                    "summary": "Host has a failed unit.",
                    "next_sane_action": "Review services evidence first.",
                    "penalties": [
                        {
                            "severity": "amber",
                            "section": "services",
                            "message": "Failed system service: x11vnc.service.",
                            "why": "systemctl reports x11vnc.service is failed.",
                            "next": "systemctl status x11vnc.service --no-pager",
                            "evidence": {"failed_system": [{"unit": "x11vnc.service"}]},
                        }
                    ],
                    "checks": {},
                },
                "evidence": {},
                "probe_errors": [],
            },
        )
        conn.commit()

    response = _route_endpoint(router, "/{scope}")(_request("/INTERNAL"), "INTERNAL")
    body = response.body.decode()

    assert response.status_code == 200
    assert "delta-action" in body
    assert "attention-delta-area" in body
    assert 'data-scroll-target="#attention-delta-area"' in body
    assert "data-codex-scenario" in body
    assert "Open a new terminal with this alert loaded into interactive Codex" in body


def test_internal_page_renders_before_first_host_scan(tmp_path, monkeypatch):
    db_path = _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    _write_test_config(config_path)
    router = build_router(str(config_path))

    response = _route_endpoint(router, "/{scope}")(_request("/INTERNAL"), "INTERNAL")
    body = response.body.decode()

    assert response.status_code == 200
    assert "No host scan has run yet." in body
    assert str(db_path) in body


def test_host_codex_action_endpoint_uses_terminal_launcher(tmp_path, monkeypatch):
    _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    _write_test_config(config_path)
    router = build_router(str(config_path))
    captured = {}

    def fake_launch(config, scenario):
        captured["config"] = config
        captured["scenario"] = scenario
        return {"status": "launch_requested", "terminal": "fake-terminal"}

    monkeypatch.setattr(api_module, "launch_host_alert_codex_terminal", fake_launch)

    response = _route_endpoint(router, "/api/host/actions/codex")(
        api_module.HostCodexActionRequest(
            section="services",
            message="Failed system service: x11vnc.service.",
            why="systemctl reports failure",
            next_action="systemctl status x11vnc.service --no-pager",
            evidence={"unit": "x11vnc.service"},
        )
    )

    assert response["status"] == "launch_requested"
    assert response["terminal"] == "fake-terminal"
    assert captured["scenario"]["message"] == "Failed system service: x11vnc.service."
    assert captured["scenario"]["evidence"]["unit"] == "x11vnc.service"


def test_live_endpoint_adds_scan_timing_without_hardware_assumptions(tmp_path, monkeypatch):
    _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        """
scan:
  interval_minutes: 15
paths:
  repo_roots: []
  explicit_repos: []
logs: []
projects: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    router = build_router(str(config_path))

    monkeypatch.setattr(
        api_module,
        "read_live_snapshot",
        lambda: {
            "cpu": {"times": {"total": 1, "idle": 1}},
            "memory": {},
            "network": {},
            "filesystems": {},
            "power": {"on_battery": False, "source": "external"},
        },
    )

    response = _route_endpoint(router, "/api/live")()

    assert response["cpu"]["times"]["total"] == 1
    assert response["power"]["source"] == "external"
    assert response["scan_timing"]["interval_seconds"] == 900
    assert response["scan_timing"]["state"] == "UNKNOWN"


def test_repo_page_renders_existing_repo(tmp_path, monkeypatch):
    db_path = _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    _write_test_config(config_path)
    router = build_router(str(config_path))
    now = utc_now()

    with connect_db(db_path) as conn:
        init_db(conn)
        conn.execute(
            """
            INSERT INTO repos (
              name, path, role, category, importance, enabled, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "demo-repo",
                "/tmp/demo-repo",
                "Demo role",
                "Demo category",
                "high",
                1,
                now,
                now,
            ),
        )
        conn.commit()

    response = _route_endpoint(router, "/repos/{repo_id}")(_request("/repos/1"), 1)

    assert response.status_code == 200
    assert response.media_type == "text/html"
    assert "demo-repo" in response.body.decode()
