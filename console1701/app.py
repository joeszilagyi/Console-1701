from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from console1701.api import PACKAGE_DIR, build_router
from console1701.config import ensure_state_dirs, load_config
from console1701.db import connect_db, init_db


def create_app(config_path: str | None = None) -> FastAPI:
    config = load_config(config_path)
    ensure_state_dirs(config)
    sqlite_cfg = config.get("sqlite", {})
    with connect_db(
        config["_db_path"],
        busy_timeout_ms=int(sqlite_cfg.get("busy_timeout_ms", 5000)),
        journal_mode=str(sqlite_cfg.get("journal_mode", "WAL")),
    ) as conn:
        init_db(conn)

    app = FastAPI(title="console-1701", version="0.1.0")
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(PACKAGE_DIR) / "static")),
        name="static",
    )
    app.include_router(build_router(config_path))
    return app
