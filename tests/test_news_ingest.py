from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

import console1701.config as config_module
from console1701.cli import main
from console1701.config import load_config
from console1701.db import connect_db, init_db, json_loads
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import purge_news_retention, run_news_scan

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "news"


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


def _file_url(path: Path) -> str:
    return f"file://{path.resolve()}"


@pytest.fixture(autouse=True)
def _isolated_console_state(monkeypatch, tmp_path):
    state_dir = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state_dir / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state_dir / "handoffs")


def test_parse_fixture_items_support_json_rss_atom_and_homepage():
    json_source = {
        "id": "json",
        "scope": "LOCAL",
        "kind": "local_file_json",
        "parser": "generic_json_items",
    }
    rss_source = {"id": "rss", "scope": "LOCAL", "kind": "local_file_rss"}
    atom_source = {"id": "atom", "scope": "ORBITAL", "kind": "atom"}
    homepage_source = {
        "id": "homepage",
        "scope": "NATIONAL",
        "kind": "homepage_headlines",
        "parser": "homepage_selectors",
        "homepage_url": "https://news.example.test/",
        "selectors": {
            "item": "article",
            "title": "h2",
            "url": "a",
            "description": "p",
        },
    }

    json_items = parse_fixture_items(json_source, (FIXTURE_DIR / "local_items.json").read_text())
    rss_items = parse_fixture_items(rss_source, (FIXTURE_DIR / "local_feed.rss").read_text())
    atom_items = parse_fixture_items(atom_source, (FIXTURE_DIR / "local_feed.atom").read_text())
    homepage_items = parse_fixture_items(
        homepage_source,
        (FIXTURE_DIR / "homepage.html").read_text(),
    )

    assert len(json_items) == 2
    assert json_items[0]["source_published_at"] == "2026-05-05T17:30:00+00:00"
    assert json_items[1]["url"] == "https://alerts.example.test/power-outage?a=1&b=2"
    assert len(rss_items) == 2
    assert rss_items[0]["tags"] == ["transit", "official"]
    assert len(atom_items) == 2
    assert atom_items[0]["tags"] == ["orbital", "forecast"]
    assert len(homepage_items) == 2
    assert homepage_items[0]["url"] == "https://news.example.test/port/cruise-terminal-plan"


def test_run_news_scan_ingests_local_fixtures_and_dedupes(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: local_json
                  name: Local JSON
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / 'local_items.json')}"
                  parser: generic_json_items
                  tags: [fixture, local]
                  priority: 60
                - id: local_rss
                  name: Local RSS
                  kind: local_file_rss
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / 'local_feed.rss')}"
                  priority: 55
        """,
    )

    first = run_news_scan(config_path)
    second = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        items = conn.execute(
            """
            SELECT title, trend_score, tags_json, evidence_json
            FROM news_items
            ORDER BY title
            """
        ).fetchall()
        fetch_runs = conn.execute("SELECT status FROM news_fetch_runs ORDER BY id").fetchall()
        clusters = conn.execute("SELECT cluster_key, item_count FROM news_clusters").fetchall()

    assert first["status"] == "complete"
    assert first["item_count"] == 4
    assert first["healthy_sources"] == 2
    assert second["status"] == "complete"
    assert len(items) == 4
    assert any(int(row["trend_score"]) == 2 for row in items)
    tag_values = {
        tag
        for row in items
        for tag in json_loads(str(row["tags_json"]), [])
    }
    evidence_rows = [json_loads(str(row["evidence_json"]), {}) for row in items]
    assert {"fixture", "local"}.issubset(tag_values)
    assert any(str(row.get("fixture_path", "")).endswith(".json") for row in evidence_rows)
    ranked_local_row = next(
        row
        for row in evidence_rows
        if str(row.get("fixture_path", "")).endswith("local_items.json")
        and row["ranking"]["factors"]["official_source_boost"] == 12
    )
    ranking = ranked_local_row["ranking"]
    assert ranking["factors"]["source_priority"] == 60
    assert ranking["factors"]["scope_priority_boost"] == 18
    assert ranking["factors"]["official_source_boost"] == 12
    assert ranking["factors"]["recency_bonus"] >= 0
    assert ranking["reasons"]
    assert [row["status"] for row in fetch_runs] == ["success", "success", "success", "success"]
    assert len(clusters) == 4


def test_run_news_scan_fails_soft_for_bad_fixture_and_non_file_source(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: good_json
                  name: Good JSON
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / 'local_items.json')}"
                - id: bad_rss
                  name: Bad RSS
                  kind: local_file_rss
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / 'malformed.rss')}"
                - id: blocked_remote
                  name: Blocked remote
                  kind: rss
                  enabled: true
                  url: "https://example.invalid/feed.xml"
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        statuses = conn.execute(
            "SELECT status, error_class FROM news_fetch_runs ORDER BY id"
        ).fetchall()
        health_rows = conn.execute(
            "SELECT state, message FROM news_source_health ORDER BY id"
        ).fetchall()
        item_count = conn.execute("SELECT COUNT(*) AS count FROM news_items").fetchone()["count"]

    assert result["status"] == "partial"
    assert result["healthy_sources"] == 1
    assert len(result["errors"]) == 2
    assert [row["status"] for row in statuses] == ["success", "parser_failed", "blocked_policy"]
    assert [row["state"] for row in health_rows] == ["healthy", "parser_failed", "blocked_policy"]
    assert int(item_count) == 2


def test_run_news_scan_respects_payload_cap_and_retention_purge(tmp_path):
    huge_fixture = tmp_path / "huge.json"
    huge_payload = {
        "items": [
            {
                "title": "x" * 500,
                "url": "https://example.test/a",
                "description": "y" * 2000,
            }
        ]
    }
    huge_fixture.write_text(json.dumps(huge_payload), encoding="utf-8")
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          retention:
            items_days: 7
            fetch_runs_days: 14
            source_health_days: 30
          fetch_policy:
            max_response_bytes: 120
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: huge_json
                  name: Huge JSON
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(huge_fixture)}"
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        source_id = conn.execute(
            "SELECT id FROM news_sources WHERE source_key = 'huge_json'"
        ).fetchone()["id"]
        conn.execute(
            """
            INSERT INTO news_items (
              source_id, scope, canonical_url, url, url_hash, title, description,
              source_published_at, first_seen_at, last_seen_at, expires_at, source_kind,
              tags_json, rank_score, trend_score, evidence_json, content_hash, status
            )
            VALUES (
              ?, 'LOCAL', 'https://expired.example/a', 'https://expired.example/a', 'deadbeef',
              'Expired item', NULL, NULL, '2026-04-01T00:00:00+00:00',
              '2026-04-01T00:00:00+00:00', '2026-04-02T00:00:00+00:00',
              'local_file_json', '[]', 0, 0, '{{}}', 'hash', 'active'
            )
            """,
            (source_id,),
        )
        conn.execute(
            """
            INSERT INTO news_fetch_runs (
              source_id, started_at, finished_at, status, item_count, evidence_json
            )
            VALUES (
              ?, '2026-04-01T00:00:00+00:00', '2026-04-01T00:00:01+00:00',
              'success', 0, '{{}}'
            )
            """,
            (source_id,),
        )
        conn.execute(
            """
            INSERT INTO news_source_health (
              source_id, observed_at, state, last_success_at, last_failure_at,
              consecutive_failures, stale_after, message, evidence_json
            )
            VALUES (?, '2026-04-01T00:00:00+00:00', 'healthy', '2026-04-01T00:00:00+00:00',
                    NULL, 0, NULL, 'old', '{{}}')
            """,
            (source_id,),
        )
        purged = purge_news_retention(conn, config, now="2026-05-11T10:00:00+00:00")
        remaining = conn.execute("SELECT COUNT(*) AS count FROM news_items").fetchone()["count"]

    assert result["status"] == "partial"
    assert result["errors"]
    assert purged == {"items": 1, "fetch_runs": 1, "source_health": 1}
    assert int(remaining) == 0


def test_parse_fixture_items_bounds_text_lengths():
    source = {"id": "json", "scope": "LOCAL", "kind": "local_file_json"}
    payload = {
        "items": [
            {
                "title": "T" * 600,
                "url": "https://example.test/bounded",
                "description": "D" * 3000,
                "published_at": "Tue, 05 May 2026 18:05:00 GMT",
            }
        ]
    }

    items = parse_fixture_items(source, json.dumps(payload))

    assert len(items[0]["title"]) == 280
    assert len(items[0]["description"]) == 1200
    assert items[0]["source_published_at"] == "2026-05-05T18:05:00+00:00"


def test_cli_news_scan_command_prints_summary(tmp_path, capsys):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: orbital_atom
                  name: Orbital Atom
                  kind: atom
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / 'local_feed.atom')}"
        """,
    )

    exit_code = main(["news-scan", "--config", str(config_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "News scan complete" in captured.out
    assert captured.err == ""


def test_cli_news_sources_command_reports_policy_and_health(tmp_path, capsys):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: orbital_atom
                  name: Orbital Atom
                  kind: atom
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / 'local_feed.atom')}"
        """,
    )

    assert main(["news-scan", "--config", str(config_path)]) == 0
    exit_code = main(["news-sources", "--config", str(config_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "ORBITAL orbital_atom enabled=yes kind=atom" in captured.out
    assert "policy=allowed_fixture_only" in captured.out
    assert "health=healthy" in captured.out
    assert "items=2" in captured.out
    assert "last_success=" in captured.out
    assert "next_eligible=" in captured.out


def test_run_news_scan_records_last_purge_and_last_result(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: local_json
                  name: Local JSON
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / 'local_items.json')}"
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        rows = conn.execute(
            """
            SELECT key, value
            FROM settings
            WHERE key IN ('news.last_purge', 'news.last_scan_result')
            """
        ).fetchall()
    settings = {str(row["key"]): json_loads(str(row["value"])) for row in rows}

    assert result["status"] == "complete"
    assert settings["news.last_purge"]["summary"] == {
        "items": 0,
        "fetch_runs": 0,
        "source_health": 0,
    }
    assert settings["news.last_purge"]["before_counts"]["news_items"] == 2
    assert settings["news.last_purge"]["after_counts"]["news_items"] == 2
    assert settings["news.last_purge"]["cutoffs"]["items_before"]
    assert settings["news.last_scan_result"]["status"] == "complete"
    assert settings["news.last_scan_result"]["item_count"] == 2
