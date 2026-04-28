from __future__ import annotations

from pathlib import Path

from starlette.requests import Request

from console1706 import config as config_module
from console1706.api import build_router
from console1706.db import connect_db, init_db, utc_now


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

    response = _route_endpoint(router, "/")(_request("/"))

    assert response.status_code == 200
    assert response.media_type == "text/html"
    assert "STATUS" in response.body.decode()
    assert str(db_path) in response.body.decode()


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
            INSERT INTO repos (name, path, role, category, importance, enabled, created_at, updated_at)
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
