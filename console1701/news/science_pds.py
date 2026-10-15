"""Fixture-only parser for one allowlisted NASA PDS collection metadata record."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

PDS_PRODUCTS_URL = "https://pds.nasa.gov/api/search/1/products/"
_COLLECTION_LID_RE = re.compile(r"urn:nasa:pds:[a-z0-9_.-]+:[a-z0-9_.-]+")


def _first_text(value: Any, max_chars: int = 150) -> str | None:
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], str):
        return None
    return bounded_text(value[0], max_chars=max_chars)


def _contract(source: dict[str, Any]) -> dict[str, Any]:
    query = source.get("query_contract")
    if not isinstance(query, dict):
        raise NewsParserError("PDS collection metadata requires an exact identifier contract")
    lid = query.get("collection_lid")
    allowlist = query.get("allowed_collection_lids")
    if (
        not isinstance(lid, str) or not _COLLECTION_LID_RE.fullmatch(lid)
        or not isinstance(allowlist, list) or not 1 <= len(allowlist) <= 10
        or lid not in allowlist or any(
            not isinstance(value, str) or not _COLLECTION_LID_RE.fullmatch(value)
            for value in allowlist
        )
        or type(query.get("timeout_seconds")) is not int
        or not 1 <= query["timeout_seconds"] <= 15
        or type(query.get("retention_days")) is not int
        or not 1 <= query["retention_days"] <= 7
    ):
        raise NewsParserError("PDS collection metadata query is not narrowly allowlisted")
    return query


def parse_pds_collection_metadata(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "SYSTEM_SOLAR" or source.get("id") != "pds_collection_metadata":
        raise NewsParserError("PDS parser requires its exact working scope and source")
    if source.get("url") != PDS_PRODUCTS_URL:
        raise NewsParserError("PDS parser requires the official collection lookup endpoint")
    query = _contract(source)
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("PDS collection metadata exceeds the 64 KiB parser cap")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed PDS collection JSON: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("type") != "Product_Collection":
        raise NewsParserError("PDS response is not one Product_Collection")
    lid = query["collection_lid"]
    lidvid = payload.get("id")
    properties = payload.get("properties")
    metadata = payload.get("metadata")
    if (
        not isinstance(lidvid, str) or not lidvid.startswith(lid + "::")
        or not isinstance(properties, dict) or _first_text(properties.get("lid")) != lid
        or not isinstance(metadata, dict)
    ):
        raise NewsParserError("PDS collection ID or metadata does not match the allowlist")
    version = bounded_text(metadata.get("version"), max_chars=30)
    title = bounded_text(payload.get("title"), max_chars=280)
    mission = _first_text(properties.get("pds:Investigation_Area.pds:name"))
    target = _first_text(properties.get("pds:Target_Identification.pds:name"))
    harvested = normalize_timestamp(_first_text(
        properties.get("ops:Harvest_Info.ops:harvest_date_time"), 50
    ))
    if (
        not version or lidvid != f"{lid}::{version}" or not title
        or not mission or not target or not harvested
    ):
        raise NewsParserError("PDS collection lacks required bounded metadata")
    member_count = _first_text(properties.get("collection_member_count"), 20)
    if member_count is not None and (not member_count.isdigit() or int(member_count) < 0):
        raise NewsParserError("PDS collection has invalid source-provided member count")
    url = PDS_PRODUCTS_URL + quote(lid, safe=":")
    item = _normalize_item(source, {
        "title": f"PDS collection metadata: {title}",
        "url": url,
        "description": "Planetary Data System collection registry metadata.",
        "published_at": harvested,
        "tags": ["official", "pds", "archive_metadata", "planetary_science"],
    }, index=0)
    item["evidence"]["pds_collection"] = {
        "collection_lid": lid,
        "collection_lidvid": lidvid,
        "version": version,
        "mission": mission,
        "target_body": target,
        "member_count": int(member_count) if member_count is not None else None,
        "registry_harvested_at": harvested,
        "date_semantics": "registry_harvest_not_science_release",
        "query_bounds": {"collection_lid": lid, "timeout_seconds": query["timeout_seconds"],
                         "retention_days": query["retention_days"]},
        "source_url": url,
        "label_downloaded": False,
        "inventory_downloaded": False,
        "data_product_downloaded": False,
        "member_traversal": False,
    }
    return [item]
