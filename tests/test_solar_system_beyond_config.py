from __future__ import annotations

import pytest
import yaml

from console1701.config import ConfigError, load_config


def _load(tmp_path, science):
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "solar_system_beyond": science,
    }))
    return load_config(path)


def test_science_config_defaults_disabled_without_reusing_system_scope(tmp_path):
    config = _load(tmp_path, {})
    science = config["solar_system_beyond"]
    assert science["enabled"] is False
    assert science["include_planetary_science"] is True
    assert science["include_catalog_archives"] is False
    assert science["allow_homepage_extractors"] is False
    assert "COSMIC" not in config["news"]["scopes"]
    assert "SYSTEM" not in config["news"]["scopes"]


@pytest.mark.parametrize(("include", "allow"), [
    ("include_tns", "allow_auth_required_sources"),
    ("include_catalog_archives", "allow_heavy_archive_sources"),
    ("include_large_archive_queries", "allow_heavy_archive_sources"),
    ("include_literature_metadata", "allow_literature_metadata"),
    ("include_social_sources", "allow_social_sources"),
])
def test_sensitive_science_categories_need_explicit_gate(tmp_path, include, allow):
    with pytest.raises(ConfigError, match=allow):
        _load(tmp_path, {include: True})
    assert _load(tmp_path, {include: True, allow: True})[
        "solar_system_beyond"
    ][include] is True


def test_science_config_rejects_invalid_flags_and_attention_values(tmp_path):
    with pytest.raises(ConfigError, match="include_exoplanets"):
        _load(tmp_path, {"include_exoplanets": "maybe"})
    with pytest.raises(ConfigError, match="transient_attention_minimum"):
        _load(tmp_path, {"transient_attention_minimum": "all"})
    with pytest.raises(ConfigError, match="allow_literature_metadata"):
        _load(tmp_path, {"literature_attention_minimum": "verified_metadata_only"})
