from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from console1701.config import NEWS_SCOPES, iter_news_sources
from console1701.db import json_loads
from console1701.news.source_policy import evaluate_source_policy


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


def _decode_news_item_row(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["tags"] = json_loads(item.pop("tags_json"), [])
    item["evidence"] = json_loads(item.pop("evidence_json"), {})
    return item


def _decode_news_cluster_row(row: sqlite3.Row) -> dict[str, Any]:
    cluster = dict(row)
    cluster["tags"] = json_loads(cluster.pop("tags_json"), [])
    cluster["evidence"] = json_loads(cluster.pop("evidence_json"), {})
    return cluster


def _decode_news_health_row(row: sqlite3.Row) -> dict[str, Any]:
    health = dict(row)
    health["evidence"] = json_loads(health.pop("evidence_json"), {})
    return health


def _latest_fetch_runs_by_source(conn: sqlite3.Connection) -> dict[int, dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT r.*
        FROM news_fetch_runs r
        JOIN (
          SELECT source_id, MAX(id) AS latest_id
          FROM news_fetch_runs
          GROUP BY source_id
        ) latest ON latest.latest_id = r.id
        """
    ).fetchall()
    latest: dict[int, dict[str, Any]] = {}
    for row in rows:
        item = dict(row)
        item["evidence"] = json_loads(item.pop("evidence_json"), {})
        latest[int(item["source_id"])] = item
    return latest


def _latest_health_by_source(conn: sqlite3.Connection) -> dict[int, dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT h.*
        FROM news_source_health h
        JOIN (
          SELECT source_id, MAX(id) AS latest_id
          FROM news_source_health
          GROUP BY source_id
        ) latest ON latest.latest_id = h.id
        """
    ).fetchall()
    return {
        int(row["source_id"]): _decode_news_health_row(row)
        for row in rows
    }


def _is_stale_health(health: dict[str, Any] | None) -> bool:
    if not health or not health.get("stale_after"):
        return False
    try:
        stale_after = datetime.fromisoformat(str(health["stale_after"]))
    except ValueError:
        return False
    return stale_after.astimezone(UTC) < datetime.now(UTC)


def _read_setting(conn: sqlite3.Connection, key: str, default: Any = None) -> Any:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    return json_loads(str(row["value"]), default)


def _next_eligible_at(
    config: dict[str, Any],
    source: dict[str, Any],
    latest_fetch_run: dict[str, Any] | None,
) -> str | None:
    fetch_policy = (config.get("news") or {}).get("fetch_policy") or {}
    interval_minutes = int(
        source.get("interval_minutes") or fetch_policy.get("default_interval_minutes") or 0
    )
    if interval_minutes <= 0:
        return None
    last_finished = (
        (latest_fetch_run or {}).get("finished_at")
        or (latest_fetch_run or {}).get("started_at")
    )
    if not last_finished:
        return None
    try:
        timestamp = datetime.fromisoformat(str(last_finished))
    except ValueError:
        return None
    return (timestamp + timedelta(minutes=interval_minutes)).isoformat(timespec="seconds")


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
        elif any(value not in {"healthy", "stale"} for value in health_states):
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
    latest_health = _latest_health_by_source(conn)
    stale_source_count = sum(1 for health in latest_health.values() if _is_stale_health(health))
    latest_success = conn.execute(
        """
        SELECT MAX(finished_at) AS latest_success
        FROM news_fetch_runs
        WHERE status = 'success'
        """
    ).fetchone()
    latest_run = conn.execute(
        """
        SELECT MAX(finished_at) AS latest_finished
        FROM news_fetch_runs
        WHERE finished_at IS NOT NULL
        """
    ).fetchone()
    last_successful_ingest_at = (
        str(latest_success["latest_success"])
        if latest_success and latest_success["latest_success"]
        else None
    )
    last_finished_ingest_at = (
        str(latest_run["latest_finished"])
        if latest_run and latest_run["latest_finished"]
        else None
    )
    last_purge = _read_setting(conn, "news.last_purge", {})
    db_path_row = conn.execute("PRAGMA database_list").fetchone()
    db_path = Path(str(db_path_row["file"])) if db_path_row and db_path_row["file"] else None
    db_size_bytes = db_path.stat().st_size if db_path and db_path.exists() else None
    return {
        "enabled": bool((config.get("news") or {}).get("enabled")),
        "configured_source_count": len(iter_news_sources(config)),
        "stored_source_count": _count(conn, "news_sources"),
        "active_item_count": _count(conn, "news_items", "WHERE status = 'active'"),
        "fetch_run_count": _count(conn, "news_fetch_runs"),
        "source_health_count": _count(conn, "news_source_health"),
        "stale_source_count": stale_source_count,
        "last_successful_ingest_at": last_successful_ingest_at,
        "last_finished_ingest_at": last_finished_ingest_at,
        "last_purge": last_purge,
        "db_size_bytes": db_size_bytes,
        "scope_states": scope_states,
    }


def get_news_sources_status(
    conn: sqlite3.Connection,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    stored_by_key = {source["source_key"]: source for source in list_news_sources(conn)}
    latest_fetch = _latest_fetch_runs_by_source(conn)
    latest_health = _latest_health_by_source(conn)
    statuses: list[dict[str, Any]] = []

    for source in iter_news_sources(config):
        policy = evaluate_source_policy(config, source)
        stored = stored_by_key.get(source["id"])
        stored_id = int(stored["id"]) if stored else None
        fetch = latest_fetch.get(stored_id) if stored_id is not None else None
        health = latest_health.get(stored_id) if stored_id is not None else None
        stale = _is_stale_health(health)
        statuses.append(
            {
                "source_key": source["id"],
                "scope": source["scope"],
                "name": source["name"],
                "kind": source["kind"],
                "url": source.get("url"),
                "homepage_url": source.get("homepage_url"),
                "enabled": bool(source.get("enabled")),
                "priority": int(source.get("priority", 50)),
                "tags": source.get("tags") or [],
                "policy": policy,
                "stored": stored,
                "latest_fetch_run": fetch,
                "latest_health": health,
                "health_state": "stale" if stale else (health.get("state") if health else None),
                "last_success_at": health.get("last_success_at") if health else None,
                "last_failure_at": health.get("last_failure_at") if health else None,
                "next_eligible_at": _next_eligible_at(config, source, fetch),
                "item_count": _count(
                    conn,
                    "news_items",
                    "WHERE source_id = ? AND status = 'active'",
                    (stored_id,),
                )
                if stored_id is not None
                else 0,
            }
        )

    statuses.sort(
        key=lambda item: (
            str(item["scope"]),
            0 if item["enabled"] else 1,
            -int(item["priority"]),
            str(item["source_key"]),
        )
    )
    return statuses


def get_news_scope_view(
    conn: sqlite3.Connection,
    config: dict[str, Any],
    scope: str,
    *,
    item_limit: int = 8,
    cluster_limit: int = 5,
    source_limit: int = 6,
) -> dict[str, Any]:
    normalized_scope = str(scope).upper()
    scope_state = get_news_scope_states(conn, config)[normalized_scope]
    items = conn.execute(
        """
        SELECT *
        FROM news_items
        WHERE scope = ? AND status = 'active'
        ORDER BY rank_score DESC, last_seen_at DESC, id DESC
        LIMIT ?
        """,
        (normalized_scope, item_limit),
    ).fetchall()
    clusters = conn.execute(
        """
        SELECT *
        FROM news_clusters
        WHERE scope = ?
        ORDER BY score DESC, last_seen_at DESC, id DESC
        LIMIT ?
        """,
        (normalized_scope, cluster_limit),
    ).fetchall()
    sources = [
        source
        for source in get_news_sources_status(conn, config)
        if source["scope"] == normalized_scope
    ][:source_limit]
    return {
        "scope": normalized_scope,
        "state": scope_state,
        "items": [_decode_news_item_row(row) for row in items],
        "clusters": [_decode_news_cluster_row(row) for row in clusters],
        "sources": sources,
    }


def get_news_overview(
    conn: sqlite3.Connection,
    config: dict[str, Any],
) -> dict[str, Any]:
    summary = get_news_storage_summary(conn, config)
    scope_views = {
        scope: get_news_scope_view(
            conn,
            config,
            scope,
            item_limit=3,
            cluster_limit=2,
            source_limit=3,
        )
        for scope in NEWS_SCOPES
    }
    sources = get_news_sources_status(conn, config)
    failing_sources = [
        source
        for source in sources
        if source.get("health_state") and source["health_state"] not in {"healthy", "stale"}
    ]
    disabled_sources = [source for source in sources if not source["enabled"]]
    return {
        "summary": summary,
        "scope_views": scope_views,
        "sources": sources,
        "failing_sources": failing_sources,
        "disabled_sources": disabled_sources,
    }


def get_news_item_detail(conn: sqlite3.Connection, item_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT *
        FROM news_items
        WHERE id = ?
        """,
        (item_id,),
    ).fetchone()
    if row is None:
        return None
    return _decode_news_item_row(row)
