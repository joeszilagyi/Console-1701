from __future__ import annotations

from datetime import UTC, datetime, timedelta

from console1706.adapters import cluster_changed_files
from console1706.rules import evaluate_repo


def _repo(**overrides):
    data = {
        "id": 1,
        "name": "ufo-records",
        "path": "/tmp/ufo-records",
        "importance": "high",
    }
    data.update(overrides)
    return data


def _snapshot(changed_files=None, **overrides):
    changed_files = changed_files or []
    clusters = cluster_changed_files(changed_files, "ufo-records")
    data = {
        "branch": "main",
        "commit_sha": "abc123",
        "commit_subject": "latest work",
        "commit_time": datetime.now(UTC).isoformat(),
        "is_dirty": bool(changed_files),
        "has_untracked": False,
        "ahead_count": None,
        "behind_count": None,
        "changed_files": changed_files,
        "path_clusters": clusters,
        "diff_fingerprint": "fp1",
        "scan_error": None,
    }
    data.update(overrides)
    return data


def _test(status):
    return {
        "detected": True,
        "command": "python3 -m pytest",
        "status": status,
        "summary": status,
        "fingerprint": f"test-{status}",
    }


def test_clean_repo_with_recent_test_pass_is_stable():
    state, attention = evaluate_repo(_repo(), _snapshot(), _test("pass"))
    assert state["state"] == "Stable"
    assert state["severity"] == "green"
    assert attention == []


def test_dirty_clustered_exporter_changes_with_test_pass_need_review():
    changed = [
        "tools/sqlite/exporters/wikipedia_cite.py",
        "tools/sqlite/tests/test_export_bibliography.py",
    ]
    state, attention = evaluate_repo(_repo(), _snapshot(changed), _test("pass"))
    assert state["state"] == "Needs review"
    assert "dirty_clustered_recent_test_pass" in state["rule_ids"]
    assert any(item["rule_id"] == "structural_code_changed" for item in attention)


def test_dirty_old_work_waits_on_human():
    changed = ["src/module.py"]
    snapshot = _snapshot(changed)
    snapshot["path_clusters"]["dirty_age_hours"] = 25
    state, attention = evaluate_repo(_repo(), snapshot, None, dirty_stale_hours=24)
    assert state["state"] == "Waiting on you"
    assert any(item["rule_id"] == "old_dirty_worktree" for item in attention)


def test_test_failure_is_broken():
    state, attention = evaluate_repo(_repo(), _snapshot(), _test("fail"))
    assert state["state"] == "Broken"
    assert state["severity"] == "red"
    assert any(item["rule_id"] == "tests_failed" for item in attention)


def test_inactive_repo_is_dormant_but_preserved():
    old = (datetime.now(UTC) - timedelta(days=90)).isoformat()
    state, _attention = evaluate_repo(_repo(), _snapshot(commit_time=old), None)
    assert state["state"] == "Dormant but preserved"


def test_code_changed_without_tests_adds_orange_attention_item():
    state, attention = evaluate_repo(_repo(), _snapshot(["src/module.py"]), None)
    assert state["state"] == "Active work"
    item = next(item for item in attention if item["rule_id"] == "code_without_test_evidence")
    assert item["severity"] == "orange"


def test_schema_or_exporter_change_adds_structural_attention_item():
    _state, attention = evaluate_repo(_repo(), _snapshot(["schema/create_tables.sql"]), None)
    item = next(item for item in attention if item["rule_id"] == "structural_code_changed")
    assert item["severity"] == "yellow"


def test_missing_repo_is_unknown_not_crash():
    state, _attention = evaluate_repo(_repo(), _snapshot(scan_error="missing_path"), None)
    assert state["state"] == "Unknown"
    assert "missing_or_not_git_repo" in state["rule_ids"]


def test_no_upstream_is_not_broken():
    state, attention = evaluate_repo(
        _repo(),
        _snapshot(ahead_count=None, behind_count=None),
        None,
    )
    assert state["state"] != "Broken"
    assert not any(item["rule_id"] == "no_upstream" for item in attention)
