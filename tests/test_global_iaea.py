from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_ranking import rank_global_event
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/global_iaea_topnews.rss"
SOURCE = {
    "id": "iaea_rss", "scope": "GLOBAL", "kind": "rss",
    "parser": "iaea_rss", "source_family": "iaea",
    "active_crisis_terms": ["Ukraine"],
}


def test_iaea_fixture_keeps_only_nuclear_safety_signals() -> None:
    fixture = FIXTURE.read_text()
    items = parse_fixture_items(SOURCE, fixture)
    assert len(items) == 2
    update, emergency = items
    assert update["url"].startswith("https://www.iaea.org/newscenter/")
    assert update["source_published_at"] == "2026-10-09T00:00:00+00:00"
    assert update["evidence"]["iaea"]["feed_pub_date"] == "26-10-09 17:15"
    assert update["evidence"]["iaea"]["publication_precision"].startswith("day")
    assert update["evidence"]["iaea"]["matched_crisis_terms"] == ["ukraine"]
    assert update["evidence"]["iaea"]["severity_confirmed"] is False
    assert emergency["evidence"]["iaea"]["urgent_title_phrase"] is True
    assert emergency["evidence"]["iaea"]["categories"] == ["Nuclear safety"]
    assert emergency["evidence"]["global_identity"] == {"institution": "IAEA"}
    assert len(parse_fixture_items({**SOURCE, "active_crisis_terms": []}, fixture)) == 1
    with pytest.raises(NewsParserError, match="unexpected channel"):
        parse_fixture_items(SOURCE, fixture.replace("IAEA Top News", "Other News"))
    with pytest.raises(NewsParserError, match="invalid official identity"):
        parse_fixture_items(SOURCE, fixture.replace("www.iaea.org", "example.org"))


def test_iaea_urgent_title_gets_context_without_impact_or_alert_claim() -> None:
    update, urgent = parse_fixture_items(SOURCE, FIXTURE.read_text())
    for item_id, item in enumerate((update, urgent), start=1):
        item["id"] = item_id
        item["evidence"]["source"] = {
            "source_family": "iaea", "official_status": "official", "priority": 70,
        }
    group = {"families": ["iaea"], "countries": [], "identifiers": [],
             "corroborated": False}
    now = "2026-10-10T12:00:00+00:00"
    update_rank = rank_global_event(group, [update], now=now)
    urgent_rank = rank_global_event(group, [urgent], now=now)
    assert update_rank["factors"]["public_impact_score"] == 0
    assert urgent_rank["factors"]["public_impact_score"] == 0
    assert urgent_rank["factors"]["official_severity_score"] == 0
    assert urgent_rank["factors"]["active_alert_score"] == 0
    assert urgent_rank["factors"]["nuclear_safety_context_score"] == 8
    assert urgent_rank["score"] > update_rank["score"]
    assert urgent_rank["public_impact_basis"] == []
    urgent["evidence"]["source"]["official_status"] = "official_candidate"
    assert rank_global_event(group, [urgent], now=now)["factors"][
        "nuclear_safety_context_score"
    ] == 0


def test_iaea_fixture_scan_is_offline(tmp_path, monkeypatch) -> None:
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
                - id: iaea_rss
                  name: IAEA fixture
                  kind: rss
                  parser: iaea_rss
                  source_family: iaea
                  official_status: official
                  active_crisis_terms: [Ukraine]
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
    with connect_db(config["_db_path"]) as conn:
        clusters = conn.execute(
            "SELECT title, evidence_json FROM news_clusters WHERE scope='GLOBAL'"
        ).fetchall()
    assert len(clusters) == 2
    ranked = {
        row["title"]: json_loads(row["evidence_json"], {})["global_event"]["ranking"]
        for row in clusters
    }
    urgent_rank = next(value for key, value in ranked.items() if "Emergency" in key)
    assert urgent_rank["factors"]["nuclear_safety_context_score"] == 8
    assert urgent_rank["factors"]["public_impact_score"] == 0
    assert urgent_rank["factors"]["active_alert_score"] == 0
