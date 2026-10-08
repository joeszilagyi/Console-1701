from __future__ import annotations

from console1701.cli import main
from console1701.config import load_config
from console1701.db import connect_db, init_db
from console1701.history import history_expired_counts, prune_history_batch


def test_prune_history_preserves_latest_repo_and_host_evidence(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    conn.execute(
        "INSERT INTO repos (id, name, path, created_at, updated_at) "
        "VALUES (1, 'repo', '/tmp/repo', '2026-01-01', '2026-01-01')"
    )
    for moment in ("2026-05-01", "2026-05-02", "2026-10-01"):
        conn.execute(
            "INSERT INTO repo_snapshots (repo_id, scanned_at) VALUES (1, ?)", (moment,)
        )
        conn.execute(
            "INSERT INTO host_snapshots (scanned_at, health_state, summary_json, "
            "snapshot_json, evidence_json, errors_json) VALUES (?, 'OK', '{}', '{}', '{}', '[]')",
            (moment,),
        )
    for moment in ("2026-05-01", "2026-05-02"):
        conn.execute(
            "INSERT INTO test_snapshots (repo_id, scanned_at, status) VALUES (1, ?, 'pass')",
            (moment,),
        )
    conn.commit()

    cutoff = "2026-07-10"
    before = history_expired_counts(conn, cutoff)
    assert before["host_snapshots"] == 2
    assert before["repo_snapshots"] == 2
    assert before["test_snapshots"] == 1

    first = prune_history_batch(conn, cutoff, batch_size=1)
    second = prune_history_batch(conn, cutoff, batch_size=1)
    conn.commit()

    assert first["host_snapshots"] == 1
    assert second["host_snapshots"] == 1
    assert history_expired_counts(conn, cutoff)["host_snapshots"] == 0
    assert conn.execute("SELECT COUNT(*) FROM host_snapshots").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM repo_snapshots").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM test_snapshots").fetchone()[0] == 1


def test_prune_history_keeps_latest_interpretation_per_scope(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    conn.execute(
        "INSERT INTO repos (id, name, path, created_at, updated_at) "
        "VALUES (1, 'repo', '/tmp/repo', '2026-01-01', '2026-01-01')"
    )
    for scope, moment in (
        ("repo", "2026-05-01"),
        ("repo", "2026-05-02"),
        ("host", "2026-05-01"),
    ):
        conn.execute(
            "INSERT INTO interpreted_states (repo_id, scope, state, severity, headline, "
            "meaning, why_it_matters, next_sane_action, evidence_json, rule_ids_json, "
            "created_at) VALUES (1, ?, 'OK', 'green', '', '', '', '', '{}', '[]', ?)",
            (scope, moment),
        )
    conn.commit()

    cutoff = "2026-07-10"
    assert history_expired_counts(conn, cutoff)["interpreted_states"] == 1
    assert prune_history_batch(conn, cutoff, batch_size=10)["interpreted_states"] == 1
    remaining = conn.execute(
        "SELECT scope, created_at FROM interpreted_states ORDER BY id"
    ).fetchall()
    assert [(row["scope"], row["created_at"]) for row in remaining] == [
        ("repo", "2026-05-02"),
        ("host", "2026-05-01"),
    ]


def test_prune_history_cli_previews_then_applies_to_its_configured_database(tmp_path, capsys):
    config_path = tmp_path / "config.yml"
    config_path.write_text("sqlite:\n  history_retention_days: 90\n")
    database = load_config(config_path)["_db_path"]
    conn = connect_db(database)
    init_db(conn)
    conn.execute(
        "INSERT INTO scan_runs (started_at, status) VALUES ('2026-05-01', 'complete')"
    )
    conn.execute(
        "INSERT INTO scan_runs (started_at, status) VALUES ('2026-10-01', 'complete')"
    )
    conn.commit()
    conn.close()

    assert main(["prune-history", "--config", str(config_path)]) == 0
    assert "scan_runs=1" in capsys.readouterr().out
    with connect_db(database) as conn:
        assert conn.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0] == 2

    assert main(["prune-history", "--config", str(config_path), "--apply", "--all"]) == 0
    assert "scan_runs=1" in capsys.readouterr().out
    with connect_db(database) as conn:
        assert conn.execute("SELECT COUNT(*) FROM scan_runs").fetchone()[0] == 1
