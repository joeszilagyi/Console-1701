from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.science_mast import MAST_COLUMNS, MAST_INVOKE_URL

FIXTURE = Path(__file__).parent / "fixtures" / "science" / "mast_caom_tiny.json"


def _source():
    return {
        "id": "mast_caom_tiny_metadata", "scope": "SYSTEM_SOLAR",
        "kind": "api_json", "parser": "mast_caom_tiny_json", "url": MAST_INVOKE_URL,
        "query_contract": {
            "service": "Mast.Caom.Filtered", "columns": list(MAST_COLUMNS),
            "format": "json", "page": 1, "row_cap": 2, "timeout_seconds": 10,
            "mission": "JWST", "target_name": "TRAPPIST-1",
            "t_min_start": 60245, "t_min_end": 60246,
        },
    }


def test_mast_tiny_metadata_preserves_observation_identity_without_products():
    items = parse_fixture_items(_source(), FIXTURE.read_text())
    assert len(items) == 2
    assert items[0]["title"] == "MAST observation metadata: JWST / TRAPPIST-1"
    assert items[0]["url"].startswith(MAST_INVOKE_URL + "?request=")
    evidence = items[0]["evidence"]["mast_caom"]
    assert evidence["mission"] == "JWST"
    assert evidence["dataset_id"] == 233637653
    assert evidence["instrument"] == "NIRSPEC/SLIT"
    assert evidence["date_semantics"] == "observation_start_not_publication_date"
    assert evidence["query_bounds"]["row_cap"] == 2
    assert evidence["product_endpoint_called"] is False


@pytest.mark.parametrize(("key", "value"), [
    ("service", "Mast.Caom.Products"), ("columns", ["*"]),
    ("row_cap", 11), ("timeout_seconds", 60), ("page", 2),
    ("target_name", "TRAPPIST-%"), ("mission", "ALL"),
    ("t_min_start", 60200),
])
def test_mast_parser_rejects_broad_or_product_query(key, value):
    source = _source()
    source["query_contract"][key] = value
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())


def test_mast_parser_rejects_truncation_extra_fields_and_wrong_source():
    source = _source()
    payload = json.loads(FIXTURE.read_text())
    payload["paging"]["rowsFiltered"] = 3
    with pytest.raises(NewsParserError, match="truncated"):
        parse_fixture_items(source, json.dumps(payload))
    payload = json.loads(FIXTURE.read_text())
    payload["data"][0]["dataURI"] = "mast:JWST/product/file.fits"
    with pytest.raises(NewsParserError, match="product"):
        parse_fixture_items(source, json.dumps(payload))
    source["url"] = "https://example.test/api/v0/invoke"
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())


def test_mast_parser_rejects_large_malformed_and_out_of_bounds_rows():
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 65_537)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "{")
    payload = deepcopy(json.loads(FIXTURE.read_text()))
    payload["data"][0]["t_min"] = 60247
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(payload))
