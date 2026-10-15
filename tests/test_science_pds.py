from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.science_pds import PDS_PRODUCTS_URL

FIXTURE = Path(__file__).parent / "fixtures" / "science" / "pds_collection_metadata.json"
LID = "urn:nasa:pds:msl_ice-dust:data_derived"


def _source():
    return {
        "id": "pds_collection_metadata", "scope": "SYSTEM_SOLAR",
        "kind": "api_json", "parser": "pds_collection_metadata",
        "url": PDS_PRODUCTS_URL,
        "query_contract": {
            "collection_lid": LID, "allowed_collection_lids": [LID],
            "timeout_seconds": 10, "retention_days": 7,
        },
    }


def test_pds_single_collection_metadata_has_honest_date_and_no_downloads():
    items = parse_fixture_items(_source(), FIXTURE.read_text())
    assert len(items) == 1
    evidence = items[0]["evidence"]["pds_collection"]
    assert evidence["collection_lid"] == LID
    assert evidence["collection_lidvid"] == LID + "::1.0"
    assert evidence["mission"] == "Mars Science Laboratory"
    assert evidence["target_body"] == "Mars"
    assert evidence["member_count"] is None
    assert evidence["date_semantics"] == "registry_harvest_not_science_release"
    assert evidence["label_downloaded"] is False
    assert evidence["inventory_downloaded"] is False
    assert evidence["data_product_downloaded"] is False


@pytest.mark.parametrize(("key", "value"), [
    ("collection_lid", "urn:nasa:pds:other:data"),
    ("allowed_collection_lids", []),
    ("allowed_collection_lids", ["urn:nasa:pds:other:data"]),
    ("timeout_seconds", 30), ("retention_days", 30),
])
def test_pds_parser_rejects_unbounded_or_unlisted_queries(key, value):
    source = _source()
    source["query_contract"][key] = value
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())


def test_pds_parser_rejects_product_mismatch_and_bad_payload():
    source = _source()
    data = json.loads(FIXTURE.read_text())
    for changed in (
        {**data, "type": "Product_Observational"},
        {**data, "id": LID + "::2.0"},
    ):
        with pytest.raises(NewsParserError):
            parse_fixture_items(source, json.dumps(changed))
    extra = deepcopy(data)
    extra["properties"]["collection_member_count"] = ["3"]
    assert parse_fixture_items(source, json.dumps(extra))[0]["evidence"]["pds_collection"][
        "member_count"
    ] == 3
    source["url"] = "https://example.test/api/search/1/products/"
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 65_537)
