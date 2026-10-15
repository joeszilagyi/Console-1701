from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_registry import list_global_source_registry
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_sources_status

FIXTURE = Path(__file__).parent / "fixtures/news/global_ecdc_news.rss"


def test_ecdc_official_rss_shape_preserves_bounded_metadata():
    registered = next(
        entry for entry in list_global_source_registry()
        if entry["source_key"] == "ecdc_rss"
    )
    assert registered["raw_url"] == "https://www.ecdc.europa.eu/en/taxonomy/term/1307/feed"
    assert registered["verification_status"] == "official_feed_seen"
    source = {"scope": "GLOBAL", "kind": "rss", "parser": "ecdc_rss"}
    items = parse_fixture_items(source, FIXTURE.read_text())
    assert len(items) == 2
    first = items[0]
    evidence = first["evidence"]["ecdc_rss"]
    assert first["scope"] == "GLOBAL"
    assert first["source_published_at"] == "2026-10-15T11:59:43+00:00"
    assert first["description"] == "A bounded synthetic summary for a regional surveillance update."
    assert "<p>" not in first["description"]
    assert evidence["categories"] == ["Surveillance"]
    assert evidence["creator"] == "ECDC"
    assert evidence["source_url"] == first["url"]
    assert evidence["source_region_scope"] == "Europe"
    assert evidence["impact_geography_assessed"] is False
    assert evidence["ranking"]["source_weight"] == (
        "below_who_don_until_convergence_or_severity"
    )
    assert "europe-context" in first["tags"]
    assert items[1]["evidence"]["ecdc_rss"]["categories"] == []


def test_ecdc_rss_rejects_unofficial_links_and_wrong_scope():
    source = {"scope": "GLOBAL", "kind": "rss", "parser": "ecdc_rss"}
    fixture = FIXTURE.read_text()
    with pytest.raises(NewsParserError, match="official HTTPS article URL"):
        parse_fixture_items(source, fixture.replace(
            "www.ecdc.europa.eu/en/news-events/synthetic-mosquito",
            "example.org/en/news-events/synthetic-mosquito",
        ))
    with pytest.raises(NewsParserError, match="GLOBAL scope"):
        parse_fixture_items({**source, "scope": "NATIONAL"}, fixture)
    with pytest.raises(NewsParserError, match="Malformed ECDC RSS"):
        parse_fixture_items(source, "<rss><channel>")


def test_ecdc_fixture_scan_is_offline_and_lower_priority_than_who(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("ECDC fixture scan attempted HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "ecdc.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: ecdc_rss
                  kind: rss
                  parser: ecdc_rss
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    config = load_config(config_path)
    source = config["news"]["scopes"]["GLOBAL"]["sources"][0]
    assert source["priority"] == 50
    assert run_news_scan(config_path)["item_count"] == 2
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope = 'GLOBAL'"
        ).fetchall()
        statuses = get_news_sources_status(conn, config)
    assert statuses[0]["health_state"] == "healthy"
    assert len(rows) == 2
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert all("ecdc_rss" in item for item in evidence)
    assert all(item["global"]["affected_countries"] == [] for item in evidence)
    assert all(item["global_event"]["ranking"]["factors"][
        "official_severity_score"
    ] == 0 for item in evidence)
