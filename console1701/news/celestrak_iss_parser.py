"""Fixture-only, metadata-only CelesTrak ISS GP parser."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from console1701.news.normalize import bounded_text

ISS_GP_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=JSON"


def parse_celestrak_iss_gp_json(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    """Expose only the public ISS catalog update time, never orbital elements."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    if (source.get("id") != "celestrak_iss_gp" or source.get("scope") != "ORBITAL"
            or source.get("source_class") != "official_iss"):
        raise NewsParserError("CelesTrak ISS parser requires its exact ORBITAL fixture source")
    try:
        rows = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed CelesTrak ISS JSON: {exc}") from exc
    if not isinstance(rows, list) or len(rows) > 1:
        raise NewsParserError("CelesTrak ISS fixture must have at most one GP record")
    if not rows:
        return []
    row = rows[0]
    if (not isinstance(row, dict) or row.get("NORAD_CAT_ID") != 25544
            or row.get("OBJECT_ID") != "1998-067A"
            or row.get("OBJECT_NAME") != "ISS (ZARYA)"
            or row.get("CLASSIFICATION_TYPE") != "U"):
        raise NewsParserError("CelesTrak ISS fixture has changed public object identity")
    epoch_raw = bounded_text(row.get("EPOCH"), max_chars=40)
    try:
        epoch = datetime.fromisoformat(epoch_raw or "")
    except ValueError as exc:
        raise NewsParserError("CelesTrak ISS fixture has no valid GP epoch") from exc
    if epoch.tzinfo is not None or not 2000 <= epoch.year <= 2100:
        raise NewsParserError("CelesTrak ISS GP epoch must be source UTC without offset")
    epoch_utc = epoch.replace(tzinfo=UTC).isoformat()
    item = _normalize_item(source, {
        "title": "ISS public catalog update",
        "url": ISS_GP_URL,
        "description": "CelesTrak has a public ISS GP record. No orbit or live position is shown.",
        "published_at": epoch_utc,
    }, index=0)
    item["evidence"]["celestrak_iss"] = {
        "catalog_id": 25544,
        "public_object": "ISS (ZARYA)",
        "gp_epoch_utc": epoch_utc,
        "source_url": ISS_GP_URL,
        "stored_fields": ["OBJECT_NAME", "OBJECT_ID", "NORAD_CAT_ID", "EPOCH"],
        "orbital_elements_stored": False,
        "display_basis": "public_catalog_freshness_only",
    }
    item["evidence"]["orbital_identity"] = {
        "event_type": "iss_catalog_status",
        "object_id": "25544",
        "public_value_class": "background",
    }
    return [item]
