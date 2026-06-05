from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from console1701.config import iter_news_sources, load_config
from console1701.news.regional_registry import (
    get_regional_source_registry_entry,
    list_regional_source_registry,
    regional_registry_config_defaults,
    regional_source_registry_summary,
)


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


def test_regional_source_registry_is_disabled_and_validated():
    entries = list_regional_source_registry()
    keys = {entry["source_key"] for entry in entries}
    summary = regional_source_registry_summary()

    assert "nws_active_alerts_wa" in keys
    assert "wsdot_traveler_api" in keys
    assert "usgs_eq_geojson" in keys
    assert len(keys) == len(entries)
    assert all(entry["scope"] == "REGIONAL" for entry in entries)
    assert all(entry["enabled"] is False for entry in entries)
    assert summary["enabled_by_default"] is False
    assert summary["source_count"] == len(entries)
    assert summary["source_class_counts"]["official_transport"] >= 1
    assert summary["verification_status_counts"]["official_page_seen"] >= 1


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
    assert source["verification_status"] == "official_page_seen"
    assert source["official_status"] == "official"
    assert source["future_phase"] == "R1"
    assert source["expected_access_kind"] == "official JSON API"

