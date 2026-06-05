from __future__ import annotations

import re
import sqlite3
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any

from console1701.config import ensure_state_dirs, iter_news_sources, load_config
from console1701.db import connect_db, init_db, json_dumps, json_loads, utc_now
from console1701.news.local_registry import list_local_source_registry
from console1701.news.normalize import cluster_key, content_hash, expires_at, url_hash
from console1701.news.parsers import (
    NewsIngestError,
    NewsParserError,
    PayloadTooLargeError,
    UnsupportedSourceError,
    load_fixture_text,
    parse_fixture_items,
)
from console1701.news.ranking import (
    apply_local_event_ranking_adjustments,
    build_rank_result,
)
from console1701.news.source_policy import evaluate_source_policy

LOCAL_EVENT_MATCH_WINDOW_HOURS = 3
LOCAL_EVENT_MIN_MATCH_SCORE = 20
LOCAL_EVENT_KEY_TOKEN_LIMIT = 12
LOCAL_EVENT_MATCH_THRESHOLD = LOCAL_EVENT_MIN_MATCH_SCORE

_LOCAL_EVENT_STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "their",
    "them",
    "there",
    "this",
    "to",
    "with",
}

_LOCAL_EVENT_TOKEN_RE = re.compile(r"[a-z0-9]+")


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
    sync_time = utc_now()
    _sync_local_source_registry(conn, synced_at=sync_time)

    scanned_sources = 0
    healthy_sources = 0
    item_count = 0
    errors: list[str] = []
    configured_sources = iter_news_sources(config)
    upserted_sources = 0
    purge_summary: dict[str, int] = {
        "items": 0,
        "fetch_runs": 0,
        "source_health": 0,
        "local_events": 0,
    }

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
        "local_events": _count_rows(conn, "local_events"),
    }


def _sync_local_source_registry(conn: sqlite3.Connection, synced_at: str) -> int:
    entries = list_local_source_registry()
    if not entries:
        return 0

    source_keys = [str(entry["source_key"]) for entry in entries]

    placeholder = ",".join(["?"] * len(entries))
    rows = conn.execute(
        "SELECT source_key FROM news_source_registry WHERE scope = ?",
        ("LOCAL",),
    ).fetchall()
    existing = {str(row["source_key"]) for row in rows}
    updated = 0

    for entry in entries:
        source_key = str(entry["source_key"])
        existing.discard(source_key)
        conn.execute(
            """
            INSERT INTO news_source_registry (
              source_key, scope, source_name, source_family, source_class, adapter,
              kind, raw_url, priority, interval_minutes, official_status,
              privacy_risk, policy_risk, parser_risk, retention_sensitivity,
              verification_status, future_phase, expected_access_kind, homepage_url,
              parser, enabled_by_default, why_it_matters, evidence_notes_json,
              seen_at, last_synced_at, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_key) DO UPDATE SET
              scope = excluded.scope,
              source_name = excluded.source_name,
              source_family = excluded.source_family,
              source_class = excluded.source_class,
              adapter = excluded.adapter,
              kind = excluded.kind,
              raw_url = excluded.raw_url,
              priority = excluded.priority,
              interval_minutes = excluded.interval_minutes,
              official_status = excluded.official_status,
              privacy_risk = excluded.privacy_risk,
              policy_risk = excluded.policy_risk,
              parser_risk = excluded.parser_risk,
              retention_sensitivity = excluded.retention_sensitivity,
              verification_status = excluded.verification_status,
              future_phase = excluded.future_phase,
              expected_access_kind = excluded.expected_access_kind,
              homepage_url = excluded.homepage_url,
              parser = excluded.parser,
              enabled_by_default = excluded.enabled_by_default,
              why_it_matters = excluded.why_it_matters,
              evidence_notes_json = excluded.evidence_notes_json,
              seen_at = COALESCE(news_source_registry.seen_at, excluded.seen_at),
              last_synced_at = excluded.last_synced_at,
              updated_at = excluded.updated_at
            """,
            (
                source_key,
                str(entry["scope"]),
                str(entry["source_name"]),
                str(entry["source_family"]),
                str(entry["source_class"]),
                str(entry["adapter"]),
                str(entry["kind"]),
                str(entry["raw_url"]),
                int(entry["priority"]),
                int(entry["interval_minutes"]),
                str(entry["official_status"]),
                str(entry["privacy_risk"]),
                str(entry["policy_risk"]),
                str(entry["parser_risk"]),
                str(entry["retention_sensitivity"]),
                str(entry["verification_status"]),
                str(entry["future_phase"]),
                str(entry["expected_access_kind"]),
                entry.get("homepage_url"),
                entry.get("parser"),
                1 if bool(entry.get("enabled")) else 0,
                str(entry.get("why_it_matters") or ""),
                json_dumps(entry.get("evidence_notes") or []),
                synced_at,
                synced_at,
                synced_at,
                synced_at,
            ),
        )
        updated += 1

    if existing:
        conn.execute(
            (
                "DELETE FROM news_source_registry WHERE scope = ? "
                f"AND source_key NOT IN ({placeholder})"
            ),
            ("LOCAL", *source_keys),
        )

    return updated


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    return int(row["count"] if row else 0)


def _retention_cutoffs(config: dict[str, Any], now: str) -> dict[str, str]:
    current = datetime.fromisoformat(now).astimezone(UTC)
    retention = (config.get("news") or {}).get("retention") or {}
    return {
        "items_before": current.isoformat(timespec="seconds"),
        "local_events_before": (
            current - timedelta(days=int(retention.get("items_days", 7)))
        ).isoformat(timespec="seconds"),
        "fetch_runs_before": (
            current - timedelta(days=int(retention.get("fetch_runs_days", 14)))
        ).isoformat(timespec="seconds"),
        "source_health_before": (
            current - timedelta(days=int(retention.get("source_health_days", 30)))
        ).isoformat(timespec="seconds"),
    }


def _source_is_enabled(config: dict[str, Any], source: dict[str, Any]) -> bool:
    scopes = (config.get("news") or {}).get("scopes") or {}
    scope_cfg = scopes.get(str(source.get("scope")) or "") or {}
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
        policy = _policy_for_source(config, source)
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
                fetch_run_id=run_id,
                seen_at=now,
                default_retention_days=default_retention_days,
                policy=policy,
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
            status="policy_blocked",
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
        stale_after = (observed_dt + timedelta(minutes=max(1, interval_minutes * 2))).isoformat(
            timespec="seconds"
        )

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


def _normalize_local_event_token(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if not text or len(text) > 120:
        return None
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    if not text:
        return None
    if text in _LOCAL_EVENT_STOPWORDS:
        return None
    return text


def _split_title_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for candidate in _LOCAL_EVENT_TOKEN_RE.findall(str(value).lower()):
        normalized = _normalize_local_event_token(candidate)
        if normalized and normalized not in tokens:
            tokens.append(normalized)
    return tokens


def _safe_parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _deduplicate_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value:
            continue
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _local_event_time_bucket(event_time: datetime | None) -> str:
    if event_time is None:
        event_time = datetime.now(UTC)
    bucket_hour = (
        event_time.hour // LOCAL_EVENT_MATCH_WINDOW_HOURS
    ) * LOCAL_EVENT_MATCH_WINDOW_HOURS
    bucket_start = event_time.replace(
        minute=0,
        second=0,
        microsecond=0,
        hour=bucket_hour,
    )
    return bucket_start.isoformat(timespec="seconds")


def _local_event_route_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for pattern in (
        r"\b(?:i-\s?\d+[a-z]?)\b",
        r"\b(?:sr\s?\d+[a-z]?)\b",
        r"\b(?:us\s?\d+)\b",
        r"\b(?:wa\s?\d+)\b",
        r"\b(?:route\s+[a-z]?\d+[a-z]?)\b",
    ):
        for match in re.finditer(pattern, text, re.IGNORECASE):
            token = re.sub(r"\s+", "-", match.group(0).lower().strip())
            token = token.replace("route-", "route-")
            if token and token not in tokens:
                tokens.append(token)
    return tokens


def _local_event_infer_type(
    source_family: str,
    item_title: str,
    evidence: dict[str, Any],
) -> str:
    lowered_title = item_title.lower()
    if "city_light_outage" in evidence or source_family == "city_light":
        return "power_outage"
    if "faa_airport_status" in evidence or source_family == "faa":
        return "airport_disruption"
    if "wsdot_alert" in evidence or source_family == "wsdot":
        if any(
            term in lowered_title for term in ("collision", "lane", "closure", "blocked", "crash")
        ):
            return "traffic_collision"
        return "road_closure"
    if "metro_advisory" in evidence or source_family == "metro":
        return "transit_disruption"
    if "nws_alert" in evidence or source_family == "nws":
        return "weather_alert"
    if "alertseattle" in evidence:
        event_type = str((evidence["alertseattle"] or {}).get("event_type") or "").lower()
        if event_type in {"utility", "weather_hazard", "transport"}:
            return {
                "utility": "power_outage",
                "weather_hazard": "weather_alert",
                "transport": "road_closure",
            }.get(event_type, "civic_alert")
        if "emergency" in event_type:
            return "civic_alert"
    if "sfd_fire_911" in evidence:
        incident = str((evidence["sfd_fire_911"] or {}).get("incident_type", "")).lower()
        if "fire" in incident:
            return "fire"
        if any(term in incident for term in ("medical", "aid", "overdose", "injury")):
            return "medical_public_impact"
        return "major_event"
    if "local_blog" in evidence:
        return "community_signal"
    if "spd_blotter" in evidence:
        details = str((evidence["spd_blotter"] or {}).get("incident_type") or "").lower()
        if "traffic" in details:
            return "road_closure"
        if "major" in details or "law_enforcement_major_incident" in details:
            return "major_event"
        return "public_safety_incident"
    if "sdot_blog" in evidence:
        details = str((evidence["sdot_blog"] or {}).get("incident_type") or "").lower()
        if "collision" in details or "traffic" in details:
            return "road_closure"
        return "transport_disruption"
    if "local_news" in evidence:
        news = evidence["local_news"] or {}
        if news.get("traffic_related"):
            return "transport_disruption"
    if any(term in lowered_title for term in ("outage", "power", "electric")):
        return "power_outage"
    if any(term in lowered_title for term in ("road", "route", "highway", "traffic")):
        return "road_closure"
    if any(term in lowered_title for term in ("storm", "wind", "snow", "flood", "alert")):
        return "weather_alert"
    return "news_story"


def _local_event_evidence_tokens(
    source: dict[str, Any], item: dict[str, Any]
) -> dict[str, list[str]]:
    evidence = dict(item.get("evidence") or {})
    source_family = str(source.get("source_family") or "").lower()
    title = str(item["title"]).lower()
    title_tokens = _split_title_tokens(title)
    route_tokens: list[str] = []
    facility_tokens: list[str] = []
    weather_tokens: list[str] = []
    airport_tokens: list[str] = []
    utility_tokens: list[str] = []
    location_tokens: list[str] = []

    for token in _local_event_route_tokens(title):
        if token:
            route_tokens.append(token)
            facility_tokens.append(token)

    if source_family in {"wsdot", "metro"}:
        route_key = "wsdot_alert" if source_family == "wsdot" else "metro_advisory"
        route_values = evidence.get(route_key) or {}
        if isinstance(route_values, dict):
            route_tokens.extend(
                str(token).lower() for token in (route_values.get("route_tokens") or [])
            )
            facility_tokens.extend(_deduplicate_ordered(route_tokens))
            for area in route_values.get("affected_service_areas") or []:
                value = str(area).strip()
                if value:
                    location_tokens.append(value.lower())

    city_light = evidence.get("city_light_outage")
    if isinstance(city_light, dict):
        area = str(city_light.get("area") or "").strip()
        if area:
            utility_tokens.append(area.lower())
            location_tokens.append(area.lower())
        for code in (
            evidence.get("city_light_outage", {}).get("filter", {}).get("matched_area_keywords")
            or []
        ):
            area = str(code).strip().lower()
            if area:
                location_tokens.append(area)

    airport = evidence.get("faa_airport_status")
    if isinstance(airport, dict):
        airport_code = str(airport.get("airport_code") or "").strip()
        if airport_code:
            airport_tokens.append(airport_code.lower())
            facility_tokens.append(f"{airport_code.lower()}-airport")
        for weather_item in (
            airport.get("weather") if isinstance(airport.get("weather"), dict) else {}
        ).values():
            if isinstance(weather_item, str):
                weather_tokens.append(weather_item.lower())

    nws_alert = evidence.get("nws_alert")
    if isinstance(nws_alert, dict):
        for zone in nws_alert.get("affected_zones") or []:
            zone_text = str(zone).strip().lower()
            if zone_text:
                weather_tokens.append(zone_text)
        area_desc = str(nws_alert.get("area_desc") or "").strip().lower()
        if area_desc:
            location_tokens.append(area_desc)

    sfd = evidence.get("sfd_fire_911")
    if isinstance(sfd, dict):
        for value in sfd.get("location_tokens") or []:
            text = str(value).strip().lower()
            if text:
                location_tokens.append(text)
        location = str(sfd.get("location") or "").strip().lower()
        if location:
            location_tokens.append(location)

    local_blog = evidence.get("local_blog")
    if isinstance(local_blog, dict):
        for value in local_blog.get("neighborhoods") or []:
            text = str(value).strip().lower()
            if text:
                location_tokens.append(text)

    spd_blotter = evidence.get("spd_blotter")
    if isinstance(spd_blotter, dict):
        for value in spd_blotter.get("route_tokens") or []:
            token = str(value).strip().lower()
            if token:
                route_tokens.append(token)
                facility_tokens.append(token)
        for value in spd_blotter.get("route_tokens") or []:
            token = str(value).strip().lower()
            if token:
                title_tokens.append(token)
        for value in spd_blotter.get("neighborhoods") or []:
            text = str(value).strip().lower()
            if text:
                location_tokens.append(text)

    sdot_blog = evidence.get("sdot_blog")
    if isinstance(sdot_blog, dict):
        for value in sdot_blog.get("route_tokens") or []:
            token = str(value).strip().lower()
            if token:
                route_tokens.append(token)
                facility_tokens.append(token)
        for value in sdot_blog.get("service_areas") or []:
            text = str(value).strip().lower()
            if text:
                location_tokens.append(text)

    local_news = evidence.get("local_news")
    if isinstance(local_news, dict):
        for value in local_news.get("route_tokens") or []:
            token = str(value).strip().lower()
            if token:
                route_tokens.append(token)
                facility_tokens.append(token)
                title_tokens.append(token)
        for value in local_news.get("service_areas") or []:
            text = str(value).strip().lower()
            if text:
                location_tokens.append(text)
    if isinstance(local_news, dict) and local_news.get("traffic_related"):
        title_tokens.append("local")
        location_tokens.append("seattle")

    if source_family in {"nws", "alertseattle", "weather"}:
        weather_tokens.extend(title_tokens)

    return {
        "title_tokens": _deduplicate_ordered(title_tokens),
        "route_tokens": _deduplicate_ordered(route_tokens),
        "facility_tokens": _deduplicate_ordered(facility_tokens),
        "weather_tokens": _deduplicate_ordered(weather_tokens),
        "airport_tokens": _deduplicate_ordered(airport_tokens),
        "utility_tokens": _deduplicate_ordered(utility_tokens),
        "location_tokens": _deduplicate_ordered(location_tokens),
    }


def _build_local_event_signature(
    source: dict[str, Any],
    item: dict[str, Any],
    seen_at: str,
) -> dict[str, Any]:
    source_family = str(source.get("source_family") or "").lower()
    event_time = _safe_parse_time(str(item.get("source_published_at") or seen_at))
    evidence = dict(item.get("evidence") or {})
    title = str(item["title"])
    title_tokens = _split_title_tokens(title)
    token_groups = _local_event_evidence_tokens(source, item)
    event_type = _local_event_infer_type(
        source_family=source_family,
        item_title=title.lower(),
        evidence=evidence,
    )
    match_tokens = _deduplicate_ordered(
        [f"title:{token}" for token in token_groups["title_tokens"]]
        + [f"route:{token}" for token in token_groups["route_tokens"]]
        + [f"facility:{token}" for token in token_groups["facility_tokens"]]
        + [f"weather:{token}" for token in token_groups["weather_tokens"]]
        + [f"airport:{token}" for token in token_groups["airport_tokens"]]
        + [f"utility:{token}" for token in token_groups["utility_tokens"]]
        + [f"location:{token}" for token in token_groups["location_tokens"]]
    )
    if len(match_tokens) == 0:
        match_tokens = [f"title:{token}" for token in title_tokens[:8]]
    key_payload = "|".join(
        [
            "LOCAL",
            event_type,
            _local_event_time_bucket(event_time),
            source_family or "unknown",
            ",".join(match_tokens[:LOCAL_EVENT_KEY_TOKEN_LIMIT]),
        ]
    )
    return {
        "scope": "LOCAL",
        "source_family": source_family,
        "source_id": source["id"],
        "event_type": event_type,
        "time_bucket": _local_event_time_bucket(event_time),
        "event_time": event_time.isoformat(timespec="seconds"),
        "title": title,
        "title_tokens": token_groups["title_tokens"],
        "match_tokens": match_tokens,
        "route_tokens": token_groups["route_tokens"],
        "facility_tokens": token_groups["facility_tokens"],
        "weather_tokens": token_groups["weather_tokens"],
        "airport_tokens": token_groups["airport_tokens"],
        "utility_tokens": token_groups["utility_tokens"],
        "location_tokens": token_groups["location_tokens"],
        "event_key": sha256(key_payload.encode("utf-8")).hexdigest(),
    }


def _local_event_match_score(
    signature: dict[str, Any],
    event_row: sqlite3.Row,
) -> int:
    candidate_tokens = set(_deduplicate_ordered(json_loads(str(event_row["geography_json"]), [])))
    candidate_type = str(event_row["event_type"] or "")
    candidate_title_tokens = set(
        _deduplicate_ordered(json_loads(str(event_row["title_tokens_json"]), []))
    )
    source_families = set(_deduplicate_ordered(json_loads(str(event_row["families_json"]), [])))
    signature_tokens = set(signature["match_tokens"])
    title_tokens = set(signature["title_tokens"])
    overlap = len(signature_tokens & candidate_tokens)
    title_overlap = len(title_tokens & candidate_title_tokens)
    score = overlap * 6 + title_overlap * 4
    if candidate_type == signature["event_type"]:
        score += 28
    score += min(18, len(source_families & {signature["source_family"]}) * 10)
    if signature["source_family"] in source_families:
        score += 10
    return score


def _local_event_severity(total_score: int) -> str:
    if total_score >= 72:
        return "critical"
    if total_score >= 55:
        return "major"
    if total_score >= 32:
        return "elevated"
    if total_score >= 12:
        return "notice"
    return "info"


def _local_event_component_scores(
    ranking: dict[str, Any],
    evidence: dict[str, Any],
    event_type: str,
) -> dict[str, int]:
    factors = ranking.get("factors") or {}
    total = int(factors.get("score", 0) if isinstance(factors, dict) else 0)
    official = int(factors.get("local_official_alert_boost", 0))
    public = int(factors.get("local_public_impact_boost", 0))
    transit = int(factors.get("local_transit_impact_boost", 0))
    utility = int(factors.get("local_utility_impact_boost", 0))
    airport = int(factors.get("local_airport_port_boost", 0))
    blog = int(factors.get("local_blog_signal_boost", 0))
    if total <= 0:
        total = max(official, public, transit, utility, airport, blog)
    return {
        "severity": _local_event_severity(total),
        "public_impact_score": public,
        "source_diversity_score": 0,
        "official_confirmation_score": official,
        "transport_impact_score": transit,
        "utility_impact_score": utility,
        "hazard_score": official if event_type in {"weather_alert"} else 0,
        "airport_port_score": airport,
        "social_echo_score": 0,
        "news_echo_score": blog,
        "total_score": total,
    }


def _upsert_local_event(
    conn: sqlite3.Connection,
    source_id: int,
    source: dict[str, Any],
    item: dict[str, Any],
    item_id: int,
    seen_at: str,
    ranking: dict[str, Any],
    retention_days: int,
) -> tuple[int, dict[str, Any]]:
    signature = _build_local_event_signature(source, item, seen_at)
    event_time = _safe_parse_time(signature["event_time"])
    if event_time is None:
        event_time = datetime.now(UTC)
    expires = expires_at(seen_at, retention_days)
    window_start = (event_time - timedelta(hours=LOCAL_EVENT_MATCH_WINDOW_HOURS)).isoformat(
        timespec="seconds"
    )
    rows = conn.execute(
        """
        SELECT id, event_type, title, representative_item_id, severity,
               public_impact_score, source_diversity_score, official_confirmation_score,
               social_echo_score, news_echo_score, transport_impact_score, utility_impact_score,
               hazard_score, airport_port_score, event_key, first_seen_at,
               last_seen_at, last_elevated_at,
               expires_at, geography_json, neighborhoods_json, title_tokens_json, source_ids_json,
               families_json, item_ids_json, evidence_json, ranking_explanation_json
        FROM local_events
        WHERE scope = ? AND status = 'active' AND last_seen_at >= ?
        ORDER BY last_seen_at DESC
        """,
        (signature["scope"], window_start),
    ).fetchall()

    best_match_score = 0
    best_row: sqlite3.Row | None = None
    for row in rows:
        score = _local_event_match_score(signature, row)
        if score > best_match_score:
            best_match_score = score
            best_row = row

    if best_match_score < LOCAL_EVENT_MATCH_THRESHOLD or best_row is None:
        component_scores = _local_event_component_scores(
            ranking=ranking,
            evidence=dict(item.get("evidence") or {}),
            event_type=signature["event_type"],
        )
        evidence_payload = {
            "evidence_items": [
                item.get("evidence") or {},
            ],
            "last_matched_item_id": int(item_id),
            "signature": signature,
        }
        components_payload = {
            "score": int(component_scores["total_score"]),
            "scope": signature["scope"],
            "source_family": signature["source_family"],
            "event_type": signature["event_type"],
            "match_threshold": LOCAL_EVENT_MATCH_THRESHOLD,
            "match_token_count": len(signature["match_tokens"]),
            "location_token_count": len(signature["location_tokens"]),
            "title_token_count": len(signature["title_tokens"]),
            "confidence_basis": [
                "time_window",
                "event_type",
                "title_tokens",
                "normalized_location_tokens",
                "source_family",
            ],
            "match_window_hours": LOCAL_EVENT_MATCH_WINDOW_HOURS,
            "signature_tokens": signature["match_tokens"][:LOCAL_EVENT_KEY_TOKEN_LIMIT],
        }
        cursor = conn.execute(
            """
            INSERT INTO local_events (
              scope, event_key, event_type, title, representative_item_id, severity,
              public_impact_score, source_diversity_score, official_confirmation_score,
              social_echo_score, news_echo_score, transport_impact_score,
              utility_impact_score, hazard_score, airport_port_score, first_seen_at,
              last_seen_at, last_elevated_at, expires_at, geography_json,
              neighborhoods_json, title_tokens_json, source_ids_json, families_json,
              item_ids_json, evidence_json, ranking_explanation_json, status
            )
            VALUES (
              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                signature["scope"],
                signature["event_key"],
                signature["event_type"],
                signature["title"],
                item_id,
                component_scores["severity"],
                component_scores["public_impact_score"],
                component_scores["source_diversity_score"],
                component_scores["official_confirmation_score"],
                component_scores["social_echo_score"],
                component_scores["news_echo_score"],
                component_scores["transport_impact_score"],
                component_scores["utility_impact_score"],
                component_scores["hazard_score"],
                component_scores["airport_port_score"],
                signature["event_time"],
                signature["event_time"],
                None,
                expires,
                json_dumps(_deduplicate_ordered(signature["match_tokens"])),
                json_dumps(signature["location_tokens"]),
                json_dumps(signature["title_tokens"]),
                json_dumps([str(source_id)]),
                json_dumps([signature["source_family"]] if signature["source_family"] else []),
                json_dumps([item_id]),
                json_dumps(evidence_payload),
                json_dumps(components_payload),
                "active",
            ),
        )
        local_event_id = int(cursor.lastrowid)
        return local_event_id, {
            "local_event_id": local_event_id,
            "event_type": signature["event_type"],
            "event_key": signature["event_key"],
            "match_score": 0,
            "matched": False,
            "item_count": 1,
            "families": [signature["source_family"]] if signature["source_family"] else [],
            "is_duplicate_family": False,
            "component_scores": component_scores,
            "signature": signature,
        }

    existing = best_row
    existing_id = int(existing["id"])
    existing_items = _deduplicate_ordered(
        [str(value) for value in json_loads(str(existing["item_ids_json"]), [])]
    )
    source_ids = _deduplicate_ordered(
        [str(value) for value in json_loads(str(existing["source_ids_json"]), [])]
    )
    families = _deduplicate_ordered(
        [str(value) for value in json_loads(str(existing["families_json"]), [])]
    )
    geometry = _deduplicate_ordered(
        _deduplicate_ordered(json_loads(str(existing["geography_json"]), []))
        + signature["match_tokens"]
    )
    neighborhoods = _deduplicate_ordered(
        _deduplicate_ordered(json_loads(str(existing["neighborhoods_json"]), []))
        + signature["location_tokens"]
    )
    merged_item_ids = _deduplicate_ordered(existing_items + [str(item_id)])
    merged_source_ids = _deduplicate_ordered(source_ids + [str(source_id)])
    merged_families = _deduplicate_ordered(
        families + ([signature["source_family"]] if signature["source_family"] else [])
    )
    duplicate_family = bool(signature["source_family"]) and signature["source_family"] in families
    existing_ranking = dict(json_loads(str(existing["ranking_explanation_json"]), {}))
    component_scores = _local_event_component_scores(
        ranking=ranking,
        evidence=dict(item.get("evidence") or {}),
        event_type=signature["event_type"],
    )
    max_transport = max(
        int(existing["transport_impact_score"]),
        component_scores["transport_impact_score"],
    )
    max_utility = max(
        int(existing["utility_impact_score"]),
        component_scores["utility_impact_score"],
    )
    max_hazard = max(int(existing["hazard_score"]), component_scores["hazard_score"])
    max_airport = max(
        int(existing["airport_port_score"]),
        component_scores["airport_port_score"],
    )
    max_official = max(
        int(existing["official_confirmation_score"]),
        component_scores["official_confirmation_score"],
    )
    max_public = max(
        int(existing["public_impact_score"]),
        component_scores["public_impact_score"],
    )
    max_total = max(int(existing_ranking.get("score", 0)), component_scores["total_score"])
    event_time_seen = signature["event_time"]
    first_seen = str(existing["first_seen_at"])
    last_seen = str(existing["last_seen_at"])
    if event_time_seen < first_seen:
        first_seen = event_time_seen
    if event_time_seen > last_seen:
        last_seen = event_time_seen
    evidence_payload = dict(json_loads(str(existing["evidence_json"]), {}))
    if not isinstance(evidence_payload, dict):
        evidence_payload = {}
    item_keys = evidence_payload.get("evidence_items")
    if not isinstance(item_keys, list):
        item_keys = []
    item_keys.append(dict(item.get("evidence") or {}))
    evidence_payload["evidence_items"] = item_keys
    evidence_payload["last_matched_item_id"] = int(item_id)
    existing_ranking["matched_count"] = int(existing_ranking.get("matched_count", 0)) + 1
    existing_ranking["match_threshold"] = LOCAL_EVENT_MATCH_THRESHOLD
    existing_ranking["match_window_hours"] = LOCAL_EVENT_MATCH_WINDOW_HOURS
    existing_ranking["match_token_count"] = len(signature["match_tokens"])
    existing_ranking["location_token_count"] = len(signature["location_tokens"])
    existing_ranking["title_token_count"] = len(signature["title_tokens"])
    existing_ranking["best_match_score"] = int(best_match_score)
    existing_ranking["confidence_basis"] = _deduplicate_ordered(
        [
            str(value)
            for value in (
                existing_ranking.get("confidence_basis")
                or [
                    "time_window",
                    "event_type",
                    "title_tokens",
                    "normalized_location_tokens",
                    "source_family",
                ]
            )
        ]
    )
    existing_ranking["last_match_score"] = best_match_score
    conn.execute(
        """
        UPDATE local_events
        SET representative_item_id = COALESCE(representative_item_id, ?),
            last_seen_at = ?,
            expires_at = ?,
            geography_json = ?,
            neighborhoods_json = ?,
            source_ids_json = ?,
            families_json = ?,
            item_ids_json = ?,
            source_diversity_score = ?,
            public_impact_score = ?,
            official_confirmation_score = ?,
            transport_impact_score = ?,
            utility_impact_score = ?,
            hazard_score = ?,
            airport_port_score = ?,
            evidence_json = ?,
            ranking_explanation_json = ?,
            severity = ?,
            title = ?,
            event_type = ?,
            title_tokens_json = ?
        WHERE id = ?
        """,
        (
            item_id,
            last_seen,
            expires,
            json_dumps(geometry),
            json_dumps(neighborhoods),
            json_dumps(merged_source_ids),
            json_dumps(merged_families),
            json_dumps(merged_item_ids),
            len(merged_families),
            max_public,
            max_official,
            max_transport,
            max_utility,
            max_hazard,
            max_airport,
            json_dumps(evidence_payload),
            json_dumps(existing_ranking),
            _local_event_severity(max_total),
            signature["title"],
            signature["event_type"],
            json_dumps(signature["title_tokens"]),
            existing_id,
        ),
    )
    return existing_id, {
        "local_event_id": existing_id,
        "event_type": signature["event_type"],
        "event_key": str(existing["event_key"]),
        "match_score": int(best_match_score),
        "matched": True,
        "item_count": len(merged_item_ids),
        "families": merged_families,
        "is_duplicate_family": duplicate_family,
        "component_scores": {
            **component_scores,
            "existing": {
                "public_impact_score": int(existing["public_impact_score"]),
                "source_diversity_score": int(existing["source_diversity_score"]),
            },
        },
        "signature": signature,
    }


def _upsert_item(
    conn: sqlite3.Connection,
    source_id: int,
    source: dict[str, Any],
    item: dict[str, Any],
    *,
    fetch_run_id: int,
    seen_at: str,
    default_retention_days: int,
    policy: dict[str, Any],
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
    latest_health_state = _latest_health_state_for_rank(conn, source_id)
    repeat_count = (
        int(existing["trend_score"]) if existing is not None and existing["trend_score"] else 0
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
    evidence["source"] = {
        "source_key": source["id"],
        "source_name": source["name"],
        "scope": source["scope"],
        "kind": source["kind"],
        "priority": int(source.get("priority", 50)),
        "tags": source.get("tags") or [],
    }
    evidence["ingest"] = {
        "fetch_run_id": fetch_run_id,
        "seen_at": seen_at,
        "fixture_only": True,
        "source_health_state_at_ingest": latest_health_state or "unknown",
    }
    evidence["policy"] = {
        "policy_state": policy.get("policy_state"),
        "basis": policy.get("basis"),
        "robots_state": policy.get("robots_state"),
        "notes": policy.get("notes") or [],
    }
    evidence["retention"] = {
        "expires_at": expire_at,
        "retention_days": retention_days,
    }
    privacy_evidence = dict(evidence.get("privacy") or {})
    privacy_evidence.setdefault("article_body_stored", False)
    privacy_evidence.setdefault("redaction_applied", False)
    evidence["privacy"] = privacy_evidence
    evidence["storage"] = {
        "canonical_url": item.get("canonical_url"),
        "url": item["url"],
        "status": "active",
    }
    item_rank = int(ranking["score"])
    local_event: dict[str, Any] | None = None
    local_event_id = None

    if existing is None:
        cursor = conn.execute(
            """
            INSERT INTO news_items (
              source_id, scope, canonical_url, url, url_hash, title, description,
              source_published_at, first_seen_at, last_seen_at, expires_at, source_kind,
              local_event_id, tags_json, rank_score, trend_score, evidence_json,
              content_hash, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
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
                local_event_id,
                json_dumps(combined_tags),
                item_rank,
                1,
                json_dumps(evidence),
                content_hash(item["title"], item.get("description")),
            ),
        )
        item_id = int(cursor.lastrowid)

        if str(source.get("scope") or "").upper() == "LOCAL":
            try:
                local_event_id, local_event = _upsert_local_event(
                    conn,
                    source_id=source_id,
                    source=source,
                    item=item,
                    item_id=item_id,
                    seen_at=seen_at,
                    ranking=ranking,
                    retention_days=retention_days,
                )
                ranking = apply_local_event_ranking_adjustments(
                    ranking,
                    source_family=source.get("source_family"),
                    local_event=local_event,
                )
                evidence["ranking"] = ranking
                item_rank = int(ranking["score"])
                evidence["local_event"] = local_event
                evidence["storage"]["status"] = "active"
                conn.execute(
                    """
                    UPDATE news_items
                    SET local_event_id = ?, rank_score = ?, evidence_json = ?
                    WHERE id = ?
                    """,
                    (local_event_id, item_rank, json_dumps(evidence), item_id),
                )
            except Exception as exc:
                evidence["local_event"] = {
                    "error": f"local_event_upsert_failed: {type(exc).__name__}: {exc}"
                }
                conn.execute(
                    """
                    UPDATE news_items
                    SET evidence_json = ?
                    WHERE id = ?
                    """,
                    (json_dumps(evidence), item_id),
                )

        return

    item_id = int(existing["id"])
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
            item_id,
        ),
    )
    if str(source.get("scope") or "").upper() == "LOCAL":
        try:
            local_event_id, local_event = _upsert_local_event(
                conn,
                source_id=source_id,
                source=source,
                item=item,
                item_id=item_id,
                seen_at=seen_at,
                ranking=ranking,
                retention_days=retention_days,
            )
            ranking = apply_local_event_ranking_adjustments(
                ranking,
                source_family=source.get("source_family"),
                local_event=local_event,
            )
            evidence["ranking"] = ranking
            item_rank = int(ranking["score"])
            evidence["local_event"] = local_event
            conn.execute(
                """
                UPDATE news_items
                SET local_event_id = ?, rank_score = ?, evidence_json = ?
                WHERE id = ?
                """,
                (local_event_id, item_rank, json_dumps(evidence), item_id),
            )
        except Exception as exc:
            evidence["local_event"] = {
                "error": f"local_event_upsert_failed: {type(exc).__name__}: {exc}"
            }
            conn.execute(
                """
                UPDATE news_items
                SET evidence_json = ?
                WHERE id = ?
                """,
                (json_dumps(evidence), item_id),
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


def _latest_health_state_for_rank(conn: sqlite3.Connection, source_id: int) -> str | None:
    row = conn.execute(
        """
        SELECT state, stale_after
        FROM news_source_health
        WHERE source_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (source_id,),
    ).fetchone()
    if row is None or not row["state"]:
        return None
    state = str(row["state"]).strip().lower()
    stale_after = row["stale_after"]
    if stale_after:
        try:
            stale_at = datetime.fromisoformat(str(stale_after))
        except ValueError:
            stale_at = None
        if stale_at and stale_at.astimezone(UTC) < datetime.now(UTC):
            return "stale"
    return state


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
            evidence.get("cluster_key") or cluster_key(str(row["title"]), str(row["url_hash"]))
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

    conn.execute(
        """
        DELETE FROM news_clusters
        WHERE representative_item_id IN (
            SELECT id
            FROM news_items
            WHERE expires_at < ?
        )
        """,
        (cutoffs["items_before"],),
    )
    deleted_items = conn.execute(
        "DELETE FROM news_items WHERE expires_at < ?",
        (cutoffs["items_before"],),
    ).rowcount
    deleted_local_events = conn.execute(
        "DELETE FROM local_events WHERE expires_at < ?",
        (cutoffs["local_events_before"],),
    ).rowcount
    deleted_fetch_runs = conn.execute(
        "DELETE FROM news_fetch_runs WHERE started_at < ?",
        (cutoffs["fetch_runs_before"],),
    ).rowcount
    deleted_health = conn.execute(
        "DELETE FROM news_source_health WHERE observed_at < ?",
        (cutoffs["source_health_before"],),
    ).rowcount
    conn.execute(
        """
        UPDATE news_items
        SET local_event_id = NULL
        WHERE local_event_id IS NOT NULL
          AND local_event_id NOT IN (SELECT id FROM local_events)
        """
    )
    return {
        "items": int(deleted_items or 0),
        "fetch_runs": int(deleted_fetch_runs or 0),
        "source_health": int(deleted_health or 0),
        "local_events": int(deleted_local_events or 0),
    }
