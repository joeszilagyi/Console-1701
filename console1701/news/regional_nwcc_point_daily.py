"""Offline NWCC daily fire points with source-snapshot activity semantics."""

from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode, urlsplit

from console1701.news.normalize import bounded_text
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

LAYER_URL = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "NWCC_Operational_Layers_view/FeatureServer/11"
)
QUERY_URL = (
    f"{LAYER_URL}/query?where=1%3D1"
    "&outFields=OBJECTID%2CFIRE_NM%2CFIRE_NUM%2CCOMPLEX%2CSTART_DATE%2C"
    "RPTD_ACRES%2CSTATUS%2CUNIT_ID%2CINCIWEB%2CINFO_LINK%2CIRWIN_ID%2C"
    "FIRE_CODE%2CGlobalID&orderByFields=START_DATE+DESC&resultRecordCount=10"
    "&returnGeometry=true&outSR=4326&f=json"
)
MAX_BYTES = 48_000
_UNIT = re.compile(r"WA[A-Z]{3}\Z")
_FIRE_NUM = re.compile(r"\d{6}\Z")
_UUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")
_FIELDS = {"OBJECTID", "FIRE_NM", "FIRE_NUM", "START_DATE", "RPTD_ACRES",
           "STATUS", "UNIT_ID", "INCIWEB", "IRWIN_ID", "GlobalID"}


def parse_nwcc_point_daily_fixture(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "REGIONAL" or source.get("id") != "nwcc_point_daily_wa":
        raise NewsParserError("NWCC daily points require their REGIONAL registry source")
    if not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("NWCC daily-point parser is fixture-only")
    if source.get("official_url") != QUERY_URL:
        raise NewsParserError("NWCC daily points require the exact official query URL")
    if len(payload_text.encode("utf-8")) > MAX_BYTES:
        raise PayloadTooLargeError("NWCC daily-point fixture exceeds 48 KB")
    try:
        fixture = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError("Malformed NWCC daily-point fixture") from exc
    if not isinstance(fixture, dict) or fixture.get("layer_url") != LAYER_URL:
        raise NewsParserError("NWCC daily-point layer provenance is missing")
    edit_ms = fixture.get("data_last_edit_ms")
    if type(edit_ms) is not int or not 1_577_836_800_000 <= edit_ms <= 4_102_444_800_000:
        raise NewsParserError("NWCC daily-point layer edit time is invalid")
    edit = datetime.fromtimestamp(edit_ms / 1000, tz=UTC)
    payload = fixture.get("query")
    if (not isinstance(payload, dict) or payload.get("error") is not None
            or payload.get("objectIdFieldName") != "OBJECTID"
            or payload.get("geometryType") != "esriGeometryPoint"
            or payload.get("exceededTransferLimit") is True
            or (payload.get("spatialReference") or {}).get("wkid") != 4326):
        raise NewsParserError("NWCC daily-point response metadata is invalid")
    fields, rows = payload.get("fields"), payload.get("features")
    if (not isinstance(fields, list) or not _FIELDS <= {
        field.get("name") for field in fields if isinstance(field, dict)
    } or not isinstance(rows, list) or len(rows) > 10):
        raise NewsParserError("NWCC daily-point response lacks bounded fields")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, feature in enumerate(rows):
        row = feature.get("attributes") if isinstance(feature, dict) else None
        point = feature.get("geometry") if isinstance(feature, dict) else None
        if not isinstance(row, dict) or not isinstance(point, dict):
            raise NewsParserError(f"NWCC daily-point row {index} lacks attributes or geometry")
        unit = row.get("UNIT_ID")
        if isinstance(unit, str) and unit.startswith("OR"):
            continue
        number = row.get("FIRE_NUM")
        if (not isinstance(unit, str) or not _UNIT.fullmatch(unit)
                or not isinstance(number, str) or not _FIRE_NUM.fullmatch(number)):
            raise NewsParserError(f"NWCC daily-point row {index} lacks WA unit/fire number")
        name = bounded_text(row.get("FIRE_NM"), max_chars=100)
        try:
            start = datetime.strptime(str(row.get("START_DATE")), "%m/%d/%Y").replace(tzinfo=UTC)
        except ValueError as exc:
            raise NewsParserError(f"NWCC daily-point row {index} has invalid start date") from exc
        lat, lon = point.get("y"), point.get("x")
        acres = row.get("RPTD_ACRES")
        if (not name or start > edit or row.get("STATUS") != "Active"
                or isinstance(lat, bool) or not isinstance(lat, (int, float))
                or isinstance(lon, bool) or not isinstance(lon, (int, float))
                or not math.isfinite(lat) or not math.isfinite(lon)
                or not 45.5 <= lat <= 49.1 or not -125 <= lon <= -116
                or isinstance(acres, bool) or not isinstance(acres, (int, float))
                or not math.isfinite(acres) or not 0 <= acres <= 20_000_000):
            raise NewsParserError(f"NWCC daily-point row {index} has invalid WA fire data")
        if any(not isinstance(row.get(field), str) or not _UUID.fullmatch(row[field])
               for field in ("IRWIN_ID", "GlobalID")):
            raise NewsParserError(f"NWCC daily-point row {index} has invalid official IDs")
        inciweb = row.get("INCIWEB")
        parts = urlsplit(inciweb) if isinstance(inciweb, str) else None
        if (parts is None or parts.scheme != "https" or parts.hostname != "inciweb.wildfire.gov"
                or not parts.path.startswith(f"/incident-information/{unit.lower()}-")
                or parts.query or parts.fragment):
            raise NewsParserError(f"NWCC daily-point row {index} has invalid InciWeb link")
        fire_key = f"{start.year}-{unit}-{number}"
        if fire_key in seen:
            raise NewsParserError(f"NWCC daily-point row {index} duplicates a fire")
        seen.add(fire_key)
        canonical = f"{LAYER_URL}?{urlencode({'fire_key': fire_key})}"
        item = _normalize_item(source, {
            "title": f"NWCC daily fire point: {name} ({unit} unit)",
            "url": inciweb,
            "canonical_url": canonical,
            "description": (
                f"NWCC layer labeled this fire Active as of {edit.date().isoformat()} "
                f"and reported {acres:g} acres. Current activity and public impact are unverified."
            ),
            "published_at": edit.isoformat(),
            "tags": ["official", "wildfire", "daily-point-snapshot"],
        }, index=index)
        item["evidence"]["nwcc_point_daily"] = {
            "fire_name": name,
            "unit_id": unit,
            "fire_number": number,
            "normalized_fire_key": fire_key,
            "start_date": start.date().isoformat(),
            "source_data_last_edit_at": edit.isoformat(),
            "status_at_source_snapshot": "Active",
            "reported_acres": float(acres),
            "latitude": float(lat),
            "longitude": float(lon),
            "irwin_id": row["IRWIN_ID"],
            "global_id": row["GlobalID"],
            "source_url": LAYER_URL,
            "query_url": QUERY_URL,
            "geography_basis": "official_WA_unit_and_point_bounds",
            "active_now_verified": False,
            "evacuation_claimed": False,
            "public_impact_inferred": False,
            "fixture_only": True,
        }
        item["evidence"]["regional_identity"] = {"fire_incident": name}
        items.append(item)
    return items
