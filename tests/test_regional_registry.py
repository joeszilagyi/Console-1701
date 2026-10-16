from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from console1701.config import iter_news_sources, load_config
from console1701.db import connect_db, init_db
from console1701.news.regional_registry import (
    get_regional_source_registry_entry,
    list_regional_source_registry,
    regional_registry_config_defaults,
    regional_source_registry_summary,
)
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_sources_status, get_news_storage_summary


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


def test_regional_source_registry_is_disabled_and_validated():
    entries = list_regional_source_registry()
    keys = {entry["source_key"] for entry in entries}
    summary = regional_source_registry_summary()
    design = json.loads(
        (Path(__file__).parents[1] / "console1701/news/regional_registry.json").read_text()
    )
    core_keys = {
        "nws_active_alerts_wa", "wsdot_traveler_api", "wsdot_highway_alerts_rss",
        "usgs_eq_geojson", "king_county_emergency_news", "pierce_road_alert_rss",
        "regional_news_rss", "nifc_imsr_current_wa",
    }

    assert len(design) == 224
    assert len(entries) == 232
    assert keys == {row["source_key"] for row in design} | core_keys
    assert "nws_active_alerts_wa" in keys
    assert "wsdot_traveler_api" in keys
    assert "wsdot_highway_alerts_rss" in keys
    assert "usgs_eq_geojson" in keys
    assert len(keys) == len(entries)
    assert all(entry["scope"] == "REGIONAL" for entry in entries)
    assert all(entry["enabled"] is False for entry in entries)
    assert summary["enabled_by_default"] is False
    assert summary["source_count"] == len(entries)
    assert summary["source_class_counts"]["official_transport"] >= 1
    assert summary["verification_status_counts"]["official_page_seen"] >= 1
    assert get_regional_source_registry_entry("usgs_eq_geojson")["parser"] == (
        "usgs_earthquake_geojson"
    )
    usgs = get_regional_source_registry_entry("usgs_eq_geojson")
    assert usgs["raw_url"].endswith("/summary/2.5_day.geojson")
    assert usgs["verification_status"] == "verified"
    wsdot_rss = get_regional_source_registry_entry("wsdot_highway_alerts_rss")
    assert wsdot_rss["raw_url"] == "https://www.wsdot.wa.gov/traffic/api/HighwayAlerts/rss.aspx"
    assert wsdot_rss["verification_status"] == "verified"
    assert wsdot_rss["enabled"] is False


def test_regional_registry_preserves_all_design_metadata():
    design = json.loads(
        (Path(__file__).parents[1] / "console1701/news/regional_registry.json").read_text()
    )
    for row in design:
        entry = get_regional_source_registry_entry(row["source_key"])
        assert entry is not None
        assert entry["enabled"] is False
        for field in (
            "source_name", "source_family", "source_class", "adapter", "raw_url",
            "official_status", "privacy_risk", "policy_risk", "parser_risk",
            "retention_sensitivity", "verification_status", "future_phase",
            "why_it_matters", "expected_access_kind",
        ):
            assert entry[field] == row[field], (row["source_key"], field)
        assert entry["priority"] == int(row["priority"])
    assert get_regional_source_registry_entry("wa_emd_division")["kind"] == "reference_only"
    assert get_regional_source_registry_entry("nws_api_docs")["kind"] == "reference_only"


def test_regional_reference_sources_cannot_ingest_when_configured(tmp_path, monkeypatch):
    def unexpected_access(*args, **kwargs):
        raise AssertionError("REGIONAL reference source attempted fixture or HTTP access")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)
    config_path = _write_config(tmp_path / "references.yml", """
        paths: {repo_roots: [], explicit_repos: []}
        regional: {enabled: true}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - {id: wa_emd_division, enabled: true, url: 'file:///missing.html'}
                - {id: nws_api_docs, enabled: true, url: 'file:///missing.xml'}
                - {id: wa_dnr_current_wildfire, enabled: true, url: 'file:///missing.json'}
                - {id: pse_outage_center, enabled: true, url: 'file:///missing.html'}
                - {id: snopud_outage_center, enabled: true, url: 'file:///missing.html'}
                - {id: tacoma_power_outages, enabled: true, url: 'file:///missing.html'}
    """)
    assert run_news_scan(config_path)["item_count"] == 0
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        states = {
            row["source_key"]: row["health_state"]
            for row in get_news_sources_status(conn, config)
        }
    assert states == {
        "wa_emd_division": "unsupported",
        "nws_api_docs": "unsupported",
        "wa_dnr_current_wildfire": "unsupported",
        "pse_outage_center": "unsupported",
        "snopud_outage_center": "unsupported",
        "tacoma_power_outages": "unsupported",
    }


def test_regional_registry_defaults_can_seed_minimal_config(tmp_path):
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            """
            news:
              scopes:
                REGIONAL:
                  sources:
                    - id: nws_active_alerts_wa
            """,
        )
    )

    source = iter_news_sources(config)[0]
    registry_entry = get_regional_source_registry_entry("nws_active_alerts_wa")
    defaults = regional_registry_config_defaults("nws_active_alerts_wa")

    assert registry_entry is not None
    assert defaults is not None
    assert source["name"] == "NWS active alerts for Washington"
    assert source["kind"] == "api_json"
    assert source["enabled"] is False
    assert source["priority"] == 100
    assert source["source_family"] == "nws"
    assert source["source_class"] == "official_weather_hazard"
    assert source["adapter"] == "official_api_json"
    assert source["verification_status"] == "verified"
    assert source["official_status"] == "official"
    assert source["future_phase"] == "R1"
    assert source["expected_access_kind"] == "documented official Washington GeoJSON alerts API"


def test_regional_registry_is_persisted_in_sqlite_news_scan(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        """
        paths: {repo_roots: [], explicit_repos: []}
        news:
          scopes:
            REGIONAL:
              sources:
                - id: nws_active_alerts_wa
        """,
    )
    result = run_news_scan(config_path)
    config = load_config(config_path)

    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        registry_rows = conn.execute(
            "SELECT source_key, enabled_by_default, source_family FROM news_source_registry "
            "WHERE scope = 'REGIONAL'"
        ).fetchall()
        storage_summary = get_news_storage_summary(conn, config)

    assert result["status"] == "disabled"
    assert len(registry_rows) == 232
    by_key = {str(row["source_key"]): row for row in registry_rows}
    nws_row = by_key.get("nws_active_alerts_wa")

    assert nws_row is not None
    assert int(nws_row["enabled_by_default"]) == 0
    assert str(nws_row["source_family"]) == "nws"
    assert storage_summary["regional_registry"]["scope"] == "REGIONAL"
    assert storage_summary["regional_registry"]["source_count"] >= len(
        list_regional_source_registry()
    )


def test_regional_registry_scan_replaces_stale_keys(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        """
        paths: {repo_roots: [], explicit_repos: []}
        news:
          scopes:
            REGIONAL:
              sources:
                - id: nws_active_alerts_wa
        """,
    )
    assert run_news_scan(config_path)["status"] == "disabled"
    config = load_config(config_path)

    with connect_db(config["_db_path"]) as conn:
        conn.execute(
            "UPDATE news_source_registry SET source_key = ? WHERE source_key = ?",
            ("obsolete_regional_source", "nws_active_alerts_wa"),
        )

    assert run_news_scan(config_path)["status"] == "disabled"
    with connect_db(config["_db_path"]) as conn:
        keys = {
            str(row["source_key"])
            for row in conn.execute(
                "SELECT source_key FROM news_source_registry WHERE scope = 'REGIONAL'"
            ).fetchall()
        }

    assert keys == {str(entry["source_key"]) for entry in list_regional_source_registry()}
