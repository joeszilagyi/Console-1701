from __future__ import annotations

import hashlib
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from console1706.adapters import cluster_changed_files, infer_adapter


class GitProbeError(RuntimeError):
    """Raised when a repo cannot be probed."""


def _run_git(repo_path: str | Path, args: list[str], timeout: int) -> tuple[int, str, str]:
    cmd = ["git", "-C", str(repo_path), *args]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, exc.stdout or "", f"Git command timed out after {timeout} seconds."
    except OSError as exc:
        return 127, "", str(exc)
    return completed.returncode, completed.stdout.rstrip("\n"), completed.stderr.strip()


def _git_stdout(repo_path: str | Path, args: list[str], timeout: int) -> str | None:
    code, stdout, _stderr = _run_git(repo_path, args, timeout)
    return stdout if code == 0 else None


def _parse_status_files(raw_status: str) -> tuple[list[str], bool]:
    files: list[str] = []
    has_untracked = False
    for line in raw_status.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:] if len(line) > 3 else ""
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if status == "??":
            has_untracked = True
        if path:
            files.append(path)
    return sorted(set(files)), has_untracked


def _parse_log_one(raw: str | None) -> dict[str, str | None]:
    if not raw:
        return {
            "commit_sha": None,
            "commit_author": None,
            "commit_time": None,
            "commit_subject": None,
        }
    parts = raw.split("\x1f", 3)
    while len(parts) < 4:
        parts.append("")
    return {
        "commit_sha": parts[0] or None,
        "commit_author": parts[1] or None,
        "commit_time": parts[2] or None,
        "commit_subject": parts[3] or None,
    }


def _parse_recent_commits(raw: str | None) -> list[dict[str, str]]:
    commits = []
    for line in (raw or "").splitlines():
        parts = line.split("\x1f", 2)
        while len(parts) < 3:
            parts.append("")
        commits.append({"sha": parts[0], "time": parts[1], "subject": parts[2]})
    return commits


def _parse_ahead_behind(raw: str | None) -> tuple[int | None, int | None]:
    if not raw:
        return None, None
    parts = raw.split()
    if len(parts) != 2:
        return None, None
    try:
        behind = int(parts[0])
        ahead = int(parts[1])
    except ValueError:
        return None, None
    return ahead, behind


def _dirty_age_hours(repo_path: Path, changed_files: list[str]) -> float | None:
    newest_mtime: float | None = None
    for file_path in changed_files:
        candidate = repo_path / file_path
        if not candidate.exists():
            continue
        try:
            mtime = candidate.stat().st_mtime
        except OSError:
            continue
        newest_mtime = mtime if newest_mtime is None else max(newest_mtime, mtime)
    if newest_mtime is None:
        return None
    age_seconds = datetime.now(UTC).timestamp() - newest_mtime
    return round(max(age_seconds, 0) / 3600, 2)


def _diff_fingerprint(
    head_sha: str | None,
    changed_files: list[str],
    shortstat: str | None,
    raw_status: str,
) -> str:
    material = "\n".join([head_sha or "", *changed_files, shortstat or "", raw_status])
    return hashlib.sha256(material.encode("utf-8", "replace")).hexdigest()


def probe_repo(
    repo_path: str | Path,
    *,
    timeout: int = 5,
    max_recent_commits: int = 8,
    max_changed_files_display: int = 80,
) -> dict[str, Any]:
    path = Path(repo_path).expanduser().resolve()
    if not path.exists():
        return {"path": str(path), "name": path.name, "scan_error": "missing_path"}
    if not (path / ".git").exists():
        code, stdout, _stderr = _run_git(path, ["rev-parse", "--is-inside-work-tree"], timeout)
        if code != 0 or stdout != "true":
            return {"path": str(path), "name": path.name, "scan_error": "not_git_repo"}

    status_code, raw_status, status_error = _run_git(
        path,
        ["status", "--porcelain=v1", "-uall"],
        timeout,
    )
    if status_code == 124:
        return {
            "path": str(path),
            "name": path.name,
            "scan_error": "git_timeout",
            "raw_git_status": status_error,
        }
    if status_code != 0:
        return {
            "path": str(path),
            "name": path.name,
            "scan_error": f"git_status_failed: {status_error}",
            "raw_git_status": raw_status,
        }

    changed_files, has_untracked = _parse_status_files(raw_status)
    branch = _git_stdout(path, ["branch", "--show-current"], timeout)
    head_sha = _git_stdout(path, ["rev-parse", "HEAD"], timeout)
    latest = _parse_log_one(
        _git_stdout(path, ["log", "-1", "--format=%H%x1f%an%x1f%ai%x1f%s"], timeout)
    )
    recent = _parse_recent_commits(
        _git_stdout(
            path,
            ["log", f"-{int(max_recent_commits)}", "--format=%h%x1f%ai%x1f%s"],
            timeout,
        )
    )

    ahead_raw = _git_stdout(
        path,
        ["rev-list", "--left-right", "--count", "@{upstream}...HEAD"],
        timeout,
    )
    ahead_count, behind_count = _parse_ahead_behind(ahead_raw)
    shortstat = _git_stdout(path, ["diff", "--shortstat"], timeout)
    diff_stat = _git_stdout(path, ["diff", "--stat"], timeout)
    diff_names = _git_stdout(path, ["diff", "--name-only"], timeout)
    worktrees = _git_stdout(path, ["worktree", "list", "--porcelain"], timeout)
    stash = _git_stdout(path, ["stash", "list"], timeout)
    stash_count = len(stash.splitlines()) if stash else 0

    display_files = changed_files[: int(max_changed_files_display)]
    adapter = infer_adapter(path.name, str(path), changed_files)
    clusters = cluster_changed_files(display_files, adapter)
    clusters["dirty_age_hours"] = _dirty_age_hours(path, changed_files)
    clusters["changed_count_total"] = len(changed_files)
    clusters["changed_files_capped"] = len(changed_files) > len(display_files)
    clusters["diff_shortstat"] = shortstat
    clusters["diff_stat"] = diff_stat
    clusters["diff_names"] = diff_names.splitlines() if diff_names else []
    clusters["worktree_count"] = len(
        [line for line in (worktrees or "").splitlines() if line.startswith("worktree ")]
    )
    clusters["stash_count"] = stash_count

    return {
        "path": str(path),
        "name": path.name,
        "branch": branch,
        "commit_sha": latest["commit_sha"] or head_sha,
        "commit_subject": latest["commit_subject"],
        "commit_author": latest["commit_author"],
        "commit_time": latest["commit_time"],
        "is_dirty": bool(raw_status.strip()),
        "has_untracked": has_untracked,
        "ahead_count": ahead_count,
        "behind_count": behind_count,
        "changed_files": display_files,
        "path_clusters": clusters,
        "recent_commits": recent,
        "diff_fingerprint": _diff_fingerprint(head_sha, changed_files, shortstat, raw_status),
        "raw_git_status": raw_status,
        "scan_error": None,
    }
