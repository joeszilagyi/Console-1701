from __future__ import annotations

from console1706.db import connect_db, init_db
from console1706.interpreter import upsert_attention_item


def test_same_attention_issue_is_deduped(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    item = {
        "fingerprint": "same-problem",
        "repo_id": None,
        "severity": "orange",
        "title": "Code changed without test evidence",
        "body": "Code changed, but no nearby tests changed.",
        "why_it_matters": "Breakage can hide here.",
        "next_sane_action": "Run tests.",
        "evidence": {"changed_files": ["src/a.py"]},
    }
    first_id = upsert_attention_item(conn, item)
    second_id = upsert_attention_item(conn, item)
    count = conn.execute("SELECT COUNT(*) AS count FROM attention_items").fetchone()["count"]
    assert first_id == second_id
    assert count == 1
