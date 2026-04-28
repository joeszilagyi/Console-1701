from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any


APP_NAME = "console-1706"
DEFAULT_CONFIG_PATH = Path.home() / ".config" / APP_NAME / "config.yml"
DEFAULT_STATE_DIR = Path.home() / ".local" / "state" / APP_NAME
DEFAULT_DB_PATH = DEFAULT_STATE_DIR / "console.sqlite"
DEFAULT_HANDOFF_DIR = DEFAULT_STATE_DIR / "handoffs"

DEFAULT_CONFIG: dict[str, Any] = {
    "server": {
        "host": "127.0.0.1",
        "port": 1706,
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
            "~/projects/console-1706/main",
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
        "allow_repos": ["console-1706", "~/projects/console-1706/main"],
    },
    "projects": [
        {
            "name": "console-1706",
            "path": "~/projects/console-1706/main",
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
    server["port"] = int(server.get("port", 1706))

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
