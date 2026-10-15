from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/global_un_press.rss"


def test_un_press_fixture_keeps_selected_institution_metadata() -> None:
    source = {
        "id": "un_press_rss", "scope": "GLOBAL", "kind": "rss",
        "parser": "un_press_rss", "source_family": "un_press",
        "active_crisis_terms": ["Middle East", "humanitarian access"],
    }
    fixture = FIXTURE.read_text()
    items = parse_fixture_items(source, fixture)
    assert len(items) == 2
    council = items[0]["evidence"]["un_press"]
    assert council["organ"] == "security_council"
    assert council["organ_basis"] == "title_only_unverified"
    assert council["matched_crisis_terms"] == ["middle east"]
    assert council["decision_or_outcome_inferred"] is False
    assert council["body_stored"] is False
    assert items[0]["source_published_at"] == "2026-10-15T10:49:02+00:00"
    assembly = items[1]["evidence"]["un_press"]
    assert assembly["organ"] == "general_assembly"
    assert assembly["matched_action_terms"] == ["adopts", "resolution"]
    assert items[1]["evidence"]["global_identity"] == {"institution": "United Nations"}
    with pytest.raises(NewsParserError, match="active_crisis_terms"):
        parse_fixture_items({**source, "active_crisis_terms": []}, fixture)
    with pytest.raises(NewsParserError, match="unexpected channel"):
        parse_fixture_items(source, fixture.replace("UN Meetings Coverage", "Other Coverage"))


def test_un_press_fixture_scan_is_offline(tmp_path, monkeypatch) -> None:
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
                - id: un_press_rss
                  name: UN Press fixture
                  kind: rss
                  parser: un_press_rss
                  source_family: un_press
                  official_status: official
                  active_crisis_terms: [Middle East, humanitarian access]
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
    assert result["item_count"] == len(rows) == 2
    assert all(json_loads(row["evidence_json"], {})["ingest"]["fixture_only"] for row in rows)
