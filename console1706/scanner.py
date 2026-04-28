from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Any

from console1706.adapters import IGNORE_DIR_NAMES, safe_repo_name
from console1706.config import ensure_state_dirs, load_config, project_for_path
from console1706.db import connect_db, init_db, json_dumps, utc_now
from console1706.git_probe import probe_repo
from console1706.interpreter import interpret_all_repos
from console1706.log_probe import probe_configured_logs
from console1706.test_probe import build_test_snapshot


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def _repo_metadata(config: dict[str, Any], path: str | Path, source: str) -> dict[str, Any]:
    resolved = str(Path(path).expanduser().resolve())
    project = project_for_path(config, resolved)
    return {
        "name": project.get("name") or safe_repo_name(resolved),
        "path": resolved,
        "role": project.get("role"),
        "category": project.get("category"),
        "importance": project.get("importance"),
        "test_commands": project.get("test_commands") or [],
        "source": source,
    }


def discover_repos(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    discovered: dict[str, dict[str, Any]] = {}
    notes: list[str] = []

    for explicit in config.get("paths", {}).get("explicit_repos", []):
        metadata = _repo_metadata(config, explicit, "explicit")
        discovered[metadata["path"]] = metadata

    max_repos = int(config.get("scan", {}).get("max_repos_per_scan", 75))
    for root_value in config.get("paths", {}).get("repo_roots", []):
        root = Path(root_value).expanduser().resolve()
        if not root.exists():
            notes.append(f"Repo root missing: {root}")
            continue
        if _is_git_repo(root):
            metadata = _repo_metadata(config, root, "root")
            discovered.setdefault(metadata["path"], metadata)
            continue

        for current, dirs, _files in os.walk(root):
            current_path = Path(current)
            dirs[:] = [name for name in dirs if name not in IGNORE_DIR_NAMES]
            try:
                relative_depth = len(current_path.relative_to(root).parts)
            except ValueError:
                relative_depth = 0
            if relative_depth > 6:
                dirs[:] = []
                continue
            if _is_git_repo(current_path):
                metadata = _repo_metadata(config, current_path, "discovered")
                discovered.setdefault(metadata["path"], metadata)
                dirs[:] = []
                if len(discovered) >= max_repos:
                    notes.append(f"Scan capped after {max_repos} repos.")
                    return list(discovered.values()), notes

    return list(discovered.values()), notes


def upsert_repo(conn: sqlite3.Connection, metadata: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()
    conn.execute(
        """
        INSERT INTO repos (name, path, role, category, importance, enabled, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
          name = excluded.name,
          role = excluded.role,
          category = excluded.category,
          importance = excluded.importance,
          enabled = 1,
          updated_at = excluded.updated_at
        """,
        (
            metadata["name"],
            metadata["path"],
            metadata.get("role"),
            metadata.get("category"),
            metadata.get("importance"),
            now,
            now,
        ),
    )
    row = conn.execute("SELECT * FROM repos WHERE path = ?", (metadata["path"],)).fetchone()
    repo = dict(row)
    repo["test_commands"] = metadata.get("test_commands") or []
    return repo


def insert_repo_snapshot(
    conn: sqlite3.Connection,
    repo_id: int,
    scanned_at: str,
    snapshot: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO repo_snapshots (
          repo_id, scanned_at, branch, commit_sha, commit_subject, commit_author,
          commit_time, is_dirty, has_untracked, ahead_count, behind_count,
          changed_files_json, path_clusters_json, recent_commits_json,
          diff_fingerprint, raw_git_status, scan_error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            repo_id,
            scanned_at,
            snapshot.get("branch"),
            snapshot.get("commit_sha"),
            snapshot.get("commit_subject"),
            snapshot.get("commit_author"),
            snapshot.get("commit_time"),
            int(bool(snapshot.get("is_dirty"))) if snapshot.get("is_dirty") is not None else None,
            (
                int(bool(snapshot.get("has_untracked")))
                if snapshot.get("has_untracked") is not None
                else None
            ),
            snapshot.get("ahead_count"),
            snapshot.get("behind_count"),
            json_dumps(snapshot.get("changed_files") or []),
            json_dumps(snapshot.get("path_clusters") or {}),
            json_dumps(snapshot.get("recent_commits") or []),
            snapshot.get("diff_fingerprint"),
            snapshot.get("raw_git_status"),
            snapshot.get("scan_error"),
        ),
    )


def insert_test_snapshot(
    conn: sqlite3.Connection,
    repo_id: int,
    scanned_at: str,
    snapshot: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO test_snapshots (
          repo_id, scanned_at, detected, command, status, duration_seconds,
          summary, raw_tail, fingerprint
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            repo_id,
            scanned_at,
            int(bool(snapshot.get("detected"))),
            snapshot.get("command"),
            snapshot.get("status"),
            snapshot.get("duration_seconds"),
            snapshot.get("summary"),
            snapshot.get("raw_tail"),
            snapshot.get("fingerprint"),
        ),
    )


def insert_log_events(conn: sqlite3.Connection, events: list[dict[str, Any]]) -> None:
    for event in events:
        conn.execute(
            """
            INSERT OR IGNORE INTO log_events (
              source, source_path, event_time, observed_at, severity, category,
              message, raw_line, fingerprint
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["source"],
                event.get("source_path"),
                event.get("event_time"),
                event["observed_at"],
                event.get("severity"),
                event.get("category"),
                event.get("message"),
                event.get("raw_line"),
                event["fingerprint"],
            ),
        )


def run_scan(config_path: str | Path | None = None) -> dict[str, Any]:
    config = load_config(config_path)
    ensure_state_dirs(config)
    sqlite_cfg = config.get("sqlite", {})
    conn = connect_db(
        config["_db_path"],
        busy_timeout_ms=int(sqlite_cfg.get("busy_timeout_ms", 5000)),
        journal_mode=str(sqlite_cfg.get("journal_mode", "WAL")),
    )
    init_db(conn)

    started_at = utc_now()
    scan_run = conn.execute(
        "INSERT INTO scan_runs (started_at, status, errors_json) VALUES (?, 'running', ?)",
        (started_at, json_dumps([])),
    ).lastrowid
    conn.commit()

    errors: list[str] = []
    repos_seen = 0
    repos_scanned = 0
    overall_timeout = float(config.get("scan", {}).get("overall_scan_timeout_seconds", 180))
    deadline = time.monotonic() + overall_timeout
    status = "complete"

    try:
        candidates, discovery_notes = discover_repos(config)
        errors.extend(discovery_notes)
        repos_seen = len(candidates)
        max_repos = int(config.get("scan", {}).get("max_repos_per_scan", 75))
        if len(candidates) > max_repos:
            candidates = candidates[:max_repos]
            errors.append(f"Scan capped after {max_repos} repos.")

        for metadata in candidates:
            if time.monotonic() > deadline:
                status = "capped"
                errors.append(f"Overall scan timeout hit after {int(overall_timeout)} seconds.")
                break
            scanned_at = utc_now()
            repo = upsert_repo(conn, metadata)
            try:
                snapshot = probe_repo(
                    metadata["path"],
                    timeout=int(config.get("scan", {}).get("git_command_timeout_seconds", 5)),
                    max_recent_commits=int(config.get("scan", {}).get("max_recent_commits", 8)),
                    max_changed_files_display=int(
                        config.get("scan", {}).get("max_changed_files_display", 80)
                    ),
                )
            except Exception as exc:
                # Defensive guard for unexpected probe errors.
                snapshot = {
                    "path": metadata["path"],
                    "name": metadata["name"],
                    "scan_error": f"probe_exception: {exc}",
                }
            insert_repo_snapshot(conn, int(repo["id"]), scanned_at, snapshot)
            if not snapshot.get("scan_error"):
                test_snapshot = build_test_snapshot(repo, snapshot, config)
                insert_test_snapshot(conn, int(repo["id"]), scanned_at, test_snapshot)
            repos_scanned += 1
            conn.commit()

        insert_log_events(conn, probe_configured_logs(config))
        interpret_all_repos(conn, config)
        conn.execute(
            """
            UPDATE scan_runs
            SET finished_at = ?, status = ?, repos_seen = ?, repos_scanned = ?, errors_json = ?
            WHERE id = ?
            """,
            (utc_now(), status, repos_seen, repos_scanned, json_dumps(errors), scan_run),
        )
        conn.commit()
        return {
            "status": status,
            "started_at": started_at,
            "finished_at": utc_now(),
            "repos_seen": repos_seen,
            "repos_scanned": repos_scanned,
            "errors": errors,
        }
    except Exception as exc:
        status = "error"
        errors.append(str(exc))
        conn.execute(
            """
            UPDATE scan_runs
            SET finished_at = ?, status = ?, repos_seen = ?, repos_scanned = ?, errors_json = ?
            WHERE id = ?
            """,
            (utc_now(), status, repos_seen, repos_scanned, json_dumps(errors), scan_run),
        )
        conn.commit()
        raise
    finally:
        conn.close()
