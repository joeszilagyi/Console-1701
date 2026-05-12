from __future__ import annotations

from pathlib import Path

from starlette.requests import Request

from console1701 import api as api_module
from console1701 import config as config_module
from console1701.api import build_router
from console1701.db import connect_db, init_db, utc_now
from console1701.news.scanner import run_news_scan
from console1701.scanner import insert_host_snapshot


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

    summary = _route_endpoint(router, "/api/news/summary")()
    scope_payload = _route_endpoint(router, "/api/news/scopes/{scope}")("LOCAL", 8)
    sources = _route_endpoint(router, "/api/news/sources")()

    with connect_db(db_path) as conn:
        init_db(conn)
        item_id = conn.execute("SELECT id FROM news_items ORDER BY id LIMIT 1").fetchone()["id"]

    item = _route_endpoint(router, "/api/news/items/{item_id}")(item_id)

    assert summary["enabled"] is True
    assert summary["active_item_count"] == 2
    assert scope_payload["state"]["state"] == "healthy"
    assert len(scope_payload["items"]) == 2
    assert sources[0]["policy"]["basis"] == "local_fixture_only"
    assert sources[0]["health_state"] == "healthy"
    assert item["title"] == "Seattle ferry delay at Colman Dock"
    assert summary["last_purge"]["summary"]["items"] == 0


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
