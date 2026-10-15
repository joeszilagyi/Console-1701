"""Tiny fixture-only NASA Exoplanet Archive PS metadata parser."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any
from urllib.parse import quote

from console1701.news.normalize import bounded_text
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

EXOPLANET_TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
PS_COLUMNS = (
    "pl_name", "hostname", "discoverymethod", "disc_year", "rowupdate",
    "soltype", "default_flag",
)


def _query_contract(source: dict[str, Any]) -> dict[str, Any]:
    query = source.get("query_contract")
    if not isinstance(query, dict):
        raise NewsParserError("Exoplanet metadata requires explicit query bounds")
    if (
        query.get("table") != "ps" or query.get("format") != "json"
        or query.get("columns") != list(PS_COLUMNS)
        or query.get("default_only") is not True
        or type(query.get("row_cap")) is not int
        or not 1 <= query["row_cap"] <= 10
    ):
        raise NewsParserError("Exoplanet metadata query is not the tiny PS allowlist")
    try:
        since = date.fromisoformat(query["since"])
        until = date.fromisoformat(query["until"])
    except (KeyError, TypeError, ValueError) as exc:
        raise NewsParserError("Exoplanet metadata requires ISO date bounds") from exc
    if not since <= until <= since + timedelta(days=7):
        raise NewsParserError("Exoplanet metadata window must be at most seven days")
    return query


def parse_exoplanet_ps_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if source.get("scope") != "SYSTEM_SOLAR" or source.get("id") != "nasa_exoplanet_ps_tap":
        raise NewsParserError("Exoplanet parser requires its exact working scope and source")
    if source.get("url") != EXOPLANET_TAP_URL:
        raise NewsParserError("Exoplanet parser requires the exact NASA TAP endpoint")
    query = _query_contract(source)
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("Exoplanet metadata exceeds the 64 KiB parser cap")
    try:
        rows = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed Exoplanet TAP JSON: {exc}") from exc
    if not isinstance(rows, list) or len(rows) > query["row_cap"]:
        raise NewsParserError("Exoplanet TAP response exceeds the configured row cap")
    items: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != set(PS_COLUMNS):
            raise NewsParserError("Exoplanet TAP row has unexpected columns")
        planet = bounded_text(row["pl_name"], max_chars=120)
        host = bounded_text(row["hostname"], max_chars=120)
        method = bounded_text(row["discoverymethod"], max_chars=100)
        solution = bounded_text(row["soltype"], max_chars=100)
        if (
            not planet or not host or type(row["default_flag"]) is not int
            or row["default_flag"] != 1
        ):
            raise NewsParserError("Exoplanet TAP row lacks a default planet and host")
        try:
            updated = date.fromisoformat(row["rowupdate"])
        except (TypeError, ValueError) as exc:
            raise NewsParserError("Exoplanet TAP row has invalid update date") from exc
        if not date.fromisoformat(query["since"]) <= updated <= date.fromisoformat(
            query["until"]
        ):
            raise NewsParserError("Exoplanet TAP row falls outside query bounds")
        year = row["disc_year"]
        if year is not None and (type(year) is not int or not 1800 <= year <= updated.year):
            raise NewsParserError("Exoplanet TAP row has invalid discovery year")
        status = (
            "confirmed" if solution and "confirmed" in solution.casefold() else
            "candidate" if solution and "candidate" in solution.casefold() else
            "unknown"
        )
        item = _normalize_item(source, {
            "title": f"Exoplanet Archive parameter update: {planet}",
            "url": "https://exoplanetarchive.ipac.caltech.edu/overview/" + quote(host),
            "description": "Planetary-system parameter metadata updated in the NASA archive.",
            "published_at": updated.isoformat(),
            "tags": ["official", "exoplanet", "archive_metadata"],
        }, index=index)
        item["evidence"]["exoplanet_archive"] = {
            "table": "ps",
            "planet_name": planet,
            "host_star": host,
            "discovery_method": method,
            "discovery_year": year,
            "solution_type": solution,
            "confirmation_status": status,
            "row_update_date": updated.isoformat(),
            "date_semantics": "parameter_update_not_discovery_date",
            "query_bounds": {key: query[key] for key in (
                "since", "until", "row_cap", "table", "columns", "default_only", "format"
            )},
            "source_url": EXOPLANET_TAP_URL,
            "data_product_downloaded": False,
            "catalog_downloaded": False,
        }
        items.append(item)
    return items
