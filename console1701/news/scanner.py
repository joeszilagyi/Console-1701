from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from console1701.config import ensure_state_dirs, iter_news_sources, load_config
from console1701.db import connect_db, init_db, json_dumps, json_loads, utc_now
from console1701.news.normalize import cluster_key, content_hash, expires_at, url_hash
from console1701.news.parsers import (
    NewsIngestError,
    NewsParserError,
    PayloadTooLargeError,
    UnsupportedSourceError,
    load_fixture_text,
    parse_fixture_items,
)
from console1701.news.ranking import build_rank_result
from console1701.news.source_policy import evaluate_source_policy


def run_news_scan(config_path: str | Path | None = None) -> dict[str, Any]:
    config = load_config(config_path)
    ensure_state_dirs(config)
    sqlite_cfg = config.get("sqlite", {})
    config_dir = Path(config["_config_path"]).resolve().parent
    conn = connect_db(
        config["_db_path"],
        busy_timeout_ms=int(sqlite_cfg.get("busy_timeout_ms", 5000)),
        journal_mode=str(sqlite_cfg.get("journal_mode", "WAL")),
    )
    init_db(conn)

    scanned_sources = 0
    healthy_sources = 0
    item_count = 0
    errors: list[str] = []
    configured_sources = iter_news_sources(config)
    upserted_sources = 0
    purge_summary: dict[str, int] = {"items": 0, "fetch_runs": 0, "source_health": 0}

    try:
        for source in configured_sources:
            _upsert_source(conn, config, source, now=utc_now())
            upserted_sources += 1
        conn.commit()

        if not bool((config.get("news") or {}).get("enabled")):
            return {
                "status": "disabled",
                "configured_sources": len(configured_sources),
                "stored_sources": upserted_sources,
                "scanned_sources": 0,
                "healthy_sources": 0,
                "item_count": 0,
                "errors": [],
                "purged": purge_summary,
            }

        for source in configured_sources:
            if not _source_is_enabled(config, source):
                continue
            scanned_sources += 1
            try:
                stored = _ingest_source(conn, config, source, config_dir=config_dir)
                item_count += stored
                healthy_sources += 1
            except NewsIngestError as exc:
                errors.append(f"{source['id']}: {exc}")
        purge_now = utc_now()
        before_counts = _news_table_counts(conn)
        purge_summary = purge_news_retention(conn, config, now=purge_now)
        after_counts = _news_table_counts(conn)
        _record_news_runtime_state(
            conn,
            "news.last_purge",
            {
                "observed_at": purge_now,
                "summary": purge_summary,
                "before_counts": before_counts,
                "after_counts": after_counts,
                "cutoffs": _retention_cutoffs(config, purge_now),
                "retention": (config.get("news") or {}).get("retention") or {},
            },
        )
        result_status = "complete" if not errors else "partial"
        result = {
            "status": result_status,
            "configured_sources": len(configured_sources),
            "stored_sources": upserted_sources,
            "scanned_sources": scanned_sources,
            "healthy_sources": healthy_sources,
            "item_count": item_count,
            "errors": errors,
            "purged": purge_summary,
        }
        _record_news_runtime_state(conn, "news.last_scan_result", result)
        conn.commit()
    finally:
        conn.close()

    return result


def _record_news_runtime_state(
    conn: sqlite3.Connection,
    key: str,
    value: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (key, json_dumps(value)),
    )


def _news_table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "news_sources": _count_rows(conn, "news_sources"),
        "news_fetch_runs": _count_rows(conn, "news_fetch_runs"),
        "news_items": _count_rows(conn, "news_items"),
        "news_clusters": _count_rows(conn, "news_clusters"),
        "news_source_health": _count_rows(conn, "news_source_health"),
    }


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return int(row["count"] if row else 0)


def _retention_cutoffs(config: dict[str, Any], now: str) -> dict[str, str]:
    current = datetime.fromisoformat(now).astimezone(UTC)
    retention = ((config.get("news") or {}).get("retention") or {})
    return {
        "items_before": current.isoformat(timespec="seconds"),
        "fetch_runs_before": (
            current - timedelta(days=int(retention.get("fetch_runs_days", 14)))
        ).isoformat(timespec="seconds"),
        "source_health_before": (
            current - timedelta(days=int(retention.get("source_health_days", 30)))
        ).isoformat(timespec="seconds"),
    }


def _source_is_enabled(config: dict[str, Any], source: dict[str, Any]) -> bool:
    scopes = ((config.get("news") or {}).get("scopes") or {})
    scope_cfg = (scopes.get(str(source.get("scope")) or "") or {})
    return bool(scope_cfg.get("enabled")) and bool(source.get("enabled"))


def _policy_for_source(config: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    policy = evaluate_source_policy(config, source)
    policy["parser"] = source.get("parser")
    policy["fixture_only"] = True
    return policy


def _upsert_source(
    conn: sqlite3.Connection,
    config: dict[str, Any],
    source: dict[str, Any],
    *,
    now: str,
) -> int:
    policy = _policy_for_source(config, source)
    config_hash = _source_config_hash(source)
    conn.execute(
        """
        INSERT INTO news_sources (
          source_key, scope, name, kind, url, homepage_url, enabled, config_hash,
          priority, tags_json, policy_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_key) DO UPDATE SET
          scope = excluded.scope,
          name = excluded.name,
          kind = excluded.kind,
          url = excluded.url,
          homepage_url = excluded.homepage_url,
          enabled = excluded.enabled,
          config_hash = excluded.config_hash,
          priority = excluded.priority,
          tags_json = excluded.tags_json,
          policy_json = excluded.policy_json,
          updated_at = excluded.updated_at
        """,
        (
            source["id"],
            source["scope"],
            source["name"],
            source["kind"],
            source.get("url"),
            source.get("homepage_url"),
            int(bool(source.get("enabled"))),
            config_hash,
            int(source.get("priority", 50)),
            json_dumps(source.get("tags") or []),
            json_dumps(policy),
            now,
            now,
        ),
    )
    row = conn.execute(
        "SELECT id FROM news_sources WHERE source_key = ?",
        (source["id"],),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"Failed to upsert source {source['id']}")
    return int(row["id"])


def _source_config_hash(source: dict[str, Any]) -> str:
    stable = {
        key: value
        for key, value in source.items()
        if key
        not in {
            "enabled",
        }
    }
    return content_hash(json_dumps(stable), str(source.get("enabled")))


def _ingest_source(
    conn: sqlite3.Connection,
    config: dict[str, Any],
    source: dict[str, Any],
    *,
    config_dir: Path,
) -> int:
    now = utc_now()
    source_id = _upsert_source(conn, config, source, now=now)
    run_id = _start_fetch_run(conn, source_id, started_at=now, source=source)
    max_bytes = int(
        ((config.get("news") or {}).get("fetch_policy") or {}).get(
            "max_response_bytes",
            1048576,
        )
    )
    default_retention_days = int(
        ((config.get("news") or {}).get("retention") or {}).get("items_days", 7)
    )

    try:
        text, path = load_fixture_text(
            source,
            config_dir=config_dir,
            max_bytes=max_bytes,
        )
        items = parse_fixture_items(source, text)
        stored_count = 0
        for item in items:
            evidence = dict(item.get("evidence") or {})
            evidence["fixture_path"] = str(path)
            evidence["fixture_size_bytes"] = len(text.encode("utf-8"))
            item["evidence"] = evidence
            _upsert_item(
                conn,
                source_id,
                source,
                item,
                seen_at=now,
                default_retention_days=default_retention_days,
            )
            stored_count += 1
        _rebuild_scope_clusters(conn, str(source["scope"]))
        _finish_fetch_run(
            conn,
            run_id,
            status="success",
            finished_at=utc_now(),
            item_count=stored_count,
            evidence={"fixture_path": str(path), "fixture_only": True},
        )
        _insert_source_health(
            conn,
            source_id,
            observed_at=utc_now(),
            state="healthy",
            last_success_at=utc_now(),
            last_failure_at=None,
            message=f"Fixture ingest succeeded for {path.name}.",
            evidence={"fixture_path": str(path), "item_count": stored_count},
            source=source,
        )
        return stored_count
    except UnsupportedSourceError as exc:
        _record_source_failure(
            conn,
            run_id,
            source_id,
            source,
            status="blocked_policy",
            error_class=type(exc).__name__,
            error_message=str(exc),
            message="Source is outside the fixture-only ingest policy.",
        )
        raise
    except PayloadTooLargeError as exc:
        _record_source_failure(
            conn,
            run_id,
            source_id,
            source,
            status="payload_too_large",
            error_class=type(exc).__name__,
            error_message=str(exc),
            message=str(exc),
        )
        raise
    except NewsParserError as exc:
        _record_source_failure(
            conn,
            run_id,
            source_id,
            source,
            status="parser_failed",
            error_class=type(exc).__name__,
            error_message=str(exc),
            message=str(exc),
        )
        raise
    except NewsIngestError as exc:
        _record_source_failure(
            conn,
            run_id,
            source_id,
            source,
            status="failed",
            error_class=type(exc).__name__,
            error_message=str(exc),
            message=str(exc),
        )
        raise


def _record_source_failure(
    conn: sqlite3.Connection,
    run_id: int,
    source_id: int,
    source: dict[str, Any],
    *,
    status: str,
    error_class: str,
    error_message: str,
    message: str,
) -> None:
    now = utc_now()
    _finish_fetch_run(
        conn,
        run_id,
        status=status,
        finished_at=now,
        item_count=0,
        error_class=error_class,
        error_message=error_message,
        evidence={"fixture_only": True},
    )
    _insert_source_health(
        conn,
        source_id,
        observed_at=now,
        state=status,
        last_success_at=_latest_health_timestamp(conn, source_id, "last_success_at"),
        last_failure_at=now,
        message=message,
        evidence={"fixture_only": True, "error_class": error_class},
        source=source,
    )


def _latest_health_timestamp(conn: sqlite3.Connection, source_id: int, column: str) -> str | None:
    row = conn.execute(
        f"""
        SELECT {column}
        FROM news_source_health
        WHERE source_id = ? AND {column} IS NOT NULL
        ORDER BY id DESC
        LIMIT 1
        """,
        (source_id,),
    ).fetchone()
    if row is None:
        return None
    return str(row[column]) if row[column] else None


def _start_fetch_run(
    conn: sqlite3.Connection,
    source_id: int,
    *,
    started_at: str,
    source: dict[str, Any],
) -> int:
    row_id = conn.execute(
        """
        INSERT INTO news_fetch_runs (
          source_id, started_at, status, item_count, robots_allowed, evidence_json
        )
        VALUES (?, ?, 'running', 0, NULL, ?)
        """,
        (
            source_id,
            started_at,
            json_dumps({"fixture_only": True, "source_kind": source.get("kind")}),
        ),
    ).lastrowid
    return int(row_id)


def _finish_fetch_run(
    conn: sqlite3.Connection,
    run_id: int,
    *,
    status: str,
    finished_at: str,
    item_count: int,
    error_class: str | None = None,
    error_message: str | None = None,
    evidence: dict[str, Any] | None = None,
) -> None:
    started = conn.execute(
        "SELECT started_at, evidence_json FROM news_fetch_runs WHERE id = ?",
        (run_id,),
    ).fetchone()
    if started is None:
        return
    started_at = datetime.fromisoformat(str(started["started_at"]))
    finished_dt = datetime.fromisoformat(finished_at)
    prior_evidence = json_loads(str(started["evidence_json"]), {})
    merged_evidence = dict(prior_evidence)
    if evidence:
        merged_evidence.update(evidence)
    conn.execute(
        """
        UPDATE news_fetch_runs
        SET finished_at = ?,
            status = ?,
            item_count = ?,
            error_class = ?,
            error_message = ?,
            duration_ms = ?,
            evidence_json = ?
        WHERE id = ?
        """,
        (
            finished_at,
            status,
            int(item_count),
            error_class,
            error_message,
            max(0, int((finished_dt - started_at).total_seconds() * 1000)),
            json_dumps(merged_evidence),
            run_id,
        ),
    )


def _insert_source_health(
    conn: sqlite3.Connection,
    source_id: int,
    *,
    observed_at: str,
    state: str,
    last_success_at: str | None,
    last_failure_at: str | None,
    message: str,
    evidence: dict[str, Any],
    source: dict[str, Any],
) -> None:
    consecutive_failures = 0
    latest = conn.execute(
        """
        SELECT consecutive_failures, state
        FROM news_source_health
        WHERE source_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (source_id,),
    ).fetchone()
    if state == "healthy":
        consecutive_failures = 0
    else:
        previous = int(latest["consecutive_failures"]) if latest is not None else 0
        consecutive_failures = previous + 1

    observed_dt = datetime.fromisoformat(observed_at)
    interval_minutes = int(source.get("interval_minutes") or 0)
    stale_after = None
    if interval_minutes > 0:
        stale_after = (
            observed_dt + timedelta(minutes=max(1, interval_minutes * 2))
        ).isoformat(timespec="seconds")

    conn.execute(
        """
        INSERT INTO news_source_health (
          source_id, observed_at, state, last_success_at, last_failure_at,
          consecutive_failures, stale_after, message, evidence_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_id,
            observed_at,
            state,
            last_success_at,
            last_failure_at,
            consecutive_failures,
            stale_after,
            message,
            json_dumps(evidence),
        ),
    )


def _upsert_item(
    conn: sqlite3.Connection,
    source_id: int,
    source: dict[str, Any],
    item: dict[str, Any],
    *,
    seen_at: str,
    default_retention_days: int,
) -> None:
    combined_tags = list(dict.fromkeys([*(source.get("tags") or []), *(item.get("tags") or [])]))
    hashed_url = url_hash(str(item["canonical_url"] or item["url"]))
    cluster = cluster_key(str(item["title"]), hashed_url)
    retention_days = int(source.get("retention_days") or default_retention_days)
    expire_at = expires_at(seen_at, retention_days)
    existing = conn.execute(
        """
        SELECT id, first_seen_at, trend_score
        FROM news_items
        WHERE source_id = ? AND url_hash = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (source_id, hashed_url),
    ).fetchone()
    latest_health_state = _latest_health_state(conn, source_id)
    repeat_count = (
        int(existing["trend_score"])
        if existing is not None and existing["trend_score"]
        else 0
    )
    ranking = build_rank_result(
        source,
        item,
        seen_at=seen_at,
        combined_tags=combined_tags,
        latest_health_state=latest_health_state,
        repeat_count=repeat_count,
    )
    evidence = dict(item.get("evidence") or {})
    evidence["cluster_key"] = cluster
    evidence["ranking"] = ranking
    item_rank = int(ranking["score"])
    if existing is None:
        conn.execute(
            """
            INSERT INTO news_items (
              source_id, scope, canonical_url, url, url_hash, title, description,
              source_published_at, first_seen_at, last_seen_at, expires_at, source_kind,
              tags_json, rank_score, trend_score, evidence_json, content_hash, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                source_id,
                source["scope"],
                item.get("canonical_url"),
                item["url"],
                hashed_url,
                item["title"],
                item.get("description"),
                item.get("source_published_at"),
                seen_at,
                seen_at,
                expire_at,
                source["kind"],
                json_dumps(combined_tags),
                item_rank,
                1,
                json_dumps(evidence),
                content_hash(item["title"], item.get("description")),
            ),
        )
        return

    conn.execute(
        """
        UPDATE news_items
        SET canonical_url = ?,
            url = ?,
            title = ?,
            description = ?,
            source_published_at = ?,
            last_seen_at = ?,
            expires_at = ?,
            tags_json = ?,
            rank_score = ?,
            trend_score = trend_score + 1,
            evidence_json = ?,
            content_hash = ?,
            status = 'active'
        WHERE id = ?
        """,
        (
            item.get("canonical_url"),
            item["url"],
            item["title"],
            item.get("description"),
            item.get("source_published_at"),
            seen_at,
            expire_at,
            json_dumps(combined_tags),
            item_rank,
            json_dumps(evidence),
            content_hash(item["title"], item.get("description")),
            int(existing["id"]),
        ),
    )


def _latest_health_state(conn: sqlite3.Connection, source_id: int) -> str | None:
    row = conn.execute(
        """
        SELECT state
        FROM news_source_health
        WHERE source_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (source_id,),
    ).fetchone()
    if row is None or not row["state"]:
        return None
    return str(row["state"])


def _rebuild_scope_clusters(conn: sqlite3.Connection, scope: str) -> None:
    rows = conn.execute(
        """
        SELECT id, title, url_hash, last_seen_at, rank_score, tags_json, evidence_json
        FROM news_items
        WHERE scope = ? AND status = 'active'
        ORDER BY rank_score DESC, last_seen_at DESC, id DESC
        """,
        (scope,),
    ).fetchall()
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        evidence = json_loads(str(row["evidence_json"]), {})
        key = str(
            evidence.get("cluster_key")
            or cluster_key(str(row["title"]), str(row["url_hash"]))
        )
        group = grouped.setdefault(
            key,
            {
                "title": str(row["title"]),
                "representative_item_id": int(row["id"]),
                "first_seen_at": str(row["last_seen_at"]),
                "last_seen_at": str(row["last_seen_at"]),
                "item_count": 0,
                "score": 0,
                "tags": [],
            },
        )
        group["item_count"] += 1
        group["score"] += int(row["rank_score"])
        group["last_seen_at"] = max(group["last_seen_at"], str(row["last_seen_at"]))
        tags = json_loads(str(row["tags_json"]), [])
        group["tags"] = list(dict.fromkeys([*group["tags"], *tags]))

    conn.execute("DELETE FROM news_clusters WHERE scope = ?", (scope,))
    for key, group in grouped.items():
        conn.execute(
            """
            INSERT INTO news_clusters (
              scope, cluster_key, title, representative_item_id, first_seen_at,
              last_seen_at, item_count, score, tags_json, evidence_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scope,
                key,
                group["title"],
                group["representative_item_id"],
                group["first_seen_at"],
                group["last_seen_at"],
                group["item_count"],
                group["score"],
                json_dumps(group["tags"]),
                json_dumps({"fixture_only": True}),
            ),
        )


def purge_news_retention(
    conn: sqlite3.Connection,
    config: dict[str, Any],
    *,
    now: str | None = None,
) -> dict[str, int]:
    cutoff_now = now or utc_now()
    cutoffs = _retention_cutoffs(config, cutoff_now)

    deleted_items = conn.execute(
        "DELETE FROM news_items WHERE expires_at < ?",
        (cutoffs["items_before"],),
    ).rowcount
    deleted_fetch_runs = conn.execute(
        "DELETE FROM news_fetch_runs WHERE started_at < ?",
        (cutoffs["fetch_runs_before"],),
    ).rowcount
    deleted_health = conn.execute(
        "DELETE FROM news_source_health WHERE observed_at < ?",
        (cutoffs["source_health_before"],),
    ).rowcount
    return {
        "items": int(deleted_items or 0),
        "fetch_runs": int(deleted_fetch_runs or 0),
        "source_health": int(deleted_health or 0),
    }
