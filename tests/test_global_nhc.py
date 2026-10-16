from __future__ import annotations

import re
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_events import correlate_global_items, global_item_signature
from console1701.news.global_ranking import rank_global_event
from console1701.news.global_registry import get_global_source_registry_entry
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
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


def test_nhc_storm_correlation_uses_family_qualified_parser_id():
    advisory = parse_fixture_items(SOURCE, FIXTURE.read_text())[0]
    advisory["id"] = 1
    advisory["evidence"]["source"] = {
        "source_family": "noaa_nhc", "official_status": "official",
    }
    revision = deepcopy(advisory)
    revision["id"] = 2
    revision["title"] = "Hurricane Trudy Public Advisory Number 10"
    revision["url"] = revision["canonical_url"] = (
        "https://www.nhc.noaa.gov/text/refresh/MIATCPEP1+shtml/151939.shtml"
    )
    revision["evidence"]["global_identity"].pop("storm_id")
    signature = global_item_signature(revision)
    assert signature["family"] == "noaa_nhc"
    assert signature["identifiers"] == {"storm_id:ep212026"}
    groups = correlate_global_items([advisory, revision])
    assert groups[0]["item_ids"] == [1, 2]
    assert groups[0]["corroborated"] is False
    assert groups[0]["matches"][0]["basis"] == ["shared_event_id"]

    foreign = deepcopy(revision)
    foreign["evidence"]["source"]["source_family"] = "un_news"
    assert global_item_signature(foreign)["identifiers"] == set()
    foreign["evidence"]["source"]["source_family"] = "noaa_nhc"
    foreign["evidence"]["nhc_rss"].pop("storm_id")
    foreign["evidence"]["global_identity"]["storm_id"] = "EP212026"
    assert global_item_signature(foreign)["identifiers"] == set()

    conflicting = deepcopy(revision)
    conflicting["evidence"]["nhc_rss"]["storm_id"] = "EP202026"
    conflicting["evidence"]["global_identity"]["storm_id"] = "EP212026"
    conflicting["url"] = conflicting["canonical_url"] = advisory["url"]
    assert [group["item_ids"] for group in correlate_global_items([
        advisory, conflicting
    ])] == [[1], [2]]


def test_nhc_watch_ranking_expires_without_a_fresh_official_public_advisory():
    advisory = parse_fixture_items(SOURCE, FIXTURE.read_text())[0]
    advisory["id"] = 1
    advisory["evidence"]["source"] = {
        "source_family": "noaa_nhc", "official_status": "official",
    }
    group = {
        "families": ["noaa_nhc"], "countries": [], "identifiers": ["nhc:EP212026"],
        "corroborated": False,
    }
    fresh = rank_global_event(group, [advisory], now="2026-10-16T02:00:00+00:00")
    stale = rank_global_event(group, [advisory], now="2026-10-16T06:00:00+00:00")
    assert fresh["factors"]["active_alert_score"] == 20
    assert fresh["factors"]["public_impact_score"] == 12
    assert "NHC advisory watch/warning terms (geography unverified)" in fresh[
        "public_impact_basis"
    ]
    assert stale["factors"]["active_alert_score"] == 0
    assert stale["factors"]["public_impact_score"] == 0
    assert "NHC advisory watch/warning terms (geography unverified)" not in stale[
        "public_impact_basis"
    ]

    advisory["evidence"]["source"]["official_status"] = "candidate"
    unverified = rank_global_event(group, [advisory], now="2026-10-16T02:00:00+00:00")
    assert unverified["factors"]["active_alert_score"] == 0
    assert unverified["factors"]["official_severity_score"] == 0


def test_nhc_basin_feed_empty_and_invalid_cases():
    empty = (
        "<rss><channel><title>NHC Atlantic</title><item><title>"
        "There are no tropical cyclones at this time."
        "</title></item></channel></rss>"
    )
    assert parse_fixture_items(SOURCE, empty) == []
    with pytest.raises(NewsParserError, match="exact fixture source identity"):
        parse_fixture_items({**SOURCE, "scope": "NATIONAL"}, FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="unknown channel/basin"):
        parse_fixture_items(SOURCE, empty.replace("NHC Atlantic", "Unknown feed"))
    with pytest.raises(NewsParserError, match="Malformed NHC"):
        parse_fixture_items(SOURCE, "<rss><channel>")
    with pytest.raises(NewsParserError, match="official HTTPS URL"):
        parse_fixture_items(SOURCE, FIXTURE.read_text().replace(
            "www.nhc.noaa.gov/text/refresh/MIATCPEP1", "example.org/text/refresh/MIATCPEP1"
        ))


def test_global_nhc_feed_rejects_unbounded_or_non_article_input():
    feed = FIXTURE.read_text()
    with pytest.raises(PayloadTooLargeError, match="64 KiB"):
        parse_fixture_items(SOURCE, feed + " " * 65_536)
    with pytest.raises(NewsParserError, match="DTD or entities"):
        parse_fixture_items(SOURCE, "<!DOCTYPE rss>" + feed)
    filler = "<item><title>There are no tropical cyclones at this time.</title></item>"
    with pytest.raises(NewsParserError, match="50 entries"):
        parse_fixture_items(SOURCE, feed.replace("</channel>", filler * 46 + "</channel>"))
    with pytest.raises(NewsParserError, match="official HTTPS URL"):
        parse_fixture_items(SOURCE, feed.replace(
            "/text/refresh/MIATCPEP1+shtml/151739.shtml", "/news/151739.shtml"
        ))
    with pytest.raises(NewsParserError, match="official HTTPS URL"):
        parse_fixture_items(SOURCE, feed.replace(
            "https://www.nhc.noaa.gov/text/refresh/MIATCPEP1",
            "https://user@www.nhc.noaa.gov/text/refresh/MIATCPEP1",
        ))
    for port, error in (("0", "official HTTPS URL"), ("abc", "invalid URL")):
        with pytest.raises(NewsParserError, match=error):
            parse_fixture_items(SOURCE, feed.replace(
                "https://www.nhc.noaa.gov/text/refresh/MIATCPEP1",
                f"https://www.nhc.noaa.gov:{port}/text/refresh/MIATCPEP1",
            ))
    with pytest.raises(NewsParserError, match="official URL or time"):
        parse_fixture_items(SOURCE, feed.replace(
            "/text/refresh/MIATCPEP5+shtml/151442.shtml",
            "/news/151442.shtml",
        ))


def test_nhc_fixture_scan_is_offline_and_does_not_infer_impact(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("NHC HTTP fetch")),
    )
    fresh_date = format_datetime(datetime.now(UTC) - timedelta(minutes=5), usegmt=True)
    fresh_fixture = tmp_path / "current-nhc.rss"
    fresh_fixture.write_text(re.sub(
        r"<pubDate>[^<]+</pubDate>", f"<pubDate>{fresh_date}</pubDate>",
        FIXTURE.read_text(),
    ))
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
                  url: "{fresh_fixture.as_uri()}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope = 'GLOBAL'"
        ).fetchall()
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope = 'GLOBAL'"
        ).fetchall()
        states = get_news_sources_status(conn, config)
    assert len(rows) == 2
    assert len(clusters) == 2
    assert states[0]["health_state"] == "healthy"
    cluster_events = [json_loads(row["evidence_json"], {})["global_event"]
                      for row in clusters]
    assert {tuple(event["identifiers"]) for event in cluster_events} == {
        ("storm_id:ep202026",), ("storm_id:ep212026",),
    }
    assert all(event["families"] == ["noaa_nhc"] for event in cluster_events)
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
