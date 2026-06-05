from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, init_db, json_dumps
from console1701.news.scanner import run_news_scan
from console1701.news.storage import (
    get_news_scope_states,
    get_news_sources_status,
    get_news_storage_summary,
    list_news_sources,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "news"


def _file_url(path: Path) -> str:
    return f"file://{path.resolve()}"


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


def _insert_news_source(
    conn,
    source_key: str,
    *,
    scope: str,
    name: str,
    kind: str = "local_file_json",
    url: str | None = None,
    enabled: bool = True,
) -> int:
    row = conn.execute(
        """
        INSERT INTO news_sources (
          source_key, scope, name, kind, url, homepage_url, enabled, config_hash,
          priority, tags_json, policy_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_key,
            scope,
            name,
            kind,
            url,
            None,
            1 if enabled else 0,
            "manual-test",
            50,
            json_dumps(["fixture"]),
            json_dumps({"basis": "test"}),
            "2026-06-01T12:00:00+00:00",
            "2026-06-01T12:00:00+00:00",
        ),
    )
    conn.commit()
    return int(row.lastrowid)


def _insert_news_source_health(
    conn,
    source_id: int,
    *,
    observed_at: str,
    state: str,
    stale_after: str | None = None,
    last_success_at: str | None = None,
    last_failure_at: str | None = None,
    message: str | None = None,
    consecutive_failures: int = 0,
) -> None:
    conn.execute(
        """
        INSERT INTO news_source_health (
          source_id, observed_at, state, last_success_at, last_failure_at,
          consecutive_failures, stale_after, message, evidence_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}')
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
        ),
    )
    conn.commit()


def _table_names(conn):
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchall()
    return {row["name"] for row in rows}


def _index_names(conn):
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'index'
        """
    ).fetchall()
    return {row["name"] for row in rows}


def _column_names(conn, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def test_news_schema_creates_metadata_tables_and_indexes(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)

    assert {
        "news_sources",
        "news_fetch_runs",
        "news_items",
        "news_clusters",
        "news_source_health",
        "local_events",
    }.issubset(_table_names(conn))
    assert {
        "idx_news_sources_scope_enabled",
        "idx_news_fetch_runs_source_started",
        "idx_news_items_scope_seen",
        "idx_news_items_source_seen",
        "idx_news_items_expires_at",
        "idx_news_items_url_hash",
        "idx_news_items_rank_scope",
        "idx_local_events_scope_time",
        "idx_local_events_key",
        "idx_local_events_expires_at",
        "idx_news_clusters_scope_score",
        "idx_news_source_health_source_observed",
        "idx_news_source_health_state",
    }.issubset(_index_names(conn))


def test_news_items_schema_does_not_store_full_article_bodies(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    columns = _column_names(conn, "news_items")

    assert "description" in columns
    assert "content_hash" in columns
    assert "local_event_id" in columns
    assert "body" not in columns
    assert "article_body" not in columns
    assert "full_text" not in columns
    assert "html" not in columns
    assert "raw_payload" not in columns
    assert "raw_payload_json" not in columns


def test_news_storage_round_trip_decodes_json_fields(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    conn.execute(
        """
        INSERT INTO news_sources (
          source_key, scope, name, kind, url, homepage_url, enabled, config_hash,
          priority, tags_json, policy_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "local_fixture",
            "LOCAL",
            "Local fixture",
            "local_file_json",
            "file://./tests/fixtures/news/local.json",
            None,
            0,
            "hash",
            10,
            json_dumps(["fixture"]),
            json_dumps({"basis": "local_file"}),
            "2026-05-05T12:00:00-07:00",
            "2026-05-05T12:00:00-07:00",
        ),
    )
    conn.commit()

    sources = list_news_sources(conn)

    assert sources[0]["source_key"] == "local_fixture"
    assert sources[0]["tags"] == ["fixture"]
    assert sources[0]["policy"] == {"basis": "local_file"}


def test_news_storage_summary_reports_disabled_defaults(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            "paths: {repo_roots: [], explicit_repos: []}",
        )
    )

    summary = get_news_storage_summary(conn, config)

    assert summary["enabled"] is False
    assert summary["configured_source_count"] == 0
    assert summary["stored_source_count"] == 0
    assert summary["scope_states"]["LOCAL"]["state"] == "disabled"


def test_news_scope_states_distinguish_not_configured_and_configured_disabled(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    not_configured = load_config(
        _write_config(
            tmp_path / "not-configured.yml",
            """
            news:
              enabled: true
            """,
        )
    )
    configured_disabled = load_config(
        _write_config(
            tmp_path / "configured-disabled.yml",
            """
            news:
              enabled: true
              scopes:
                LOCAL:
                  sources:
                    - id: local_fixture
                      name: Local fixture
                      kind: local_file_json
            """,
        )
    )

    assert get_news_scope_states(conn, not_configured)["LOCAL"]["state"] == "not_configured"
    configured_disabled_state = get_news_scope_states(conn, configured_disabled)["LOCAL"]

    assert configured_disabled_state["state"] == "configured_disabled"


def test_news_scope_states_report_enabled_source_never_run(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            """
            news:
              enabled: true
              scopes:
                LOCAL:
                  sources:
                    - id: local_fixture
                      name: Local fixture
                      kind: local_file_json
                      enabled: true
            """,
        )
    )

    state = get_news_scope_states(conn, config)["LOCAL"]

    assert state["state"] == "configured_never_run"
    assert state["enabled_source_count"] == 1


def test_news_scope_states_report_stale_source_state_when_health_is_stale(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
            news:
              enabled: true
              scopes:
                LOCAL:
                  enabled: true
                  sources:
                    - id: local_fixture
                      name: Local fixture
                      kind: local_file_json
                      enabled: true
                      url: "{_file_url(FIXTURE_DIR / "local_items.json")}"
            """,
    )
    run_news_scan(config_path)
    config = load_config(config_path)

    with connect_db(config["_db_path"]) as handle:
        init_db(handle)
        source_id = int(
            handle.execute(
                "SELECT id FROM news_sources WHERE source_key = 'local_fixture'"
            ).fetchone()["id"]
        )
        stale_before = datetime(2020, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat()
        handle.execute(
            """
            INSERT INTO news_source_health (
              source_id, observed_at, state, last_success_at, last_failure_at,
              consecutive_failures, stale_after, message, evidence_json
            )
            VALUES (?, ?, 'healthy', ?, NULL, 0, ?, 'forced stale for test', '{}')
            """,
            (
                source_id,
                stale_before,
                stale_before,
                stale_before,
            ),
        )
        handle.commit()
        states = get_news_scope_states(handle, config)
        summary = get_news_storage_summary(handle, config)

    assert states["LOCAL"]["state"] == "stale"
    assert states["LOCAL"]["source_state_counts"].get("stale") == 1
    assert summary["stale_source_count"] == 1


def test_news_scope_states_report_failing_state_for_parser_failed_source(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: local_fixture
                  name: Local fixture
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_items.json")}"
                - id: bad_rss
                  name: Bad RSS
                  enabled: true
                  kind: local_file_rss
                  url: "{_file_url(FIXTURE_DIR / "malformed.rss")}"
        """,
    )
    run_news_scan(config_path)
    config = load_config(config_path)

    with connect_db(config["_db_path"]) as handle:
        init_db(handle)
        scope_states = get_news_scope_states(handle, config)
        summary = get_news_storage_summary(handle, config)

    assert scope_states["LOCAL"]["state"] == "failing"
    assert scope_states["LOCAL"]["source_state_counts"].get("parser_failed") == 1
    assert scope_states["LOCAL"]["source_state_counts"].get("healthy") == 1
    assert summary["failing_source_count"] == 1


def test_news_scope_states_report_social_source_blocked_when_social_disabled(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    config = {
        "news": {
            "enabled": True,
            "scopes": {
                "LOCAL": {
                    "enabled": True,
                    "sources": [
                        {
                            "id": "social_candidate_fixture",
                            "name": "Local social candidate fixture",
                            "scope": "LOCAL",
                            "kind": "local_file_json",
                            "enabled": True,
                            "url": "file:///tmp/social.json",
                            "source_class": "social_candidate",
                            "source_family": "bluesky",
                        },
                    ],
                },
            },
        },
        "local": {
            "allow_social_sources": False,
        },
    }

    scope_states = get_news_scope_states(conn, config)
    source_statuses = get_news_sources_status(conn, config)

    assert scope_states["LOCAL"]["state"] == "failing"
    assert scope_states["LOCAL"]["source_state_counts"].get("social_disabled") == 1
    assert source_statuses[0]["health_state"] == "social_disabled"
    assert (
        source_statuses[0]["health_message"]
        == "LOCAL social source is blocked until local.allow_social_sources is enabled."
    )


def test_news_scope_states_report_homepage_extraction_disabled(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    config = {
        "news": {
            "enabled": True,
            "fetch_policy": {
                "allow_homepage_extractors": False,
            },
            "scopes": {
                "LOCAL": {
                    "enabled": True,
                    "sources": [
                        {
                            "id": "homepage_fixture",
                            "name": "Local homepage fixture",
                            "scope": "LOCAL",
                            "kind": "homepage_headlines",
                            "enabled": True,
                            "url": "file:///tmp/homepage.json",
                        },
                    ],
                },
            },
        },
        "local": {},
    }
    scope_states = get_news_scope_states(conn, config)

    assert scope_states["LOCAL"]["state"] == "failing"
    assert scope_states["LOCAL"]["source_state_counts"].get("homepage_disabled") == 1

    source_statuses = get_news_sources_status(conn, config)
    assert source_statuses[0]["health_state"] == "homepage_disabled"
    assert source_statuses[0]["health_message"] == "Homepage extraction is disabled by config."


def test_news_system_scope_matrix_reports_stale_and_failing_states(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    stale_at = datetime(2020, 1, 1, tzinfo=UTC).isoformat()
    fail_at = datetime(2026, 5, 1, tzinfo=UTC).isoformat()

    local_stale_source_id = _insert_news_source(
        conn,
        "local_stale_fixture",
        scope="LOCAL",
        name="Local stale fixture",
        url="file:///tmp/local-stale.json",
        enabled=True,
    )
    regional_failing_source_id = _insert_news_source(
        conn,
        "regional_parser_fail",
        scope="REGIONAL",
        name="Regional parser fail fixture",
        kind="local_file_json",
        url="file:///tmp/regional-bad.json",
        enabled=True,
    )

    _insert_news_source_health(
        conn,
        local_stale_source_id,
        observed_at=stale_at,
        state="healthy",
        stale_after=stale_at,
        last_success_at=stale_at,
        message="forced stale test",
    )
    _insert_news_source_health(
        conn,
        regional_failing_source_id,
        observed_at=fail_at,
        state="parser_failed",
        last_failure_at=fail_at,
        message="forced parser failure test",
        consecutive_failures=2,
    )

    summary = get_news_storage_summary(
        conn,
        {
            "news": {
                "enabled": True,
                "scopes": {
                    "LOCAL": {
                        "enabled": True,
                        "sources": [
                            {
                                "id": "local_stale_fixture",
                                "scope": "LOCAL",
                                "name": "Local stale fixture",
                                "kind": "local_file_json",
                                "enabled": True,
                                "url": "file:///tmp/local-stale.json",
                            }
                        ],
                    },
                    "REGIONAL": {
                        "enabled": True,
                        "sources": [
                            {
                                "id": "regional_parser_fail",
                                "scope": "REGIONAL",
                                "name": "Regional parser fail fixture",
                                "kind": "local_file_json",
                                "enabled": True,
                                "url": "file:///tmp/regional-bad.json",
                            }
                        ],
                    },
                    "NATIONAL": {"enabled": True, "sources": []},
                    "GLOBAL": {"enabled": True, "sources": []},
                    "ORBITAL": {"enabled": False, "sources": []},
                },
            },
        },
    )

    assert summary["scope_states"]["LOCAL"]["state"] == "stale"
    assert summary["scope_states"]["REGIONAL"]["state"] == "failing"
    assert summary["scope_states"]["NATIONAL"]["state"] == "not_configured"
    assert summary["scope_states"]["GLOBAL"]["state"] == "not_configured"
    assert summary["scope_states"]["ORBITAL"]["state"] == "not_configured"
    assert summary["source_state_counts"]["stale"] == 1
    assert summary["source_state_counts"]["parser_failed"] == 1
    assert summary["stale_source_count"] == 1
