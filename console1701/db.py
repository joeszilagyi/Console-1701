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


def _has_table_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(str(row["name"]) == column for row in rows)


def _has_index(conn: sqlite3.Connection, table: str, index: str) -> bool:
    rows = conn.execute(f"PRAGMA index_list({table})").fetchall()
    return any(str(row["name"]) == index for row in rows)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ?",
        (table,),
    ).fetchone()
    return bool(row)


def _ensure_news_migrations(conn: sqlite3.Connection) -> None:
    if _has_table_column(conn, "news_items", "local_event_id"):
        return

    conn.execute(
        """
        ALTER TABLE news_items
        ADD COLUMN local_event_id INTEGER
        """
    )
    if not _has_index(conn, "news_items", "idx_news_items_local_event"):
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_news_items_local_event
            ON news_items(local_event_id)
            """
        )


def _migrate_source_registry_scope_key(conn: sqlite3.Connection, schema: str) -> None:
    if not _table_exists(conn, "news_source_registry"):
        return
    old_unique_key = any(
        bool(index["unique"])
        and [str(row["name"]) for row in conn.execute(f"PRAGMA index_info({index['name']})")]
        == ["source_key"]
        for index in conn.execute("PRAGMA index_list(news_source_registry)")
    )
    if not old_unique_key:
        return

    marker = "CREATE TABLE IF NOT EXISTS news_source_registry ("
    start = schema.index(marker)
    end = schema.index(");", start) + 2
    create_v2 = schema[start:end].replace(
        marker, "CREATE TABLE news_source_registry_v2 (", 1
    )
    columns = [
        str(row["name"]) for row in conn.execute("PRAGMA table_info(news_source_registry)")
    ]
    column_names = ", ".join(columns)
    conn.execute("SAVEPOINT migrate_news_source_registry")
    try:
        conn.execute(create_v2)
        conn.execute(
            f"INSERT INTO news_source_registry_v2 ({column_names}) "
            f"SELECT {column_names} FROM news_source_registry"
        )
        conn.execute("DROP TABLE news_source_registry")
        conn.execute("ALTER TABLE news_source_registry_v2 RENAME TO news_source_registry")
        conn.execute("RELEASE SAVEPOINT migrate_news_source_registry")
    except Exception:
        conn.execute("ROLLBACK TO SAVEPOINT migrate_news_source_registry")
        conn.execute("RELEASE SAVEPOINT migrate_news_source_registry")
        raise


def _migrate_news_sources_scope_key(conn: sqlite3.Connection, schema: str) -> None:
    if not _table_exists(conn, "news_sources"):
        return
    old_unique_key = any(
        bool(index["unique"])
        and [str(row["name"]) for row in conn.execute(f"PRAGMA index_info({index['name']})")]
        == ["source_key"]
        for index in conn.execute("PRAGMA index_list(news_sources)")
    )
    if not old_unique_key:
        return

    marker = "CREATE TABLE IF NOT EXISTS news_sources ("
    start = schema.index(marker)
    end = schema.index(");", start) + 2
    create_v2 = schema[start:end].replace(marker, "CREATE TABLE news_sources_v2 (", 1)
    columns = [str(row["name"]) for row in conn.execute("PRAGMA table_info(news_sources)")]
    column_names = ", ".join(columns)
    foreign_keys_enabled = bool(conn.execute("PRAGMA foreign_keys").fetchone()[0])
    # init_db commits before return; toggling enforcement outside a transaction lets us
    # rebuild the referenced table while retaining its IDs and child rows atomically.
    conn.commit()
    conn.execute("PRAGMA foreign_keys=OFF")
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(create_v2)
        conn.execute(
            f"INSERT INTO news_sources_v2 ({column_names}) "
            f"SELECT {column_names} FROM news_sources"
        )
        conn.execute("DROP TABLE news_sources")
        conn.execute("ALTER TABLE news_sources_v2 RENAME TO news_sources")
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise sqlite3.IntegrityError("news_sources scope-key migration violates foreign keys")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.execute(f"PRAGMA foreign_keys={'ON' if foreign_keys_enabled else 'OFF'}")


def init_db(conn: sqlite3.Connection) -> None:
    if _table_exists(conn, "news_items") and not _has_table_column(
        conn, "news_items", "local_event_id"
    ):
        _ensure_news_migrations(conn)
    schema = files("console1701").joinpath("schema.sql").read_text(encoding="utf-8")
    _migrate_news_sources_scope_key(conn, schema)
    _migrate_source_registry_scope_key(conn, schema)
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
