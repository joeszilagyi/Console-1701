from __future__ import annotations

import json
from pathlib import Path

import pytest

from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items

FIXTURE = Path(__file__).parent / "fixtures" / "science" / "gcn_circular.json"


def _source():
    return {
        "id": "gcn_circulars", "scope": "SYSTEM_SOLAR", "kind": "api_json",
        "parser": "gcn_circular_fixture", "fixture_only": True,
        "official_url": "https://gcn.nasa.gov/circulars",
        "url": f"file://{FIXTURE}",
    }


def test_gcn_circular_retains_public_metadata_and_drops_body_and_contacts():
    item = parse_fixture_items(_source(), FIXTURE.read_text())[0]
    evidence = item["evidence"]["gcn_circular"]
    assert item["title"] == "GRB 230410A: Fermi GBM Final Real-time Localization"
    assert item["source_published_at"] == "2023-04-10T11:36:21+00:00"
    assert item["url"] == "https://gcn.nasa.gov/circulars/33603"
    assert evidence["event_id"] == "GRB 230410A"
    assert evidence["status"] == "preliminary_report"
    assert evidence["body_stored"] is False
    assert evidence["submitter_stored"] is False
    assert evidence["sky_map_downloaded"] is False
    serialized = json.dumps(item)
    assert "fixture@example.test" not in serialized
    assert "map.fits" not in serialized


@pytest.mark.parametrize(("subject", "status"), [
    ("Retraction: GRB 230410A", "retracted"),
    ("Correction: GRB 230410A", "correction"),
    ("Follow-up observations of GRB 230410A", "follow_up"),
    ("Planned observations of GRB 230410A", "proposal"),
])
def test_gcn_circular_labels_only_explicit_subject_prefixes(subject, status):
    payload = json.loads(FIXTURE.read_text())
    payload["subject"] = subject
    item = parse_fixture_items(_source(), json.dumps(payload))[0]
    assert item["evidence"]["gcn_circular"]["status"] == status


@pytest.mark.parametrize(("field", "value"), [
    ("circularId", True), ("circularId", 0),
    ("subject", None), ("createdOn", "1681126581000"),
    ("createdOn", -1), ("eventId", "private@example.test"),
])
def test_gcn_circular_rejects_invalid_identity_or_timestamp(field, value):
    payload = json.loads(FIXTURE.read_text())
    payload[field] = value
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(payload))


def test_gcn_circular_rejects_wrong_source_live_url_malformed_and_large_payload():
    source = _source()
    source["id"] = "gcn_notices"
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())
    source = _source()
    source["url"] = "https://gcn.nasa.gov/circulars/33603.json"
    source["fixture_only"] = False
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "{")
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 65_537)
