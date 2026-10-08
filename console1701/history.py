from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Any

from console1701.db import json_dumps, utc_now

# Attention items and handoff packets are durable decisions, not scan history.
# News rows have a separate, shorter retention policy.
HISTORY_TABLES = {
    "scan_runs": ("started_at", None),
    "host_snapshots": ("scanned_at", None),
    "repo_snapshots": ("scanned_at", "repo_id"),
    "test_snapshots": ("scanned_at", "repo_id"),
    "interpreted_states": ("created_at", "repo_id, scope"),
    "log_events": ("observed_at", None),
}


def history_cutoff(now: str, retention_days: int) -> str:
    return (datetime.fromisoformat(now) - timedelta(days=retention_days)).isoformat(
        timespec="seconds"
    )


def _candidate_filter(
    conn: sqlite3.Connection, table: str, timestamp_column: str, group_by: str | None
) -> tuple[str, list[Any]]:
    where = f"{timestamp_column} < ?"
    params: list[Any] = []
    if group_by:
        latest_ids = [
            int(row["id"])
            for row in conn.execute(
                f"SELECT MAX(id) AS id FROM {table} GROUP BY {group_by}"
            ).fetchall()
        ]
        if latest_ids:
            placeholders = ",".join("?" for _ in latest_ids)
            where += f" AND id NOT IN ({placeholders})"
            params.extend(latest_ids)
    elif table in {"scan_runs", "host_snapshots"}:
        latest = conn.execute(f"SELECT MAX(id) AS id FROM {table}").fetchone()
        if latest["id"] is not None:
            where += " AND id != ?"
            params.append(int(latest["id"]))
    return where, params


def history_expired_counts(conn: sqlite3.Connection, cutoff: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table, (timestamp_column, group_by) in HISTORY_TABLES.items():
        where, keep_params = _candidate_filter(conn, table, timestamp_column, group_by)
        row = conn.execute(
            f"SELECT COUNT(*) AS count FROM {table} WHERE {where}",
            (cutoff, *keep_params),
        ).fetchone()
        counts[table] = int(row["count"])
    return counts


def prune_history_batch(
    conn: sqlite3.Connection, cutoff: str, *, batch_size: int
) -> dict[str, int]:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    deleted: dict[str, int] = {}
    for table, (timestamp_column, group_by) in HISTORY_TABLES.items():
        where, keep_params = _candidate_filter(conn, table, timestamp_column, group_by)
        rows = conn.execute(
            f"SELECT id FROM {table} WHERE {where} ORDER BY id LIMIT ?",
            (cutoff, *keep_params, batch_size),
        ).fetchall()
        ids = [int(row["id"]) for row in rows]
        if ids:
            placeholders = ",".join("?" for _ in ids)
            conn.execute(f"DELETE FROM {table} WHERE id IN ({placeholders})", ids)
        deleted[table] = len(ids)
    return deleted


def record_history_prune(
    conn: sqlite3.Connection, *, cutoff: str, deleted: dict[str, int]
) -> None:
    result = {"at": utc_now(), "cutoff": cutoff, "deleted": deleted}
    conn.execute(
        "INSERT INTO settings (key, value) VALUES ('history.last_prune', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (json_dumps(result),),
    )
