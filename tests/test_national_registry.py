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
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_storage_summary


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


def test_national_source_inventory_is_disabled_and_complete():
    entries = list_national_source_registry()
    keys = {entry["source_key"] for entry in entries}
    summary = national_source_registry_summary()

    assert len(entries) == len(keys) == 227
    assert all(entry["scope"] == "NATIONAL" and entry["enabled"] is False for entry in entries)
    assert summary["source_count"] == 227
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
    assert source["url"] == "https://api.weather.gov/alerts/active"
    assert source["parser"] == "nws_alerts_json"
    assert source["source_class"] == "official_weather_hazard"
    assert source["verification_status"] == "official_page_seen"


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
        tmp_path / "config.yml", "paths: {repo_roots: [], explicit_repos: []}"
    )
    assert run_news_scan(config_path)["status"] == "disabled"
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT scope FROM news_source_registry WHERE source_key = ? ORDER BY scope",
            ("nws_active_alerts_api",),
        ).fetchall()
        national_count = conn.execute(
            "SELECT COUNT(*) AS count FROM news_source_registry WHERE scope = 'NATIONAL'"
        ).fetchone()["count"]
        summary = get_news_storage_summary(conn, config)

    assert [str(row["scope"]) for row in rows] == ["LOCAL", "NATIONAL"]
    assert national_count == 227
    assert summary["national_registry"]["source_count"] == 227


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
