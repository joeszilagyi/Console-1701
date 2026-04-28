from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from console1706.db import (
    json_loads,
    latest_interpretation,
    latest_repo_snapshot,
    latest_test_snapshot,
    row_to_dict,
)
from console1706.rules import SEVERITY_RANK, worst_severity


def _decode_interpretation(row: sqlite3.Row | None) -> dict[str, Any] | None:
    data = row_to_dict(row)
    if not data:
        return None
    data["evidence"] = json_loads(data.pop("evidence_json"), {})
    data["rule_ids"] = json_loads(data.pop("rule_ids_json"), [])
    return data


def _decode_attention(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["evidence"] = json_loads(data.pop("evidence_json"), {})
    return data


def _decode_scan(row: sqlite3.Row | None) -> dict[str, Any] | None:
    data = row_to_dict(row)
    if data:
        data["errors"] = json_loads(data.pop("errors_json"), [])
    return data


def get_repo_cards(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM repos WHERE enabled = 1 ORDER BY name COLLATE NOCASE"
    ).fetchall()
    cards: list[dict[str, Any]] = []
    for row in rows:
        repo = dict(row)
        snapshot = latest_repo_snapshot(conn, int(repo["id"]))
        test = latest_test_snapshot(conn, int(repo["id"]))
        interpretation = latest_interpretation(conn, int(repo["id"]))
        attention_count = conn.execute(
            """
            SELECT COUNT(*) AS count FROM attention_items
            WHERE repo_id = ? AND status = 'open'
            """,
            (repo["id"],),
        ).fetchone()["count"]
        cards.append(
            {
                "repo": repo,
                "snapshot": snapshot,
                "test": test,
                "interpretation": interpretation,
                "attention_count": attention_count,
            }
        )
    return cards


def get_repo_detail(conn: sqlite3.Connection, repo_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM repos WHERE id = ?", (repo_id,)).fetchone()
    if not row:
        return None
    repo = dict(row)
    return {
        "repo": repo,
        "snapshot": latest_repo_snapshot(conn, repo_id),
        "test": latest_test_snapshot(conn, repo_id),
        "interpretation": latest_interpretation(conn, repo_id),
        "attention": get_attention_items(conn, repo_id=repo_id),
    }


def get_attention_items(
    conn: sqlite3.Connection,
    *,
    repo_id: int | None = None,
    include_resolved: bool = False,
) -> list[dict[str, Any]]:
    clauses = []
    params: list[Any] = []
    if repo_id is not None:
        clauses.append("repo_id = ?")
        params.append(repo_id)
    if not include_resolved:
        clauses.append("status = 'open'")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT * FROM attention_items
        {where}
        ORDER BY
          CASE severity
            WHEN 'red' THEN 4
            WHEN 'orange' THEN 3
            WHEN 'yellow' THEN 2
            WHEN 'blue' THEN 1
            ELSE 0
          END DESC,
          last_seen DESC
        LIMIT 100
        """,
        params,
    ).fetchall()
    return [_decode_attention(row) for row in rows]


def get_recent_events(conn: sqlite3.Connection, limit: int = 50) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    attention_rows = conn.execute(
        """
        SELECT a.*, r.name AS repo_name
        FROM attention_items a
        LEFT JOIN repos r ON r.id = a.repo_id
        WHERE a.status = 'open'
        ORDER BY a.last_seen DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    for row in attention_rows:
        events.append(
            {
                "time": row["last_seen"],
                "source": row["repo_name"] or "console",
                "severity": row["severity"],
                "category": "ATTENTION",
                "message": row["title"],
            }
        )

    log_rows = conn.execute(
        """
        SELECT * FROM log_events
        WHERE category NOT IN ('UNKNOWN')
        ORDER BY COALESCE(event_time, observed_at) DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    for row in log_rows:
        events.append(
            {
                "time": row["event_time"] or row["observed_at"],
                "source": row["source"],
                "severity": row["severity"],
                "category": row["category"],
                "message": row["message"],
            }
        )

    events.sort(key=lambda event: event.get("time") or "", reverse=True)
    return events[:limit]


def get_handoffs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT h.*, r.name AS repo_name, r.path AS repo_path
        FROM handoff_packets h
        LEFT JOIN repos r ON r.id = h.repo_id
        ORDER BY h.created_at DESC, h.id DESC
        LIMIT 100
        """
    ).fetchall()
    handoffs = []
    for row in rows:
        data = dict(row)
        data["evidence"] = json_loads(data.pop("evidence_json"), {})
        handoffs.append(data)
    return handoffs


def get_interpretation_evidence(
    conn: sqlite3.Connection,
    interpretation_id: int,
) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT i.*, r.name AS repo_name, r.path AS repo_path
        FROM interpreted_states i
        LEFT JOIN repos r ON r.id = i.repo_id
        WHERE i.id = ?
        """,
        (interpretation_id,),
    ).fetchone()
    return _decode_interpretation(row)


def get_latest_scan(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT * FROM scan_runs
        ORDER BY started_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    return _decode_scan(row)


def get_system_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    latest_scan = get_latest_scan(conn)
    cards = get_repo_cards(conn)
    attention = get_attention_items(conn)
    severities = []
    for item in attention:
        severities.append(item["severity"])
    for card in cards:
        if card["interpretation"]:
            severities.append(card["interpretation"]["severity"])
    worst = worst_severity(severities, default="gray" if not cards else "green")

    if worst == "red":
        system_state = "BROKEN"
    elif worst in {"orange", "yellow"}:
        system_state = "CAUTION"
    elif any(
        card["interpretation"] and card["interpretation"]["severity"] == "blue"
        for card in cards
    ):
        system_state = "WORKING"
    elif not cards:
        system_state = "UNKNOWN"
    elif worst == "gray":
        system_state = "IDLE"
    else:
        system_state = "OK"

    primary_attention = attention[0] if attention else None
    active_area = "unknown"
    latest_state = None
    for card in cards:
        interp = card.get("interpretation")
        if not interp:
            continue
        if latest_state is None or interp["created_at"] > latest_state["created_at"]:
            latest_state = interp
        clusters = (interp.get("evidence") or {}).get("path_clusters") or {}
        if clusters.get("primary_area") and clusters.get("primary_area") != "none":
            active_area = clusters["primary_area"]
            break

    if primary_attention:
        last_event = primary_attention["title"]
        next_action = primary_attention["next_sane_action"]
    elif latest_state:
        last_event = latest_state["headline"]
        next_action = latest_state["next_sane_action"]
    else:
        last_event = "No scan has run yet." if not latest_scan else "No meaningful events found."
        next_action = (
            "Run: console-1706 scan" if not latest_scan else "Add repos to config if needed."
        )

    return {
        "system_state": system_state,
        "human_attention": bool(attention),
        "active_area": active_area,
        "last_scan": latest_scan,
        "last_meaningful_event": last_event,
        "next_sane_action": next_action,
        "repo_count": len(cards),
        "attention_count": len(attention),
        "severity_rank": SEVERITY_RANK.get(worst, 0),
        "db_path": str(Path(conn.execute("PRAGMA database_list").fetchone()["file"])),
    }
