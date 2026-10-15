from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import ConfigError, iter_news_sources, load_config
from console1701.db import connect_db, init_db
from console1701.news.local_registry import (
    get_local_source_registry_entry,
    list_local_source_registry,
    local_registry_config_defaults,
    local_source_registry_summary,
)
from console1701.news.scanner import run_news_scan
from console1701.news.storage import (
    get_local_registry_state,
    get_news_sources_status,
    get_news_storage_summary,
)


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


def test_local_source_registry_is_disabled_and_validated():
    entries = list_local_source_registry()
    keys = {entry["source_key"] for entry in entries}
    summary = local_source_registry_summary()
    design = json.loads(
        (Path(__file__).parents[1] / "console1701/news/local_registry.json").read_text()
    )

    assert len(entries) == 119
    assert keys == {row["source_key"] for row in design}
    assert "sfd_fire_911_dataset" in keys
    assert "alertseattle_feed" in keys
    assert "nws_active_alerts_api" in keys
    assert "west_seattle_blog_feed" in keys
    assert "reddit_seattle" in keys
    assert len(keys) == len(entries)
    assert all(entry["scope"] == "LOCAL" for entry in entries)
    assert all(entry["enabled"] is False for entry in entries)
    assert summary["enabled_by_default"] is False
    assert summary["source_count"] == len(entries)
    assert summary["source_class_counts"]["official_transport"] >= 2
    assert summary["verification_status_counts"]["candidate_needs_verification"] >= 1


def test_local_registry_design_rows_preserve_metadata_without_enabling_ingest():
    design = json.loads(
        (Path(__file__).parents[1] / "console1701/news/local_registry.json").read_text()
    )
    rows = {row["source_key"]: row for row in design}
    reviewed_overrides = {
        "sfd_fire_911_dataset", "alertseattle_feed", "metro_service_advisories_rss",
        "wsdot_traffic_api", "nws_active_alerts_api", "usgs_earthquake_geojson",
        "city_light_outages_home", "faa_airport_status_sea", "west_seattle_blog_feed",
        "reddit_seattle",
    }
    for key, row in rows.items():
        if key in reviewed_overrides:
            continue
        entry = get_local_source_registry_entry(key)
        assert entry is not None
        for field in (
            "source_name", "source_family", "source_class", "adapter", "raw_url",
            "official_status", "privacy_risk", "policy_risk", "parser_risk",
            "retention_sensitivity", "verification_status", "future_phase",
            "why_it_matters", "expected_access_kind",
        ):
            assert entry[field] == row[field], (key, field)
        assert entry["priority"] == int(row["priority"])
    for key in (
        "seattle_em_alert_signup", "spd_arcgis_dashboard",
        "seattle_open_data_home", "seattle_traffic_cameras_arcgis_api",
    ):
        entry = get_local_source_registry_entry(key)
        row = rows[key]
        assert entry is not None
        assert entry["enabled"] is False
        assert entry["scope"] == "LOCAL"
        assert entry["raw_url"] == row["raw_url"]
        assert entry["source_family"] == row["source_family"]
        assert entry["source_class"] == row["source_class"]
        assert entry["adapter"] == row["adapter"]
        assert entry["verification_status"] == row["verification_status"]
        assert entry["future_phase"] == row["future_phase"]
    assert get_local_source_registry_entry("spd_arcgis_dashboard")["kind"] == "reference_only"
    assert get_local_source_registry_entry("seattle_em_alert_signup")["kind"] == "reference_only"
    assert get_local_source_registry_entry("city_light_outages_home")["kind"] == "reference_only"
    assert get_local_source_registry_entry("faa_airport_status_sea")["kind"] == "reference_only"


def test_local_reference_sources_cannot_ingest_when_configured(tmp_path, monkeypatch):
    def unexpected_access(*args, **kwargs):
        raise AssertionError("LOCAL reference source attempted fixture or HTTP access")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)
    config_path = _write_config(tmp_path / "references.yml", """
        paths: {repo_roots: [], explicit_repos: []}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - {id: city_light_outages_home, enabled: true, url: 'file:///missing.html'}
                - {id: faa_airport_status_sea, enabled: true, url: 'file:///missing.xml'}
    """)
    assert run_news_scan(config_path)["item_count"] == 0
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        states = {
            row["source_key"]: row["health_state"]
            for row in get_news_sources_status(conn, config)
        }
    assert states == {
        "city_light_outages_home": "unsupported",
        "faa_airport_status_sea": "unsupported",
    }


def test_local_registry_defaults_can_seed_minimal_config(tmp_path):
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            """
            news:
              scopes:
                LOCAL:
                  sources:
                    - id: nws_active_alerts_api
            """,
        )
    )

    source = iter_news_sources(config)[0]
    registry_entry = get_local_source_registry_entry("nws_active_alerts_api")
    defaults = local_registry_config_defaults("nws_active_alerts_api")

    assert registry_entry is not None
    assert defaults is not None
    assert source["name"] == "NWS active alerts API"
    assert source["kind"] == "api_json"
    assert source["enabled"] is False
    assert source["priority"] == 95
    assert source["source_family"] == "nws"
    assert source["source_class"] == "official_weather_hazard"
    assert source["adapter"] == "official_api_json"
    assert source["verification_status"] == "verified"
    assert source["official_status"] == "official"
    assert source["future_phase"] == "L6"
    assert source["expected_access_kind"] == "documented official Washington GeoJSON alerts API"
    assert "Official active hazard alerts" in source["evidence_notes"][1]


def test_local_registry_exposes_faa_airport_status_probe_only_defaults():
    source = get_local_source_registry_entry("faa_airport_status_sea")

    assert source is not None
    assert source["verification_status"] == "source_health_probe_only"
    assert source["expected_access_kind"] == "public airport-status page and NAS Status XML"
    assert "machine-readable path" in source["why_it_matters"]


def test_local_registry_exposes_city_light_probe_only_defaults():
    source = get_local_source_registry_entry("city_light_outages_home")

    assert source is not None
    assert source["verification_status"] == "source_health_probe_only"
    assert source["expected_access_kind"] == "public outage page and map web app"
    assert "machine-readable endpoint remains unverified" in source["why_it_matters"]


def test_local_registry_defaults_keep_user_overrides(tmp_path):
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            """
            news:
              scopes:
                LOCAL:
                  sources:
                    - id: alertseattle_feed
                      name: Custom AlertSeattle
                      priority: 42
                      tags: [custom]
            """,
        )
    )

    source = iter_news_sources(config)[0]

    assert source["name"] == "Custom AlertSeattle"
    assert source["priority"] == 42
    assert source["tags"] == ["custom"]
    assert source["kind"] == "rss"
    assert source["source_class"] == "official_alert"


def test_local_registry_social_source_still_requires_explicit_allowance(tmp_path):
    with pytest.raises(ConfigError, match="local.allow_social_sources true"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  scopes:
                    LOCAL:
                      sources:
                        - id: reddit_seattle
                """,
            )
        )


def test_local_registry_neighborhood_blog_still_requires_explicit_allowance(tmp_path):
    with pytest.raises(ConfigError, match="local.allow_neighborhood_blogs true"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  scopes:
                    LOCAL:
                      sources:
                        - id: west_seattle_blog_feed
                """,
            )
        )


def test_news_summary_exposes_local_registry_counts(tmp_path):
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            "paths: {repo_roots: [], explicit_repos: []}",
        )
    )
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)

    summary = get_news_storage_summary(conn, config)

    assert summary["local_registry"]["scope"] == "LOCAL"
    assert summary["local_registry"]["enabled_by_default"] is False
    assert summary["local_registry"]["source_count"] == 119


def test_local_registry_is_persisted_in_sqlite_news_scan(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        "paths: {repo_roots: [], explicit_repos: []}",
    )
    result = run_news_scan(config_path)
    config = load_config(config_path)

    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        registry_rows = conn.execute(
            "SELECT source_key, enabled_by_default, source_family FROM news_source_registry"
        ).fetchall()
        local_count = conn.execute(
            "SELECT COUNT(*) FROM news_source_registry WHERE scope = 'LOCAL'"
        ).fetchone()[0]
        registry_state = get_local_registry_state(conn)

    assert result["status"] == "disabled"
    assert len(registry_rows) >= len(list_local_source_registry())
    assert local_count == 119
    by_key = {str(row["source_key"]): row for row in registry_rows}
    nws_row = by_key.get("nws_active_alerts_api")

    assert nws_row is not None
    assert int(nws_row["enabled_by_default"]) == 0
    assert str(nws_row["source_family"]) == "nws"
    assert registry_state["enabled_by_default"] is False
    assert registry_state["source_count"] >= len(list_local_source_registry())
