from __future__ import annotations

import hashlib
import subprocess
import time
from pathlib import Path
from typing import Any


def detect_test_support(repo_path: str | Path) -> dict[str, Any]:
    path = Path(repo_path)
    detected = False
    reasons: list[str] = []
    suggested: list[str] = []

    if (path / "pyproject.toml").exists() and (path / "tests").exists():
        detected = True
        reasons.append("pyproject.toml and tests/ found")
        suggested.append("python3 -m pytest")
    if (path / "package.json").exists():
        detected = True
        reasons.append("package.json found")
        suggested.append("npm test")
    if (path / "Makefile").exists():
        try:
            makefile = (path / "Makefile").read_text(encoding="utf-8", errors="replace")
        except OSError:
            makefile = ""
        if "\ntest:" in f"\n{makefile}":
            detected = True
            reasons.append("Makefile test target found")
            suggested.append("make test")

    return {"detected": detected, "reasons": reasons, "suggested_commands": suggested}


def should_auto_run_tests(
    repo: dict[str, Any],
    config: dict[str, Any],
    commands: list[str],
) -> bool:
    policy = config.get("test_policy", {})
    if not policy.get("auto_run", False):
        return False
    allowed = {str(item) for item in policy.get("allow_repos", [])}
    names = {str(repo.get("name")), str(repo.get("path"))}
    return bool(commands and allowed.intersection(names))


def _tail(text: str, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _fingerprint(command: str | None, repo_fingerprint: str | None, status: str, tail: str) -> str:
    material = "\x1f".join([command or "", repo_fingerprint or "", status, tail[-500:]])
    return hashlib.sha256(material.encode("utf-8", "replace")).hexdigest()


def run_test_command(command: str, repo_path: str | Path, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=repo_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        duration = time.monotonic() - started
        output = _tail("\n".join(part for part in [completed.stdout, completed.stderr] if part))
        status = "pass" if completed.returncode == 0 else "fail"
        summary = "Tests passed." if status == "pass" else "Tests failed."
        return {
            "detected": True,
            "command": command,
            "status": status,
            "duration_seconds": round(duration, 3),
            "summary": summary,
            "raw_tail": output,
        }
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        output = _tail("\n".join(part for part in [exc.stdout or "", exc.stderr or ""] if part))
        return {
            "detected": True,
            "command": command,
            "status": "timeout",
            "duration_seconds": round(duration, 3),
            "summary": f"Test command timed out after {timeout} seconds.",
            "raw_tail": output,
        }
    except OSError as exc:
        duration = time.monotonic() - started
        return {
            "detected": True,
            "command": command,
            "status": "error",
            "duration_seconds": round(duration, 3),
            "summary": str(exc),
            "raw_tail": str(exc),
        }


def build_test_snapshot(
    repo: dict[str, Any],
    snapshot: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    project_commands = repo.get("test_commands") or []
    detected = detect_test_support(repo["path"])
    commands = list(project_commands or detected["suggested_commands"])
    timeout = int(config.get("test_policy", {}).get("default_timeout_seconds", 120))

    if should_auto_run_tests(repo, config, commands):
        result = run_test_command(commands[0], repo["path"], timeout)
    elif commands or detected["detected"]:
        command = commands[0] if commands else None
        result = {
            "detected": True,
            "command": command,
            "status": "not_run",
            "duration_seconds": None,
            "summary": "Tests are configured or detected, but auto-run is disabled.",
            "raw_tail": "",
        }
    else:
        result = {
            "detected": False,
            "command": None,
            "status": "not_detected",
            "duration_seconds": None,
            "summary": "No obvious test command was detected.",
            "raw_tail": "",
        }

    result["fingerprint"] = _fingerprint(
        result.get("command"),
        snapshot.get("diff_fingerprint"),
        result["status"],
        result.get("raw_tail") or "",
    )
    return result
