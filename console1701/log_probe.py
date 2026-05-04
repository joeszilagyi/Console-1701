from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_LOG_TAIL_MAX_BYTES = 262_144
MAX_DIRECTORY_CANDIDATES = 100
DEFAULT_DIRECTORY_FILE_LIMIT = 8
MAX_LINES_PER_FILE = 200
MAX_MESSAGE_CHARS = 1000
MAX_RAW_LINE_CHARS = 4000
TEXT_LOG_SUFFIXES = frozenset({".log", ".jsonl", ".txt"})


def _now() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def _fingerprint(source: str, source_path: str, raw_line: str) -> str:
    material = "\x1f".join([source, source_path, raw_line])
    return hashlib.sha256(material.encode("utf-8", "replace")).hexdigest()


def _status_event(
    source: str,
    source_path: str | Path,
    *,
    severity: str,
    category: str,
    message: str,
    raw_line: str = "",
) -> dict[str, Any]:
    path_text = str(source_path)
    return {
        "source": source,
        "source_path": path_text,
        "event_time": None,
        "observed_at": _now(),
        "severity": severity,
        "category": category,
        "message": message,
        "raw_line": raw_line,
        "fingerprint": _fingerprint(source, path_text, raw_line or category),
    }


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def tail_file(path: Path, max_bytes: int) -> str:
    max_bytes = max(0, max_bytes)
    if max_bytes == 0:
        return ""
    with path.open("rb") as handle:
        try:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(size - max_bytes, 0))
        except OSError:
            handle.seek(0)
        data = handle.read(max_bytes)
    return data.decode("utf-8", errors="replace")


def classify_message(message: str) -> tuple[str, str]:
    upper = message.upper()
    if "TEST_FAIL" in upper or "PYTEST FAILED" in upper or "FAILED" in upper:
        return "red", "TEST_FAIL"
    if "ERROR" in upper or "TRACEBACK" in upper or "FATAL" in upper:
        return "red", "ERROR"
    if "WARN" in upper:
        return "yellow", "WARN"
    if "TEST_PASS" in upper or "PASSED" in upper:
        return "green", "TEST_PASS"
    if "START" in upper:
        return "blue", "START"
    if "STOP" in upper or "DONE" in upper:
        return "blue", "STOP"
    if "EXPORT" in upper:
        return "blue", "EXPORT"
    if "IMPORT" in upper:
        return "blue", "IMPORT"
    if "CODEX" in upper:
        return "blue", "CODEX_RUN"
    return "gray", "UNKNOWN"


def parse_log_line(source: str, source_path: Path, raw_line: str) -> dict[str, Any]:
    observed = _now()
    line = raw_line.rstrip("\n")
    event_time = None
    message = line
    category = "UNKNOWN"
    severity = "gray"

    if line.strip():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            event_time = (
                payload.get("timestamp")
                or payload.get("time")
                or payload.get("created_at")
                or payload.get("event_time")
            )
            message = str(
                payload.get("message")
                or payload.get("event")
                or payload.get("entrypoint")
                or payload
            )
            severity, category = classify_message(
                " ".join(str(value) for value in payload.values())
            )
        else:
            severity, category = classify_message(line)

    return {
        "source": source,
        "source_path": str(source_path),
        "event_time": event_time,
        "observed_at": observed,
        "severity": severity,
        "category": category,
        "message": message[:MAX_MESSAGE_CHARS],
        "raw_line": line[:MAX_RAW_LINE_CHARS],
        "fingerprint": _fingerprint(source, str(source_path), line),
    }


def _recent_directory_files(path: Path, limit: int = DEFAULT_DIRECTORY_FILE_LIMIT) -> list[Path]:
    candidates: list[Path] = []
    try:
        for child in path.rglob("*"):
            if not child.is_file():
                continue
            if child.suffix.lower() not in TEXT_LOG_SUFFIXES:
                continue
            candidates.append(child)
            if len(candidates) > MAX_DIRECTORY_CANDIDATES:
                break
    except OSError:
        return []
    candidates.sort(key=_safe_mtime, reverse=True)
    return candidates[:limit]


def probe_configured_logs(config: dict[str, Any]) -> list[dict[str, Any]]:
    scan_config = config.get("scan", {})
    if not isinstance(scan_config, dict):
        scan_config = {}
    max_bytes = _positive_int(
        scan_config.get("log_tail_max_bytes"),
        DEFAULT_LOG_TAIL_MAX_BYTES,
    )
    events: list[dict[str, Any]] = []
    logs_config = config.get("logs", [])
    if not isinstance(logs_config, list):
        return [
            _status_event(
                "log",
                "<invalid-logs-config>",
                severity="yellow",
                category="LOG_CONFIG_ERROR",
                message="Configured logs value must be a list.",
            )
        ]
    for log in logs_config:
        if not isinstance(log, dict):
            events.append(
                _status_event(
                    "log",
                    "<invalid-log-config>",
                    severity="yellow",
                    category="LOG_CONFIG_ERROR",
                    message="Configured log entry must be a mapping.",
                )
            )
            continue
        if not log.get("enabled", True):
            continue
        source = log.get("name") or log.get("type") or "log"
        path_value = log.get("path")
        if not path_value:
            events.append(
                _status_event(
                    source,
                    "<missing-log-path>",
                    severity="yellow",
                    category="LOG_CONFIG_ERROR",
                    message="Configured log entry is missing a path.",
                )
            )
            continue
        try:
            path = Path(path_value).expanduser()
        except TypeError:
            events.append(
                _status_event(
                    source,
                    "<invalid-log-path>",
                    severity="yellow",
                    category="LOG_CONFIG_ERROR",
                    message="Configured log path must be a string or path-like value.",
                )
            )
            continue
        if not path.exists():
            events.append(
                _status_event(
                    source,
                    path,
                    severity="gray",
                    category="LOG_MISSING",
                    message="Configured log file was not found.",
                    raw_line="missing",
                )
            )
            continue
        paths = _recent_directory_files(path) if path.is_dir() else [path]
        for file_path in paths:
            try:
                tail = tail_file(file_path, max_bytes)
            except OSError as exc:
                events.append(
                    _status_event(
                        source,
                        file_path,
                        severity="yellow",
                        category="LOG_READ_ERROR",
                        message=str(exc),
                        raw_line=str(exc),
                    )
                )
                continue
            for line in tail.splitlines()[-MAX_LINES_PER_FILE:]:
                if line.strip():
                    events.append(parse_log_line(source, file_path, line))
    return events
