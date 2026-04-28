from __future__ import annotations

from console1706.handoff import build_handoff_markdown


def test_handoff_packet_contains_controlled_sections():
    markdown = build_handoff_markdown(
        {
            "repo": {"name": "ufo-records", "path": "/tmp/ufo-records"},
            "snapshot": {
                "branch": "main",
                "is_dirty": True,
                "commit_sha": "abc123",
                "commit_subject": "Add exporter",
                "ahead_count": None,
                "behind_count": None,
                "changed_files": ["tools/sqlite/exporters/wikipedia_cite.py"],
                "recent_commits": [],
            },
            "interpretation": {
                "headline": "Coherent uncommitted work looks ready for review",
                "state": "Needs review",
                "meaning": "The changes appear related and tests recently passed.",
                "next_sane_action": "Review the diff.",
                "evidence": {},
            },
            "test": {"command": "python3 -m pytest", "status": "pass", "summary": "Tests passed."},
            "attention": [],
        },
        task="Tell me what remains before commit.",
        generated_at="2026-04-28T12:00:00-07:00",
    )
    assert "## CONTROLLED_CONTEXT_BEGIN" in markdown
    assert "## CONTROLLED_CONTEXT_END" in markdown
    assert "## LLM_TASK_BEGIN" in markdown
    assert "Tell me what remains before commit." in markdown
    assert "## OUTPUT_CONTRACT_BEGIN" in markdown
    assert "## OUTPUT_CONTRACT_END" in markdown
