"""Fixture-only NWCC large-fire metadata from its public ArcGIS view."""

from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode, urlsplit

from console1701.news.normalize import bounded_text
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

DATASET_URL = "https://www.arcgis.com/home/item.html?id=d2408259cd05480f876acc7a51840ff4"
LAYER_URL = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "NWCC_Large_Fire_Information_Public_View/FeatureServer/0"
)
QUERY_URL = (
    f"{LAYER_URL}/query?where=UNIT_ID%20LIKE%20%27WA%25%27"
    "&outFields=FIRE_NM%2CFIRE_NUM%2CUNIT_ID%2CSTART_DATE%2CRPTD_ACRES%2C"
    "Percent_Contained%2CEditDate%2CINCIWEB%2CGlobalID"
    "&orderByFields=EditDate%20DESC&resultRecordCount=100&returnGeometry=false&f=json"
)
MAX_BYTES = 65_536
MAX_ROWS = 100
_UNIT = re.compile(r"WA[A-Z]{3}\Z")
_FIRE_NUM = re.compile(r"\d{6}\Z")
_GLOBAL_ID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")
_FIELDS = {
    "FIRE_NM", "FIRE_NUM", "UNIT_ID", "START_DATE", "RPTD_ACRES",
    "Percent_Contained", "EditDate", "INCIWEB", "GlobalID",
}


def parse_nwcc_large_fire_fixture(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "REGIONAL" or source.get("id") != "nwcc_large_fire_wa":
        raise NewsParserError("NWCC large-fire fixture requires its REGIONAL registry source")
    if not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("NWCC large-fire parser is fixture-only")
    if source.get("official_url") != QUERY_URL:
        raise NewsParserError("NWCC large-fire fixture requires the exact official query URL")
    if len(payload_text.encode("utf-8")) > MAX_BYTES:
        raise PayloadTooLargeError("NWCC large-fire fixture exceeds 64 KiB")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError("Malformed NWCC large-fire JSON fixture") from exc
    if (not isinstance(payload, dict) or payload.get("error") is not None
            or payload.get("objectIdFieldName") != "OBJECTID"
            or payload.get("geometryType") != "esriGeometryPoint"
            or payload.get("exceededTransferLimit") is True):
        raise NewsParserError("NWCC large-fire response has invalid or incomplete metadata")
    fields = payload.get("fields")
    rows = payload.get("features")
    if (not isinstance(fields, list) or not _FIELDS <= {
        field.get("name") for field in fields if isinstance(field, dict)
    } or not isinstance(rows, list) or len(rows) > MAX_ROWS):
        raise NewsParserError("NWCC large-fire response lacks bounded fields")

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, feature in enumerate(rows):
        row = feature.get("attributes") if isinstance(feature, dict) else None
        if not isinstance(row, dict):
            raise NewsParserError(f"NWCC large-fire feature {index} has no attributes")
        unit, fire_num = row.get("UNIT_ID"), row.get("FIRE_NUM")
        if (not isinstance(unit, str) or not _UNIT.fullmatch(unit)
                or not isinstance(fire_num, str) or not _FIRE_NUM.fullmatch(fire_num)):
            raise NewsParserError(f"NWCC large-fire feature {index} lacks a WA unit/fire number")
        name = bounded_text(row.get("FIRE_NM"), max_chars=100)
        try:
            start = datetime.strptime(str(row.get("START_DATE")), "%m/%d/%Y").replace(tzinfo=UTC)
        except ValueError as exc:
            raise NewsParserError(
                f"NWCC large-fire feature {index} has invalid start date"
            ) from exc
        raw_edit = row.get("EditDate")
        if type(raw_edit) is not int or not 1_577_836_800_000 <= raw_edit <= 4_102_444_800_000:
            raise NewsParserError(f"NWCC large-fire feature {index} has invalid edit time")
        edit = datetime.fromtimestamp(raw_edit / 1000, tz=UTC)
        if not name or start > edit:
            raise NewsParserError(f"NWCC large-fire feature {index} lacks valid name/timing")
        acres = row.get("RPTD_ACRES")
        percent = row.get("Percent_Contained")
        if (isinstance(acres, bool) or not isinstance(acres, (int, float))
                or not math.isfinite(acres) or not 0 <= acres <= 20_000_000
                or type(percent) is not int or not 0 <= percent <= 100):
            raise NewsParserError(
                f"NWCC large-fire feature {index} has invalid acreage/containment"
            )
        global_id = row.get("GlobalID")
        if not isinstance(global_id, str) or not _GLOBAL_ID.fullmatch(global_id):
            raise NewsParserError(f"NWCC large-fire feature {index} has invalid GlobalID")
        inciweb = row.get("INCIWEB")
        parts = urlsplit(inciweb) if isinstance(inciweb, str) else None
        if (parts is None or parts.scheme != "https" or parts.hostname != "inciweb.wildfire.gov"
                or not parts.path.startswith(f"/incident-information/{unit.lower()}-")
                or parts.query or parts.fragment):
            raise NewsParserError(f"NWCC large-fire feature {index} has invalid InciWeb link")
        incident_id = f"WA-{unit[2:]}-{fire_num}"
        fire_key = f"{start.year}-{unit}-{fire_num}"
        if fire_key in seen:
            raise NewsParserError(f"NWCC large-fire feature {index} duplicates an incident")
        seen.add(fire_key)
        canonical = f"{DATASET_URL}&{urlencode({'incident_id': incident_id, 'year': start.year})}"
        item = _normalize_item(source, {
            "title": f"NWCC large-fire report: {name} ({unit} unit)",
            "url": inciweb,
            "canonical_url": canonical,
            "description": (
                f"NWCC reports {acres:g} acres and {percent}% containment. "
                "The record edit time does not establish current fire activity or public impact."
            ),
            "published_at": edit.isoformat(),
            "tags": ["official", "wildfire", "large-fire-information"],
        }, index=index)
        item["evidence"]["nwcc_large_fire"] = {
            "fire_name": name,
            "unit_id": unit,
            "fire_number": fire_num,
            "incident_id": incident_id,
            "normalized_fire_key": fire_key,
            "start_date": start.date().isoformat(),
            "edit_at": edit.isoformat(),
            "reported_acres": float(acres),
            "percent_contained": percent,
            "global_id": global_id,
            "inciweb_url": inciweb,
            "source_url": DATASET_URL,
            "query_url": QUERY_URL,
            "canonical_url_basis": "local_unit_number_year_key_not_source_deep_link",
            "geography_basis": "official_WA_management_unit_not_fire_point",
            "active_fire_claimed": False,
            "evacuation_claimed": False,
            "public_impact_inferred": False,
            "fixture_only": True,
        }
        item["evidence"]["regional_identity"] = {"fire_incident": name}
        items.append(item)
    return items
