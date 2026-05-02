from __future__ import annotations

from pathlib import Path

from starlette.requests import Request

from console1706 import config as config_module
from console1706.api import build_router
from console1706.db import connect_db, init_db, utc_now
from console1706.scanner import insert_host_snapshot


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
    assert "Local Debian system console" in body
    assert "Machine readout" in body
    assert "demo-host" in body
    assert str(db_path) in body
    assert body.index("Machine readout") < body.index("Local work")


def test_root_page_renders_before_first_host_scan(tmp_path, monkeypatch):
    db_path = _use_temp_state(monkeypatch, tmp_path)
    config_path = tmp_path / "config.yml"
    _write_test_config(config_path)
    router = build_router(str(config_path))

    response = _route_endpoint(router, "/")(_request("/"))
    body = response.body.decode()

    assert response.status_code == 200
    assert "No host scan has run yet." in body
    assert str(db_path) in body


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
