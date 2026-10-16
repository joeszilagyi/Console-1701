from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_ranking import rank_global_event
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/news"


@pytest.mark.parametrize(
    "parser,kind,fixture,event_id,alert,coordinates,bbox",
    [
        (
            "gdacs_rss", "rss", "global_gdacs.rss", "1001338", "Orange",
            [157.4, 11.0], [144.4, -2.0, 170.4, 24.0],
        ),
        (
            "gdacs_geojson", "api_json", "global_gdacs.geojson", "1571782", "Green",
            [-86.049, 10.3031], [-86.049, 10.3031, -86.049, 10.3031],
        ),
    ],
)
def test_gdacs_official_fixture_parser_preserves_evidence(
    parser, kind, fixture, event_id, alert, coordinates, bbox
):
    source = {"scope": "GLOBAL", "kind": kind, "parser": parser}
    items = parse_fixture_items(source, (FIXTURES / fixture).read_text())
    assert len(items) == 1
    item = items[0]
    evidence = item["evidence"]["gdacs"]
    assert item["scope"] == "GLOBAL"
    assert item["source_published_at"] is not None
    assert evidence["event_id"] == event_id
    assert evidence["alert_level"] == alert
    assert evidence["severity"] is not None
    assert evidence["country"] in {"Guam", "Costa Rica"}
    assert evidence["coordinates"] == coordinates
    assert evidence["bbox"] == bbox
    assert evidence["updated_at"] is not None
    assert evidence["source_url"] == item["url"]
    assert evidence["ranking"]["official_alert"] is True
    assert evidence["ranking"]["alert_level_weight"] > 0
    assert evidence["source_health"]["fixture_parser"] is True


def test_gdacs_fixture_parser_rejects_unofficial_url_and_wrong_scope():
    source = {"scope": "GLOBAL", "kind": "api_json", "parser": "gdacs_geojson"}
    fixture = (FIXTURES / "global_gdacs.geojson").read_text()
    with pytest.raises(NewsParserError, match="official HTTPS report URL"):
        bad_url = fixture.replace("www.gdacs.org/report.aspx", "example.org/report.aspx")
        parse_fixture_items(source, bad_url)
    with pytest.raises(NewsParserError, match="GLOBAL scope"):
        parse_fixture_items({**source, "scope": "LOCAL"}, fixture)


def test_gdacs_guam_alert_supplies_source_backed_us_relevance():
    source = {"scope": "GLOBAL", "kind": "rss", "parser": "gdacs_rss"}
    item, = parse_fixture_items(source, (FIXTURES / "global_gdacs.rss").read_text())
    item["id"] = 1
    item["evidence"]["source"] = {
        "source_family": "gdacs", "official_status": "official", "priority": 70,
    }
    ranking = rank_global_event(
        {"families": ["gdacs"], "countries": ["Guam"], "identifiers": [],
         "corroborated": False},
        [item], now="2026-10-15T20:00:00+00:00",
    )
    assert ranking["impact_tags"] == ["us"]
    assert ranking["factors"]["us_or_local_impact_score"] == 10
    assert "GDACS alert for source-reported U.S. jurisdiction" in (
        ranking["public_impact_basis"]
    )


def test_gdacs_fixtures_ingest_into_global_without_http(tmp_path, monkeypatch):
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
                - id: gdacs_feed_fixture
                  name: GDACS RSS fixture
                  kind: rss
                  parser: gdacs_rss
                  source_family: gdacs
                  official_status: official
                  enabled: true
                  url: "file://{FIXTURES / 'global_gdacs.rss'}"
                - id: gdacs_api_fixture
                  name: GDACS GeoJSON fixture
                  kind: api_json
                  parser: gdacs_geojson
                  source_family: gdacs
                  official_status: official
                  enabled: true
                  url: "file://{FIXTURES / 'global_gdacs.geojson'}"
    """).strip() + "\n")
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope = 'GLOBAL' ORDER BY id"
        ).fetchall()
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope = 'GLOBAL'"
        ).fetchall()
    assert result["status"] == "complete"
    assert result["item_count"] == 2
    assert {json_loads(row["evidence_json"], {})["gdacs"]["event_id"] for row in rows} == {
        "1001338", "1571782"
    }
    rankings = [json_loads(row["evidence_json"], {})["global_event"]["ranking"]
                for row in clusters]
    assert len(rankings) == 2
    assert sorted(ranking["factors"]["us_or_local_impact_score"]
                  for ranking in rankings) == [0, 10]
    assert sorted(tuple(ranking["impact_tags"]) for ranking in rankings) == [(), ("us",)]
