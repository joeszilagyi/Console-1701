"""Fixture-only NIFC WFIGS current/recent Washington wildfire metadata."""

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
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "WFIGS_Incident_Locations_Current/FeatureServer/0"
)
DATASET_URL = (
    "https://data-nifc.opendata.arcgis.com/datasets/"
    "nifc::current-wildland-fire-incident-locations/explore"
)
_FIELDS = (
    "OBJECTID", "IrwinID", "UniqueFireIdentifier", "IncidentName",
    "FireDiscoveryDateTime", "ModifiedOnDateTime_dt", "IncidentSize",
    "PercentContained", "POOState", "POOCounty", "ActiveFireCandidate",
    "ContainmentDateTime", "ControlDateTime", "FireOutDateTime",
    "IncidentTypeCategory", "POOJurisdictionalAgency", "POOJurisdictionalUnit",
)
QUERY_URL = LAYER_URL + "/query?" + urlencode({
    "where": (
        "POOState = 'US-WA' AND IncidentTypeCategory = 'WF' "
        "AND ActiveFireCandidate = 1 AND IncidentSize >= 1000 "
        "AND ModifiedOnDateTime_dt >= DATE '2026-10-01'"
    ),
    "outFields": ",".join(_FIELDS),
    "orderByFields": "ModifiedOnDateTime_dt DESC",
    "resultRecordCount": "25",
    "returnGeometry": "false",
    "f": "json",
})
MAX_BYTES = 32_768
MAX_ROWS = 25
_UNIQUE_ID = re.compile(r"20\d{2}-WA[A-Z0-9]{2,5}-\d{4,8}\Z")
_IRWIN_ID = re.compile(r"\{[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}\}\Z")


def _timestamp(value: Any, *, field: str) -> str:
    if type(value) is not int or not 1_577_836_800_000 <= value <= 4_102_444_800_000:
        raise NewsParserError(f"NIFC WFIGS {field} has invalid timestamp")
    return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat()


def parse_nifc_wfigs_fixture(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if source.get("scope") != "REGIONAL" or source.get("id") != "nifc_wfigs_current_wa":
        raise NewsParserError("NIFC WFIGS fixture requires its REGIONAL registry source")
    if not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("NIFC WFIGS parser is fixture-only")
    if source.get("official_url") != QUERY_URL:
        raise NewsParserError("NIFC WFIGS fixture requires the exact official query URL")
    if len(payload_text.encode("utf-8")) > MAX_BYTES:
        raise PayloadTooLargeError("NIFC WFIGS fixture exceeds 32 KiB")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError("Malformed NIFC WFIGS JSON fixture") from exc
    if (not isinstance(payload, dict) or payload.get("error") is not None
            or payload.get("objectIdFieldName") != "OBJECTID"
            or payload.get("geometryType") != "esriGeometryPoint"
            or payload.get("exceededTransferLimit") is True):
        raise NewsParserError("NIFC WFIGS response has invalid or incomplete metadata")
    fields, rows = payload.get("fields"), payload.get("features")
    if (not isinstance(fields, list) or not set(_FIELDS) <= {
        field.get("name") for field in fields if isinstance(field, dict)
    } or not isinstance(rows, list) or len(rows) > MAX_ROWS):
        raise NewsParserError("NIFC WFIGS response lacks bounded fields")

    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, feature in enumerate(rows):
        row = feature.get("attributes") if isinstance(feature, dict) else None
        if not isinstance(row, dict):
            raise NewsParserError(f"NIFC WFIGS feature {index} lacks attributes")
        unique = row.get("UniqueFireIdentifier")
        irwin = row.get("IrwinID")
        if (not isinstance(unique, str) or not _UNIQUE_ID.fullmatch(unique)
                or unique in seen or not isinstance(irwin, str)
                or not _IRWIN_ID.fullmatch(irwin)
                or row.get("POOState") != "US-WA"
                or row.get("IncidentTypeCategory") != "WF"
                or type(row.get("ActiveFireCandidate")) is not int
                or row["ActiveFireCandidate"] != 1):
            raise NewsParserError(f"NIFC WFIGS feature {index} lacks WA wildfire identity")
        seen.add(unique)
        name = bounded_text(row.get("IncidentName"), max_chars=100)
        county = bounded_text(row.get("POOCounty"), max_chars=80)
        discovered = _timestamp(row.get("FireDiscoveryDateTime"), field="discovery")
        modified = _timestamp(row.get("ModifiedOnDateTime_dt"), field="modified")
        if (not name or not county or discovered > modified
                or modified < "2026-10-01T00:00:00+00:00"):
            raise NewsParserError(f"NIFC WFIGS feature {index} has invalid name or timing")
        acres = row.get("IncidentSize")
        percent = row.get("PercentContained")
        if (isinstance(acres, bool) or not isinstance(acres, (int, float))
                or not math.isfinite(acres) or not 1_000 <= acres <= 20_000_000
                or percent is not None and (
                    isinstance(percent, bool) or not isinstance(percent, (int, float))
                    or not math.isfinite(percent) or not 0 <= percent <= 100
                )):
            raise NewsParserError(f"NIFC WFIGS feature {index} has invalid size/containment")
        ended = {
            field: (_timestamp(row[field], field=field) if row.get(field) is not None else None)
            for field in ("ContainmentDateTime", "ControlDateTime", "FireOutDateTime")
        }
        if any(value and value < discovered for value in ended.values()):
            raise NewsParserError(f"NIFC WFIGS feature {index} has invalid lifecycle timing")
        item = _normalize_item(source, {
            "title": f"NIFC WFIGS incident: {name} fire in Washington",
            "url": DATASET_URL,
            "canonical_url": f"{DATASET_URL}?{urlencode({'fire_id': unique})}",
            "description": (
                f"WFIGS reports {acres:g} acres and "
                f"{f'{percent:g}% containment' if percent is not None else 'unknown containment'}. "
                "ActiveFireCandidate does not establish current fire activity."
            ),
            "published_at": modified,
            "tags": ["official", "wildfire", "current-recent-incident"],
        }, index=index)
        item["evidence"]["nifc_wfigs"] = {
            "unique_fire_identifier": unique,
            "irwin_id": irwin,
            "fire_name": name,
            "county": county,
            "discovery_at": discovered,
            "modified_at": modified,
            "reported_acres": float(acres),
            "percent_contained": float(percent) if percent is not None else None,
            "active_fire_candidate": True,
            "active_fire_claimed": False,
            "evacuation_claimed": False,
            "public_impact_inferred": False,
            "source_url": DATASET_URL,
            "query_url": QUERY_URL,
            "canonical_url_basis": "local_unique_fire_id_query_not_source_deep_link",
            "geography_basis": "official_WA_point_of_origin_state_and_county",
            "fixture_only": True,
            **{
                {"ContainmentDateTime": "containment_at",
                 "ControlDateTime": "control_at",
                 "FireOutDateTime": "out_at"}[field]: value
                for field, value in ended.items()
            },
        }
        item["evidence"]["regional_identity"] = {
            "fire_incident": name, "county": county,
        }
        items.append(item)
    return items
