from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from console1706.adapters import is_code_file, is_structural_file, is_test_file

SEVERITY_RANK = {
    "green": 0,
    "blue": 1,
    "gray": 1,
    "yellow": 2,
    "orange": 3,
    "red": 4,
}


def fingerprint(*parts: object) -> str:
    material = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(material.encode("utf-8", "replace")).hexdigest()


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z")
        except ValueError:
            return None


def age_days(value: str | None) -> float | None:
    parsed = parse_time(value)
    if not parsed:
        return None
    now = datetime.now(UTC).astimezone(parsed.tzinfo)
    return max((now - parsed).total_seconds(), 0) / 86400


def _test_failed(test_snapshot: dict[str, Any] | None) -> bool:
    return bool(test_snapshot and test_snapshot.get("status") in {"fail", "timeout", "error"})


def _test_passed(test_snapshot: dict[str, Any] | None) -> bool:
    return bool(test_snapshot and test_snapshot.get("status") == "pass")


def _state(
    *,
    repo_id: int | None,
    state: str,
    severity: str,
    headline: str,
    meaning: str,
    why_it_matters: str,
    next_sane_action: str,
    evidence: dict[str, Any],
    rule_ids: list[str],
) -> dict[str, Any]:
    return {
        "repo_id": repo_id,
        "scope": "repo",
        "state": state,
        "severity": severity,
        "headline": headline,
        "meaning": meaning,
        "why_it_matters": why_it_matters,
        "next_sane_action": next_sane_action,
        "evidence": evidence,
        "rule_ids": rule_ids,
    }


def _attention(
    *,
    repo_id: int | None,
    rule_id: str,
    severity: str,
    title: str,
    body: str,
    why_it_matters: str,
    next_sane_action: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "repo_id": repo_id,
        "rule_id": rule_id,
        "fingerprint": fingerprint(repo_id, rule_id, evidence.get("diff_fingerprint"), title),
        "severity": severity,
        "title": title,
        "body": body,
        "why_it_matters": why_it_matters,
        "next_sane_action": next_sane_action,
        "evidence": evidence,
    }


def evaluate_repo(
    repo: dict[str, Any],
    snapshot: dict[str, Any] | None,
    test_snapshot: dict[str, Any] | None,
    *,
    dirty_stale_hours: float = 24,
    inactive_days_warning: float = 14,
    inactive_days_stale: float = 45,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    repo_id = repo.get("id")
    importance = repo.get("importance") or "normal"
    snapshot = snapshot or {}
    clusters = snapshot.get("path_clusters") or {}
    changed_files = snapshot.get("changed_files") or []
    scan_error = snapshot.get("scan_error")
    test_status = test_snapshot.get("status") if test_snapshot else None
    recent_test_pass = _test_passed(test_snapshot)
    tests_failed = _test_failed(test_snapshot)
    dirty = bool(snapshot.get("is_dirty"))
    dirty_age_hours = clusters.get("dirty_age_hours")
    inactive_days = age_days(snapshot.get("commit_time"))

    evidence = {
        "repo": {"id": repo_id, "name": repo.get("name"), "path": repo.get("path")},
        "branch": snapshot.get("branch"),
        "commit_sha": snapshot.get("commit_sha"),
        "commit_subject": snapshot.get("commit_subject"),
        "commit_time": snapshot.get("commit_time"),
        "is_dirty": dirty,
        "has_untracked": bool(snapshot.get("has_untracked")),
        "ahead_count": snapshot.get("ahead_count"),
        "behind_count": snapshot.get("behind_count"),
        "changed_files": changed_files,
        "path_clusters": clusters,
        "test": test_snapshot,
        "scan_error": scan_error,
        "diff_fingerprint": snapshot.get("diff_fingerprint"),
    }

    attention: list[dict[str, Any]] = []

    if tests_failed:
        attention.append(
            _attention(
                repo_id=repo_id,
                rule_id="tests_failed",
                severity="red",
                title="Tests are failing",
                body="The latest test evidence for this repo is failing or timed out.",
                why_it_matters=(
                    "A failing test means recent or existing code is not matching "
                    "expected behavior."
                ),
                next_sane_action=(
                    "Open the failing test evidence and inspect the latest changed files."
                ),
                evidence=evidence,
            )
        )

    if dirty:
        code_changed = bool(clusters.get("code_changed")) or any(
            is_code_file(path) for path in changed_files
        )
        tests_changed = bool(clusters.get("tests_changed")) or any(
            is_test_file(path) for path in changed_files
        )
        if code_changed and not tests_changed and not recent_test_pass:
            attention.append(
                _attention(
                    repo_id=repo_id,
                    rule_id="code_without_test_evidence",
                    severity="orange",
                    title="Code changed without test evidence",
                    body=(
                        "Code changed, but no nearby tests changed and no fresh passing "
                        "test was found."
                    ),
                    why_it_matters=(
                        "This is where local breakage can hide behind a clean-looking "
                        "worktree summary."
                    ),
                    next_sane_action="Run or review tests before trusting this work.",
                    evidence=evidence,
                )
            )
        if bool(clusters.get("structural")) or any(
            is_structural_file(path) for path in changed_files
        ):
            attention.append(
                _attention(
                    repo_id=repo_id,
                    rule_id="structural_code_changed",
                    severity="yellow",
                    title="Structural code changed",
                    body="A file in a structural area changed. Downstream output may be affected.",
                    why_it_matters=(
                        "Schema, exporter, importer, and migration changes can alter data "
                        "or generated output."
                    ),
                    next_sane_action="Review generated output or compatibility before committing.",
                    evidence=evidence,
                )
            )
        if dirty_age_hours is not None and float(dirty_age_hours) > float(dirty_stale_hours):
            attention.append(
                _attention(
                    repo_id=repo_id,
                    rule_id="old_dirty_worktree",
                    severity="orange",
                    title="Old uncommitted work is sitting here",
                    body="This worktree has uncommitted changes and no recent file movement.",
                    why_it_matters=(
                        "Old dirty worktrees are easy to accidentally build on without "
                        "knowing what changed."
                    ),
                    next_sane_action="Review the diff before starting more work in this repo.",
                    evidence=evidence,
                )
            )

    if scan_error in {"missing_path", "not_git_repo"}:
        return (
            _state(
                repo_id=repo_id,
                state="Unknown",
                severity="gray",
                headline="Configured repo path is unavailable",
                meaning="This configured repo path does not exist or is not a Git repo right now.",
                why_it_matters=(
                    "The console cannot make a trustworthy interpretation without local evidence."
                ),
                next_sane_action="Check the config path or mount/location.",
                evidence=evidence,
                rule_ids=["missing_or_not_git_repo"],
            ),
            attention,
        )

    if scan_error == "git_timeout":
        return (
            _state(
                repo_id=repo_id,
                state="Needs attention",
                severity="orange",
                headline="Git was too slow or stuck",
                meaning="The scanner timed out while asking Git for local status.",
                why_it_matters=(
                    "Slow Git can mean a huge repo, filesystem issue, or an interrupted "
                    "operation."
                ),
                next_sane_action="Inspect repo health manually.",
                evidence=evidence,
                rule_ids=["git_timeout"],
            ),
            attention,
        )

    if scan_error:
        return (
            _state(
                repo_id=repo_id,
                state="Unknown",
                severity="gray",
                headline="Scanner could not read this repo cleanly",
                meaning="A local probe failed before the console could interpret this repo.",
                why_it_matters=(
                    "A failed probe is evidence about the scanner or filesystem, not the "
                    "code itself."
                ),
                next_sane_action="Open the evidence and fix the local read/probe problem.",
                evidence=evidence,
                rule_ids=["scan_error"],
            ),
            attention,
        )

    if tests_failed:
        return (
            _state(
                repo_id=repo_id,
                state="Broken",
                severity="red",
                headline="Tests are failing",
                meaning="This repo is currently not safe to build on without review.",
                why_it_matters=(
                    "A failing test means recent or existing code is not matching "
                    "expected behavior."
                ),
                next_sane_action=(
                    "Open the failing test evidence and inspect the latest changed files."
                ),
                evidence=evidence,
                rule_ids=["tests_failed"],
            ),
            attention,
        )

    if dirty and dirty_age_hours is not None and float(dirty_age_hours) > float(dirty_stale_hours):
        return (
            _state(
                repo_id=repo_id,
                state="Waiting on you",
                severity="orange",
                headline="Old uncommitted work is sitting here",
                meaning=(
                    "This may be abandoned work, unfinished Codex output, or something "
                    "you meant to inspect."
                ),
                why_it_matters=(
                    "Old dirty worktrees are easy to accidentally build on without "
                    "knowing what changed."
                ),
                next_sane_action="Review the diff before starting more work in this repo.",
                evidence=evidence,
                rule_ids=["dirty_stale"],
            ),
            attention,
        )

    if dirty and clusters.get("coherent") and recent_test_pass:
        return (
            _state(
                repo_id=repo_id,
                state="Needs review",
                severity="yellow",
                headline="Coherent uncommitted work looks ready for review",
                meaning="The changes appear related and tests recently passed.",
                why_it_matters=(
                    "This is often the point where a human should inspect output and commit if it "
                    "matches intent."
                ),
                next_sane_action=(
                    "Review the diff and generated output, then commit if it matches intent."
                ),
                evidence=evidence,
                rule_ids=["dirty_clustered_recent_test_pass"],
            ),
            attention,
        )

    if dirty:
        state_name = "In surgery" if clusters.get("structural") else "Active work"
        severity = "yellow" if clusters.get("structural") else "blue"
        return (
            _state(
                repo_id=repo_id,
                state=state_name,
                severity=severity,
                headline="Uncommitted local work is present",
                meaning=(
                    f"Changes are clustered around {clusters.get('primary_area', 'local files')}."
                    if clusters.get("coherent")
                    else "Changes are scattered and should be reviewed before trusting this state."
                ),
                why_it_matters=(
                    "A dirty worktree is normal during work, but it is not a stable baseline."
                ),
                next_sane_action=(
                    "Review the changed files and run tests if this is code."
                    if not recent_test_pass
                    else "Review the diff and decide whether to commit."
                ),
                evidence=evidence,
                rule_ids=["dirty_worktree"],
            ),
            attention,
        )

    if (
        inactive_days is not None
        and inactive_days > float(inactive_days_stale)
        and importance != "critical"
    ):
        return (
            _state(
                repo_id=repo_id,
                state="Dormant but preserved",
                severity="gray",
                headline="Quiet but preserved",
                meaning="No recent activity. This is not a problem unless you expected movement.",
                why_it_matters="Quiet projects should not be treated as failures by default.",
                next_sane_action="Ignore unless this project should be active.",
                evidence=evidence,
                rule_ids=["inactive_stale"],
            ),
            attention,
        )

    if recent_test_pass:
        return (
            _state(
                repo_id=repo_id,
                state="Stable",
                severity="green",
                headline="Clean and recently tested",
                meaning="This repo appears safe at the current commit.",
                why_it_matters=(
                    "Clean worktree plus recent passing tests is a strong local stability signal."
                ),
                next_sane_action="No action needed.",
                evidence=evidence,
                rule_ids=["clean_recent_test_pass"],
            ),
            attention,
        )

    if inactive_days is not None and inactive_days > float(inactive_days_warning):
        return (
            _state(
                repo_id=repo_id,
                state="Quiet",
                severity="gray",
                headline="This project has gone quiet",
                meaning="There has not been recent local Git activity.",
                why_it_matters=(
                    "Quiet is fine unless you expected Codex, a script, or yourself to be "
                    "working here."
                ),
                next_sane_action="Ignore unless this project should be active.",
                evidence=evidence,
                rule_ids=["inactive_warning"],
            ),
            attention,
        )

    return (
        _state(
            repo_id=repo_id,
            state="Stable",
            severity="green",
            headline="Clean worktree",
            meaning="Git reports no local changes. No local failure evidence was found.",
            why_it_matters=(
                "A clean worktree is the safest baseline available without fresh test evidence."
            ),
            next_sane_action=(
                "No action needed."
                if test_status != "not_run"
                else "Run tests if you need stronger confidence."
            ),
            evidence=evidence,
            rule_ids=["clean_worktree"],
        ),
        attention,
    )


def worst_severity(values: list[str], default: str = "green") -> str:
    if not values:
        return default
    return max(values, key=lambda value: SEVERITY_RANK.get(value, 0))
