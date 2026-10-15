from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_sources_status

FIXTURE = Path(__file__).parent / "fixtures/news/global_reliefweb_disasters.json"


def test_reliefweb_disaster_fixture_preserves_humanitarian_evidence():
    source = {"scope": "GLOBAL", "kind": "api_json", "parser": "reliefweb_disasters_json"}
    items = parse_fixture_items(source, FIXTURE.read_text())
    assert len(items) == 1
    item = items[0]
    evidence = item["evidence"]["reliefweb_disaster"]
    assert evidence["id"] == "51000"
    assert evidence["status"] == "current"
    assert evidence["countries"] == ["Fictional Archipelago", "Example Island"]
    assert evidence["primary_type"] == "Tropical Cyclone"
    assert evidence["event_date"] == "2026-10-14T12:00:00+00:00"
    assert evidence["updated_at"] == "2026-10-15T09:00:00+00:00"
    assert evidence["reports_count"] == 3
    assert evidence["source_url"] == item["url"]
    assert evidence["ranking"]["active"] is True

    with pytest.raises(NewsParserError, match="official identity or URL"):
        bad_url = FIXTURE.read_text().replace("reliefweb.int/disaster", "example.org/disaster")
        parse_fixture_items(source, bad_url)


def test_reliefweb_disaster_fixture_scan_is_offline(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("fixture scan must not fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "config.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: reliefweb_disaster_fixture
                  name: ReliefWeb disaster fixture
                  kind: api_json
                  parser: reliefweb_disasters_json
                  source_family: reliefweb
                  official_status: official
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope = 'GLOBAL'"
        ).fetchall()
    assert result["status"] == "complete"
    assert result["item_count"] == 1
    assert json_loads(rows[0]["evidence_json"], {})["reliefweb_disaster"]["id"] == "51000"


def test_reliefweb_registered_source_requires_approved_appname(tmp_path, monkeypatch):
    def unexpected_access(*args, **kwargs):
        raise AssertionError("unapproved ReliefWeb source attempted ingest")

    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", unexpected_access)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_access)
    config_path = tmp_path / "auth.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true, allow_auth_required_sources: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: reliefweb_disasters
                  enabled: true
                  parser: reliefweb_disasters_json
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        statuses = get_news_sources_status(conn, config)
    assert result["status"] == "partial"
    assert result["item_count"] == 0
    assert statuses[0]["health_state"] == "auth_required"
    assert statuses[0]["policy"]["auth_required"] is True
