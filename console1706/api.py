from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from console1706.config import load_config
from console1706.db import connect_db, init_db
from console1706.evidence import (
    get_attention_items,
    get_handoffs,
    get_host_history,
    get_host_summary,
    get_interpretation_evidence,
    get_latest_host_snapshot,
    get_recent_events,
    get_repo_cards,
    get_repo_detail,
    get_system_summary,
)
from console1706.handoff import DEFAULT_TASK, create_handoff_packet
from console1706.live_probe import read_live_snapshot
from console1706.scanner import run_scan
from console1706.terminal_action import TerminalLaunchError, launch_host_alert_codex_terminal

PACKAGE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
_SCAN_LOCK = threading.Lock()
SCOPE_NAMES = ("INTERNAL", "LOCAL", "REGIONAL", "NATIONAL", "GLOBAL", "ORBITAL", "SYSTEM")
NAV_SCOPE_NAMES = ("OVERVIEW", *SCOPE_NAMES)


class HandoffRequest(BaseModel):
    repo_id: int
    task: str = DEFAULT_TASK
    title: str | None = None


class HostCodexActionRequest(BaseModel):
    section: str = "host"
    message: str
    why: str | None = None
    next_action: str | None = None
    evidence: Any | None = None


def _config(config_path: str | None) -> dict[str, Any]:
    return load_config(config_path)


def _conn(config_path: str | None):
    config = _config(config_path)
    sqlite_cfg = config.get("sqlite", {})
    conn = connect_db(
        config["_db_path"],
        busy_timeout_ms=int(sqlite_cfg.get("busy_timeout_ms", 5000)),
        journal_mode=str(sqlite_cfg.get("journal_mode", "WAL")),
    )
    init_db(conn)
    return conn


def _run_scan_locked(config_path: str | None) -> None:
    try:
        run_scan(config_path)
    finally:
        _SCAN_LOCK.release()


def build_router(config_path: str | None = None) -> APIRouter:
    router = APIRouter()

    def render_index(request: Request, active_scope: str = "LOCAL"):
        with _conn(config_path) as conn:
            summary = get_system_summary(conn)
            host = get_latest_host_snapshot(conn)
            host_summary = get_host_summary(conn)
            host_history = get_host_history(conn, limit=8)
            repos = get_repo_cards(conn)
            attention = get_attention_items(conn)
            events = get_recent_events(conn)
            handoffs = get_handoffs(conn)
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "summary": summary,
                "host": host,
                "host_summary": host_summary,
                "host_history": host_history,
                "repos": repos,
                "attention": attention,
                "events": events,
                "handoffs": handoffs,
                "scopes": NAV_SCOPE_NAMES,
                "active_scope": active_scope,
            },
        )

    @router.get("/", response_class=HTMLResponse)
    def index(request: Request):
        return render_index(request, "OVERVIEW")

    @router.get("/{scope}", response_class=HTMLResponse)
    def scoped_index(request: Request, scope: str):
        normalized = scope.upper()
        if normalized == "OVERVIEW":
            return render_index(request, "OVERVIEW")
        if normalized not in SCOPE_NAMES:
            raise HTTPException(status_code=404, detail="Scope not found")
        return render_index(request, normalized)

    @router.get("/repos/{repo_id}", response_class=HTMLResponse)
    def repo_page(request: Request, repo_id: int):
        with _conn(config_path) as conn:
            detail = get_repo_detail(conn, repo_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Repo not found")
        return templates.TemplateResponse(request, "repo.html", {"detail": detail})

    @router.get("/api/health")
    def health():
        config = _config(config_path)
        return {
            "status": "ok",
            "service": "console-1706",
            "host": config["server"]["host"],
            "port": config["server"]["port"],
            "db_path": config["_db_path"],
        }

    @router.get("/api/summary")
    def summary():
        with _conn(config_path) as conn:
            return get_system_summary(conn)

    @router.get("/api/repos")
    def repos():
        with _conn(config_path) as conn:
            return get_repo_cards(conn)

    @router.get("/api/repos/{repo_id}")
    def repo_detail(repo_id: int):
        with _conn(config_path) as conn:
            detail = get_repo_detail(conn, repo_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Repo not found")
        return detail

    @router.get("/api/attention")
    def attention():
        with _conn(config_path) as conn:
            return get_attention_items(conn)

    @router.get("/api/events")
    def events():
        with _conn(config_path) as conn:
            return get_recent_events(conn)

    @router.get("/api/host")
    def host():
        with _conn(config_path) as conn:
            latest = get_latest_host_snapshot(conn)
            return {
                "summary": get_host_summary(conn),
                "snapshot": latest,
                "evidence": latest.get("evidence") if latest else {},
            }

    @router.get("/api/host/history")
    def host_history(limit: int = 20):
        with _conn(config_path) as conn:
            return get_host_history(conn, limit=max(1, min(int(limit), 100)))

    @router.get("/api/live")
    def live():
        config = _config(config_path)
        scan_cfg = config.get("scan", {})
        interval_minutes = float(scan_cfg.get("interval_minutes", 30) or 30)
        payload = read_live_snapshot()
        with _conn(config_path) as conn:
            host_summary = get_host_summary(conn)
        payload["scan_timing"] = {
            "server_epoch_seconds": time.time(),
            "last_scan": host_summary.get("last_scan"),
            "last_scan_display": host_summary.get("last_scan_display"),
            "interval_seconds": max(1, int(interval_minutes * 60)),
            "state": host_summary.get("state"),
            "severity": host_summary.get("severity"),
            "score": host_summary.get("score"),
            "penalty_count": len(host_summary.get("penalties") or []),
        }
        return payload

    @router.post("/api/host/actions/codex")
    def host_codex_action(payload: HostCodexActionRequest):
        config = _config(config_path)
        try:
            return launch_host_alert_codex_terminal(config, payload.model_dump())
        except TerminalLaunchError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @router.get("/api/evidence/{interpretation_id}")
    def evidence(interpretation_id: int):
        with _conn(config_path) as conn:
            data = get_interpretation_evidence(conn, interpretation_id)
        if not data:
            raise HTTPException(status_code=404, detail="Evidence not found")
        return data

    @router.get("/api/handoffs")
    def handoffs():
        with _conn(config_path) as conn:
            return get_handoffs(conn)

    @router.post("/api/scan")
    def scan(background_tasks: BackgroundTasks):
        if not _SCAN_LOCK.acquire(blocking=False):
            return {"status": "already_running"}
        background_tasks.add_task(_run_scan_locked, config_path)
        return {"status": "started"}

    @router.post("/api/handoffs")
    def create_handoff(payload: HandoffRequest):
        config = _config(config_path)
        with _conn(config_path) as conn:
            try:
                return create_handoff_packet(
                    conn,
                    config,
                    repo_id=payload.repo_id,
                    task=payload.task,
                    title=payload.title,
                )
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router
