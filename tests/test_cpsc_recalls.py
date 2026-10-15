from __future__ import annotations

import json
from pathlib import Path

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.national_policy import classify_national_item
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.ranking import build_rank_result
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/national/cpsc_recalls_2026_10_01.json"


def _source():
    return {
        "id": "cpsc_recalls_api", "scope": "NATIONAL", "kind": "api_json",
        "parser": "cpsc_recalls_json", "fixture_only": True,
        "url": "https://www.saferproducts.gov/RestWebServices/Recall",
        "query_contract": {"recall_date_start": "2026-10-01", "recall_date_end": "2026-10-02",
                           "format": "json", "timeout_seconds": 10},
    }


def test_cpsc_fixture_preserves_recall_identity_hazard_and_instruction_url():
    items = parse_fixture_items(_source(), FIXTURE.read_text())
    assert len(items) == 3
    first = items[0]["evidence"]["cpsc_recall"]
    assert first["recall_id"] == 11013
    assert first["recall_number"] == "27003"
    assert first["products"]
    assert first["hazards"]
    assert first["public_instruction_url"] == items[0]["url"]
    assert first["distribution_scope"] == "not_structured_in_api"
    assert first["images_downloaded"] is False
    assert "death_risk" in first["risk_indicators"]
    assert items[0]["source_published_at"] == "2026-10-01T00:00:00+00:00"


def test_cpsc_risk_indicator_does_not_claim_reported_deaths():
    item = parse_fixture_items(_source(), FIXTURE.read_text())[0]
    evidence = item["evidence"]["cpsc_recall"]
    assert "death_risk" in evidence["risk_indicators"]
    assert "death_reports" not in evidence
    assert evidence["injury_report_text"]


def test_cpsc_source_risk_contributes_to_national_attention_and_rank():
    source = _source() | {"official_status": "official", "source_family": "cpsc",
                          "priority": 70}
    item = parse_fixture_items(source, FIXTURE.read_text())[0]
    policy = classify_national_item(source, item)
    assert policy["attention_state"] == "elevated"
    assert policy["official_impact_score"] == 25
    ranking = build_rank_result(
        source, item, seen_at="2026-10-02T00:00:00+00:00", combined_tags=item["tags"],
        latest_health_state="healthy", repeat_count=0,
    )
    assert ranking["factors"]["national_consumer_safety_bonus"] == 25


@pytest.mark.parametrize(("field", "value"), [
    ("RecallID", 0), ("RecallDate", "2025-01-01"),
    ("URL", "https://example.com/Recalls/fake"), ("URL", "http://cpsc.gov/Recalls/2026/x"),
])
def test_cpsc_rejects_invalid_or_out_of_bounds_row(field, value):
    rows = json.loads(FIXTURE.read_text())
    rows[0][field] = value
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(rows))


def test_cpsc_rejects_unbounded_queries_and_wrong_source():
    source = _source()
    source["query_contract"]["recall_date_end"] = "2026-11-01"
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())
    source = _source()
    source["fixture_only"] = False
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 1_048_577)
    source = _source()
    source["url"] = FIXTURE.resolve().as_uri()
    source["official_url"] = "https://example.test/Recall"
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())


def test_cpsc_rejects_malformed_or_too_many_rows():
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "{")
    rows = json.loads(FIXTURE.read_text())
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(rows * 34))


def test_cpsc_fixture_scans_offline_with_bounded_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected HTTP")),
    )
    config_path = tmp_path / "cpsc.yml"
    config_path.write_text(f"""
paths: {{repo_roots: [], explicit_repos: []}}
news:
  enabled: true
  scopes:
    NATIONAL:
      enabled: true
      sources:
        - id: cpsc_recalls_api
          name: CPSC recalls fixture
          kind: api_json
          parser: cpsc_recalls_json
          source_family: cpsc
          source_class: official_recall
          official_status: official
          fixture_only: true
          enabled: true
          url: "{FIXTURE.resolve().as_uri()}"
          official_url: https://www.saferproducts.gov/RestWebServices/Recall
          query_contract:
            recall_date_start: '2026-10-01'
            recall_date_end: '2026-10-02'
            format: json
            timeout_seconds: 10
""".strip() + "\n", encoding="utf-8")
    result = run_news_scan(config_path)
    assert result["status"] == "complete", result
    assert result["item_count"] == 3
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchall()
    assert len(rows) == 3
    assert all(json_loads(row["evidence_json"], {})["ingest"]["fixture_only"]
               for row in rows)
