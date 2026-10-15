from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_registry import get_global_source_registry_entry
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_sources_status

FIXTURE = Path(__file__).parent / "fixtures/news/global_nhc_ep.rss"
SOURCE = {"scope": "GLOBAL", "kind": "rss", "parser": "nhc_basin_rss"}


def test_nhc_basin_feed_preserves_explicit_storm_evidence():
    entry = get_global_source_registry_entry("nhc_rss")
    assert entry is not None
    assert entry["raw_url"] == "https://www.nhc.noaa.gov/index-ep.xml"
    assert entry["verification_status"] == "official_feed_seen"
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 2  # The advisory supersedes its summary; outlook is not an alert.
    first = items[0]
    evidence = first["evidence"]["nhc_rss"]
    assert first["title"] == "Hurricane Trudy Public Advisory Number 9a"
    assert first["source_published_at"] == "2026-10-15T17:39:09+00:00"
    assert evidence["storm_id"] == "EP212026"
    assert evidence["storm_name"] == "Trudy"
    assert evidence["wallet"] == "EP1"
    assert evidence["basin"] == "eastern_pacific"
    assert evidence["advisory_type"] == "public_advisory"
    assert evidence["advisory_number"] == "9a"
    assert evidence["watch_warning_terms"] == ["Tropical Storm Watch"]
    assert evidence["watch_warning_geography_verified"] is False
    assert first["evidence"]["global_identity"]["storm_id"] == "EP212026"
    assert items[1]["evidence"]["nhc_rss"]["advisory_type"] == "storm_summary"
    assert items[1]["evidence"]["nhc_rss"]["storm_id"] == "EP202026"


def test_nhc_basin_feed_empty_and_invalid_cases():
    empty = (
        "<rss><channel><title>NHC Atlantic</title><item><title>"
        "There are no tropical cyclones at this time."
        "</title></item></channel></rss>"
    )
    assert parse_fixture_items(SOURCE, empty) == []
    with pytest.raises(NewsParserError, match="GLOBAL scope"):
        parse_fixture_items({**SOURCE, "scope": "NATIONAL"}, FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="unknown channel/basin"):
        parse_fixture_items(SOURCE, empty.replace("NHC Atlantic", "Unknown feed"))
    with pytest.raises(NewsParserError, match="Malformed NHC"):
        parse_fixture_items(SOURCE, "<rss><channel>")
    with pytest.raises(NewsParserError, match="official HTTPS URL"):
        parse_fixture_items(SOURCE, FIXTURE.read_text().replace(
            "www.nhc.noaa.gov/text/refresh/MIATCPEP1", "example.org/text/refresh/MIATCPEP1"
        ))


def test_nhc_fixture_scan_is_offline_and_does_not_infer_impact(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("NHC HTTP fetch")),
    )
    config_path = tmp_path / "nhc.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: nhc_rss
                  kind: rss
                  parser: nhc_basin_rss
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope = 'GLOBAL'"
        ).fetchall()
        states = get_news_sources_status(conn, config)
    assert len(rows) == 2
    assert states[0]["health_state"] == "healthy"
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert {row["global"]["event_type"] for row in evidence} == {"tropical_cyclone"}
    assert all(row["global"]["affected_countries"] == [] for row in evidence)
    assert all(row["global"]["geography_basis"] == "not_provided" for row in evidence)
    assert any(
        "NHC advisory watch/warning terms (geography unverified)"
        in row["global"]["public_impact_basis"]
        for row in evidence
    )
    assert all(
        row["global_event"]["ranking"]["factors"]["official_severity_score"] >= 18
        for row in evidence
    )
