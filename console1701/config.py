from __future__ import annotations

from copy import deepcopy
from math import isfinite
from pathlib import Path
from typing import Any

APP_NAME = "console-1701"
DEFAULT_CONFIG_PATH = Path.home() / ".config" / APP_NAME / "config.yml"
DEFAULT_STATE_DIR = Path.home() / ".local" / "state" / APP_NAME
DEFAULT_DB_PATH = DEFAULT_STATE_DIR / "console.sqlite"
DEFAULT_HANDOFF_DIR = DEFAULT_STATE_DIR / "handoffs"

NEWS_SCOPES = ("LOCAL", "REGIONAL", "NATIONAL", "GLOBAL", "ORBITAL", "SYSTEM_SOLAR")
NEWS_SCOPE_LABELS = {
    "LOCAL": "Seattle",
    "REGIONAL": "Washington / PNW",
    "NATIONAL": "United States",
    "GLOBAL": "World",
    "ORBITAL": "Orbital",
    "SYSTEM_SOLAR": "Cosmic",
}
NEWS_SOURCE_KINDS = {
    "rss",
    "atom",
    "api_json",
    "open_data_json",
    "homepage_headlines",
    "reference_only",
    "local_file_json",
    "local_file_rss",
}
NEWS_HOMEPAGE_SOURCE_KINDS = {"homepage_headlines"}
REGIONAL_SOURCE_CLASSES = {
    "county_emergency",
    "local_tv_radio",
    "official_alert",
    "official_air_quality",
    "official_airport_port",
    "official_emergency",
    "official_ferry",
    "official_incident",
    "official_open_data",
    "official_public_health",
    "official_seismic_volcano",
    "official_state_civic",
    "official_transport",
    "official_transit",
    "official_utility",
    "official_water_flood",
    "official_wildfire",
    "official_weather_hazard",
    "policy_reference",
    "public_media",
    "regional_news",
    "social_candidate",
    "source_health_only",
    "unofficial_aggregator",
}
REGIONAL_ADAPTER_TYPES = {
    "api_json",
    "airport_status_json_or_xml",
    "arcgis_dashboard_research",
    "arcgis_feature_service_candidate",
    "atom",
    "cap_alerts",
    "disabled",
    "generic_json_items",
    "geojson_feed",
    "gtfs_realtime_alerts",
    "hydrology_api_json",
    "manual_review_only",
    "official_api_json",
    "official_rss",
    "open511_json",
    "rss",
    "rss_atom",
    "socrata_json",
    "source_health_probe_only",
    "static_html_headline_candidate",
    "wordpress_feed_candidate",
}
REGIONAL_RISK_LEVELS = {"low", "medium", "high"}
REGIONAL_VERIFICATION_STATUSES = {
    "candidate_needs_verification",
    "candidate_policy_sensitive",
    "manual_review_only",
    "official_feed_seen",
    "official_page_seen",
    "source_health_probe_only",
    "unofficial_secondary",
    "user_seeded",
    "verified",
}
LOCAL_SOURCE_CLASSES = {
    "local_news",
    "neighborhood_blog",
    "official_air_quality",
    "official_airport_port",
    "official_alert",
    "official_incident",
    "official_open_data",
    "official_school_civic",
    "official_transport",
    "official_utility",
    "official_weather_hazard",
    "policy_reference",
    "social_candidate",
    "source_health_only",
    "unofficial_aggregator",
}
LOCAL_ADAPTER_TYPES = {
    "airport_status_json_or_xml",
    "api_json",
    "arcgis_dashboard_research",
    "arcgis_feature_service_candidate",
    "atom",
    "disabled",
    "generic_json_items",
    "gtfs_realtime_alerts",
    "homepage_selectors",
    "manual_review_only",
    "official_api_json",
    "rss",
    "rss_atom",
    "socrata_json",
    "source_health_probe_only",
    "static_html_headline_candidate",
    "wordpress_feed_candidate",
}
LOCAL_RISK_LEVELS = {"low", "medium", "high"}
LOCAL_RETENTION_SENSITIVITIES = {"low", "medium", "high"}
LOCAL_VERIFICATION_STATUSES = {
    "candidate_needs_verification",
    "candidate_policy_sensitive",
    "manual_review_only",
    "source_health_probe_only",
    "unofficial_secondary",
    "user_seeded",
    "verified",
}
LOCAL_SOCIAL_SOURCE_FAMILIES = {"bluesky", "reddit", "x_api"}

DEFAULT_LOCAL_CONFIG: dict[str, Any] = {
    "enabled": False,
    "default_place_label": "Seattle",
    "include_airport": True,
    "include_port": True,
    "include_king_county_transit": True,
    "include_wsdot_seattle_corridors": True,
    "include_ferries": True,
    "hazard_radius_miles": 75,
    "earthquake_min_magnitude": 3.0,
    "allow_neighborhood_blogs": False,
    "allow_social_sources": False,
}

DEFAULT_REGIONAL_CONFIG: dict[str, Any] = {
    "enabled": False,
    "label": "Washington / PNW",
    "primary_region": "Washington",
    "secondary_regions": ["Puget Sound", "Pacific Northwest", "Cascadia"],
    "include_oregon_when_relevant": True,
    "include_bc_when_relevant": True,
    "include_transport_corridors": True,
    "include_wildfire_smoke": True,
    "include_seismic_volcano": True,
    "include_public_health": True,
    "include_state_government": True,
    "include_regional_news": True,
    "hazard_radius_miles": 250,
    "allow_social_sources": False,
    "allow_homepage_extractors": False,
}

DEFAULT_NATIONAL_CONFIG: dict[str, Any] = {
    "enabled": False,
    "default_place_label": "United States",
    "include_federal_alerts": True,
    "include_weather_hazards": True,
    "include_disasters": True,
    "include_public_health": True,
    "include_recalls": True,
    "include_transportation": True,
    "include_aviation": True,
    "include_cybersecurity": True,
    "include_energy_grid": True,
    "include_economic_releases": True,
    "include_federal_register": True,
    "include_congress": False,
    "include_courts": False,
    "include_national_news": True,
    "include_social_sources": False,
    "include_state_events_when_national_impact": True,
    "earthquake_min_magnitude": 5.0,
    "hurricane_attention_minimum": "watch",
    "severe_weather_attention_minimum": "warning",
    "wildfire_national_attention_min_acres": 1000,
    "recall_attention_classes": ["Class I", "high_public_impact"],
    "cyber_attention_minimum": [
        "known_exploited", "emergency_directive", "high_impact_advisory"
    ],
}

DEFAULT_GLOBAL_CONFIG: dict[str, Any] = {
    "enabled": False,
    "default_place_label": "World",
    "include_disasters": True,
    "include_humanitarian": True,
    "include_public_health": True,
    "include_weather_hazards": True,
    "include_tropical_cyclones": True,
    "include_earthquakes": True,
    "include_tsunami": True,
    "include_volcanoes": True,
    "include_wildfire_smoke": True,
    "include_air_quality": True,
    "include_conflict_humanitarian": True,
    "include_diplomacy_institutions": True,
    "include_transport_supply_chain": True,
    "include_cybersecurity": True,
    "include_global_economy": False,
    "include_global_news": True,
    "include_social_sources": False,
    "include_us_impact_tags": True,
    "include_local_impact_tags": True,
    "allow_auth_required_sources": False,
    "allow_heavy_open_data_sources": False,
    "allow_homepage_extractors": False,
    "conflict_sources_require_policy_review": True,
    "earthquake_min_magnitude": 6.0,
    "tsunami_attention_minimum": "watch",
    "tropical_cyclone_attention_minimum": "watch",
    "gdacs_attention_minimum": "orange",
    "humanitarian_attention_minimum": "disaster",
    "outbreak_attention_minimum": "who_don",
    "conflict_attention_minimum": "official_or_multi_source",
    "wildfire_attention_minimum": "major_or_smoke_impact",
}

DEFAULT_ORBITAL_CONFIG: dict[str, Any] = {
    "enabled": False,
    "default_place_label": "Orbital",
    "include_space_weather": True,
    "include_aurora": True,
    "kp_min_index": 5.0,
    "aurora_locations": [],
    "include_neo_close_approaches": True,
    "neo_max_lunar_distance": 5.0,
    "neo_min_diameter_km": 0.05,
    "include_fireballs": True,
    "fireball_min_impact_kt": 0.1,
    "fireball_max_age_days": 30,
    "include_launches": True,
    "include_crewed_spaceflight": True,
    "include_iss": True,
    "include_reentries": True,
    "include_debris": False,
    "include_satellite_catalog": False,
    "include_conjunction_awareness": False,
    "include_space_agency_news": True,
    "include_spaceflight_news": True,
    "include_astronomy_transients": True,
    "include_social_sources": False,
    "allow_auth_required_sources": False,
    "allow_restricted_sources": False,
    "allow_tactical_sources": False,
    "allow_homepage_extractors": False,
}

DEFAULT_SOLAR_SYSTEM_BEYOND_CONFIG: dict[str, Any] = {
    "enabled": False,
    "include_planetary_science": True,
    "include_interplanetary_missions": True,
    "include_exoplanets": True,
    "include_telescope_science": True,
    "include_major_space_agency_science": True,
    "include_transients": True,
    "include_gcn": True,
    "include_tns": False,
    "include_gravitational_waves": False,
    "include_neutrino_alerts": False,
    "include_catalog_archives": False,
    "include_literature_metadata": False,
    "include_social_sources": False,
    "include_large_archive_queries": False,
    "allow_auth_required_sources": False,
    "allow_heavy_archive_sources": False,
    "allow_literature_metadata": False,
    "allow_social_sources": False,
    "allow_homepage_extractors": False,
    "transient_attention_minimum": "official_alert_or_multi_source",
    "exoplanet_attention_minimum": "agency_release_or_confirmed_catalog_delta",
    "telescope_science_attention_minimum": "official_release_or_multi_source",
    "planetary_attention_minimum": "mission_update_or_agency_release",
    "literature_attention_minimum": "disabled",
}

DEFAULT_NEWS_CONFIG: dict[str, Any] = {
    "enabled": False,
    "retention": {
        "items_days": 7,
        "fetch_runs_days": 14,
        "source_health_days": 30,
        "raw_payload_debug_enabled": False,
        "raw_payload_debug_ttl_hours": 6,
    },
    "fetch_policy": {
        "global_concurrency": 2,
        "default_timeout_seconds": 10,
        "default_interval_minutes": 30,
        "default_backoff_minutes": 120,
        "max_response_bytes": 1048576,
        "user_agent": "console-1701 local recent-signal monitor",
        "allow_official_http": False,
        "page_load_external_fetches": False,
        "respect_robots_txt": True,
        "allow_homepage_extractors": False,
    },
    "scopes": {
        scope: {"enabled": False, "label": label, "sources": []}
        for scope, label in NEWS_SCOPE_LABELS.items()
    },
}

DEFAULT_CONFIG: dict[str, Any] = {
    "server": {
        "host": "127.0.0.1",
        "port": 1701,
        "browser_refresh_seconds": 60,
    },
    "scan": {
        "interval_minutes": 30,
        "max_repos_per_scan": 75,
        "overall_scan_timeout_seconds": 180,
        "per_repo_timeout_seconds": 20,
        "git_command_timeout_seconds": 5,
        "log_tail_max_bytes": 262144,
        "max_recent_commits": 8,
        "max_changed_files_display": 80,
        "dirty_stale_hours": 24,
        "inactive_days_warning": 14,
        "inactive_days_stale": 45,
        "allow_network": False,
        "allow_git_fetch": False,
    },
    "sqlite": {
        "busy_timeout_ms": 5000,
        "journal_mode": "WAL",
        "history_retention_days": 90,
        "history_prune_batch_size": 1000,
    },
    "paths": {
        "repo_roots": ["~/projects"],
        "explicit_repos": [
            "~/projects/console-1701/main",
            "~/projects/ufo-records",
            "~/projects/TCL",
        ],
    },
    "ignore": {
        "paths": [
            "**/.git/**",
            "**/.venv/**",
            "**/venv/**",
            "**/node_modules/**",
            "**/__pycache__/**",
            "**/.pytest_cache/**",
            "**/.mypy_cache/**",
            "**/.ruff_cache/**",
            "**/dist/**",
            "**/build/**",
            "**/vendor/**",
            "**/archive/**",
        ]
    },
    "logs": [{"name": "codex", "path": "~/.codex", "type": "codex", "enabled": True}],
    "test_policy": {
        "auto_run": True,
        "default_timeout_seconds": 120,
        "allow_repos": ["console-1701", "~/projects/console-1701/main"],
    },
    "system_probe": {
        "command_timeout_seconds": 3,
        "allow_external_connectivity_checks": False,
        "external_check_urls": ["https://www.debian.org/"],
        "external_check_timeout_seconds": 3,
        "show_sensitive_identifiers": False,
        "critical_services": [],
    },
    "regional": DEFAULT_REGIONAL_CONFIG,
    "local": DEFAULT_LOCAL_CONFIG,
    "national": DEFAULT_NATIONAL_CONFIG,
    "global": DEFAULT_GLOBAL_CONFIG,
    "solar_system_beyond": DEFAULT_SOLAR_SYSTEM_BEYOND_CONFIG,
    "news": DEFAULT_NEWS_CONFIG,
    "projects": [
        {
            "name": "console-1701",
            "path": "~/projects/console-1701/main",
            "role": "Local-only repo and workflow console",
            "category": "Operational dashboard",
            "importance": "critical",
            "test_commands": ["./.venv/bin/pytest"],
        },
        {
            "name": "ufo-records",
            "path": "~/projects/ufo-records",
            "role": "Long-horizon UFO research database and tooling",
            "category": "Research machinery",
            "importance": "high",
            "test_commands": ["python3 -m pytest tools/sqlite/tests"],
        },
        {
            "name": "TCL",
            "path": "~/projects/TCL",
            "role": "Time travel constraints library and adversarial theory project",
            "category": "Theory/library project",
            "importance": "high",
            "test_commands": [],
        },
    ],
}


class ConfigError(RuntimeError):
    """Raised when config cannot be read or normalized."""


def _yaml_module():
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise ConfigError(
            "PyYAML is required to read or write config files. Install with "
            "python -m pip install -e '.[dev]' after python3-venv is available."
        ) from exc
    return yaml


def expand_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def config_path_from_arg(path: str | None = None) -> Path:
    return expand_path(path) if path else DEFAULT_CONFIG_PATH


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config_path = config_path_from_arg(str(path)) if path else DEFAULT_CONFIG_PATH
    config = deepcopy(DEFAULT_CONFIG)
    if config_path.exists():
        yaml = _yaml_module()
        try:
            loaded = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"Malformed config at {config_path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise ConfigError(f"Config at {config_path} must be a YAML mapping.")
        config = deep_merge(config, loaded)

    config["_config_path"] = str(config_path)
    config["_state_dir"] = str(DEFAULT_STATE_DIR)
    config["_db_path"] = str(DEFAULT_DB_PATH)
    config["_handoff_dir"] = str(DEFAULT_HANDOFF_DIR)
    normalize_config(config)
    return config


def normalize_config(config: dict[str, Any]) -> None:
    server = config.setdefault("server", {})
    if server.get("host") != "127.0.0.1":
        server["host"] = "127.0.0.1"
    server["port"] = int(server.get("port", 1701))

    paths = config.setdefault("paths", {})
    paths["repo_roots"] = [str(expand_path(path)) for path in paths.get("repo_roots", [])]
    paths["explicit_repos"] = [str(expand_path(path)) for path in paths.get("explicit_repos", [])]

    for project in config.get("projects", []):
        if "path" in project:
            project["path"] = str(expand_path(project["path"]))

    for log in config.get("logs", []):
        if "path" in log:
            log["path"] = str(expand_path(log["path"]))

    policy = config.setdefault("test_policy", {})
    normalized_allow: list[str] = []
    for item in policy.get("allow_repos", []):
        value = str(item)
        if value.startswith("~") or value.startswith("/"):
            normalized_allow.append(str(expand_path(value)))
        else:
            normalized_allow.append(value)
    policy["allow_repos"] = normalized_allow

    sqlite_cfg = _require_mapping(config.setdefault("sqlite", {}), "sqlite")
    sqlite_cfg["history_retention_days"] = _coerce_int(
        sqlite_cfg.get("history_retention_days", 90),
        "sqlite.history_retention_days",
        minimum=1,
    )
    sqlite_cfg["history_prune_batch_size"] = _coerce_int(
        sqlite_cfg.get("history_prune_batch_size", 1000),
        "sqlite.history_prune_batch_size",
        minimum=1,
    )
    if sqlite_cfg["history_prune_batch_size"] > 10000:
        raise ConfigError("sqlite.history_prune_batch_size must be at most 10000.")

    normalize_local_config(config)
    normalize_regional_config(config)
    normalize_national_config(config)
    normalize_global_config(config)
    normalize_orbital_config(config)
    normalize_solar_system_beyond_config(config)
    normalize_news_config(config)


def _require_mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{path} must be a mapping.")
    return value


def _coerce_bool(value: Any, path: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    raise ConfigError(f"{path} must be true or false.")


def _coerce_int(value: Any, path: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool):
        raise ConfigError(f"{path} must be an integer.")
    try:
        integer = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{path} must be an integer.") from exc
    if minimum is not None and integer < minimum:
        raise ConfigError(f"{path} must be at least {minimum}.")
    return integer


def _coerce_float(value: Any, path: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool):
        raise ConfigError(f"{path} must be a number.")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{path} must be a number.") from exc
    if minimum is not None and number < minimum:
        raise ConfigError(f"{path} must be at least {minimum}.")
    return number


def _require_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{path} must be a non-empty string.")
    return value.strip()


def _normalize_string_list(value: Any, path: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError(f"{path} must be a list of strings.")
    normalized: list[str] = []
    for index, item in enumerate(value):
        normalized.append(_require_string(item, f"{path}[{index}]"))
    return normalized


def _normalize_optional_keyword(
    source_cfg: dict[str, Any],
    key: str,
    path: str,
    *,
    allowed: set[str] | None = None,
) -> str | None:
    if key not in source_cfg or source_cfg[key] is None:
        return None
    value = _require_string(source_cfg[key], f"{path}.{key}").lower()
    if allowed is not None and value not in allowed:
        raise ConfigError(f"{path}.{key} must be one of: {', '.join(sorted(allowed))}.")
    source_cfg[key] = value
    return value


def _apply_scope_registry_defaults(source_cfg: dict[str, Any], scope: str) -> dict[str, Any]:
    if scope not in {"LOCAL", "REGIONAL", "NATIONAL", "GLOBAL", "ORBITAL"}:
        # Science candidates need individual adapter signoff before they may
        # seed a configured source; the internal scope still has a UI state.
        return source_cfg
    source_key = str(source_cfg.get("id") or "").strip()
    if not source_key:
        return source_cfg
    if scope == "LOCAL":
        from console1701.news.local_registry import local_registry_config_defaults

        defaults = local_registry_config_defaults(source_key)
    elif scope == "REGIONAL":
        from console1701.news.regional_registry import regional_registry_config_defaults

        defaults = regional_registry_config_defaults(source_key)
    elif scope == "NATIONAL":
        from console1701.news.national_registry import national_registry_config_defaults

        defaults = national_registry_config_defaults(source_key)
    elif scope == "GLOBAL":
        from console1701.news.global_registry import global_registry_config_defaults

        defaults = global_registry_config_defaults(source_key)
    else:
        from console1701.news.orbital_registry import orbital_registry_config_defaults

        defaults = orbital_registry_config_defaults(source_key)
    if not defaults:
        return source_cfg
    return deep_merge(defaults, source_cfg)


def normalize_local_config(config: dict[str, Any]) -> None:
    local = _require_mapping(config.setdefault("local", deepcopy(DEFAULT_LOCAL_CONFIG)), "local")
    local["enabled"] = _coerce_bool(local.get("enabled", False), "local.enabled")
    local["default_place_label"] = _require_string(
        local.get("default_place_label", "Seattle"),
        "local.default_place_label",
    )
    for key in (
        "include_airport",
        "include_port",
        "include_king_county_transit",
        "include_wsdot_seattle_corridors",
        "include_ferries",
        "allow_neighborhood_blogs",
        "allow_social_sources",
    ):
        local[key] = _coerce_bool(local.get(key, DEFAULT_LOCAL_CONFIG[key]), f"local.{key}")
    local["hazard_radius_miles"] = _coerce_int(
        local.get("hazard_radius_miles", 75),
        "local.hazard_radius_miles",
        minimum=0,
    )
    local["earthquake_min_magnitude"] = _coerce_float(
        local.get("earthquake_min_magnitude", 3.0),
        "local.earthquake_min_magnitude",
        minimum=0.0,
    )


def normalize_regional_config(config: dict[str, Any]) -> None:
    regional = _require_mapping(
        config.setdefault("regional", deepcopy(DEFAULT_REGIONAL_CONFIG)),
        "regional",
    )
    regional["enabled"] = _coerce_bool(regional.get("enabled", False), "regional.enabled")
    regional["label"] = _require_string(
        regional.get("label", "Washington / PNW"),
        "regional.label",
    )
    regional["primary_region"] = _require_string(
        regional.get("primary_region", "Washington"),
        "regional.primary_region",
    )
    regional["secondary_regions"] = _normalize_string_list(
        regional.get("secondary_regions", DEFAULT_REGIONAL_CONFIG["secondary_regions"]),
        "regional.secondary_regions",
    )
    for key in (
        "include_oregon_when_relevant",
        "include_bc_when_relevant",
        "include_transport_corridors",
        "include_wildfire_smoke",
        "include_seismic_volcano",
        "include_public_health",
        "include_state_government",
        "include_regional_news",
        "allow_social_sources",
        "allow_homepage_extractors",
    ):
        regional[key] = _coerce_bool(
            regional.get(key, DEFAULT_REGIONAL_CONFIG[key]),
            f"regional.{key}",
        )
    regional["hazard_radius_miles"] = _coerce_int(
        regional.get("hazard_radius_miles", 250),
        "regional.hazard_radius_miles",
        minimum=0,
    )


def normalize_national_config(config: dict[str, Any]) -> None:
    national = _require_mapping(
        config.setdefault("national", deepcopy(DEFAULT_NATIONAL_CONFIG)), "national"
    )
    national["enabled"] = _coerce_bool(national.get("enabled", False), "national.enabled")
    national["default_place_label"] = _require_string(
        national.get("default_place_label", "United States"),
        "national.default_place_label",
    )
    for key, default in DEFAULT_NATIONAL_CONFIG.items():
        if key.startswith("include_"):
            national[key] = _coerce_bool(national.get(key, default), f"national.{key}")
    national["earthquake_min_magnitude"] = _coerce_float(
        national.get("earthquake_min_magnitude", 5.0),
        "national.earthquake_min_magnitude", minimum=0.0,
    )
    if not isfinite(national["earthquake_min_magnitude"]):
        raise ConfigError("national.earthquake_min_magnitude must be finite.")
    national["wildfire_national_attention_min_acres"] = _coerce_int(
        national.get("wildfire_national_attention_min_acres", 1000),
        "national.wildfire_national_attention_min_acres", minimum=0,
    )
    for key, allowed in (
        ("hurricane_attention_minimum", {"watch", "warning"}),
        ("severe_weather_attention_minimum", {"advisory", "watch", "warning"}),
    ):
        value = _require_string(national.get(key), f"national.{key}").lower()
        if value not in allowed:
            raise ConfigError(f"national.{key} must be one of: {', '.join(sorted(allowed))}.")
        national[key] = value
    for key in ("recall_attention_classes", "cyber_attention_minimum"):
        national[key] = _normalize_string_list(national.get(key), f"national.{key}")


def normalize_global_config(config: dict[str, Any]) -> None:
    global_cfg = _require_mapping(
        config.setdefault("global", deepcopy(DEFAULT_GLOBAL_CONFIG)), "global"
    )
    global_cfg["enabled"] = _coerce_bool(global_cfg.get("enabled", False), "global.enabled")
    global_cfg["default_place_label"] = _require_string(
        global_cfg.get("default_place_label", "World"), "global.default_place_label"
    )
    for key, default in DEFAULT_GLOBAL_CONFIG.items():
        if key.startswith(("include_", "allow_")) or key == (
            "conflict_sources_require_policy_review"
        ):
            global_cfg[key] = _coerce_bool(global_cfg.get(key, default), f"global.{key}")
    global_cfg["earthquake_min_magnitude"] = _coerce_float(
        global_cfg.get("earthquake_min_magnitude", 6.0),
        "global.earthquake_min_magnitude",
        minimum=0.0,
    )
    if not isfinite(global_cfg["earthquake_min_magnitude"]):
        raise ConfigError("global.earthquake_min_magnitude must be finite.")
    for key, allowed in (
        ("tsunami_attention_minimum", {"watch", "warning"}),
        ("tropical_cyclone_attention_minimum", {"watch", "warning"}),
        ("gdacs_attention_minimum", {"green", "orange", "red"}),
        ("humanitarian_attention_minimum", {"disaster", "crisis"}),
        ("outbreak_attention_minimum", {"who_don", "official_public_health"}),
        ("conflict_attention_minimum", {"official_or_multi_source", "official_only"}),
        ("wildfire_attention_minimum", {"major_or_smoke_impact", "major_only"}),
    ):
        value = _require_string(global_cfg.get(key), f"global.{key}").lower()
        if value not in allowed:
            raise ConfigError(f"global.{key} must be one of: {', '.join(sorted(allowed))}.")
        global_cfg[key] = value


def normalize_orbital_config(config: dict[str, Any]) -> None:
    orbital = _require_mapping(
        config.setdefault("orbital", deepcopy(DEFAULT_ORBITAL_CONFIG)), "orbital"
    )
    orbital["default_place_label"] = _require_string(
        orbital.get("default_place_label", "Orbital"), "orbital.default_place_label"
    )
    for key, default in DEFAULT_ORBITAL_CONFIG.items():
        if key.startswith(("include_", "allow_")) or key == "enabled":
            orbital[key] = _coerce_bool(orbital.get(key, default), f"orbital.{key}")
    try:
        kp_minimum = float(orbital.get("kp_min_index", 5.0))
    except (TypeError, ValueError) as exc:
        raise ConfigError("orbital.kp_min_index must be numeric") from exc
    if not isfinite(kp_minimum) or not 0 <= kp_minimum <= 9:
        raise ConfigError("orbital.kp_min_index must be between 0 and 9")
    orbital["kp_min_index"] = kp_minimum
    for key, default, lower, upper in (
        ("neo_max_lunar_distance", 5.0, 0.1, 50.0),
        ("neo_min_diameter_km", 0.05, 0.0, 10.0),
        ("fireball_min_impact_kt", 0.1, 0.0, 1000.0),
    ):
        try:
            value = float(orbital.get(key, default))
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"orbital.{key} must be numeric") from exc
        if not isfinite(value) or not lower <= value <= upper:
            raise ConfigError(f"orbital.{key} must be between {lower} and {upper}")
        orbital[key] = value
    orbital["fireball_max_age_days"] = _coerce_int(
        orbital.get("fireball_max_age_days", 30),
        "orbital.fireball_max_age_days", minimum=1,
    )
    if orbital["fireball_max_age_days"] > 365:
        raise ConfigError("orbital.fireball_max_age_days must be at most 365")
    locations = orbital.get("aurora_locations", [])
    if not isinstance(locations, list) or len(locations) > 8:
        raise ConfigError("orbital.aurora_locations must be a list of at most 8 locations")
    normalized_locations = []
    for index, location in enumerate(locations):
        path = f"orbital.aurora_locations[{index}]"
        if not isinstance(location, dict):
            raise ConfigError(f"{path} must be a mapping")
        name = _require_string(location.get("name"), f"{path}.name")
        if len(name) > 80:
            raise ConfigError(f"{path}.name must be at most 80 characters")
        scope = _require_string(location.get("scope"), f"{path}.scope").upper()
        if scope not in {"LOCAL", "REGIONAL"}:
            raise ConfigError(f"{path}.scope must be LOCAL or REGIONAL")
        try:
            latitude = float(location["latitude"])
            longitude = float(location["longitude"])
            radius = float(location.get("radius_degrees", 2.0))
            minimum = float(location.get("min_intensity", 50.0))
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigError(f"{path} requires numeric latitude and longitude") from exc
        if not all(isfinite(value) for value in (latitude, longitude, radius, minimum)):
            raise ConfigError(f"{path} contains a non-finite number")
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ConfigError(f"{path} has invalid latitude or longitude")
        if not (0.5 <= radius <= 10 and 0 <= minimum <= 100):
            raise ConfigError(f"{path} radius or minimum intensity is out of range")
        normalized_locations.append({
            "name": name, "scope": scope, "latitude": latitude,
            "longitude": longitude, "radius_degrees": radius,
            "min_intensity": minimum,
        })
    orbital["aurora_locations"] = normalized_locations


def normalize_solar_system_beyond_config(config: dict[str, Any]) -> None:
    science = _require_mapping(
        config.setdefault("solar_system_beyond", deepcopy(DEFAULT_SOLAR_SYSTEM_BEYOND_CONFIG)),
        "solar_system_beyond",
    )
    for key, default in DEFAULT_SOLAR_SYSTEM_BEYOND_CONFIG.items():
        if key == "enabled" or key.startswith(("include_", "allow_")):
            science[key] = _coerce_bool(
                science.get(key, default), f"solar_system_beyond.{key}"
            )
    for key, allowed in (
        ("transient_attention_minimum", {"official_alert_or_multi_source", "official_only"}),
        ("exoplanet_attention_minimum", {
            "agency_release_or_confirmed_catalog_delta", "agency_release_only",
        }),
        ("telescope_science_attention_minimum", {
            "official_release_or_multi_source", "official_release_only",
        }),
        ("planetary_attention_minimum", {
            "mission_update_or_agency_release", "agency_release_only",
        }),
        ("literature_attention_minimum", {"disabled", "verified_metadata_only"}),
    ):
        value = _require_string(science.get(key), f"solar_system_beyond.{key}").lower()
        if value not in allowed:
            choices = ", ".join(sorted(allowed))
            raise ConfigError(f"solar_system_beyond.{key} must be one of: {choices}.")
        science[key] = value
    for include, allow in (
        ("include_tns", "allow_auth_required_sources"),
        ("include_catalog_archives", "allow_heavy_archive_sources"),
        ("include_large_archive_queries", "allow_heavy_archive_sources"),
        ("include_literature_metadata", "allow_literature_metadata"),
        ("include_social_sources", "allow_social_sources"),
    ):
        if science[include] and not science[allow]:
            raise ConfigError(f"solar_system_beyond.{include} requires {allow}.")
    if science["literature_attention_minimum"] != "disabled" and not science[
        "allow_literature_metadata"
    ]:
        raise ConfigError(
            "solar_system_beyond.literature_attention_minimum requires "
            "allow_literature_metadata."
        )


def _normalize_local_source_metadata(
    source_cfg: dict[str, Any],
    *,
    path: str,
    local_cfg: dict[str, Any],
) -> None:
    source_family = _normalize_optional_keyword(source_cfg, "source_family", path)
    source_class = _normalize_optional_keyword(
        source_cfg,
        "source_class",
        path,
        allowed=LOCAL_SOURCE_CLASSES,
    )
    _normalize_optional_keyword(source_cfg, "adapter", path, allowed=LOCAL_ADAPTER_TYPES)
    _normalize_optional_keyword(
        source_cfg,
        "verification_status",
        path,
        allowed=LOCAL_VERIFICATION_STATUSES,
    )
    for key in ("privacy_risk", "policy_risk", "parser_risk"):
        _normalize_optional_keyword(source_cfg, key, path, allowed=LOCAL_RISK_LEVELS)
    _normalize_optional_keyword(
        source_cfg,
        "retention_sensitivity",
        path,
        allowed=LOCAL_RETENTION_SENSITIVITIES,
    )

    is_social = source_class == "social_candidate" or source_family in LOCAL_SOCIAL_SOURCE_FAMILIES
    if is_social and not bool(local_cfg.get("allow_social_sources")):
        raise ConfigError(
            f"{path} is a LOCAL social source; set local.allow_social_sources true first."
        )
    if source_class == "neighborhood_blog" and not bool(
        local_cfg.get("allow_neighborhood_blogs")
    ):
        raise ConfigError(
            f"{path} is a LOCAL neighborhood blog source; set "
            "local.allow_neighborhood_blogs true first."
        )


def _normalize_regional_source_metadata(
    source_cfg: dict[str, Any],
    *,
    path: str,
    regional_cfg: dict[str, Any],
) -> None:
    source_family = _normalize_optional_keyword(source_cfg, "source_family", path)
    source_class = _normalize_optional_keyword(
        source_cfg,
        "source_class",
        path,
        allowed=REGIONAL_SOURCE_CLASSES,
    )
    _normalize_optional_keyword(source_cfg, "adapter", path, allowed=REGIONAL_ADAPTER_TYPES)
    _normalize_optional_keyword(
        source_cfg,
        "verification_status",
        path,
        allowed=REGIONAL_VERIFICATION_STATUSES,
    )
    for key in ("privacy_risk", "policy_risk", "parser_risk"):
        _normalize_optional_keyword(source_cfg, key, path, allowed=REGIONAL_RISK_LEVELS)
    _normalize_optional_keyword(
        source_cfg,
        "retention_sensitivity",
        path,
        allowed=REGIONAL_RISK_LEVELS,
    )

    is_social = source_class == "social_candidate" or source_family in LOCAL_SOCIAL_SOURCE_FAMILIES
    if is_social and not bool(regional_cfg.get("allow_social_sources")):
        raise ConfigError(
            f"{path} is a REGIONAL social source; set regional.allow_social_sources true first."
        )
    if source_cfg.get("kind") in NEWS_HOMEPAGE_SOURCE_KINDS and not bool(
        regional_cfg.get("allow_homepage_extractors")
    ):
        raise ConfigError(
            f"{path} kind uses homepage extraction; set regional.allow_homepage_extractors true "
            "first."
        )


def _normalize_global_source_metadata(
    source_cfg: dict[str, Any], *, path: str, global_cfg: dict[str, Any]
) -> None:
    from console1701.news.global_registry import (
        GLOBAL_ADAPTER_TYPES,
        GLOBAL_AUTH_REQUIRED_SOURCE_KEYS,
        GLOBAL_FUTURE_PHASES,
        GLOBAL_OFFICIAL_STATUSES,
        GLOBAL_RISK_LEVELS,
        GLOBAL_SOURCE_CLASSES,
        GLOBAL_SOURCE_FAMILIES,
        GLOBAL_VERIFICATION_STATUSES,
    )

    _normalize_optional_keyword(source_cfg, "source_family", path, allowed=GLOBAL_SOURCE_FAMILIES)
    source_class = _normalize_optional_keyword(
        source_cfg, "source_class", path, allowed=GLOBAL_SOURCE_CLASSES
    )
    _normalize_optional_keyword(source_cfg, "adapter", path, allowed=GLOBAL_ADAPTER_TYPES)
    _normalize_optional_keyword(
        source_cfg, "official_status", path, allowed=GLOBAL_OFFICIAL_STATUSES
    )
    _normalize_optional_keyword(
        source_cfg, "verification_status", path, allowed=GLOBAL_VERIFICATION_STATUSES
    )
    future_phase = _normalize_optional_keyword(
        source_cfg, "future_phase", path, allowed={phase.lower() for phase in GLOBAL_FUTURE_PHASES}
    )
    if future_phase:
        source_cfg["future_phase"] = future_phase.upper()
    for key in ("privacy_risk", "policy_risk", "parser_risk", "retention_sensitivity"):
        _normalize_optional_keyword(source_cfg, key, path, allowed=GLOBAL_RISK_LEVELS)
    source_cfg["conflict_sensitive"] = _coerce_bool(
        source_cfg.get(
            "conflict_sensitive", source_class == "official_conflict_humanitarian"
        ),
        f"{path}.conflict_sensitive",
    )
    source_cfg["sensitivity_flags"] = _normalize_string_list(
        source_cfg.get("sensitivity_flags", []), f"{path}.sensitivity_flags"
    )
    supported_sensitivity_flags = {
        "conflict_adjacent", "war_ticker", "graphic_violence", "casualty_speculation",
        "targeted_person_tracking", "private_distress", "doxxing", "source_laundering",
    }
    if any(flag not in supported_sensitivity_flags for flag in source_cfg["sensitivity_flags"]):
        raise ConfigError(f"{path}.sensitivity_flags contains an unsupported value.")

    source_enabled = _coerce_bool(source_cfg.get("enabled", False), f"{path}.enabled")
    auth_required = (
        source_cfg.get("id") in GLOBAL_AUTH_REQUIRED_SOURCE_KEYS
        or source_cfg.get("auth") is not None
    )
    if source_enabled and auth_required and not global_cfg["allow_auth_required_sources"]:
        raise ConfigError(
            f"{path} requires auth; set global.allow_auth_required_sources true first."
        )
    if "policy_reviewed" in source_cfg:
        source_cfg["policy_reviewed"] = _coerce_bool(
            source_cfg["policy_reviewed"], f"{path}.policy_reviewed"
        )
    if (
        source_enabled
        and source_class == "official_conflict_humanitarian"
        and source_cfg.get("policy_risk") == "high"
        and global_cfg["conflict_sources_require_policy_review"]
        and not source_cfg.get("policy_reviewed")
    ):
        raise ConfigError(f"{path} requires recorded GLOBAL conflict-source policy review.")


def _normalize_news_source(
    source: Any,
    *,
    scope: str,
    index: int,
    allow_homepage_extractors: bool,
    local_cfg: dict[str, Any],
    regional_cfg: dict[str, Any],
    national_cfg: dict[str, Any],
    global_cfg: dict[str, Any],
    orbital_cfg: dict[str, Any],
    seen_source_keys: set[tuple[str, str]],
) -> dict[str, Any]:
    path = f"news.scopes.{scope}.sources[{index}]"
    source_cfg = _require_mapping(source, path)

    source_key = _require_string(source_cfg.get("id"), f"{path}.id")
    scoped_key = (scope, source_key)
    if scoped_key in seen_source_keys:
        raise ConfigError(f"Duplicate news source id within {scope}: {source_key}")
    seen_source_keys.add(scoped_key)

    source_cfg = _apply_scope_registry_defaults(source_cfg, scope)
    source_cfg["id"] = source_key
    source_cfg["name"] = _require_string(source_cfg.get("name"), f"{path}.name")
    source_cfg["kind"] = _require_string(source_cfg.get("kind"), f"{path}.kind")
    source_cfg["kind"] = source_cfg["kind"].lower()
    if source_cfg["kind"] not in NEWS_SOURCE_KINDS:
        raise ConfigError(
            f"{path}.kind must be one of: {', '.join(sorted(NEWS_SOURCE_KINDS))}."
        )
    if (
        source_cfg["kind"] in NEWS_HOMEPAGE_SOURCE_KINDS
        and not allow_homepage_extractors
        and scope != "GLOBAL"
    ):
        raise ConfigError(
            f"{path}.kind uses homepage extraction, but "
            "news.fetch_policy.allow_homepage_extractors is false."
        )

    source_scope = str(source_cfg.get("scope") or scope).upper()
    if source_scope not in NEWS_SCOPES:
        raise ConfigError(f"{path}.scope must be one of: {', '.join(NEWS_SCOPES)}.")
    if source_scope != scope:
        raise ConfigError(f"{path}.scope must match parent scope {scope}.")
    source_cfg["scope"] = source_scope
    if source_scope == "LOCAL":
        _normalize_local_source_metadata(source_cfg, path=path, local_cfg=local_cfg)
    if source_scope == "REGIONAL":
        _normalize_regional_source_metadata(source_cfg, path=path, regional_cfg=regional_cfg)
    if source_scope == "NATIONAL":
        from console1701.news.national_registry import (
            NATIONAL_ADAPTER_TYPES,
            NATIONAL_OFFICIAL_STATUSES,
            NATIONAL_RISK_LEVELS,
            NATIONAL_SOURCE_CLASSES,
            NATIONAL_VERIFICATION_STATUSES,
        )

        _normalize_optional_keyword(source_cfg, "source_family", path)
        if "economic_release_terms" in source_cfg:
            source_cfg["economic_release_terms"] = _normalize_string_list(
                source_cfg["economic_release_terms"], f"{path}.economic_release_terms"
            )[:20]
        _normalize_optional_keyword(
            source_cfg, "source_class", path, allowed=NATIONAL_SOURCE_CLASSES
        )
        _normalize_optional_keyword(source_cfg, "adapter", path, allowed=NATIONAL_ADAPTER_TYPES)
        _normalize_optional_keyword(
            source_cfg, "official_status", path, allowed=NATIONAL_OFFICIAL_STATUSES
        )
        _normalize_optional_keyword(
            source_cfg,
            "verification_status",
            path,
            allowed=NATIONAL_VERIFICATION_STATUSES,
        )
        for key in ("privacy_risk", "policy_risk", "parser_risk", "retention_sensitivity"):
            _normalize_optional_keyword(source_cfg, key, path, allowed=NATIONAL_RISK_LEVELS)
        if str(source_cfg.get("parser") or "").strip().lower() == "usgs_earthquake_geojson":
            source_cfg.setdefault(
                "min_magnitude", national_cfg["earthquake_min_magnitude"]
            )
        source_family = str(source_cfg.get("source_family") or "").strip().lower()
        source_class = str(source_cfg.get("source_class") or "").strip().lower()
        if (
            source_class == "social_candidate" or source_family in LOCAL_SOCIAL_SOURCE_FAMILIES
        ) and not national_cfg["include_social_sources"]:
            raise ConfigError(
                f"{path} is a NATIONAL social source; set "
                "national.include_social_sources true first."
            )
    if source_scope == "GLOBAL":
        _normalize_global_source_metadata(source_cfg, path=path, global_cfg=global_cfg)
        if str(source_cfg.get("parser") or "").strip().lower() == "usgs_earthquake_geojson":
            source_cfg.setdefault("min_magnitude", global_cfg["earthquake_min_magnitude"])
        if (source_key == "usgs_eq_geojson_global" and source_cfg.get("enabled")
                and str(source_cfg.get("url") or "").startswith("https://")):
            from console1701.news.official_http import USGS_GLOBAL_EARTHQUAKES_URL

            interval = _coerce_int(
                source_cfg.get("interval_minutes", 0), f"{path}.interval_minutes", minimum=30
            )
            if (
                source_cfg["url"] != USGS_GLOBAL_EARTHQUAKES_URL
                or source_cfg.get("parser") != "usgs_earthquake_geojson"
                or source_cfg["kind"] != "api_json"
                or source_cfg.get("verification_status") != "verified"
            ):
                raise ConfigError(f"{path} must use the verified GLOBAL USGS feed contract.")
            source_cfg["interval_minutes"] = interval
    if source_scope == "ORBITAL":
        from console1701.news.orbital_registry import (
            ORBITAL_ADAPTER_TYPES,
            ORBITAL_OFFICIAL_STATUSES,
            ORBITAL_RISK_LEVELS,
            ORBITAL_SOURCE_CLASSES,
            ORBITAL_SOURCE_FAMILIES,
            ORBITAL_VERIFICATION_STATUSES,
        )

        _normalize_optional_keyword(
            source_cfg, "source_family", path, allowed=ORBITAL_SOURCE_FAMILIES
        )
        _normalize_optional_keyword(
            source_cfg, "source_class", path, allowed=ORBITAL_SOURCE_CLASSES
        )
        _normalize_optional_keyword(source_cfg, "adapter", path, allowed=ORBITAL_ADAPTER_TYPES)
        _normalize_optional_keyword(
            source_cfg, "official_status", path, allowed=ORBITAL_OFFICIAL_STATUSES
        )
        _normalize_optional_keyword(
            source_cfg, "verification_status", path, allowed=ORBITAL_VERIFICATION_STATUSES
        )
        for key in ("privacy_risk", "policy_risk", "parser_risk", "retention_sensitivity"):
            _normalize_optional_keyword(source_cfg, key, path, allowed=ORBITAL_RISK_LEVELS)
        if str(source_cfg.get("parser") or "").strip().lower() == "swpc_aurora_json":
            source_cfg["aurora_locations"] = orbital_cfg["aurora_locations"]
        if str(source_cfg.get("parser") or "").strip().lower() == "swpc_kp_json":
            source_cfg["min_k_index"] = orbital_cfg["kp_min_index"]
        if str(source_cfg.get("parser") or "").strip().lower() == "jpl_cad_json":
            source_cfg["max_lunar_distance"] = orbital_cfg["neo_max_lunar_distance"]
            source_cfg["min_diameter_km"] = orbital_cfg["neo_min_diameter_km"]
        if str(source_cfg.get("parser") or "").strip().lower() == "jpl_fireball_json":
            source_cfg["min_impact_kt"] = orbital_cfg["fireball_min_impact_kt"]
            source_cfg["max_age_days"] = orbital_cfg["fireball_max_age_days"]
    if source_scope == "SYSTEM_SOLAR":
        from console1701.news.science_registry import get_science_source_registry_entry
        from console1701.news.science_sources import SCIENCE_FIXTURE_SOURCES

        fixture = SCIENCE_FIXTURE_SOURCES.get(source_key)
        registry = get_science_source_registry_entry(source_key)
        url = str(source_cfg.get("url") or "")
        is_fixture = url.startswith("file://") and source_cfg.get("fixture_only") is True
        is_verified_live = (
            source_key == "esa_space_science_feed"
            and fixture is not None
            and url == fixture[1]
            and source_cfg.get("fixture_only") is False
            and source_cfg["kind"] == "rss"
        )
        if (
            fixture is None
            or registry is None
            or source_cfg.get("parser") != fixture[0]
            or source_cfg.get("official_url") != fixture[1]
            or not (is_fixture or is_verified_live)
            or source_cfg["kind"] not in {"rss", "api_json", "local_file_json"}
        ):
            raise ConfigError(
                f"{path} must be an exact COSMIC fixture or the verified ESA live RSS source."
            )
        for field in (
            "source_family", "source_class", "official_status",
            "verification_status", "expected_access_kind",
        ):
            if field in source_cfg and source_cfg[field] != registry[field]:
                raise ConfigError(f"{path}.{field} must match the science registry.")
            source_cfg[field] = registry[field]
        if is_verified_live:
            source_cfg["interval_minutes"] = _coerce_int(
                source_cfg.get("interval_minutes", 60), f"{path}.interval_minutes", minimum=60
            )

    source_cfg["enabled"] = _coerce_bool(source_cfg.get("enabled", False), f"{path}.enabled")
    source_cfg["priority"] = _coerce_int(source_cfg.get("priority", 50), f"{path}.priority")
    if "interval_minutes" in source_cfg:
        source_cfg["interval_minutes"] = _coerce_int(
            source_cfg["interval_minutes"],
            f"{path}.interval_minutes",
            minimum=0,
        )
    if "timeout_seconds" in source_cfg:
        source_cfg["timeout_seconds"] = _coerce_int(
            source_cfg["timeout_seconds"],
            f"{path}.timeout_seconds",
            minimum=1,
        )
    if "retention_days" in source_cfg:
        source_cfg["retention_days"] = _coerce_int(
            source_cfg["retention_days"],
            f"{path}.retention_days",
            minimum=1,
        )
    source_cfg["tags"] = _normalize_string_list(source_cfg.get("tags", []), f"{path}.tags")
    source_cfg["evidence_notes"] = _normalize_string_list(
        source_cfg.get("evidence_notes", []),
        f"{path}.evidence_notes",
    )

    if "selectors" in source_cfg and source_cfg["kind"] not in NEWS_HOMEPAGE_SOURCE_KINDS:
        raise ConfigError(f"{path}.selectors are only valid for homepage_headlines sources.")
    if "auth" in source_cfg:
        _require_mapping(source_cfg["auth"], f"{path}.auth")

    return source_cfg


def normalize_news_config(config: dict[str, Any]) -> None:
    news = _require_mapping(config.setdefault("news", deepcopy(DEFAULT_NEWS_CONFIG)), "news")
    local_cfg = _require_mapping(
        config.setdefault("local", deepcopy(DEFAULT_LOCAL_CONFIG)),
        "local",
    )
    regional_cfg = _require_mapping(
        config.setdefault("regional", deepcopy(DEFAULT_REGIONAL_CONFIG)),
        "regional",
    )
    national_cfg = _require_mapping(
        config.setdefault("national", deepcopy(DEFAULT_NATIONAL_CONFIG)),
        "national",
    )
    global_cfg = _require_mapping(
        config.setdefault("global", deepcopy(DEFAULT_GLOBAL_CONFIG)),
        "global",
    )
    orbital_cfg = _require_mapping(
        config.setdefault("orbital", deepcopy(DEFAULT_ORBITAL_CONFIG)),
        "orbital",
    )
    news["enabled"] = _coerce_bool(news.get("enabled", False), "news.enabled")

    retention = _require_mapping(news.setdefault("retention", {}), "news.retention")
    retention["items_days"] = _coerce_int(
        retention.get("items_days", 7),
        "news.retention.items_days",
        minimum=1,
    )
    retention["fetch_runs_days"] = _coerce_int(
        retention.get("fetch_runs_days", 14),
        "news.retention.fetch_runs_days",
        minimum=1,
    )
    retention["source_health_days"] = _coerce_int(
        retention.get("source_health_days", 30),
        "news.retention.source_health_days",
        minimum=1,
    )
    retention["raw_payload_debug_enabled"] = _coerce_bool(
        retention.get("raw_payload_debug_enabled", False),
        "news.retention.raw_payload_debug_enabled",
    )
    retention["raw_payload_debug_ttl_hours"] = _coerce_int(
        retention.get("raw_payload_debug_ttl_hours", 6),
        "news.retention.raw_payload_debug_ttl_hours",
        minimum=1,
    )

    fetch_policy = _require_mapping(news.setdefault("fetch_policy", {}), "news.fetch_policy")
    fetch_policy["global_concurrency"] = _coerce_int(
        fetch_policy.get("global_concurrency", 2),
        "news.fetch_policy.global_concurrency",
        minimum=1,
    )
    fetch_policy["default_timeout_seconds"] = _coerce_int(
        fetch_policy.get("default_timeout_seconds", 10),
        "news.fetch_policy.default_timeout_seconds",
        minimum=1,
    )
    fetch_policy["default_interval_minutes"] = _coerce_int(
        fetch_policy.get("default_interval_minutes", 30),
        "news.fetch_policy.default_interval_minutes",
        minimum=0,
    )
    fetch_policy["default_backoff_minutes"] = _coerce_int(
        fetch_policy.get("default_backoff_minutes", 120),
        "news.fetch_policy.default_backoff_minutes",
        minimum=1,
    )
    fetch_policy["max_response_bytes"] = _coerce_int(
        fetch_policy.get("max_response_bytes", 1048576),
        "news.fetch_policy.max_response_bytes",
        minimum=1,
    )
    fetch_policy["user_agent"] = _require_string(
        fetch_policy.get("user_agent", "console-1701 local recent-signal monitor"),
        "news.fetch_policy.user_agent",
    )
    if len(fetch_policy["user_agent"]) > 256 or any(
        char in fetch_policy["user_agent"] for char in "\r\n"
    ):
        raise ConfigError("news.fetch_policy.user_agent must be one line of at most 256 chars.")
    fetch_policy["allow_official_http"] = _coerce_bool(
        fetch_policy.get("allow_official_http", False),
        "news.fetch_policy.allow_official_http",
    )
    fetch_policy["page_load_external_fetches"] = _coerce_bool(
        fetch_policy.get("page_load_external_fetches", False),
        "news.fetch_policy.page_load_external_fetches",
    )
    if fetch_policy["page_load_external_fetches"]:
        raise ConfigError("news.fetch_policy.page_load_external_fetches must remain false.")
    fetch_policy["respect_robots_txt"] = _coerce_bool(
        fetch_policy.get("respect_robots_txt", True),
        "news.fetch_policy.respect_robots_txt",
    )
    fetch_policy["allow_homepage_extractors"] = _coerce_bool(
        fetch_policy.get("allow_homepage_extractors", False),
        "news.fetch_policy.allow_homepage_extractors",
    )

    scopes = _require_mapping(news.setdefault("scopes", {}), "news.scopes")
    unknown_scopes = sorted(set(scopes) - set(NEWS_SCOPES))
    if unknown_scopes:
        raise ConfigError(f"Unknown news scope(s): {', '.join(unknown_scopes)}.")

    seen_source_keys: set[tuple[str, str]] = set()
    for scope in NEWS_SCOPES:
        scope_cfg = _require_mapping(
            scopes.setdefault(
                scope,
                {"enabled": False, "label": NEWS_SCOPE_LABELS[scope], "sources": []},
            ),
            f"news.scopes.{scope}",
        )
        scope_cfg["enabled"] = _coerce_bool(
            scope_cfg.get("enabled", False),
            f"news.scopes.{scope}.enabled",
        )
        scope_cfg["label"] = _require_string(
            scope_cfg.get("label", NEWS_SCOPE_LABELS[scope]),
            f"news.scopes.{scope}.label",
        )
        sources = scope_cfg.setdefault("sources", [])
        if not isinstance(sources, list):
            raise ConfigError(f"news.scopes.{scope}.sources must be a list.")
        scope_cfg["sources"] = [
            _normalize_news_source(
                source,
                scope=scope,
                index=index,
                allow_homepage_extractors=fetch_policy["allow_homepage_extractors"],
                local_cfg=local_cfg,
                regional_cfg=regional_cfg,
                national_cfg=national_cfg,
                global_cfg=global_cfg,
                orbital_cfg=orbital_cfg,
                seen_source_keys=seen_source_keys,
            )
            for index, source in enumerate(sources)
        ]


def iter_news_sources(config: dict[str, Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for scope in NEWS_SCOPES:
        scope_cfg = ((config.get("news") or {}).get("scopes") or {}).get(scope) or {}
        for source in scope_cfg.get("sources") or []:
            sources.append(source)
    return sources


def ensure_state_dirs(config: dict[str, Any] | None = None) -> None:
    state_dir = Path((config or {}).get("_state_dir", DEFAULT_STATE_DIR))
    handoff_dir = Path((config or {}).get("_handoff_dir", DEFAULT_HANDOFF_DIR))
    state_dir.mkdir(parents=True, exist_ok=True)
    handoff_dir.mkdir(parents=True, exist_ok=True)


def default_config_text() -> str:
    yaml = _yaml_module()
    return yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False)


def init_config(path: str | Path | None = None, overwrite: bool = False) -> Path:
    config_path = config_path_from_arg(str(path)) if path else DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists() and not overwrite:
        return config_path
    config_path.write_text(default_config_text(), encoding="utf-8")
    return config_path


def project_for_path(config: dict[str, Any], repo_path: str | Path) -> dict[str, Any]:
    repo = str(expand_path(repo_path))
    for project in config.get("projects", []):
        if project.get("path") == repo:
            return project
    return {}
