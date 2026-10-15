from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/global_who_don.json"
SOURCE = {"scope": "GLOBAL", "kind": "api_json", "parser": "who_don_json"}


def test_who_don_fixture_preserves_official_evidence_without_inferred_counts():
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 1
    item = items[0]
    evidence = item["evidence"]["who_don"]
    assert item["url"] == (
        "https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON620"
    )
    assert item["source_published_at"] == "2026-10-10T15:00:00+00:00"
    assert evidence["updated_at"] == "2026-10-13T09:22:55+00:00"
    assert evidence["hazard_label"] == "Pneumonia of undetermined etiology"
    assert evidence["geography_label"] == "the Russian Federation"
    assert evidence["geography_basis"] == "title_suffix_unverified"
    assert evidence["case_counts_extracted"] is False
    assert evidence["ranking"]["official_public_health"] is True
    assert "Full article body" not in str(item)

    with pytest.raises(NewsParserError, match="safe article slug"):
        parse_fixture_items(SOURCE, FIXTURE.read_text().replace("2026-DON620", "../bad"))


def test_who_don_fixture_scan_has_no_http_and_persists_evidence(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("fixture scan must not fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "who.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: who_don_fixture
                  name: WHO DON fixture
                  kind: api_json
                  parser: who_don_json
                  source_family: who
                  official_status: official
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT description, evidence_json FROM news_items WHERE scope = 'GLOBAL'"
        ).fetchall()
    assert result["status"] == "complete"
    assert result["item_count"] == len(rows) == 1
    assert "Full article body" not in str(dict(rows[0]))
    assert json_loads(rows[0]["evidence_json"], {})["who_don"]["don_id"] == "2026-DON620"
