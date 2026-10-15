from __future__ import annotations

import json
from pathlib import Path

import pytest

from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items

FIXTURE = Path(__file__).parent / "fixtures" / "science" / "gcn_notice.json"


def _source():
    return {
        "id": "gcn_notices", "scope": "SYSTEM_SOLAR", "kind": "api_json",
        "parser": "gcn_notice_fixture", "fixture_only": True,
        "url": "https://gcn.nasa.gov/docs/notices",
    }


def test_gcn_notice_preserves_event_status_and_ignores_sky_map():
    item = parse_fixture_items(_source(), FIXTURE.read_text())[0]
    assert item["title"] == "GCN DSA-110 initial: FRB 20261015A"
    assert item["source_published_at"] == "2026-10-15T18:00:00+00:00"
    evidence = item["evidence"]["gcn_notice"]
    assert evidence["trigger_time"] == "2026-10-15T17:59:10+00:00"
    assert evidence["trigger_id"] == "261015aaaa"
    assert evidence["coordinates_icrs_deg"] == [346.7785, 12.6325]
    assert evidence["status"] == "preliminary"
    assert evidence["sky_map_downloaded"] is False
    assert "healpix_file" not in evidence


@pytest.mark.parametrize(("alert_type", "status"), [
    ("update", "preliminary"), ("retraction", "retracted"),
])
def test_gcn_notice_tracks_updates_and_retractions(alert_type, status):
    payload = json.loads(FIXTURE.read_text())
    payload["alert_type"] = alert_type
    item = parse_fixture_items(_source(), json.dumps(payload))[0]
    assert item["evidence"]["gcn_notice"]["status"] == status


@pytest.mark.parametrize(("field", "value"), [
    ("alert_tense", "test"), ("alert_tense", "injection"),
    ("alert_type", "rumor"), ("mission", None),
    ("ra", -1), ("dec", 91),
    ("$schema", "https://example.test/schema.json"),
])
def test_gcn_notice_rejects_test_fake_or_invalid_metadata(field, value):
    payload = json.loads(FIXTURE.read_text())
    payload[field] = value
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(payload))


def test_gcn_notice_rejects_wrong_source_malformed_and_large_payload():
    source = _source()
    source["fixture_only"] = False
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "{")
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 65_537)
