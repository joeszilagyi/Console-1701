from __future__ import annotations

import pytest

import console1701.config as config_module
import console1701.db as db_module


@pytest.fixture(autouse=True)
def isolated_console_state(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Keep every test away from the running console's SQLite database."""
    state_dir = tmp_path / "state"
    database = state_dir / "console.sqlite"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", database)
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state_dir / "handoffs")
    monkeypatch.setattr(db_module, "DEFAULT_DB_PATH", database)
