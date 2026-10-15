from __future__ import annotations

from copy import deepcopy

import pytest

from console1701.config import load_config
from console1701.db import connect_db, init_db
from console1701.news.scanner import purge_news_retention, run_news_scan
from console1701.news.science_registry import (
    SCIENCE_SOURCE_REGISTRY,
    get_science_source_registry_entry,
    list_science_source_registry,
    validate_science_registry,
)


def test_science_inventory_is_disabled_and_keeps_system_as_app_health():
    assert len(SCIENCE_SOURCE_REGISTRY) == 177
    assert len({row["source_key"] for row in SCIENCE_SOURCE_REGISTRY}) == 177
    assert all(row["scope"] == "SYSTEM_SOLAR" for row in SCIENCE_SOURCE_REGISTRY)
    assert all(row["enabled"] is False and row["parser"] is None for row in SCIENCE_SOURCE_REGISTRY)
    assert all(row["source_health_behavior"] for row in SCIENCE_SOURCE_REGISTRY)
    assert get_science_source_registry_entry("heasarc_home")["source_health_behavior"] in {
        "source_health_only", "heavy_archive_disabled"
    }
    assert any(row["source_health_behavior"] == "auth_required" for row in SCIENCE_SOURCE_REGISTRY)
    assert get_science_source_registry_entry("esa_space_science_feed")[
        "source_health_behavior"
    ] == "disabled"
    assert get_science_source_registry_entry("nasa_exoplanet_ps_tap")[
        "source_health_behavior"
    ] == "disabled"
    assert any(
        row["source_health_behavior"] == "heavy_archive_disabled"
        for row in SCIENCE_SOURCE_REGISTRY
    )


def test_science_registry_accessors_do_not_mutate_source_inventory():
    first = list_science_source_registry()[0]
    key = first["source_key"]
    first["source_key"] = "changed"
    assert get_science_source_registry_entry(key)["source_key"] == key
    assert get_science_source_registry_entry("missing") is None


@pytest.mark.parametrize(("field", "value"), [
    ("scope", "SYSTEM"),
    ("source_class", "unrestricted_archive"),
    ("adapter", "unsafe_fetch"),
    ("verification_status", "verified_live"),
    ("raw_url", "http://example.test/feed"),
    ("refresh_interval", "0 min"),
    ("priority", "101"),
])
def test_science_registry_rejects_unsafe_or_unknown_entries(field, value):
    row = deepcopy(SCIENCE_SOURCE_REGISTRY[0])
    row[field] = value
    with pytest.raises(ValueError):
        validate_science_registry([row])


def test_science_registry_rejects_duplicate_keys():
    row = deepcopy(SCIENCE_SOURCE_REGISTRY[0])
    with pytest.raises(ValueError, match="duplicate"):
        validate_science_registry([row, row])


def test_disabled_science_registry_syncs_without_fetch_and_events_expire(tmp_path):
    path = tmp_path / "config.yml"
    path.write_text("paths: {repo_roots: [], explicit_repos: []}\n")
    result = run_news_scan(path)
    assert result["status"] == "disabled"
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT source_key, enabled_by_default FROM news_source_registry "
            "WHERE scope = 'SYSTEM_SOLAR'"
        ).fetchall()
        assert len(rows) == 177
        assert all(row["enabled_by_default"] == 0 for row in rows)
        assert conn.execute(
            "SELECT COUNT(*) FROM news_sources WHERE scope = 'SYSTEM_SOLAR'"
        ).fetchone()[0] == 0
        conn.execute(
            "INSERT INTO science_events (event_key, event_type, title, first_seen_at, "
            "last_seen_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("old", "transient", "Old fixture", "2026-10-01T00:00:00+00:00",
             "2026-10-01T00:00:00+00:00", "2026-10-02T00:00:00+00:00"),
        )
        assert purge_news_retention(conn, config, now="2026-10-15T00:00:00+00:00")[
            "science_events"
        ] == 1
        assert conn.execute("SELECT COUNT(*) FROM science_events").fetchone()[0] == 0
        init_db(conn)
        assert conn.execute(
            "SELECT COUNT(*) FROM news_source_registry WHERE scope = 'SYSTEM_SOLAR'"
        ).fetchone()[0] == 177
