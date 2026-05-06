from __future__ import annotations

import sqlite3
from typing import Any

from console1701.config import NEWS_SCOPES, iter_news_sources
from console1701.db import json_loads


def _count(
    conn: sqlite3.Connection,
    table: str,
    where: str = "",
    params: tuple[Any, ...] = (),
) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table} {where}", params).fetchone()
    return int(row["count"] if row else 0)


def _latest_health_states(conn: sqlite3.Connection, scope: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT h.state
        FROM news_source_health h
        JOIN news_sources s ON s.id = h.source_id
        JOIN (
          SELECT source_id, MAX(id) AS latest_id
          FROM news_source_health
          GROUP BY source_id
        ) latest ON latest.latest_id = h.id
        WHERE s.scope = ?
        """,
        (scope,),
    ).fetchall()
    return [str(row["state"]) for row in rows]


def list_news_sources(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM news_sources
        ORDER BY scope, enabled DESC, priority DESC, source_key
        """
    ).fetchall()
    sources: list[dict[str, Any]] = []
    for row in rows:
        source = dict(row)
        source["tags"] = json_loads(source.pop("tags_json"), [])
        source["policy"] = json_loads(source.pop("policy_json"), {})
        sources.append(source)
    return sources


def get_news_scope_states(
    conn: sqlite3.Connection,
    config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return honest per-scope recent-signal states without fetching anything."""

    news_cfg = config.get("news") or {}
    configured_sources = iter_news_sources(config)
    configured_by_scope: dict[str, list[dict[str, Any]]] = {scope: [] for scope in NEWS_SCOPES}
    for source in configured_sources:
        configured_by_scope.setdefault(str(source.get("scope")), []).append(source)

    states: dict[str, dict[str, Any]] = {}
    for scope in NEWS_SCOPES:
        scope_cfg = ((news_cfg.get("scopes") or {}).get(scope)) or {}
        sources = configured_by_scope.get(scope, [])
        enabled_sources = [source for source in sources if source.get("enabled")]
        db_sources = _count(conn, "news_sources", "WHERE scope = ?", (scope,))
        db_enabled_sources = _count(
            conn,
            "news_sources",
            "WHERE scope = ? AND enabled = 1",
            (scope,),
        )
        active_items = _count(
            conn,
            "news_items",
            "WHERE scope = ? AND status = 'active'",
            (scope,),
        )
        health_states = _latest_health_states(conn, scope)

        if not news_cfg.get("enabled"):
            state = "disabled"
            message = "External news ingest is disabled by config."
        elif not sources:
            state = "not_configured"
            message = f"No {scope} sources are configured."
        elif not enabled_sources:
            state = "configured_disabled"
            message = f"{scope} sources are configured but disabled."
        elif not health_states and (db_sources == 0 or db_enabled_sources == 0):
            state = "configured_never_run"
            message = f"{scope} sources are enabled but have not been ingested yet."
        elif any(
            value in {"failing", "parser_failed", "blocked_policy"}
            for value in health_states
        ):
            state = "failing"
            message = f"{scope} has failing or policy-blocked sources."
        elif "stale" in health_states:
            state = "stale"
            message = f"{scope} source health is stale."
        elif health_states and all(value == "healthy" for value in health_states):
            state = "healthy"
            message = f"{scope} sources are healthy."
        else:
            state = "configured_never_run"
            message = f"{scope} source health has not produced a stable state yet."

        states[scope] = {
            "scope": scope,
            "label": scope_cfg.get("label") or scope,
            "state": state,
            "message": message,
            "configured_source_count": len(sources),
            "enabled_source_count": len(enabled_sources),
            "stored_source_count": db_sources,
            "stored_enabled_source_count": db_enabled_sources,
            "active_item_count": active_items,
            "latest_health_states": health_states,
        }

    return states


def get_news_storage_summary(conn: sqlite3.Connection, config: dict[str, Any]) -> dict[str, Any]:
    scope_states = get_news_scope_states(conn, config)
    return {
        "enabled": bool((config.get("news") or {}).get("enabled")),
        "configured_source_count": len(iter_news_sources(config)),
        "stored_source_count": _count(conn, "news_sources"),
        "active_item_count": _count(conn, "news_items", "WHERE status = 'active'"),
        "fetch_run_count": _count(conn, "news_fetch_runs"),
        "source_health_count": _count(conn, "news_source_health"),
        "scope_states": scope_states,
    }
