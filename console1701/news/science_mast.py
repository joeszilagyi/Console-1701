"""Fixture-only parsing of a narrow MAST CAOM observation metadata response."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

from console1701.news.normalize import bounded_text
from console1701.news.parsers import (
    ArchiveFirehoseBlockedError,
    NewsParserError,
    PayloadTooLargeError,
    _normalize_item,
)
from console1701.news.science_sources import exact_science_endpoint

MAST_INVOKE_URL = "https://mast.stsci.edu/api/v0/invoke"
MAST_COLUMNS = (
    "obs_collection", "obs_id", "obsid", "target_name", "instrument_name", "t_min",
)
_MJD_EPOCH = datetime(1858, 11, 17, tzinfo=UTC)


def _contract(source: dict[str, Any]) -> dict[str, Any]:
    query = source.get("query_contract")
    if not isinstance(query, dict) or query.get("service") != "Mast.Caom.Filtered":
        raise ArchiveFirehoseBlockedError("MAST metadata requires the CAOM filtered service")
    if (
        query.get("columns") != list(MAST_COLUMNS)
        or query.get("format") != "json"
        or query.get("page") != 1
        or type(query.get("row_cap")) is not int
        or not 1 <= query["row_cap"] <= 10
        or type(query.get("timeout_seconds")) is not int
        or not 1 <= query["timeout_seconds"] <= 15
        or query.get("mission") not in {"JWST", "HST"}
    ):
        raise ArchiveFirehoseBlockedError("MAST metadata query exceeds the tiny allowlist")
    target = query.get("target_name")
    if not isinstance(target, str) or not 2 <= len(target) <= 100 or any(
        char in target for char in ("%", "*", "?", "\n")
    ):
        raise ArchiveFirehoseBlockedError("MAST metadata requires a named target without wildcards")
    start, end = query.get("t_min_start"), query.get("t_min_end")
    if (
        isinstance(start, bool) or isinstance(end, bool)
        or not isinstance(start, (int, float)) or not isinstance(end, (int, float))
        or not math.isfinite(start) or not math.isfinite(end)
        or not 40_000 <= start < end <= start + 7
    ):
        raise ArchiveFirehoseBlockedError(
            "MAST metadata requires a seven-day MJD observation window"
        )
    return query


def _observation_url(obsid: int) -> str:
    request = {
        "service": "Mast.Caom.Filtered",
        "params": {
            "columns": ",".join(MAST_COLUMNS),
            "filters": [{"paramName": "obsid", "values": [str(obsid)]}],
        },
        "format": "json", "pagesize": 1, "page": 1,
    }
    return MAST_INVOKE_URL + "?request=" + quote(json.dumps(request, separators=(",", ":")))


def parse_mast_caom_tiny_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if source.get("scope") != "SYSTEM_SOLAR" or source.get("id") != "mast_caom_tiny_metadata":
        raise NewsParserError("MAST parser requires its exact working scope and source")
    if not exact_science_endpoint(source, MAST_INVOKE_URL):
        raise NewsParserError("MAST parser requires the exact official API endpoint")
    query = _contract(source)
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("MAST metadata exceeds the 64 KiB parser cap")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed MAST JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("status") != "COMPLETE":
        raise NewsParserError("MAST metadata query did not complete")
    paging, rows = payload.get("paging"), payload.get("data")
    if not isinstance(paging, dict) or not isinstance(rows, list):
        raise NewsParserError("MAST metadata response lacks paging or rows")
    if (
        paging.get("page") != 1 or paging.get("pageSize") != query["row_cap"]
        or paging.get("pagesFiltered") != 1
        or type(paging.get("rowsFiltered")) is not int
        or paging["rowsFiltered"] != len(rows)
        or len(rows) > query["row_cap"]
    ):
        raise ArchiveFirehoseBlockedError("MAST metadata response is truncated or exceeds row cap")
    items: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != set(MAST_COLUMNS):
            raise NewsParserError("MAST metadata row has unexpected or product columns")
        mission = row["obs_collection"]
        target = bounded_text(row["target_name"], max_chars=100)
        obs_id = bounded_text(row["obs_id"], max_chars=180)
        instrument = bounded_text(row["instrument_name"], max_chars=100)
        obsid = row["obsid"]
        mjd = row["t_min"]
        if (
            mission != query["mission"] or target != query["target_name"] or not obs_id
            or type(obsid) is not int or obsid <= 0
            or isinstance(mjd, bool) or not isinstance(mjd, (int, float))
            or not math.isfinite(mjd) or not query["t_min_start"] <= mjd <= query["t_min_end"]
        ):
            raise NewsParserError("MAST metadata row falls outside query bounds")
        observation_time = (_MJD_EPOCH + timedelta(days=mjd)).isoformat(timespec="seconds")
        item = _normalize_item(source, {
            "title": f"MAST observation metadata: {mission} / {target}",
            "url": _observation_url(obsid),
            "description": "Observation metadata in the MAST archive.",
            "published_at": observation_time,
            "tags": ["official", "mast", "archive_metadata", mission.casefold()],
        }, index=index)
        item["evidence"]["mast_caom"] = {
            "mission": mission,
            "target_name": target,
            "observation_id": obs_id,
            "dataset_id": obsid,
            "instrument": instrument,
            "observation_mjd": mjd,
            "date_semantics": "observation_start_not_publication_date",
            "query_bounds": dict(query),
            "source_url": MAST_INVOKE_URL,
            "data_product_downloaded": False,
            "product_endpoint_called": False,
        }
        items.append(item)
    return items
