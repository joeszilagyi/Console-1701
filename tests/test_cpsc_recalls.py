from __future__ import annotations

import json
from pathlib import Path

import pytest

from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items

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


def test_cpsc_rejects_malformed_or_too_many_rows():
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "{")
    rows = json.loads(FIXTURE.read_text())
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(rows * 34))
