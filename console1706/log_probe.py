from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _fingerprint(source: str, source_path: str, raw_line: str) -> str:
    material = "\x1f".join([source, source_path, raw_line])
    return hashlib.sha256(material.encode("utf-8", "replace")).hexdigest()


def tail_file(path: Path, max_bytes: int) -> str:
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
        "message": message[:1000],
        "raw_line": line[:4000],
        "fingerprint": _fingerprint(source, str(source_path), line),
    }


def _recent_directory_files(path: Path, limit: int = 8) -> list[Path]:
    candidates: list[Path] = []
    try:
        for child in path.rglob("*"):
            if not child.is_file():
                continue
            if child.suffix.lower() not in {".log", ".jsonl", ".txt"}:
                continue
            candidates.append(child)
            if len(candidates) > 100:
                break
    except OSError:
        return []
    candidates.sort(key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
    return candidates[:limit]


def probe_configured_logs(config: dict[str, Any]) -> list[dict[str, Any]]:
    max_bytes = int(config.get("scan", {}).get("log_tail_max_bytes", 262144))
    events: list[dict[str, Any]] = []
    for log in config.get("logs", []):
        if not log.get("enabled", True):
            continue
        source = log.get("name") or log.get("type") or "log"
        path = Path(log["path"]).expanduser()
        if not path.exists():
            events.append(
                {
                    "source": source,
                    "source_path": str(path),
                    "event_time": None,
                    "observed_at": _now(),
                    "severity": "gray",
                    "category": "LOG_MISSING",
                    "message": "Configured log file was not found.",
                    "raw_line": "",
                    "fingerprint": _fingerprint(source, str(path), "missing"),
                }
            )
            continue
        paths = _recent_directory_files(path) if path.is_dir() else [path]
        for file_path in paths:
            try:
                tail = tail_file(file_path, max_bytes)
            except OSError as exc:
                events.append(
                    {
                        "source": source,
                        "source_path": str(file_path),
                        "event_time": None,
                        "observed_at": _now(),
                        "severity": "yellow",
                        "category": "LOG_READ_ERROR",
                        "message": str(exc),
                        "raw_line": "",
                        "fingerprint": _fingerprint(source, str(file_path), str(exc)),
                    }
                )
                continue
            for line in tail.splitlines()[-200:]:
                if line.strip():
                    events.append(parse_log_line(source, file_path, line))
    return events
