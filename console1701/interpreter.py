from __future__ import annotations

import sqlite3
from typing import Any

from console1701.db import json_dumps, latest_repo_snapshot, latest_test_snapshot, utc_now
from console1701.rules import evaluate_repo


def insert_interpretation(conn: sqlite3.Connection, state: dict[str, Any]) -> int:
    now = utc_now()
    cursor = conn.execute(
        """
        INSERT INTO interpreted_states (
          repo_id, scope, state, severity, headline, meaning, why_it_matters,
          next_sane_action, evidence_json, rule_ids_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            state.get("repo_id"),
            state["scope"],
            state["state"],
            state["severity"],
            state["headline"],
            state["meaning"],
            state["why_it_matters"],
            state["next_sane_action"],
            json_dumps(state["evidence"]),
            json_dumps(state["rule_ids"]),
            now,
        ),
    )
    return int(cursor.lastrowid)


def upsert_attention_item(conn: sqlite3.Connection, item: dict[str, Any]) -> int:
    now = utc_now()
    existing = conn.execute(
        "SELECT id FROM attention_items WHERE fingerprint = ?",
        (item["fingerprint"],),
    ).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE attention_items
            SET severity = ?, title = ?, body = ?, why_it_matters = ?,
                next_sane_action = ?, evidence_json = ?, status = 'open',
                last_seen = ?, resolved_at = NULL
            WHERE fingerprint = ?
            """,
            (
                item["severity"],
                item["title"],
                item["body"],
                item["why_it_matters"],
                item["next_sane_action"],
                json_dumps(item["evidence"]),
                now,
                item["fingerprint"],
            ),
        )
        return int(existing["id"])

    cursor = conn.execute(
        """
        INSERT INTO attention_items (
          fingerprint, repo_id, severity, title, body, why_it_matters,
          next_sane_action, evidence_json, status, first_seen, last_seen
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
        """,
        (
            item["fingerprint"],
            item.get("repo_id"),
            item["severity"],
            item["title"],
            item["body"],
            item["why_it_matters"],
            item["next_sane_action"],
            json_dumps(item["evidence"]),
            now,
            now,
        ),
    )
    return int(cursor.lastrowid)


def resolve_absent_attention(
    conn: sqlite3.Connection,
    repo_id: int,
    current_fingerprints: set[str],
) -> None:
    now = utc_now()
    rows = conn.execute(
        """
        SELECT fingerprint FROM attention_items
        WHERE repo_id = ? AND status = 'open'
        """,
        (repo_id,),
    ).fetchall()
    for row in rows:
        if row["fingerprint"] not in current_fingerprints:
            conn.execute(
                """
                UPDATE attention_items
                SET status = 'resolved', resolved_at = ?, last_seen = ?
                WHERE fingerprint = ?
                """,
                (now, now, row["fingerprint"]),
            )


def interpret_repo(
    conn: sqlite3.Connection,
    repo: dict[str, Any],
    config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scan_cfg = config.get("scan", {})
    snapshot = latest_repo_snapshot(conn, int(repo["id"]))
    test_snapshot = latest_test_snapshot(conn, int(repo["id"]))
    state, attention = evaluate_repo(
        repo,
        snapshot,
        test_snapshot,
        dirty_stale_hours=scan_cfg.get("dirty_stale_hours", 24),
        inactive_days_warning=scan_cfg.get("inactive_days_warning", 14),
        inactive_days_stale=scan_cfg.get("inactive_days_stale", 45),
    )
    insert_interpretation(conn, state)
    fingerprints: set[str] = set()
    for item in attention:
        upsert_attention_item(conn, item)
        fingerprints.add(item["fingerprint"])
    resolve_absent_attention(conn, int(repo["id"]), fingerprints)
    return state, attention


def interpret_all_repos(conn: sqlite3.Connection, config: dict[str, Any]) -> None:
    repos = conn.execute(
        "SELECT * FROM repos WHERE enabled = 1 ORDER BY name COLLATE NOCASE"
    ).fetchall()
    for row in repos:
        interpret_repo(conn, dict(row), config)
    conn.commit()
