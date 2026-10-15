from __future__ import annotations

from copy import deepcopy

import pytest

from console1701.news.science_registry import (
    SCIENCE_SOURCE_REGISTRY,
    get_science_source_registry_entry,
    list_science_source_registry,
    validate_science_registry,
)


def test_science_inventory_is_disabled_and_keeps_system_as_app_health():
    assert len(SCIENCE_SOURCE_REGISTRY) == 170
    assert len({row["source_key"] for row in SCIENCE_SOURCE_REGISTRY}) == 170
    assert all(row["scope"] == "SYSTEM_SOLAR" for row in SCIENCE_SOURCE_REGISTRY)
    assert all(row["enabled"] is False and row["parser"] is None for row in SCIENCE_SOURCE_REGISTRY)
    assert all(row["source_health_behavior"] for row in SCIENCE_SOURCE_REGISTRY)
    assert get_science_source_registry_entry("heasarc_home")["source_health_behavior"] in {
        "source_health_only", "heavy_archive_disabled"
    }
    assert any(row["source_health_behavior"] == "auth_required" for row in SCIENCE_SOURCE_REGISTRY)
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
