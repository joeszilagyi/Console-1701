from __future__ import annotations

from pathlib import Path

from console1701.db import connect_db
from console1701.scanner import run_scan


def test_scan_releases_write_transaction_before_running_repo_tests(monkeypatch, tmp_path):
    from console1701 import scanner
    from console1701.config import load_config

    repo = tmp_path / "repo"
    repo.mkdir()
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        f"paths:\n  repo_roots: []\n  explicit_repos: [{repo}]\n"
    )
    database = load_config(config_path)["_db_path"]
    assert Path(database).is_relative_to(tmp_path)

    monkeypatch.setattr(scanner, "probe_system", lambda _config: {"health": {"state": "OK"}})
    monkeypatch.setattr(scanner, "probe_repo", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(scanner, "probe_configured_logs", lambda _config: [])
    monkeypatch.setattr(scanner, "interpret_all_repos", lambda _conn, _config: None)

    def run_tests(_repo, _snapshot, _config):
        with connect_db(database, busy_timeout_ms=100) as other:
            other.execute("BEGIN IMMEDIATE")
            other.execute("ROLLBACK")
        return {"detected": True, "status": "pass"}

    monkeypatch.setattr(scanner, "build_test_snapshot", run_tests)

    assert run_scan(config_path)["status"] == "complete"
