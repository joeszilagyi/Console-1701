from __future__ import annotations

from console1701.codex_probe import codex_activity_hint


def test_codex_activity_hint_uses_codex_log_source_without_message_match():
    hint = codex_activity_hint(
        {"commit_subject": "ordinary work", "changed_files": [], "path_clusters": {}},
        [{"source": "codex", "category": "CODEX_RUN", "message": "Tool call: exec_command"}],
    )

    assert hint == "Codex appears to have worked here. This is a detected pattern, not proof."


def test_codex_activity_hint_uses_commit_subject():
    hint = codex_activity_hint(
        {"commit_subject": "Codex adjusted scanner", "changed_files": [], "path_clusters": {}},
    )

    assert hint == "Codex appears to have worked here. This is a detected pattern, not proof."


def test_codex_activity_hint_uses_coherent_dirty_cluster():
    hint = codex_activity_hint(
        {
            "is_dirty": True,
            "changed_files": ["console1701/api.py", "tests/test_app.py"],
            "path_clusters": {"coherent": True, "changed_count": 2},
        },
    )

    assert hint == "This looks like a coherent agent pass. This is a detected pattern, not proof."


def test_codex_activity_hint_returns_none_without_local_signal():
    hint = codex_activity_hint(
        {
            "is_dirty": False,
            "commit_subject": "manual cleanup",
            "changed_files": ["README.md"],
            "path_clusters": {"coherent": False, "changed_count": 1},
        },
        [{"source": "app", "category": "INFO", "message": "normal scan"}],
    )

    assert hint is None
