"""Fixture-only WA DNR fire statistics without an active-incident claim."""

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
    "https://gis.dnr.wa.gov/site3/rest/services/Public_Wildfire/"
    "WADNR_PUBLIC_WD_WildFire_Data/MapServer/1"
)
QUERY_FIELDS = (
    "OBJECTID,FIREEVENT_ID,INCIDENT_NM,INCIDENT_ID,COUNTY_LABEL_NM,"
    "ACRES_BURNED,DSCVR_DT,CONTROL_DT,FIRE_OUT_DT,"
    "FIREEVNT_CLASS_LABEL_NM,START_JURISDICTION_AGENCY_NM"
)
QUERY_URL = f"{LAYER_URL}/query?" + urlencode({
    "where": "DSCVR_DT >= DATE '2026-07-01' AND ACRES_BURNED >= 1000",
    "outFields": QUERY_FIELDS,
    "orderByFields": "DSCVR_DT DESC",
    "resultRecordCount": "40", "returnGeometry": "false", "f": "json",
})
SMALL_QUERY_URL = f"{LAYER_URL}/query?" + urlencode({
    "where": "DSCVR_DT >= DATE '2026-09-01' AND ACRES_BURNED >= 100",
    "outFields": QUERY_FIELDS,
    "orderByFields": "DSCVR_DT DESC",
    "resultRecordCount": "10", "returnGeometry": "false", "f": "json",
})
MAX_BYTES = 16_384
_FIELDS = {
    "OBJECTID", "FIREEVENT_ID", "INCIDENT_NM", "INCIDENT_ID", "COUNTY_LABEL_NM",
    "ACRES_BURNED", "DSCVR_DT", "CONTROL_DT", "FIRE_OUT_DT",
    "FIREEVNT_CLASS_LABEL_NM", "START_JURISDICTION_AGENCY_NM",
}
_COUNTY = re.compile(r"[A-Z][A-Z ]{1,29}\Z")


def _date(value: Any, *, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if type(value) is not int or not 1_577_836_800_000 <= value <= 4_102_444_800_000:
        raise NewsParserError("WA DNR fire statistics contain an invalid date")
    return datetime.fromtimestamp(value / 1000, tz=UTC).date().isoformat()


def parse_wa_dnr_fire_statistics_fixture(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "REGIONAL" or source.get("id") != "wa_dnr_fire_statistics":
        raise NewsParserError("WA DNR fire statistics require the REGIONAL registry source")
    if not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("WA DNR fire statistics parser is fixture-only")
    query_url = source.get("official_url")
    if query_url not in {QUERY_URL, SMALL_QUERY_URL}:
        raise NewsParserError("WA DNR fire statistics require the exact official query")
    min_date, min_acres, max_rows = (
        ("2026-07-01", 1000, 40) if query_url == QUERY_URL
        else ("2026-09-01", 100, 10)
    )
    if len(payload_text.encode("utf-8")) > MAX_BYTES:
        raise PayloadTooLargeError("WA DNR fire statistics exceed 16 KiB")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError("Malformed WA DNR fire statistics JSON") from exc
    if (not isinstance(payload, dict) or payload.get("error") is not None
            or payload.get("displayFieldName") != "INCIDENT_NM"):
        raise NewsParserError("WA DNR fire statistics lack the official layer envelope")
    fields = payload.get("fields")
    rows = payload.get("features")
    if (not isinstance(fields, list) or not _FIELDS <= {
            field.get("name") for field in fields if isinstance(field, dict)
        } or not isinstance(rows, list) or len(rows) > max_rows
            or payload.get("exceededTransferLimit") is True):
        raise NewsParserError("WA DNR fire statistics lack bounded fields")

    items: list[dict[str, Any]] = []
    seen: set[int] = set()
    for index, feature in enumerate(rows):
        row = feature.get("attributes") if isinstance(feature, dict) else None
        if not isinstance(row, dict):
            raise NewsParserError(f"WA DNR fire feature {index} lacks attributes")
        if row.get("FIREEVNT_CLASS_LABEL_NM") != "WF":
            continue
        event_id = row.get("FIREEVENT_ID")
        incident_id = row.get("INCIDENT_ID")
        if (type(event_id) is not int or event_id <= 0 or event_id in seen
                or type(incident_id) is not int or incident_id <= 0):
            raise NewsParserError(f"WA DNR fire feature {index} lacks unique incident identity")
        seen.add(event_id)
        name = bounded_text(row.get("INCIDENT_NM"), max_chars=100)
        county = bounded_text(row.get("COUNTY_LABEL_NM"), max_chars=30)
        acres = row.get("ACRES_BURNED")
        if (not name or not isinstance(county, str) or not _COUNTY.fullmatch(county)
                or isinstance(acres, bool) or not isinstance(acres, (int, float))
                or not math.isfinite(acres) or not min_acres <= acres <= 20_000_000):
            raise NewsParserError(f"WA DNR fire feature {index} lacks bounded report fields")
        discovered = _date(row.get("DSCVR_DT"), required=True)
        controlled = _date(row.get("CONTROL_DT"))
        out = _date(row.get("FIRE_OUT_DT"))
        if discovered < min_date or (controlled and controlled < discovered) or (
            out and out < discovered
        ):
            raise NewsParserError(f"WA DNR fire feature {index} has inconsistent dates")
        if controlled and out and out < controlled:
            raise NewsParserError(f"WA DNR fire feature {index} has reversed lifecycle dates")
        jurisdiction = bounded_text(row.get("START_JURISDICTION_AGENCY_NM"), max_chars=80)
        record_url = f"{LAYER_URL}/query?" + urlencode({
            "where": f"FIREEVENT_ID={event_id}",
            "outFields": "FIREEVENT_ID,INCIDENT_NM,COUNTY_LABEL_NM,ACRES_BURNED,"
                         "DSCVR_DT,CONTROL_DT,FIRE_OUT_DT",
            "returnGeometry": "false", "f": "pjson",
        })
        item = _normalize_item(source, {
            "title": f"WA DNR fire statistics: {name.title()} in {county.title()} County",
            "url": record_url,
            "description": (
                f"WA DNR reports {acres:g} acres. Active fire and public impact "
                "are not established by this statistics layer."
            ),
            "published_at": discovered,
            "tags": ["official", "wildfire", "fire-statistics"],
        }, index=index)
        item["evidence"]["wa_dnr_fire_statistics"] = {
            "fire_event_id": event_id,
            "incident_id": incident_id,
            "fire_name": name,
            "county": county.title(),
            "reported_acres": float(acres),
            "discovery_date": discovered,
            "date_precision": "day",
            "control_date": controlled,
            "fire_out_date": out,
            "lifecycle_status": (
                "out_date_reported" if out else
                "control_date_reported" if controlled else "unknown"
            ),
            "start_jurisdiction_agency": jurisdiction,
            "active_fire_claimed": False,
            "evacuation_claimed": False,
            "public_impact_inferred": False,
            "source_url": LAYER_URL,
            "query_url": query_url,
            "item_url_kind": "official_record_query",
            "fixture_only": True,
        }
        item["evidence"]["regional_identity"] = {
            "fire_incident": name, "county": county.title(),
        }
        items.append(item)
    return items
