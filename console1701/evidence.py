from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from console1701.db import (
    json_loads,
    latest_interpretation,
    latest_repo_snapshot,
    latest_test_snapshot,
    row_to_dict,
)
from console1701.rules import SEVERITY_RANK, worst_severity

_TIMESTAMP_PREFIX = re.compile(
    r"^\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))\s+(.*)$"
)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _format_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    parsed = _parse_timestamp(value)
    if not parsed:
        return value
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone()
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _repo_activity_time(card: dict[str, Any]) -> datetime | None:
    snapshot = card.get("snapshot") or {}
    if snapshot.get("scan_error") in {"missing_path", "not_git_repo", "git_timeout"}:
        return None

    if snapshot.get("is_dirty"):
        scanned_at = _parse_timestamp(snapshot.get("scanned_at"))
        dirty_age_hours = ((snapshot.get("path_clusters") or {}).get("dirty_age_hours"))
        if scanned_at and dirty_age_hours is not None:
            try:
                return scanned_at - timedelta(hours=float(dirty_age_hours))
            except (TypeError, ValueError):
                pass

    return _parse_timestamp(snapshot.get("commit_time"))


def _repo_activity_sort_value(card: dict[str, Any]) -> float:
    activity_time = _repo_activity_time(card)
    if not activity_time:
        return float("-inf")
    return activity_time.timestamp()


def _split_prefixed_timestamp(message: str) -> tuple[str | None, str]:
    match = _TIMESTAMP_PREFIX.match(message)
    if not match:
        return None, " ".join(message.split())
    return match.group(1), " ".join(match.group(2).split())


def _summarize_codex_message(message: str, category: str) -> str | None:
    _timestamp, stripped = _split_prefixed_timestamp(message)

    tool_match = re.search(r"ToolCall:\s*([A-Za-z0-9_.-]+)", stripped)
    if tool_match:
        return f"Tool call: {tool_match.group(1)}"

    if "Shutting down Codex instance" in stripped:
        return "Session shutdown"
    if "failed to record rollout items" in stripped:
        return "Error: failed to record rollout items"
    if "ignoring interface.defaultPrompt" in stripped:
        return "Plugin manifest warning: ignoring interface.defaultPrompt"
    if "maximum of 3 prompts is supported" in stripped:
        return "Plugin manifest warning: maximum of 3 prompts is supported"

    error_match = re.search(r"\bERROR\b.*?:\s*(.*)", stripped)
    if error_match:
        detail = error_match.group(1).split(" path=", 1)[0].strip()
        return f"Error: {detail}" if detail else "Codex error"

    warn_match = re.search(r"\bWARN\b.*?:\s*(.*)", stripped)
    if warn_match:
        detail = warn_match.group(1).split(" path=", 1)[0].strip()
        return f"Warning: {detail}" if detail else "Codex warning"

    low_signal_markers = (
        "submission_dispatch",
        "session_task.turn",
        "model_client.stream_responses_websocket",
        "model_client.websocket_connection",
        "codex_core::client: new",
        "codex_core::client: close",
        "codex_core::session: new",
        "codex_core::session: close",
        "codex_core::session::handlers: new",
        "codex_core::session::handlers: close",
        "thread_spawn",
        "codex_core::tasks: close",
        "codex_core::shell_snapshot:",
        "session_init.",
    )
    if any(marker in stripped for marker in low_signal_markers):
        return None

    if category == "CODEX_RUN":
        return "Codex activity"
    return stripped[:160]


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


def _decode_host_snapshot(row: sqlite3.Row | None) -> dict[str, Any] | None:
    data = row_to_dict(row)
    if not data:
        return None
    data["summary"] = json_loads(data.pop("summary_json"), {})
    data["snapshot"] = json_loads(data.pop("snapshot_json"), {})
    data["evidence"] = json_loads(data.pop("evidence_json"), {})
    data["errors"] = json_loads(data.pop("errors_json"), [])
    return data


def _safe_percent(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _host_changes(
    latest: dict[str, Any] | None,
    previous: dict[str, Any] | None,
) -> list[str]:
    if not latest:
        return ["No host snapshot has been recorded yet."]
    if not previous:
        return ["No previous host snapshot to compare yet."]

    latest_snapshot = latest.get("snapshot") or {}
    previous_snapshot = previous.get("snapshot") or {}
    changes: list[str] = []
    if latest.get("health_state") != previous.get("health_state"):
        changes.append(
            "Health changed from "
            f"{previous.get('health_state') or 'UNKNOWN'} to {latest.get('health_state')}."
        )

    latest_root = ((latest_snapshot.get("storage") or {}).get("root") or {}).get("use_percent")
    previous_root = ((previous_snapshot.get("storage") or {}).get("root") or {}).get(
        "use_percent"
    )
    latest_root_percent = _safe_percent(latest_root)
    previous_root_percent = _safe_percent(previous_root)
    if latest_root_percent is not None and previous_root_percent is not None:
        delta = latest_root_percent - previous_root_percent
        if abs(delta) >= 1:
            changes.append(f"Root filesystem usage changed by {delta:+.1f} percentage points.")

    latest_services = latest_snapshot.get("services") or {}
    previous_services = previous_snapshot.get("services") or {}
    latest_failed = int(latest_services.get("failed_system_count") or 0) + int(
        latest_services.get("failed_user_count") or 0
    )
    previous_failed = int(previous_services.get("failed_system_count") or 0) + int(
        previous_services.get("failed_user_count") or 0
    )
    if latest_failed != previous_failed:
        changes.append(f"Failed service count changed from {previous_failed} to {latest_failed}.")

    latest_route = bool((latest_snapshot.get("network") or {}).get("default_route"))
    previous_route = bool((previous_snapshot.get("network") or {}).get("default_route"))
    if latest_route != previous_route:
        changes.append("Default route appeared." if latest_route else "Default route disappeared.")

    latest_kernel = (latest_snapshot.get("kernel") or {}).get("release")
    previous_kernel = (previous_snapshot.get("kernel") or {}).get("release")
    if latest_kernel and previous_kernel and latest_kernel != previous_kernel:
        changes.append(f"Kernel changed from {previous_kernel} to {latest_kernel}.")

    return changes or ["No material host changes since the previous scan."]


def get_latest_host_snapshot(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT * FROM host_snapshots
        ORDER BY scanned_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    return _decode_host_snapshot(row)


def get_host_history(conn: sqlite3.Connection, limit: int = 20) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, scanned_at, hostname, os_pretty_name, kernel_release, uptime_seconds,
               health_state, health_score, summary_json
        FROM host_snapshots
        ORDER BY scanned_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    history = []
    for row in rows:
        data = dict(row)
        data["summary"] = json_loads(data.pop("summary_json"), {})
        data["scanned_at_display"] = _format_timestamp(data.get("scanned_at"))
        history.append(data)
    return history


def get_host_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    latest = get_latest_host_snapshot(conn)
    if not latest:
        return {
            "state": "UNKNOWN",
            "score": None,
            "severity": "gray",
            "headline": "No host scan has run yet.",
            "summary": "Run a scan to collect local Debian host evidence.",
            "next_sane_action": "Run: console-1701 scan",
            "penalties": [],
            "checks": {},
            "changes": ["No host snapshot has been recorded yet."],
            "last_scan_display": None,
        }

    previous_rows = conn.execute(
        """
        SELECT * FROM host_snapshots
        WHERE id != ?
        ORDER BY scanned_at DESC, id DESC
        LIMIT 1
        """,
        (latest["id"],),
    ).fetchone()
    previous = _decode_host_snapshot(previous_rows)
    summary = dict(latest.get("summary") or {})
    summary.setdefault("state", latest.get("health_state") or "UNKNOWN")
    summary.setdefault("score", latest.get("health_score"))
    summary.setdefault("severity", "gray")
    summary["hostname"] = latest.get("hostname")
    summary["os_pretty_name"] = latest.get("os_pretty_name")
    summary["kernel_release"] = latest.get("kernel_release")
    summary["uptime_seconds"] = latest.get("uptime_seconds")
    summary["last_scan"] = latest.get("scanned_at")
    summary["last_scan_display"] = _format_timestamp(latest.get("scanned_at"))
    summary["changes"] = _host_changes(latest, previous)
    return summary


def get_repo_cards(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM repos WHERE enabled = 1").fetchall()
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
    cards.sort(key=lambda card: str(card["repo"].get("name") or "").lower())
    cards.sort(
        key=_repo_activity_sort_value,
        reverse=True,
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
        (limit * 2,),
    ).fetchall()
    for row in attention_rows:
        raw_time = row["last_seen"]
        events.append(
            {
                "_sort_time": raw_time or "",
                "time": _format_timestamp(raw_time) or raw_time,
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
        (limit * 6,),
    ).fetchall()
    for row in log_rows:
        embedded_time, cleaned_message = _split_prefixed_timestamp(row["message"])
        raw_time = row["event_time"] or embedded_time or row["observed_at"]
        message = cleaned_message
        if row["source"] == "codex":
            message = _summarize_codex_message(row["message"], row["category"])
            if not message:
                continue
        events.append(
            {
                "_sort_time": raw_time or "",
                "time": _format_timestamp(raw_time) or raw_time,
                "source": row["source"],
                "severity": row["severity"],
                "category": row["category"],
                "message": message,
            }
        )

    events.sort(key=lambda event: event.get("_sort_time") or "", reverse=True)
    for event in events:
        event.pop("_sort_time", None)
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
            "Run: console-1701 scan" if not latest_scan else "Add repos to config if needed."
        )

    return {
        "system_state": system_state,
        "human_attention": bool(attention),
        "active_area": active_area,
        "last_scan": latest_scan,
        "last_scan_display": _format_timestamp(
            (latest_scan or {}).get("finished_at") or (latest_scan or {}).get("started_at")
        ),
        "last_meaningful_event": last_event,
        "next_sane_action": next_action,
        "repo_count": len(cards),
        "attention_count": len(attention),
        "severity_rank": SEVERITY_RANK.get(worst, 0),
        "db_path": str(Path(conn.execute("PRAGMA database_list").fetchone()["file"])),
    }
