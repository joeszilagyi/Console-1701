from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import (
    DEFAULT_CONFIG,
    ConfigError,
    iter_news_sources,
    load_config,
    normalize_config,
)
from console1701.db import connect_db
from console1701.news.global_registry import (
    get_global_source_registry_entry,
    global_source_registry_summary,
    list_global_source_registry,
)
from console1701.news.scanner import run_news_scan
from console1701.news.source_policy import evaluate_source_policy
from console1701.news.storage import get_news_sources_status, get_news_storage_summary


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


def test_global_inventory_is_complete_and_disabled():
    entries = list_global_source_registry()
    keys = {str(entry["source_key"]) for entry in entries}
    summary = global_source_registry_summary()

    assert len(entries) == len(keys) == 174
    assert all(entry["scope"] == "GLOBAL" and entry["enabled"] is False for entry in entries)
    assert all(entry["source_health_behavior"] for entry in entries)
    assert summary["source_count"] == 174
    assert summary["enabled_by_default"] is False
    gdacs = get_global_source_registry_entry("gdacs_feed_reference")
    assert gdacs is not None and gdacs["kind"] == "rss"
    assert gdacs["verification_status"] == "official_page_seen"
    bom = get_global_source_registry_entry("wmo_bom_cap_rss")
    assert bom is not None and bom["kind"] == "rss"
    assert bom["enabled"] is False
    assert bom["raw_url"] == (
        "https://severeweather.wmo.int/v2/cap-alerts/au-bom-en/rss.xml"
    )


def test_wmo_dashboard_and_directory_remain_reference_only(tmp_path, monkeypatch):
    for key in ("wmo_sww", "wmo_sources"):
        entry = get_global_source_registry_entry(key)
        assert entry is not None
        assert entry["adapter"] == "source_health_probe_only"
        assert entry["kind"] == "reference_only"
        assert entry["refresh_interval"] == "24 h"

    def unexpected_access(*args, **kwargs):
        raise AssertionError("WMO reference attempted file or HTTP ingest")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)
    config_path = _write_config(tmp_path / "wmo.yml", """
        paths: {repo_roots: [], explicit_repos: []}
        global: {enabled: true}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - {id: wmo_sww, enabled: true, url: 'file:///missing-sww.xml'}
                - {id: wmo_sources, enabled: true, url: 'file:///missing-sources.xml'}
    """)
    result = run_news_scan(config_path)
    assert result["item_count"] == 0
    assert result["scanned_sources"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        states = {
            row["source_key"]: row["health_state"]
            for row in get_news_sources_status(conn, config)
        }
    assert states == {"wmo_sww": "unsupported", "wmo_sources": "unsupported"}


def test_global_registry_seeds_config_and_sqlite_without_fetch(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        """
        paths: {repo_roots: [], explicit_repos: []}
        news:
          scopes:
            GLOBAL:
              sources:
                - id: gdacs_feed_reference
        """,
    )
    config = load_config(config_path)
    source = iter_news_sources(config)[0]
    assert config["global"]["enabled"] is False
    assert source["name"] == "GDACS feed reference"
    assert source["scope"] == "GLOBAL"
    assert source["enabled"] is False
    assert source["source_family"] == "gdacs"

    assert run_news_scan(config_path)["status"] == "disabled"
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT source_key, enabled_by_default FROM news_source_registry "
            "WHERE scope = 'GLOBAL'"
        ).fetchall()
        summary = get_news_storage_summary(conn, config)
    assert len(rows) == 174
    assert all(row["enabled_by_default"] == 0 for row in rows)
    assert summary["global_registry"]["source_count"] == 174


def test_every_global_inventory_entry_can_seed_config_under_explicit_policy_gates():
    for entry in list_global_source_registry():
        config = deepcopy(DEFAULT_CONFIG)
        config["global"].update(
            include_social_sources=True,
            allow_auth_required_sources=True,
            allow_heavy_open_data_sources=True,
            allow_homepage_extractors=True,
        )
        config["news"]["fetch_policy"]["allow_homepage_extractors"] = True
        config["news"]["scopes"]["GLOBAL"]["sources"] = [
            {"id": entry["source_key"], "policy_reviewed": True}
        ]
        normalize_config(config)
        source = iter_news_sources(config)[0]
        assert source["enabled"] is False
        assert source["scope"] == "GLOBAL"


@pytest.mark.parametrize(
    "key,value",
    [
        ("source_family", "invented_family"),
        ("source_class", "invented_class"),
        ("adapter", "invented_adapter"),
        ("verification_status", "invented_status"),
    ],
)
def test_global_source_metadata_rejects_unknown_enums(tmp_path, key, value):
    config_path = _write_config(
        tmp_path / "invalid.yml",
        f"""
        news:
          scopes:
            GLOBAL:
              sources:
                - {{id: gdacs_feed_reference, {key}: {value}}}
        """,
    )
    with pytest.raises(ConfigError, match=key):
        load_config(config_path)


def test_global_config_flags_and_thresholds_are_validated(tmp_path):
    config = load_config(_write_config(tmp_path / "default.yml", "global: {}"))
    assert config["global"]["enabled"] is False
    assert config["global"]["include_disasters"] is True
    assert config["global"]["include_social_sources"] is False
    assert config["global"]["include_global_economy"] is False
    assert config["global"]["earthquake_min_magnitude"] == 6.0
    for invalid in (
        "global: {include_disasters: maybe}",
        "global: {earthquake_min_magnitude: .nan}",
        "global: {gdacs_attention_minimum: purple}",
    ):
        with pytest.raises(ConfigError):
            load_config(_write_config(tmp_path / "invalid.yml", invalid))


def test_global_social_heavy_homepage_gates_remain_visible_in_source_health(tmp_path):
    cases = (
        (
            "social",
            "{id: reddit_worldnews, kind: rss, enabled: true}",
            "social_disabled",
            "global: {include_social_sources: true}",
        ),
        (
            "heavy",
            "{id: hdx_home, kind: api_json, enabled: true}",
            "heavy_open_data_disabled",
            "global: {allow_heavy_open_data_sources: true}",
        ),
        (
            "homepage",
            "{id: gdacs_home, enabled: true}",
            "homepage_extract_disabled",
            "global: {allow_homepage_extractors: true}",
        ),
    )
    for label, source, blocked_state, allowed_global in cases:
        shared_policy = "news: {fetch_policy: {allow_homepage_extractors: true}, "
        blocked_text = "global: {}\n" + shared_policy + (
            f"scopes: {{GLOBAL: {{sources: [{source}]}}}}}}"
        )
        blocked = load_config(_write_config(tmp_path / f"{label}-blocked.yml", blocked_text))
        blocked_source = iter_news_sources(blocked)[0]
        assert evaluate_source_policy(blocked, blocked_source)["gate_state"] == blocked_state

        allowed_text = allowed_global + "\n" + shared_policy + (
            f"scopes: {{GLOBAL: {{sources: [{source}]}}}}}}"
        )
        allowed = load_config(_write_config(tmp_path / f"{label}-allowed.yml", allowed_text))
        allowed_source = iter_news_sources(allowed)[0]
        assert evaluate_source_policy(allowed, allowed_source)["gate_state"] != blocked_state


def test_global_auth_and_conflict_config_require_explicit_gates(tmp_path):
    cases = (
        (
            "auth",
            "{id: nasa_firms_api, enabled: true}",
            "global.allow_auth_required_sources true",
            "global: {allow_auth_required_sources: true}",
        ),
        (
            "conflict",
            "{id: conflict_fixture, name: Conflict fixture, kind: api_json, "
            "source_family: unocha, source_class: official_conflict_humanitarian, "
            "policy_risk: high, enabled: true}",
            "requires recorded GLOBAL conflict-source policy review",
            "global: {}",
        ),
    )
    for label, source, expected_error, allowed_global in cases:
        shared_policy = "news: {fetch_policy: {allow_homepage_extractors: true}, "
        config_text = (
            "global: {}\n"
            + shared_policy
            + f"scopes: {{GLOBAL: {{sources: [{source}]}}}}}}"
        )
        with pytest.raises(ConfigError, match=expected_error):
            load_config(_write_config(tmp_path / f"{label}-blocked.yml", config_text))

        if label == "conflict":
            allowed_source = source[:-1] + ", policy_reviewed: true}"
        else:
            allowed_source = source
        allowed_text = (
            allowed_global + "\n" + shared_policy
            + f"scopes: {{GLOBAL: {{sources: [{allowed_source}]}}}}}}"
        )
        allowed = load_config(_write_config(tmp_path / f"{label}-allowed.yml", allowed_text))
        assert len(iter_news_sources(allowed)) == 1
        if label == "conflict":
            assert iter_news_sources(allowed)[0]["conflict_sensitive"] is True
