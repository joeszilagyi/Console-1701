from __future__ import annotations

from console1706.db import connect_db, init_db, utc_now
from console1706.evidence import get_repo_cards


def test_repo_cards_prioritize_configured_importance(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    now = utc_now()

    rows = [
        ("bug-worktree", "/tmp/bug-worktree", None),
        ("wiki", "/tmp/wiki", "critical"),
        ("console-1706", "/tmp/console-1706", "critical"),
        ("ufo-records", "/tmp/ufo-records", "high"),
    ]
    for name, path, importance in rows:
        conn.execute(
            """
            INSERT INTO repos (name, path, importance, enabled, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (name, path, importance, now, now),
        )
    conn.commit()

    cards = get_repo_cards(conn)

    assert [card["repo"]["name"] for card in cards] == [
        "console-1706",
        "wiki",
        "ufo-records",
        "bug-worktree",
    ]
