from __future__ import annotations

from pathlib import Path

from console1701.db import connect_db, init_db
from console1701.handoff import build_handoff_markdown, create_handoff_packet


def _insert_repo(conn) -> int:
    created_at = "2026-05-03T12:00:00-07:00"
    cursor = conn.execute(
        """
        INSERT INTO repos (name, path, enabled, created_at, updated_at)
        VALUES (?, ?, 1, ?, ?)
        """,
        ("ufo-records", "/tmp/ufo-records", created_at, created_at),
    )
    conn.commit()
    return int(cursor.lastrowid)


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


def test_create_handoff_packet_keeps_duplicate_titles_as_separate_files(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    repo_id = _insert_repo(conn)
    config = {"_handoff_dir": str(tmp_path / "handoffs")}

    first = create_handoff_packet(
        conn,
        config,
        repo_id=repo_id,
        task="Review the first packet.",
        title="Daily review",
    )
    second = create_handoff_packet(
        conn,
        config,
        repo_id=repo_id,
        task="Review the second packet.",
        title="Daily review",
    )

    assert first["path"] != second["path"]
    assert "Review the first packet." in Path(first["path"]).read_text(encoding="utf-8")
    assert "Review the second packet." in Path(second["path"]).read_text(encoding="utf-8")
    rows = conn.execute("SELECT path FROM handoff_packets ORDER BY id").fetchall()
    assert [row["path"] for row in rows] == [first["path"], second["path"]]
