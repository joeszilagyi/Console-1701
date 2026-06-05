from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

APP_NAME = "console-1701"
DEFAULT_CONFIG_PATH = Path.home() / ".config" / APP_NAME / "config.yml"
DEFAULT_STATE_DIR = Path.home() / ".local" / "state" / APP_NAME
DEFAULT_DB_PATH = DEFAULT_STATE_DIR / "console.sqlite"
DEFAULT_HANDOFF_DIR = DEFAULT_STATE_DIR / "handoffs"

NEWS_SCOPES = ("LOCAL", "REGIONAL", "NATIONAL", "GLOBAL", "ORBITAL")
NEWS_SCOPE_LABELS = {
    "LOCAL": "Seattle",
    "REGIONAL": "Washington / PNW",
    "NATIONAL": "United States",
    "GLOBAL": "World",
    "ORBITAL": "Orbital",
}
NEWS_SOURCE_KINDS = {
    "rss",
    "atom",
    "api_json",
    "open_data_json",
    "homepage_headlines",
    "local_file_json",
    "local_file_rss",
}
NEWS_HOMEPAGE_SOURCE_KINDS = {"homepage_headlines"}
REGIONAL_SOURCE_CLASSES = {
    "county_emergency",
    "local_tv_radio",
    "official_alert",
    "official_air_quality",
    "official_seismic_volcano",
    "official_transport",
    "official_utility",
    "official_wildfire",
    "official_weather_hazard",
    "policy_reference",
    "regional_news",
    "social_candidate",
    "source_health_only",
    "unofficial_aggregator",
}
REGIONAL_ADAPTER_TYPES = {
    "api_json",
    "atom",
    "disabled",
    "generic_json_items",
    "manual_review_only",
    "official_api_json",
    "rss",
    "rss_atom",
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
    },
    "paths": {
        "repo_roots": ["~/projects", "~/wiki"],
        "explicit_repos": [
            "~/projects/console-1701/main",
            "~/projects/ufo-records",
            "~/projects/TCL",
            "~/wiki",
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
    "logs": [
        {
            "name": "ufo-actions",
            "path": "~/wiki/ufo-actions.log",
            "type": "ufo_actions",
            "enabled": True,
        },
        {"name": "codex", "path": "~/.codex", "type": "codex", "enabled": True},
    ],
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
        {
            "name": "wiki",
            "path": "~/wiki",
            "role": (
                "Working area for prompts, article drafts, logs, country runs, "
                "and source machinery"
            ),
            "category": "Research workbench",
            "importance": "critical",
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

    normalize_local_config(config)
    normalize_regional_config(config)
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
    if scope not in {"LOCAL", "REGIONAL"}:
        return source_cfg
    source_key = str(source_cfg.get("id") or "").strip()
    if not source_key:
        return source_cfg
    if scope == "LOCAL":
        from console1701.news.local_registry import local_registry_config_defaults

        defaults = local_registry_config_defaults(source_key)
    else:
        from console1701.news.regional_registry import regional_registry_config_defaults

        defaults = regional_registry_config_defaults(source_key)
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


def _normalize_news_source(
    source: Any,
    *,
    scope: str,
    index: int,
    allow_homepage_extractors: bool,
    local_cfg: dict[str, Any],
    regional_cfg: dict[str, Any],
    seen_source_keys: set[str],
) -> dict[str, Any]:
    path = f"news.scopes.{scope}.sources[{index}]"
    source_cfg = _require_mapping(source, path)

    source_key = _require_string(source_cfg.get("id"), f"{path}.id")
    if source_key in seen_source_keys:
        raise ConfigError(f"Duplicate news source id: {source_key}")
    seen_source_keys.add(source_key)

    source_cfg = _apply_scope_registry_defaults(source_cfg, scope)
    source_cfg["id"] = source_key
    source_cfg["name"] = _require_string(source_cfg.get("name"), f"{path}.name")
    source_cfg["kind"] = _require_string(source_cfg.get("kind"), f"{path}.kind")
    source_cfg["kind"] = source_cfg["kind"].lower()
    if source_cfg["kind"] not in NEWS_SOURCE_KINDS:
        raise ConfigError(
            f"{path}.kind must be one of: {', '.join(sorted(NEWS_SOURCE_KINDS))}."
        )
    if source_cfg["kind"] in NEWS_HOMEPAGE_SOURCE_KINDS and not allow_homepage_extractors:
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

    seen_source_keys: set[str] = set()
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
