from __future__ import annotations

from datetime import datetime

from console1701.db import connect_db, init_db, utc_now
from console1701.evidence import (
    _host_changes,
    get_recent_events,
    get_repo_cards,
    get_system_summary,
)


def test_host_changes_identify_concrete_service_network_and_storage_transitions():
    previous = {
        "health_state": "OK",
        "snapshot": {
            "storage": {"root": {"use_percent": 84.0}},
            "services": {
                "failed_system": [{"unit": "old.service"}],
                "failed_user": [],
                "failed_system_count": 1,
                "failed_user_count": 0,
            },
            "network": {
                "default_route": {"dev": "eth0", "gateway": "192.0.2.1"},
                "interfaces": [{"ifname": "lo"}, {"ifname": "eth0"}],
                "dns": {"servers": ["192.0.2.53"]},
            },
        },
    }
    latest = {
        "health_state": "OK",
        "snapshot": {
            "storage": {"root": {"use_percent": 86.0}},
            "services": {
                "failed_system": [{"unit": "new.service"}],
                "failed_user": [],
                "failed_system_count": 1,
                "failed_user_count": 0,
            },
            "network": {
                "default_route": {"dev": "eth1", "gateway": "192.0.2.254"},
                "interfaces": [{"ifname": "lo"}, {"ifname": "eth1"}],
                "dns": {"servers": ["198.51.100.53"]},
            },
        },
    }

    assert _host_changes(latest, previous) == [
        "Root filesystem usage changed by +2.0 percentage points.",
        "Root filesystem crossed the 85% warning threshold.",
        "New failed services: system:new.service.",
        "Recovered services: system:old.service.",
        "Default route interface or gateway changed.",
        "Network interfaces appeared: eth1.",
        "Network interfaces disappeared: eth0.",
        "DNS resolver set changed.",
    ]


def test_host_changes_fall_back_to_counts_for_older_service_snapshots():
    previous = {"snapshot": {"services": {"failed_system_count": 0}, "network": {}}}
    latest = {"snapshot": {"services": {"failed_system_count": 1}, "network": {}}}

    assert _host_changes(latest, previous) == ["Failed service count changed from 0 to 1."]


def test_repo_cards_prioritize_configured_importance(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    now = utc_now()

    rows = [
        ("bug-worktree", "/tmp/bug-worktree", None),
        ("wiki", "/tmp/wiki", "critical"),
        ("console-1701", "/tmp/console-1701", "critical"),
        ("ufo-records", "/tmp/ufo-records", "high"),
    ]
    repo_ids: dict[str, int] = {}
    for name, path, importance in rows:
        conn.execute(
            """
            INSERT INTO repos (name, path, importance, enabled, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (name, path, importance, now, now),
        )
        repo_ids[name] = conn.execute(
            "SELECT id FROM repos WHERE path = ?",
            (path,),
        ).fetchone()["id"]
    snapshots = [
        (repo_ids["wiki"], "2026-04-28T12:00:00-07:00"),
        (repo_ids["console-1701"], "2026-04-28T10:00:00-07:00"),
        (repo_ids["ufo-records"], "2026-04-27T10:00:00-07:00"),
        (repo_ids["bug-worktree"], "2026-04-26T10:00:00-07:00"),
    ]
    for repo_id, commit_time in snapshots:
        conn.execute(
            """
            INSERT INTO repo_snapshots (
              repo_id, scanned_at, commit_time, changed_files_json, path_clusters_json,
              recent_commits_json, scan_error
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                repo_id,
                commit_time,
                commit_time,
                "[]",
                "{}",
                "[]",
                None,
            ),
        )
    conn.commit()

    cards = get_repo_cards(conn)

    assert [card["repo"]["name"] for card in cards] == [
        "wiki",
        "console-1701",
        "ufo-records",
        "bug-worktree",
    ]


def test_recent_events_summarize_codex_and_strip_timezone_markers(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    conn.execute(
        """
        INSERT INTO log_events (
          source, source_path, event_time, observed_at, severity, category,
          message, raw_line, fingerprint
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "codex",
            "/tmp/codex.log",
            None,
            "2026-04-28T06:52:55-07:00",
            "blue",
            "CODEX_RUN",
            (
                "2026-04-28T13:51:18.256520Z INFO session_loop{...}: "
                'codex_core::stream_events_utils: ToolCall: exec_command {"cmd":"ls"}'
            ),
            "",
            "codex-toolcall",
        ),
    )
    conn.commit()

    events = get_recent_events(conn, limit=10)

    assert events[0]["message"] == "Tool call: exec_command"
    assert "T" not in events[0]["time"]
    assert "Z" not in events[0]["time"]
    assert "+" not in events[0]["time"]


def test_recent_events_drop_low_signal_codex_transport_noise(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    conn.execute(
        """
        INSERT INTO log_events (
          source, source_path, event_time, observed_at, severity, category,
          message, raw_line, fingerprint
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "codex",
            "/tmp/codex.log",
            None,
            "2026-04-28T06:52:55-07:00",
            "blue",
            "CODEX_RUN",
            "2026-04-28T13:50:58.143312Z INFO session_loop{...}: codex_core::client: close",
            "",
            "codex-close",
        ),
    )
    conn.commit()

    assert get_recent_events(conn, limit=10) == []


def test_system_summary_formats_last_scan_without_timezone_suffix(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    conn.execute(
        """
        INSERT INTO scan_runs (
          started_at, finished_at, status, repos_seen, repos_scanned, errors_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "2026-04-28T06:52:55-07:00",
            "2026-04-28T06:55:01-07:00",
            "complete",
            1,
            1,
            "[]",
        ),
    )
    conn.commit()

    summary = get_system_summary(conn)

    expected_local_time = datetime.fromisoformat("2026-04-28T06:55:01-07:00").astimezone()
    assert summary["last_scan_display"] == expected_local_time.strftime("%Y-%m-%d %H:%M:%S")
