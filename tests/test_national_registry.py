from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import ConfigError, iter_news_sources, load_config
from console1701.db import connect_db, init_db
from console1701.news.national_registry import (
    get_national_source_registry_entry,
    list_national_source_registry,
    national_source_registry_summary,
)
from console1701.news.parsers import NWS_NATIONAL_SEVERE_ALERTS_URL
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_sources_status, get_news_storage_summary


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


def test_national_source_inventory_is_disabled_and_complete():
    entries = list_national_source_registry()
    keys = {entry["source_key"] for entry in entries}
    summary = national_source_registry_summary()

    assert len(entries) == len(keys) == 232
    assert all(entry["scope"] == "NATIONAL" and entry["enabled"] is False for entry in entries)
    assert summary["source_count"] == 232
    assert summary["enabled_by_default"] is False
    nws = get_national_source_registry_entry("nws_active_alerts_api")
    usgs = get_national_source_registry_entry("usgs_eq_geojson")
    assert nws is not None and nws["parser"] == "nws_alerts_json"
    assert usgs is not None and usgs["parser"] == "usgs_earthquake_geojson"


def test_national_registry_defaults_seed_minimal_config(tmp_path):
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            """
            news:
              scopes:
                NATIONAL:
                  sources:
                    - id: nws_active_alerts_api
            """,
        )
    )
    source = iter_news_sources(config)[0]

    assert source["scope"] == "NATIONAL"
    assert source["enabled"] is False
    assert source["url"] == NWS_NATIONAL_SEVERE_ALERTS_URL
    assert source["parser"] == "nws_alerts_json"
    assert source["source_class"] == "official_weather_hazard"
    assert source["verification_status"] == "verified"


def test_national_registry_metadata_rejects_unknown_enum(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        """
        news:
          scopes:
            NATIONAL:
              sources:
                - {id: nws_active_alerts_api, source_class: invented_class}
        """,
    )
    with pytest.raises(ConfigError, match="source_class must be one of"):
        load_config(config_path)


def test_national_registry_persists_with_overlapping_scope_keys(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        """
        paths: {repo_roots: [], explicit_repos: []}
        news:
          scopes:
            LOCAL:
              sources:
                - id: nws_active_alerts_api
            NATIONAL:
              sources:
                - id: nws_active_alerts_api
        """,
    )
    assert run_news_scan(config_path)["status"] == "disabled"
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT scope FROM news_source_registry WHERE source_key = ? ORDER BY scope",
            ("nws_active_alerts_api",),
        ).fetchall()
        configured_rows = conn.execute(
            "SELECT id, scope FROM news_sources WHERE source_key = ? ORDER BY scope",
            ("nws_active_alerts_api",),
        ).fetchall()
        national_count = conn.execute(
            "SELECT COUNT(*) AS count FROM news_source_registry WHERE scope = 'NATIONAL'"
        ).fetchone()["count"]
        source_statuses = get_news_sources_status(conn, config)
        summary = get_news_storage_summary(conn, config)

    assert [str(row["scope"]) for row in rows] == ["LOCAL", "NATIONAL", "REGIONAL"]
    assert [str(row["scope"]) for row in configured_rows] == ["LOCAL", "NATIONAL"]
    assert configured_rows[0]["id"] != configured_rows[1]["id"]
    assert {(row["scope"], row["source_key"]) for row in source_statuses} == {
        ("LOCAL", "nws_active_alerts_api"),
        ("NATIONAL", "nws_active_alerts_api"),
    }
    assert all(row["stored"] is not None for row in source_statuses)
    assert national_count == 232
    assert summary["national_registry"]["source_count"] == 232


def test_same_source_key_ingests_independent_local_and_national_fixtures(tmp_path):
    fixture = Path(__file__).resolve().parent / "fixtures/news/national_nws_alerts.json"
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - {{id: nws_active_alerts_api, enabled: true, url: 'file://{fixture}'}}
            NATIONAL:
              enabled: true
              sources:
                - {{id: nws_active_alerts_api, enabled: true, url: 'file://{fixture}'}}
        """,
    )
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            """
            SELECT s.scope, s.id, COUNT(i.id) AS item_count, COUNT(DISTINCT r.id) AS fetch_count
            FROM news_sources s
            LEFT JOIN news_items i ON i.source_id = s.id
            LEFT JOIN news_fetch_runs r ON r.source_id = s.id
            WHERE s.source_key = 'nws_active_alerts_api'
            GROUP BY s.scope, s.id ORDER BY s.scope
            """
        ).fetchall()

    assert result["status"] == "complete"
    assert [row["scope"] for row in rows] == ["LOCAL", "NATIONAL"]
    assert rows[0]["id"] != rows[1]["id"]
    assert all(row["fetch_count"] == 1 and row["item_count"] >= 1 for row in rows)


def test_api_key_sources_require_local_auth_before_any_ingest(tmp_path, monkeypatch):
    config_path = _write_config(
        tmp_path / "config.yml",
        """
        paths: {repo_roots: [], explicit_repos: []}
        national: {enabled: true}
        news:
          enabled: true
          scopes:
            NATIONAL:
              enabled: true
              sources:
                - {id: congress_api, enabled: true, url: 'file:///tmp/congress.json'}
                - {id: bea_developers, enabled: true, url: 'file:///tmp/bea.json'}
                - {id: fred_api_docs, enabled: true, url: 'file:///tmp/fred.json'}
                - {id: airnow_api_docs, enabled: true, url: 'file:///tmp/airnow.json'}
                - {id: custom_keyed, name: Custom keyed source, kind: local_file_json,
                   enabled: true, url: 'file:///tmp/custom.json', auth: {api_key: ''}}
        """,
    )

    def unexpected_access(*_args, **_kwargs):
        raise AssertionError("Auth-required source attempted fixture or network access")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        statuses = get_news_sources_status(conn, config)
        fetch_states = {
            str(row["status"])
            for row in conn.execute("SELECT status FROM news_fetch_runs").fetchall()
        }
        item_count = conn.execute("SELECT COUNT(*) AS count FROM news_items").fetchone()["count"]

    assert result["status"] == "partial"
    assert result["scanned_sources"] == 5
    assert len(result["errors"]) == 5
    assert {status["health_state"] for status in statuses} == {"auth_required"}
    assert all(status["policy"]["auth_required"] for status in statuses)
    assert all(not status["policy"]["auth_configured"] for status in statuses)
    assert fetch_states == {"auth_required"}
    assert item_count == 0


def test_existing_source_registry_migrates_to_scoped_unique_key(tmp_path):
    schema = files("console1701").joinpath("schema.sql").read_text(encoding="utf-8")
    old_schema = schema.replace(
        "source_key TEXT NOT NULL,\n  scope TEXT NOT NULL,\n  source_name TEXT NOT NULL",
        "source_key TEXT NOT NULL UNIQUE,\n  scope TEXT NOT NULL,\n  source_name TEXT NOT NULL",
        1,
    ).replace(
        "  updated_at TEXT NOT NULL,\n  UNIQUE(scope, source_key)\n",
        "  updated_at TEXT NOT NULL\n",
        1,
    )
    with connect_db(tmp_path / "legacy.sqlite") as conn:
        conn.executescript(old_schema)
        conn.execute(
            """
            INSERT INTO news_source_registry (
              source_key, scope, source_name, source_family, source_class, adapter,
              kind, raw_url, priority, interval_minutes, official_status, privacy_risk,
              policy_risk, parser_risk, retention_sensitivity, verification_status,
              future_phase, expected_access_kind, last_synced_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "nws_active_alerts_api", "LOCAL", "Legacy NWS", "nws",
                "official_weather_hazard", "official_api_json", "api_json",
                "https://api.weather.gov/alerts/active?area=WA", 95, 10, "official",
                "low", "low", "medium", "medium", "verified", "L6",
                "official API", "2026-10-15", "2026-10-15", "2026-10-15",
            ),
        )
        init_db(conn)
        conn.execute(
            """INSERT INTO news_source_registry
               (source_key, scope, source_name, source_family, source_class, adapter,
                kind, raw_url, priority, interval_minutes, official_status, privacy_risk,
                policy_risk, parser_risk, retention_sensitivity, verification_status,
                future_phase, expected_access_kind, last_synced_at, created_at, updated_at)
               SELECT source_key, 'NATIONAL', source_name, source_family, source_class,
                      adapter, kind, raw_url, priority, interval_minutes, official_status,
                      privacy_risk, policy_risk, parser_risk, retention_sensitivity,
                      verification_status, future_phase, expected_access_kind,
                      last_synced_at, created_at, updated_at
               FROM news_source_registry WHERE scope = 'LOCAL'"""
        )
        rows = conn.execute(
            "SELECT scope, source_name FROM news_source_registry WHERE source_key = ? "
            "ORDER BY scope",
            ("nws_active_alerts_api",),
        ).fetchall()

    assert [(row["scope"], row["source_name"]) for row in rows] == [
        ("LOCAL", "Legacy NWS"),
        ("NATIONAL", "Legacy NWS"),
    ]


def test_existing_configured_source_migrates_without_losing_child_rows(tmp_path):
    schema = files("console1701").joinpath("schema.sql").read_text(encoding="utf-8")
    old_schema = schema.replace(
        "source_key TEXT NOT NULL,\n  scope TEXT NOT NULL,\n  name TEXT NOT NULL",
        "source_key TEXT NOT NULL UNIQUE,\n  scope TEXT NOT NULL,\n  name TEXT NOT NULL",
        1,
    ).replace(
        "  updated_at TEXT NOT NULL,\n  UNIQUE(scope, source_key)\n);\n\n"
        "CREATE TABLE IF NOT EXISTS news_fetch_runs",
        "  updated_at TEXT NOT NULL\n);\n\nCREATE TABLE IF NOT EXISTS news_fetch_runs",
        1,
    )
    with connect_db(tmp_path / "legacy-source.sqlite") as conn:
        conn.executescript(old_schema)
        source_id = conn.execute(
            """
            INSERT INTO news_sources
              (source_key, scope, name, kind, config_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "nws_active_alerts_api", "LOCAL", "Legacy NWS", "api_json", "legacy",
                "2026-10-15", "2026-10-15",
            ),
        ).lastrowid
        conn.execute(
            "INSERT INTO news_fetch_runs (source_id, started_at, status) VALUES (?, ?, ?)",
            (source_id, "2026-10-15", "success"),
        )
        conn.execute(
            """
            INSERT INTO news_items
              (source_id, scope, url, url_hash, title, first_seen_at, last_seen_at,
               expires_at, source_kind)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id, "LOCAL", "https://api.weather.gov/alerts/legacy", "legacy-hash",
                "Legacy alert", "2026-10-15", "2026-10-15", "2026-10-16", "api_json",
            ),
        )
        init_db(conn)
        conn.execute(
            """
            INSERT INTO news_sources
              (source_key, scope, name, kind, config_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "nws_active_alerts_api", "NATIONAL", "National NWS", "api_json",
                "national", "2026-10-15", "2026-10-15",
            ),
        )
        sources = conn.execute(
            "SELECT id, scope FROM news_sources WHERE source_key = ? ORDER BY scope",
            ("nws_active_alerts_api",),
        ).fetchall()
        fetch_source_id = conn.execute("SELECT source_id FROM news_fetch_runs").fetchone()[0]
        item_source_id = conn.execute("SELECT source_id FROM news_items").fetchone()[0]
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        foreign_keys_enabled = conn.execute("PRAGMA foreign_keys").fetchone()[0]

    assert [row["scope"] for row in sources] == ["LOCAL", "NATIONAL"]
    assert sources[0]["id"] == source_id == fetch_source_id == item_source_id
    assert sources[1]["id"] != source_id
    assert violations == []
    assert foreign_keys_enabled == 1
