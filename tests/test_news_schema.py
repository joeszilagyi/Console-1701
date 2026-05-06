from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, init_db, json_dumps
from console1701.news.storage import (
    get_news_scope_states,
    get_news_storage_summary,
    list_news_sources,
)


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


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
    }.issubset(_table_names(conn))
    assert {
        "idx_news_sources_scope_enabled",
        "idx_news_fetch_runs_source_started",
        "idx_news_items_scope_seen",
        "idx_news_items_source_seen",
        "idx_news_items_expires_at",
        "idx_news_items_url_hash",
        "idx_news_items_rank_scope",
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
