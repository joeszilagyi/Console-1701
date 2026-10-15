from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import ConfigError, iter_news_sources, load_config
from console1701.db import connect_db
from console1701.news.orbital_registry import (
    get_orbital_source_registry_entry,
    list_orbital_source_registry,
    orbital_source_registry_summary,
)
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_storage_summary


def _write(path: Path, body: str) -> Path:
    path.write_text(dedent(body).strip() + "\n")
    return path


def test_orbital_inventory_is_complete_disabled_and_validated():
    entries = list_orbital_source_registry()
    keys = {entry["source_key"] for entry in entries}
    summary = orbital_source_registry_summary()
    assert len(entries) == len(keys) == 136
    assert all(entry["scope"] == "ORBITAL" and entry["enabled"] is False
               for entry in entries)
    assert all(entry["source_health_behavior"] for entry in entries)
    assert summary["source_count"] == 136
    assert summary["enabled_by_default"] is False
    assert get_orbital_source_registry_entry("swpc_alerts_json")["kind"] == "api_json"
    assert get_orbital_source_registry_entry("nasa_rss_feeds")["kind"] == "rss"
    assert get_orbital_source_registry_entry("orbital_fixture_pack")["kind"] == (
        "local_file_json"
    )
    assert get_orbital_source_registry_entry("orbital_arcgis_reentry_candidate")[
        "kind"
    ] == "reference_only"


def test_orbital_registry_seeds_config_and_sqlite_without_fetch(tmp_path, monkeypatch):
    path = _write(tmp_path / "config.yml", """
        paths: {repo_roots: [], explicit_repos: []}
        news:
          scopes:
            ORBITAL:
              sources:
                - id: swpc_alerts_json
    """)
    config = load_config(path)
    source = iter_news_sources(config)[0]
    assert source["name"] == "SWPC alerts JSON"
    assert source["scope"] == "ORBITAL"
    assert source["url"] == "https://services.swpc.noaa.gov/products/alerts.json"
    assert source["enabled"] is False
    assert source["verification_status"] == "official_page_seen"
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    assert run_news_scan(path)["status"] == "disabled"
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT source_key, enabled_by_default FROM news_source_registry "
            "WHERE scope = 'ORBITAL'"
        ).fetchall()
        summary = get_news_storage_summary(conn, config)
    assert len(rows) == 136
    assert all(row["enabled_by_default"] == 0 for row in rows)
    assert summary["orbital_registry"]["source_count"] == 136


def test_orbital_reference_cannot_ingest_even_with_file_override(tmp_path, monkeypatch):
    path = _write(tmp_path / "reference.yml", """
        paths: {repo_roots: [], explicit_repos: []}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: swpc_home
                  enabled: true
                  url: file:///missing-reference.html
    """)
    monkeypatch.setattr(
        "console1701.news.scanner.load_fixture_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no fixture read")),
    )
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    assert run_news_scan(path)["item_count"] == 0


def test_orbital_config_rejects_invalid_registry_enum(tmp_path):
    path = _write(tmp_path / "bad.yml", """
        paths: {repo_roots: [], explicit_repos: []}
        news:
          scopes:
            ORBITAL:
              sources:
                - id: swpc_alerts_json
                  source_class: invented
    """)
    with pytest.raises(ConfigError, match="source_class"):
        load_config(path)
