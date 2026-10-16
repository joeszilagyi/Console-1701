"""Fixture-only metadata for NIFC's current IMSR Washington incident view."""

from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

from console1701.news.normalize import bounded_text
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

LAYER_URL = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/ArcGIS/rest/services/"
    "IMSR_Incident_Locations_Most_Recent_View/FeatureServer/0"
)
DATASET_URL = "https://data-nifc.opendata.arcgis.com/datasets/20c1f27e9db94bc2a2ae1b183e4620d6_0/explore"
QUERY_URL = (
    f"{LAYER_URL}/query?where=IsLatest%3d%27x%27+AND+incident_id+LIKE+%27WA-%25%27"
    "&outFields=incident_id%2cfire_name%2cpost_date_isoformat%2cIsLatest%2csize%2c"
    "x100pct%2clatitude%2clongitude%2cUniqueFireIdentifier%2cinitial_imsr_date%2cnew_to_imsr"
    "&orderByFields=post_date_isoformat+DESC&resultRecordCount=100&returnGeometry=false&f=json"
)
MAX_BYTES = 65_536
MAX_ROWS = 100
_INCIDENT_ID = re.compile(r"WA-([A-Z0-9]{2,5})-(\d{4,8})\Z")
_UNIQUE_ID = re.compile(r"20\d{2}-WA[A-Z0-9]{2,5}-\d{4,8}\Z")
_FIELDS = {
    "incident_id", "fire_name", "post_date_isoformat", "IsLatest", "size",
    "x100pct", "latitude", "longitude", "UniqueFireIdentifier",
}


def _number(value: Any, field: str, *, lower: float, upper: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise NewsParserError(f"NIFC IMSR {field} must be numeric")
    number = float(value)
    if not math.isfinite(number) or not lower <= number <= upper:
        raise NewsParserError(f"NIFC IMSR {field} is outside the allowed range")
    return number


def parse_nifc_imsr_fixture(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if source.get("scope") != "REGIONAL" or source.get("id") != "nifc_imsr_current_wa":
        raise NewsParserError("NIFC IMSR fixture requires its REGIONAL registry source")
    if not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("NIFC IMSR parser is fixture-only")
    if source.get("official_url") != QUERY_URL:
        raise NewsParserError("NIFC IMSR fixture requires the exact official query URL")
    if len(payload_text.encode("utf-8")) > MAX_BYTES:
        raise PayloadTooLargeError("NIFC IMSR fixture exceeds 64 KiB")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError("Malformed NIFC IMSR JSON fixture") from exc
    if (not isinstance(payload, dict) or payload.get("error") is not None
            or payload.get("objectIdFieldName") != "OBJECTID"
            or payload.get("geometryType") != "esriGeometryPoint"
            or payload.get("exceededTransferLimit") is True):
        raise NewsParserError("NIFC IMSR response has invalid or incomplete metadata")
    fields = payload.get("fields")
    rows = payload.get("features")
    if (not isinstance(fields, list) or not _FIELDS <= {
        field.get("name") for field in fields if isinstance(field, dict)
    } or not isinstance(rows, list) or len(rows) > MAX_ROWS):
        raise NewsParserError("NIFC IMSR response lacks bounded fields")

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, feature in enumerate(rows):
        row = feature.get("attributes") if isinstance(feature, dict) else None
        if not isinstance(row, dict):
            raise NewsParserError(f"NIFC IMSR feature {index} has no attributes")
        incident_id = row.get("incident_id")
        match = _INCIDENT_ID.fullmatch(incident_id) if isinstance(incident_id, str) else None
        unique = row.get("UniqueFireIdentifier")
        if (match is None or incident_id in seen or not isinstance(unique, str)
                or not _UNIQUE_ID.fullmatch(unique)
                or unique[5:] != f"WA{match[1]}-{match[2]}"
                or row.get("IsLatest") != "x"):
            raise NewsParserError(f"NIFC IMSR feature {index} lacks current WA identity")
        seen.add(incident_id)
        name = bounded_text(row.get("fire_name"), max_chars=100)
        raw_date = row.get("post_date_isoformat")
        if not name or type(raw_date) is not int or not 20_000_000 <= raw_date <= 21_000_000:
            raise NewsParserError(f"NIFC IMSR feature {index} lacks report name or date")
        try:
            report_at = datetime.strptime(str(raw_date), "%Y%m%d").replace(tzinfo=UTC).isoformat()
        except ValueError as exc:
            raise NewsParserError(f"NIFC IMSR feature {index} has invalid report date") from exc
        acres = _number(row.get("size"), "size", lower=0, upper=20_000_000)
        latitude = _number(row.get("latitude"), "latitude", lower=45.5, upper=49.1)
        longitude = _number(row.get("longitude"), "longitude", lower=-125, upper=-116)
        contained = row.get("x100pct") == "c"
        if row.get("x100pct") not in ("", "c", None):
            raise NewsParserError(f"NIFC IMSR feature {index} has unknown containment flag")
        item = _normalize_item(source, {
            "title": f"NIFC IMSR: {name} fire in Washington",
            "url": DATASET_URL,
            "canonical_url": f"{DATASET_URL}?{urlencode({'incident_id': incident_id})}",
            "description": (
                f"Listed in the current NIFC IMSR at {acres:g} acres. "
                "Current activity and evacuation status are not established by this field."
            ),
            "published_at": report_at,
            "tags": ["official", "wildfire", "current-imsr"],
        }, index=index)
        item["evidence"]["nifc_imsr"] = {
            "incident_id": incident_id,
            "unique_fire_identifier": unique,
            "fire_name": name,
            "report_date": report_at,
            "report_date_precision": "day",
            "listed_in_current_imsr": True,
            "reported_size_acres": acres,
            "reported_100_percent_contained": contained,
            "latitude": latitude, "longitude": longitude,
            "geography_basis": "official_incident_prefix_and_point_bounds",
            "active_fire_claimed": False,
            "evacuation_claimed": False,
            "source_url": DATASET_URL,
            "query_url": QUERY_URL,
            "canonical_url_basis": "local_incident_id_query_not_source_deep_link",
            "fixture_only": True,
            "ranking": {
                "official_current_report_context": (
                    12 if acres >= 10_000 and not contained else
                    6 if acres >= 1_000 and not contained else 0
                ),
                "public_impact_inferred": False,
            },
        }
        item["evidence"]["regional_identity"] = {"fire_incident": name}
        items.append(item)
    return items
