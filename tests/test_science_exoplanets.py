from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.science_exoplanets import EXOPLANET_TAP_URL, PS_COLUMNS

FIXTURE = Path(__file__).parent / "fixtures" / "science" / "exoplanet_ps_tiny.json"


def _source():
    return {
        "id": "nasa_exoplanet_ps_tap",
        "scope": "SYSTEM_SOLAR",
        "kind": "api_json",
        "parser": "exoplanet_ps_json",
        "url": EXOPLANET_TAP_URL,
        "query_contract": {
            "table": "ps", "format": "json", "columns": list(PS_COLUMNS),
            "default_only": True, "row_cap": 2,
            "since": "2026-10-14", "until": "2026-10-15",
        },
    }


def test_tiny_exoplanet_metadata_keeps_update_semantics_and_query_bounds():
    items = parse_fixture_items(_source(), FIXTURE.read_text())
    assert len(items) == 2
    assert items[0]["title"] == "Exoplanet Archive parameter update: TOI-4567 b"
    assert items[0]["source_published_at"] == "2026-10-15T00:00:00+00:00"
    evidence = items[0]["evidence"]["exoplanet_archive"]
    assert evidence["host_star"] == "TOI-4567"
    assert evidence["discovery_method"] == "Transit"
    assert evidence["confirmation_status"] == "confirmed"
    assert evidence["date_semantics"] == "parameter_update_not_discovery_date"
    assert evidence["query_bounds"]["row_cap"] == 2
    assert evidence["catalog_downloaded"] is False


@pytest.mark.parametrize(("key", "value"), [
    ("table", "pscomppars"), ("row_cap", 11), ("row_cap", 0),
    ("columns", ["*"]), ("default_only", False),
    ("since", "2026-09-01"), ("format", "csv"),
])
def test_exoplanet_parser_rejects_broad_query_contract(key, value):
    source = _source()
    source["query_contract"][key] = value
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())


def test_exoplanet_parser_rejects_extra_rows_columns_and_wrong_source():
    source = _source()
    rows = json.loads(FIXTURE.read_text())
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, json.dumps(rows + [rows[0]]))
    extra = deepcopy(rows)
    extra[0]["full_catalog"] = "unexpected"
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, json.dumps(extra))
    source["url"] = "https://example.test/TAP/sync"
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())


def test_exoplanet_parser_rejects_large_and_malformed_payload():
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 65_537)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "[")
