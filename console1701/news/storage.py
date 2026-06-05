from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from console1701.config import NEWS_SCOPES, iter_news_sources
from console1701.db import json_loads
from console1701.news.local_registry import local_source_registry_summary
from console1701.news.source_policy import evaluate_source_policy

SOURCE_HEALTH_STATE_ALIASES = {
    "blocked_policy": "policy_blocked",
    "payload_too_large": "failing",
    "failed": "failing",
}

SOURCE_HEALTH_STATE_MESSAGES = {
    "disabled": "Source is disabled in config.",
    "configured_never_run": "Source is enabled but has not completed ingest yet.",
    "healthy": "Source completed ingest successfully.",
    "stale": "Source health is older than the allowed freshness window.",
    "failing": "Source ingest is failing without a parser- or policy-specific state.",
    "parser_failed": "Source fixture could not be parsed.",
    "policy_blocked": "Source is blocked by the current ingest policy.",
    "auth_required": "Source declares auth but no credential material is configured.",
    "social_disabled": (
        "LOCAL social source is blocked until local.allow_social_sources is enabled."
    ),
    "homepage_disabled": "Homepage extraction is disabled by config.",
    "manual_review_only": "Source is gated for manual review in this phase.",
    "unsupported": "Source is configured in an unsupported way for this phase.",
}


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


def _normalize_source_health_state(raw_state: str | None) -> str | None:
    if not raw_state:
        return None
    normalized = str(raw_state).strip().lower()
    return SOURCE_HEALTH_STATE_ALIASES.get(normalized, normalized)


def _base_source_state(
    policy: dict[str, Any],
    source_enabled: bool,
    source_url: str | None,
    source_adapter: str | None = None,
) -> tuple[str, str]:
    if not source_enabled:
        return "disabled", SOURCE_HEALTH_STATE_MESSAGES["disabled"]
    if policy.get("auth_required") and not policy.get("auth_configured"):
        return "auth_required", SOURCE_HEALTH_STATE_MESSAGES["auth_required"]
    if policy.get("social_source_blocked"):
        return "social_disabled", SOURCE_HEALTH_STATE_MESSAGES["social_disabled"]
    if policy.get("homepage_extractor_blocked"):
        return "homepage_disabled", SOURCE_HEALTH_STATE_MESSAGES["homepage_disabled"]
    if policy.get("uses_homepage_extractor") and not policy.get("homepage_extractor_allowed"):
        return "manual_review_only", SOURCE_HEALTH_STATE_MESSAGES["manual_review_only"]
    if str(source_adapter or "").strip().lower() == "manual_review_only":
        return "manual_review_only", SOURCE_HEALTH_STATE_MESSAGES["manual_review_only"]
    if source_url and not policy.get("scope_enabled"):
        return "policy_blocked", SOURCE_HEALTH_STATE_MESSAGES["policy_blocked"]
    if source_url and policy.get("policy_state") == "blocked_fixture_phase":
        return "policy_blocked", SOURCE_HEALTH_STATE_MESSAGES["policy_blocked"]
    return "configured_never_run", SOURCE_HEALTH_STATE_MESSAGES["configured_never_run"]


def _resolve_source_state(
    *,
    source_enabled: bool,
    source_url: str | None,
    policy: dict[str, Any],
    fetch: dict[str, Any] | None,
    health: dict[str, Any] | None,
    source_adapter: str | None,
    stale: bool,
) -> tuple[str, str]:
    base_state, base_message = _base_source_state(
        policy,
        source_enabled,
        source_url,
        source_adapter,
    )
    if base_state != "configured_never_run":
        return base_state, base_message
    if stale:
        return "stale", SOURCE_HEALTH_STATE_MESSAGES["stale"]
    raw_health_state = _normalize_source_health_state(health.get("state") if health else None)
    if raw_health_state:
        default_message = SOURCE_HEALTH_STATE_MESSAGES.get(raw_health_state)
        message = str((health or {}).get("message") or default_message)
        return raw_health_state, message
    raw_fetch_state = _normalize_source_health_state(fetch.get("status") if fetch else None)
    if raw_fetch_state and raw_fetch_state != "success":
        evidence = (fetch or {}).get("evidence") or {}
        detail = str((fetch or {}).get("error_message") or evidence.get("detail") or "").strip()
        message = detail or SOURCE_HEALTH_STATE_MESSAGES.get(raw_fetch_state, base_message)
        return raw_fetch_state, message
    return base_state, base_message


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


def _decode_local_event_row(row: sqlite3.Row) -> dict[str, Any]:
    event = dict(row)
    item_ids = [str(value) for value in json_loads(event.pop("item_ids_json"), [])]
    source_ids = [str(value) for value in json_loads(event.pop("source_ids_json"), [])]
    event["item_ids"] = item_ids
    event["source_ids"] = source_ids
    event["geography_tokens"] = json_loads(event.pop("geography_json"), [])
    event["neighborhoods"] = json_loads(event.pop("neighborhoods_json"), [])
    event["title_tokens"] = json_loads(event.pop("title_tokens_json"), [])
    event["families"] = json_loads(event.pop("families_json"), [])
    event["evidence"] = json_loads(event.pop("evidence_json"), {})
    event["ranking_explanation"] = json_loads(event.pop("ranking_explanation_json"), {})
    event["geography_basis"] = {
        "signature_tokens": event["geography_tokens"],
        "location_tokens": event["neighborhoods"],
        "title_tokens": event["title_tokens"],
    }
    match_contract = event["ranking_explanation"] or {}
    event["matching_contract"] = {
        "scope": str(event.get("scope") or ""),
        "event_type": str(event.get("event_type") or ""),
        "source_families": [value for value in event.get("families") if value],
        "match_threshold": int(match_contract.get("match_threshold", 20)),
        "match_window_hours": int(match_contract.get("match_window_hours", 3)),
        "confidence_basis": list(match_contract.get("confidence_basis", [])),
        "match_token_count": int(
            match_contract.get("match_token_count", len(event["geography_tokens"]))
        ),
        "location_token_count": int(
            match_contract.get("location_token_count", len(event["neighborhoods"]))
        ),
        "title_token_count": int(
            match_contract.get("title_token_count", len(event["title_tokens"]))
        ),
        "last_match_score": int(match_contract.get("last_match_score", 0)),
        "best_match_score": int(
            match_contract.get("best_match_score", match_contract.get("last_match_score", 0))
        ),
        "matched_count": int(match_contract.get("matched_count", 0)),
        "source_severity_score": int(match_contract.get("source_severity_score", 0)),
        "topic_repetition_score": int(match_contract.get("topic_repetition_score", 0)),
        "topic_repetition_tokens": list(match_contract.get("topic_repetition_tokens", [])),
    }
    event["item_count"] = len(item_ids)
    event["source_count"] = len(source_ids)
    return event


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


def _recent_fetch_runs_by_source(
    conn: sqlite3.Connection,
    *,
    limit_per_source: int = 3,
) -> dict[int, list[dict[str, Any]]]:
    rows = conn.execute(
        """
        SELECT *
        FROM news_fetch_runs
        ORDER BY source_id, id DESC
        """
    ).fetchall()
    history: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        source_id = int(row["source_id"])
        bucket = history.setdefault(source_id, [])
        if len(bucket) >= limit_per_source:
            continue
        item = dict(row)
        item["evidence"] = json_loads(item.pop("evidence_json"), {})
        bucket.append(item)
    return history


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
    return {int(row["source_id"]): _decode_news_health_row(row) for row in rows}


def _recent_health_by_source(
    conn: sqlite3.Connection,
    *,
    limit_per_source: int = 3,
) -> dict[int, list[dict[str, Any]]]:
    rows = conn.execute(
        """
        SELECT *
        FROM news_source_health
        ORDER BY source_id, id DESC
        """
    ).fetchall()
    history: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        source_id = int(row["source_id"])
        bucket = history.setdefault(source_id, [])
        if len(bucket) >= limit_per_source:
            continue
        bucket.append(_decode_news_health_row(row))
    return history


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
    last_finished = (latest_fetch_run or {}).get("finished_at") or (latest_fetch_run or {}).get(
        "started_at"
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
    source_statuses = get_news_sources_status(conn, config)
    source_statuses_by_scope: dict[str, list[dict[str, Any]]] = {scope: [] for scope in NEWS_SCOPES}
    for status in source_statuses:
        source_statuses_by_scope.setdefault(str(status["scope"]), []).append(status)
    for scope in NEWS_SCOPES:
        scope_cfg = ((news_cfg.get("scopes") or {}).get(scope)) or {}
        sources = configured_by_scope.get(scope, [])
        enabled_sources = [source for source in sources if source.get("enabled")]
        status_rows = source_statuses_by_scope.get(scope, [])
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
        health_states = [
            str(status["health_state"]) for status in status_rows if status.get("health_state")
        ]
        blocking_states = {
            "auth_required",
            "failing",
            "homepage_disabled",
            "manual_review_only",
            "parser_failed",
            "policy_blocked",
            "unsupported",
            "social_disabled",
        }

        if not news_cfg.get("enabled"):
            state = "disabled"
            message = "External news ingest is disabled by config."
        elif not sources:
            state = "not_configured"
            message = f"No {scope} sources are configured."
        elif not enabled_sources:
            state = "configured_disabled"
            message = f"{scope} sources are configured but disabled."
        elif health_states and all(value == "configured_never_run" for value in health_states):
            state = "configured_never_run"
            message = f"{scope} sources are enabled but have not been ingested yet."
        elif not health_states and (db_sources == 0 or db_enabled_sources == 0):
            state = "configured_never_run"
            message = f"{scope} sources are enabled but have not been ingested yet."
        elif any(value in blocking_states for value in health_states):
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
            "source_state_counts": _state_counts(status_rows),
        }

    return states


def get_news_storage_summary(conn: sqlite3.Connection, config: dict[str, Any]) -> dict[str, Any]:
    source_statuses = get_news_sources_status(conn, config)
    scope_states = get_news_scope_states(conn, config)
    config_warnings = get_news_config_warnings(config)
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
        str(latest_run["latest_finished"]) if latest_run and latest_run["latest_finished"] else None
    )
    last_purge = _read_setting(conn, "news.last_purge", {})
    last_scan_result = _read_setting(conn, "news.last_scan_result", {})
    db_path_row = conn.execute("PRAGMA database_list").fetchone()
    db_path = Path(str(db_path_row["file"])) if db_path_row and db_path_row["file"] else None
    db_size_bytes = db_path.stat().st_size if db_path and db_path.exists() else None
    source_state_counts = _state_counts(source_statuses)
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
        "last_scan_result": last_scan_result,
        "db_size_bytes": db_size_bytes,
        "config_warnings": config_warnings,
        "local_registry": get_local_registry_state(conn),
        "scope_states": scope_states,
        "source_state_counts": source_state_counts,
        "failing_source_count": int(
            source_state_counts.get("failing", 0) + source_state_counts.get("parser_failed", 0)
        ),
        "policy_blocked_source_count": int(source_state_counts.get("policy_blocked", 0)),
        "parser_failed_source_count": int(source_state_counts.get("parser_failed", 0)),
    }


def get_local_registry_state(conn: sqlite3.Connection) -> dict[str, Any]:
    try:
        rows = conn.execute(
            "SELECT * FROM news_source_registry WHERE scope = 'LOCAL'",
        ).fetchall()
    except sqlite3.OperationalError:
        return local_source_registry_summary()

    if not rows:
        return local_source_registry_summary()

    source_count = 0
    source_classes: dict[str, int] = {}
    future_phases: dict[str, int] = {}
    official_status_counts: dict[str, int] = {}
    verification_status_counts: dict[str, int] = {}

    for row in rows:
        source_count += 1
        source_classes[str(row["source_class"])] = (
            source_classes.get(str(row["source_class"]), 0) + 1
        )
        future_phases[str(row["future_phase"])] = future_phases.get(str(row["future_phase"]), 0) + 1
        official_status_counts[str(row["official_status"])] = (
            official_status_counts.get(str(row["official_status"]), 0) + 1
        )
        verification_status_counts[str(row["verification_status"])] = (
            verification_status_counts.get(str(row["verification_status"]), 0) + 1
        )

    return {
        "scope": "LOCAL",
        "enabled_by_default": bool(any(bool(int(row["enabled_by_default"])) for row in rows)),
        "source_count": source_count,
        "source_class_counts": source_classes,
        "future_phase_counts": future_phases,
        "official_status_counts": official_status_counts,
        "verification_status_counts": verification_status_counts,
    }


def get_news_sources_status(
    conn: sqlite3.Connection,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    stored_by_key = {source["source_key"]: source for source in list_news_sources(conn)}
    latest_fetch = _latest_fetch_runs_by_source(conn)
    recent_fetch = _recent_fetch_runs_by_source(conn)
    latest_health = _latest_health_by_source(conn)
    recent_health = _recent_health_by_source(conn)
    statuses: list[dict[str, Any]] = []

    for source in iter_news_sources(config):
        policy = evaluate_source_policy(config, source)
        stored = stored_by_key.get(source["id"])
        stored_id = int(stored["id"]) if stored else None
        fetch = latest_fetch.get(stored_id) if stored_id is not None else None
        health = latest_health.get(stored_id) if stored_id is not None else None
        stale = _is_stale_health(health)
        health_state, health_message = _resolve_source_state(
            source_enabled=bool(source.get("enabled")),
            source_url=str(source.get("url") or "").strip() or None,
            policy=policy,
            fetch=fetch,
            health=health,
            source_adapter=str(source.get("adapter") or source.get("parser") or "").strip() or None,
            stale=stale,
        )
        statuses.append(
            {
                "source_key": source["id"],
                "scope": source["scope"],
                "name": source["name"],
                "kind": source["kind"],
                "source_family": source.get("source_family"),
                "source_class": source.get("source_class"),
                "official_status": source.get("official_status"),
                "future_phase": source.get("future_phase"),
                "expected_access_kind": source.get("expected_access_kind"),
                "policy_risk": source.get("policy_risk"),
                "parser_risk": source.get("parser_risk"),
                "retention_sensitivity": source.get("retention_sensitivity"),
                "adapter": source.get("adapter") or source.get("parser"),
                "verification_status": source.get("verification_status"),
                "url": source.get("url"),
                "homepage_url": source.get("homepage_url"),
                "enabled": bool(source.get("enabled")),
                "priority": int(source.get("priority", 50)),
                "tags": source.get("tags") or [],
                "policy": policy,
                "stored": stored,
                "latest_fetch_run": fetch,
                "recent_fetch_runs": (
                    recent_fetch.get(stored_id, []) if stored_id is not None else []
                ),
                "latest_health": health,
                "recent_health_rows": (
                    recent_health.get(stored_id, []) if stored_id is not None else []
                ),
                "health_state": health_state,
                "health_message": health_message,
                "raw_health_state": health.get("state") if health else None,
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


def _state_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        state = str(row.get("health_state") or "").strip()
        if not state:
            continue
        counts[state] = counts.get(state, 0) + 1
    return counts


def get_news_config_warnings(config: dict[str, Any]) -> list[str]:
    news_cfg = config.get("news") or {}
    warnings: list[str] = []
    sources = iter_news_sources(config)
    enabled_sources = [source for source in sources if source.get("enabled")]

    if news_cfg.get("enabled") and not enabled_sources:
        warnings.append("News is enabled, but no sources are enabled.")

    for scope in NEWS_SCOPES:
        scope_cfg = ((news_cfg.get("scopes") or {}).get(scope)) or {}
        scope_sources = scope_cfg.get("sources") or []
        if scope_cfg.get("enabled") and not scope_sources:
            warnings.append(f"{scope} is enabled, but no sources are configured for it.")

    for source in sources:
        policy = evaluate_source_policy(config, source)
        source_key = str(source["id"])
        url = str(source.get("url") or "").strip()
        if source.get("enabled") and not url:
            warnings.append(f"{source_key} is enabled but has no URL configured.")
        elif source.get("enabled") and not url.startswith("file://"):
            warnings.append(
                f"{source_key} is enabled but blocked in the current fixture-only ingest phase."
            )
        if policy.get("auth_required") and not policy.get("auth_configured"):
            warnings.append(f"{source_key} declares auth, but no auth material is configured.")
        if source.get("enabled") and not (
            (((news_cfg.get("scopes") or {}).get(source.get("scope"))) or {}).get("enabled")
        ):
            warnings.append(
                f"{source_key} is enabled, but parent scope {source.get('scope')} is disabled."
            )

    return warnings


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


def get_news_local_event_detail(
    conn: sqlite3.Connection,
    event_id: int,
) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT *
        FROM local_events
        WHERE id = ?
        """,
        (event_id,),
    ).fetchone()
    if row is None:
        return None

    event = _decode_local_event_row(row)
    item_ids = [int(value) for value in event["item_ids"] if str(value).isdigit()]
    if item_ids:
        placeholders = ",".join(["?"] * len(item_ids))
        item_rows = conn.execute(
            f"""
            SELECT
              i.id,
              i.title,
              i.scope,
              i.url,
              i.last_seen_at,
              s.source_key,
              s.name AS source_name
            FROM news_items i
            JOIN news_sources s ON s.id = i.source_id
            WHERE i.id IN ({placeholders})
            """,
            item_ids,
        ).fetchall()
        id_to_item = {
            int(item["id"]): {
                "id": int(item["id"]),
                "title": str(item["title"]),
                "scope": str(item["scope"]),
                "url": str(item["url"]),
                "last_seen_at": str(item["last_seen_at"]),
                "source_key": str(item["source_key"]),
                "source_name": str(item["source_name"]),
            }
            for item in item_rows
        }
        event["items"] = [
            id_to_item[identifier] for identifier in item_ids if identifier in id_to_item
        ]
    else:
        event["items"] = []

    return event


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


def get_news_item_detail(
    conn: sqlite3.Connection,
    item_id: int,
) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT
          i.*,
          s.source_key,
          s.name AS source_name,
          s.priority AS source_priority,
          s.enabled AS source_enabled,
          s.url AS source_url,
          s.tags_json AS source_tags_json,
          s.policy_json AS source_policy_json
        FROM news_items
        i
        JOIN news_sources s ON s.id = i.source_id
        WHERE i.id = ?
        """,
        (item_id,),
    ).fetchone()
    if row is None:
        return None
    item = _decode_news_item_row(row)
    source = {
        "id": int(row["source_id"]),
        "source_key": str(row["source_key"]),
        "name": str(row["source_name"]),
        "scope": str(row["scope"]),
        "kind": str(row["source_kind"]),
        "priority": int(row["source_priority"]),
        "enabled": bool(row["source_enabled"]),
        "url": str(row["source_url"] or ""),
        "tags": json_loads(str(row["source_tags_json"]), []),
        "policy": json_loads(str(row["source_policy_json"]), {}),
    }
    latest_health = _latest_health_by_source(conn).get(source["id"])
    latest_fetch = _latest_fetch_runs_by_source(conn).get(source["id"])
    stale = _is_stale_health(latest_health)
    state, message = _resolve_source_state(
        source_enabled=source["enabled"],
        source_url=source["url"] or None,
        policy=source["policy"],
        fetch=latest_fetch,
        health=latest_health,
        stale=stale,
    )
    item["source"] = source
    item["latest_health"] = latest_health
    item["latest_fetch_run"] = latest_fetch
    item["health_state"] = state
    item["health_message"] = message
    evidence = dict(item.get("evidence") or {})
    evidence.setdefault("source", {})
    evidence["source"].setdefault("source_key", source["source_key"])
    evidence["source"].setdefault("source_name", source["name"])
    evidence["source"].setdefault("scope", source["scope"])
    evidence["source"].setdefault("kind", source["kind"])
    evidence["source"].setdefault("priority", source["priority"])
    evidence.setdefault("policy", {})
    evidence["policy"].setdefault("policy_state", source["policy"].get("policy_state"))
    evidence["policy"].setdefault("basis", source["policy"].get("basis"))
    evidence["policy"].setdefault("robots_state", source["policy"].get("robots_state"))
    evidence["policy"].setdefault("notes", source["policy"].get("notes") or [])
    evidence.setdefault("source_health", {})
    evidence["source_health"].setdefault("state", state)
    evidence["source_health"].setdefault("message", message)
    evidence.setdefault("retention", {})
    evidence["retention"].setdefault("expires_at", item.get("expires_at"))
    evidence.setdefault("privacy", {})
    evidence["privacy"].setdefault("article_body_stored", False)
    evidence["privacy"].setdefault("redaction_applied", False)
    evidence.setdefault("storage", {})
    evidence["storage"].setdefault("canonical_url", item.get("canonical_url"))
    evidence["storage"].setdefault("url", item.get("url"))
    evidence["storage"].setdefault("status", item.get("status"))
    local_event_summary = dict(evidence.get("local_event") or {})
    local_event_id = row["local_event_id"]
    if local_event_id:
        local_event = get_news_local_event_detail(conn, int(local_event_id))
        if local_event:
            item["local_event"] = local_event
            evidence["local_event"] = {
                "summary": local_event_summary or None,
                "event": local_event,
            }
        else:
            evidence["local_event"] = local_event_summary or None
    else:
        evidence["local_event"] = local_event_summary
    item["evidence"] = evidence
    return item
