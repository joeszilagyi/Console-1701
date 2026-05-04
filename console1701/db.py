from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

from console1701.config import DEFAULT_DB_PATH


def utc_now() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def connect_db(
    db_path: str | Path | None = None,
    *,
    busy_timeout_ms: int = 5000,
    journal_mode: str = "WAL",
) -> sqlite3.Connection:
    path = Path(db_path or DEFAULT_DB_PATH).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
    conn.execute(f"PRAGMA journal_mode={journal_mode}")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    schema = files("console1701").joinpath("schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def json_loads(value: str | None, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def latest_repo_snapshot(conn: sqlite3.Connection, repo_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT * FROM repo_snapshots
        WHERE repo_id = ?
        ORDER BY scanned_at DESC, id DESC
        LIMIT 1
        """,
        (repo_id,),
    ).fetchone()
    data = row_to_dict(row)
    if not data:
        return None
    data["changed_files"] = json_loads(data.pop("changed_files_json"), [])
    data["path_clusters"] = json_loads(data.pop("path_clusters_json"), {})
    data["recent_commits"] = json_loads(data.pop("recent_commits_json"), [])
    return data


def latest_test_snapshot(conn: sqlite3.Connection, repo_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT * FROM test_snapshots
        WHERE repo_id = ?
        ORDER BY scanned_at DESC, id DESC
        LIMIT 1
        """,
        (repo_id,),
    ).fetchone()
    return row_to_dict(row)


def latest_interpretation(conn: sqlite3.Connection, repo_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT * FROM interpreted_states
        WHERE repo_id = ? AND scope = 'repo'
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (repo_id,),
    ).fetchone()
    data = row_to_dict(row)
    if data:
        data["evidence"] = json_loads(data.pop("evidence_json"), {})
        data["rule_ids"] = json_loads(data.pop("rule_ids_json"), [])
    return data
