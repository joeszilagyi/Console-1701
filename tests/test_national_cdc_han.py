"""CDC HAN's current first-party search view is fixture-only notice metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.cdc_han import QUERY, SEARCH_URL
from console1701.news.official_http import is_supported_official_source
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/national/cdc_han_search_2026_10_15.json"


def _source(path: Path = FIXTURE) -> dict:
    return {
        "id": "cdc_han_notices", "name": "CDC HAN notice index",
        "scope": "NATIONAL", "kind": "api_json", "parser": "cdc_han_search_fixture",
        "source_family": "cdc", "official_status": "official",
        "official_url": SEARCH_URL, "url": path.resolve().as_uri(),
        "query_contract": QUERY, "enabled": True,
    }


def test_cdc_han_current_search_snapshot_preserves_notice_identity_without_impact():
    source = _source()
    assert is_supported_official_source({**source, "url": SEARCH_URL}) is False
    items = parse_fixture_items(source, FIXTURE.read_text())
    assert len(items) == 14  # The archive index page is not a HAN notice.
    by_id = {item["evidence"]["cdc_han"]["notice_id"]: item for item in items}
    assert "CDCHAN-00533" in by_id
    assert "CDCHAN-00529" in by_id
    advisory = by_id["CDCHAN-00533"]
    update = by_id["CDCHAN-00529"]
    assert advisory["evidence"]["cdc_han"]["message_type_hint"] == "Health Advisory"
    assert update["evidence"]["cdc_han"]["message_type_hint"] == "Health Update"
    assert advisory["evidence"]["cdc_han"]["message_type"] == "Health Advisory"
    assert advisory["evidence"]["cdc_han"]["distribution_date"] == "2026-09-10"
    assert advisory["evidence"]["cdc_han"]["distribution_time"] is None
    assert update["evidence"]["cdc_han"]["message_type"] == "Health Update"
    assert update["evidence"]["cdc_han"]["distribution_date"] == "2026-05-18"
    assert all(item["evidence"]["cdc_han"]["message_type"] for item in items)
    assert sum(bool(item["evidence"]["cdc_han"]["public_instruction_url"])
               for item in items) == 10
    assert sum(item["evidence"]["cdc_han"]["distribution_date"] is not None
               for item in items) == 13
    assert by_id["CDCHAN-00527"]["evidence"]["cdc_han"]["distribution_time"] == (
        "10:00 AM ET"
    )
    expected_instants = {
        "00527": "2026-04-02T14:00:00+00:00",
        "00526": "2026-01-20T17:30:00+00:00",
        "00525": "2025-12-03T17:30:00+00:00",
        "00524": "2025-09-18T16:00:00+00:00",
        "00521": "2025-02-06T16:15:00+00:00",
    }
    for suffix, instant in expected_instants.items():
        row = by_id[f"CDCHAN-{suffix}"]
        assert row["source_published_at"] == instant
        assert row["evidence"]["cdc_han"]["distribution_instant_utc"] == instant
        assert row["evidence"]["cdc_han"]["index_last_reviewed_at"] != instant
    assert by_id["CDCHAN-00522"]["evidence"]["cdc_han"][
        "distribution_instant_utc"
    ] is None
    assert by_id["CDCHAN-00522"]["source_published_at"] == (
        "2025-03-07T05:00:00+00:00"
    )
    assert by_id["CDCHAN-00527"]["evidence"]["cdc_han"][
        "notice_page_observed_at"
    ] == "2026-10-15"
    assert by_id["CDCHAN-00527"]["evidence"]["cdc_han"][
        "distribution_time_basis"
    ] == "official_notice_page_at_a_glance_ET"
    assert by_id["CDCHAN-00523"]["evidence"]["cdc_han"]["message_type"] == (
        "Health Update"
    )
    assert by_id["CDCHAN-00532"]["evidence"]["cdc_han"]["message_type_basis"] == (
        "official_notice_page_summary_lead"
    )
    assert by_id["CDCHAN-00531"]["evidence"]["cdc_han"]["message_type_basis"] == (
        "official_notice_page_badge"
    )
    assert by_id["CDCHAN-00522"]["evidence"]["cdc_han"]["distribution_date"] is None
    assert by_id["CDCHAN-00522"]["evidence"]["cdc_han"]["message_type"] == (
        "Health Advisory"
    )
    assert "page_summary_html" not in json.dumps(advisory["evidence"])
    assert "summary_lead_html" not in json.dumps(advisory["evidence"])
    assert advisory["evidence"]["cdc_han"]["public_impact_verified"] is False
    assert advisory["evidence"]["cdc_han"]["public_instruction_url"] == (
        "https://www.cdc.gov/han/php/notices/han00533.html"
        "#cdc_health_alert_section_5-recommendations-for-the-public"
    )
    assert update["evidence"]["cdc_han"]["public_instruction_url"] is None
    assert advisory["evidence"]["national_identity"]["official_event_ids"] == [
        "cdc_han:cdchan-00533"
    ]
    assert advisory["source_published_at"] == "2026-09-10T04:00:00+00:00"
    assert all(item["url"].startswith("https://www.cdc.gov/han/php/notices/han")
               for item in items)


def test_cdc_han_rejects_wrong_contract_or_poisoned_notice_metadata():
    raw = FIXTURE.read_text()
    index_only = json.loads(raw)
    index_only.pop("notice_summaries")
    assert all(item["evidence"]["cdc_han"]["message_type"] is None for item in (
        parse_fixture_items(_source(), json.dumps(index_only))
    ))
    with pytest.raises(NewsParserError, match="exact official search contract"):
        parse_fixture_items({**_source(), "official_url": "https://example.org/search"}, raw)
    with pytest.raises(NewsParserError, match="exact official search contract"):
        parse_fixture_items({**_source(), "url": SEARCH_URL}, raw)
    with pytest.raises(NewsParserError, match="exact official search contract"):
        parse_fixture_items({**_source(), "query_contract": {**QUERY, "rows": "200"}}, raw)
    payload = json.loads(raw)
    payload["responseHeader"]["params"]["fq"] = "permalink:*"
    with pytest.raises(NewsParserError, match="bounded search response"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(raw)
    payload["response"]["docs"][0]["permalink"] = "https://evil.example/han00533.html"
    with pytest.raises(NewsParserError, match="invalid CDC URL"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(raw)
    payload["response"]["docs"][1]["permalink"] = payload["response"]["docs"][0][
        "permalink"
    ]
    with pytest.raises(NewsParserError, match="stable notice metadata"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(raw)
    payload["notice_summaries"][0]["page_summary_html"] = payload[
        "notice_summaries"
    ][0]["page_summary_html"].replace("CDCHAN-00533", "CDCHAN-00529")
    with pytest.raises(NewsParserError, match="distribution fields"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(raw)
    payload["notice_summaries"][0]["page_summary_html"] = payload[
        "notice_summaries"
    ][0]["page_summary_html"].replace("CDC Health Advisory", "CDC Health Alert")
    with pytest.raises(NewsParserError, match="unverified message type"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(raw)
    payload["notice_summaries"][0]["summary_lead_html"] = payload[
        "notice_summaries"
    ][0]["summary_lead_html"].replace("Health Advisory", "Health Update")
    with pytest.raises(NewsParserError, match="lead conflicts"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(raw)
    payload["notice_summaries"][0]["recommendation_anchor_html"] = payload[
        "notice_summaries"
    ][0]["recommendation_anchor_html"].replace(
        "Recommendations for the Public", "Recommendations for Clinicians"
    )
    with pytest.raises(NewsParserError, match="recommendation anchor"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(raw)
    payload["notice_summaries"][0]["permalink"] = (
        "https://www.cdc.gov/han/php/notices/han99999.html"
    )
    with pytest.raises(NewsParserError, match="distribution fields"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(raw)
    no_date = next(row for row in payload["notice_summaries"]
                   if row["permalink"].endswith("han00522.html"))
    no_date["page_summary_html"] = no_date["page_summary_html"].replace(
        "Distributed via the CDC Health Alert Network</p>",
        "Distributed via the CDC Health Alert Network</p><p>CDCHAN-00522</p>",
    )
    with pytest.raises(NewsParserError, match="distribution fields"):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(raw)
    timed = next(row for row in payload["notice_summaries"]
                 if row["permalink"].endswith("han00527.html"))
    timed["page_summary_html"] = timed["page_summary_html"].replace(
        "10:00 AM ET", "25:00 AM ET"
    )
    with pytest.raises(NewsParserError, match="distribution date"):
        parse_fixture_items(_source(), json.dumps(payload))
    with pytest.raises(PayloadTooLargeError, match="64 KiB"):
        parse_fixture_items(_source(), raw + " " * 65_536)


def test_cdc_han_offline_scan_stores_metadata_without_fetch_or_alert_claim(tmp_path, monkeypatch):
    source = _source()
    config_path = tmp_path / "config.yml"
    config_path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {"enabled": True, "scopes": {"NATIONAL": {
            "enabled": True, "sources": [source],
        }}},
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("HAN fixture attempted HTTP"))
    ))
    assert run_news_scan(config_path)["item_count"] == 14
    with connect_db(load_config(config_path)["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT title, source_published_at, evidence_json FROM news_items "
            "WHERE scope='NATIONAL'"
        ).fetchall()
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='NATIONAL'"
        ).fetchall()
    assert len(rows) == 14
    timed = next(row for row in rows if "Medetomidine" in row["title"])
    assert timed["source_published_at"] == "2026-04-02T14:00:00+00:00"
    assert len(clusters) == 14
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert all(row["ingest"]["fixture_only"] for row in evidence)
    assert all(row["cdc_han"]["active_alert_verified"] is False for row in evidence)
    assert sum(row["cdc_han"]["message_type"] is not None for row in evidence) == 14
    assert all(row["national_policy"]["official_impact_score"] == 0 for row in evidence)
    assert all(json_loads(row["evidence_json"], {})["national_event"]["ranking"][
        "factors"
    ]["active_alert_score"] == 0 for row in clusters)
