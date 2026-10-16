"""Fixture-only OpenFEMA declaration metadata; place rows form one event."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

API_URL = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries"
_DECLARATION_RE = re.compile(r"(DR|EM|FM)-(\d{1,6})-([A-Z]{2})\Z")
_TERRITORIES = {"AS", "GU", "MP", "PR", "VI"}
_FLAGS = ("ihProgramDeclared", "iaProgramDeclared", "paProgramDeclared", "hmProgramDeclared")
MAX_BYTES = 65_536
MAX_ROWS = 20


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise NewsParserError(f"OpenFEMA {field} must be a UTC timestamp")
    normalized = normalize_timestamp(value)
    if not normalized:
        raise NewsParserError(f"OpenFEMA {field} is invalid")
    return normalized


def parse_openfema_declarations_fixture(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if (source.get("scope") != "NATIONAL"
            or source.get("id") != "openfema_disaster_declarations"
            or not str(source.get("url") or "").startswith("file://")
            or source.get("official_url") != API_URL):
        raise NewsParserError("OpenFEMA parser requires its exact NATIONAL local fixture")
    if len(payload_text.encode("utf-8")) > MAX_BYTES:
        raise PayloadTooLargeError("OpenFEMA fixture exceeds 64 KiB")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError("Malformed OpenFEMA fixture JSON") from exc
    rows = payload.get("DisasterDeclarationsSummaries") if isinstance(payload, dict) else None
    if (not isinstance(rows, list) or len(rows) > MAX_ROWS
            or not isinstance(payload.get("metadata"), dict)
            or payload["metadata"].get("entityname") != "DisasterDeclarationsSummaries"
            or payload["metadata"].get("version") != "v2"):
        raise NewsParserError("OpenFEMA fixture has an invalid v2 bounded response")

    groups: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"OpenFEMA row {index} is not an object")
        number = row.get("disasterNumber")
        place = str(row.get("placeCode") or "")
        declaration = row.get("femaDeclarationString")
        match = (
            _DECLARATION_RE.fullmatch(declaration)
            if isinstance(declaration, str) else None
        )
        state = row.get("state")
        region = row.get("region")
        if (type(number) is not int or number < 1 or not re.fullmatch(r"\d{1,8}", place)
                or match is None or int(match[2]) != number or match[3] != state
                or row.get("declarationType") != match[1]
                or type(region) is not int or not 1 <= region <= 10):
            raise NewsParserError(f"OpenFEMA row {index} has inconsistent declaration identity")
        title = bounded_text(row.get("declarationTitle"), max_chars=180)
        incident_type = bounded_text(row.get("incidentType"), max_chars=80)
        area = bounded_text(row.get("designatedArea"), max_chars=120)
        if not title or not incident_type or not area:
            raise NewsParserError(f"OpenFEMA row {index} lacks bounded declaration metadata")
        declared = _timestamp(row.get("declarationDate"), "declarationDate")
        refreshed = _timestamp(row.get("lastRefresh"), "lastRefresh")
        incident_begin = _timestamp(row.get("incidentBeginDate"), "incidentBeginDate")
        incident_end = (
            _timestamp(row["incidentEndDate"], "incidentEndDate")
            if row.get("incidentEndDate") is not None else None
        )
        if (incident_end and incident_end < incident_begin) or refreshed < declared:
            raise NewsParserError(f"OpenFEMA row {index} has inconsistent dates")
        if any(type(row.get(flag)) is not bool for flag in (*_FLAGS, "tribalRequest")):
            raise NewsParserError(f"OpenFEMA row {index} lacks assistance/tribal flags")
        entry = {
            "place_code": place, "designated_area": area, "last_refresh": refreshed,
            "tribal_request": row["tribalRequest"],
            "assistance": {flag: row[flag] for flag in _FLAGS},
        }
        group = groups.setdefault(declaration, {
            "number": number, "state": state, "region": region,
            "type": match[1], "title": title, "incident_type": incident_type,
            "declaration_date": declared, "incident_begin": incident_begin,
            "incident_end": incident_end, "places": {},
        })
        stable = ("number", "state", "region", "type", "title", "incident_type",
                  "declaration_date", "incident_begin", "incident_end")
        if any(group[key] != value for key, value in zip(
            stable, (number, state, region, match[1], title, incident_type,
                     declared, incident_begin, incident_end), strict=True
        )):
            raise NewsParserError(f"OpenFEMA declaration {declaration} has inconsistent rows")
        prior = group["places"].get(place)
        if prior is None or refreshed > prior["last_refresh"]:
            group["places"][place] = entry

    items: list[dict[str, Any]] = []
    for index, (declaration, group) in enumerate(groups.items()):
        places = sorted(group["places"].values(), key=lambda entry: entry["place_code"])
        latest = max(entry["last_refresh"] for entry in places)
        recent_at_refresh = (
            datetime.fromisoformat(latest) - datetime.fromisoformat(group["declaration_date"])
            <= timedelta(days=7)
        )
        url = f"https://www.fema.gov/disaster/{group['number']}"
        item = _normalize_item(source, {
            "title": f"FEMA {declaration}: {group['title']}",
            "url": url, "published_at": group["declaration_date"],
            "description": "Federal disaster declaration metadata; current hazard status unknown.",
            "tags": ["official", "fema", "disaster-declaration", group["type"].lower()],
        }, index=index)
        item["evidence"]["openfema_declaration"] = {
            "declaration": declaration, "disaster_number": group["number"],
            "declaration_type": group["type"], "declaration_date": group["declaration_date"],
            "incident_type": group["incident_type"], "incident_begin": group["incident_begin"],
            "incident_end": group["incident_end"], "state": group["state"],
            "region": group["region"], "places": places, "last_refresh": latest,
            "source_url": API_URL, "dataset_version": "v2", "fixture_only": True,
            "active_hazard_claimed": False, "exact_footprint_claimed": False,
            "recent_declaration_at_refresh": recent_at_refresh,
            "ranking": {"public_impact_score": 22 if recent_at_refresh else 0,
                        "basis": "FEMA declaration date, not dataset refresh date"},
        }
        tribal = any(entry["tribal_request"] for entry in places)
        state = group["state"]
        item["evidence"]["national_identity"] = {
            "event_type": "disaster_declaration", "agency": "FEMA",
            "official_event_ids": [f"fema:{declaration.lower()}"],
            "affected_states": [state] if state not in _TERRITORIES and not tribal else [],
            "affected_territories": [state] if state in _TERRITORIES and not tribal else [],
            "fema_regions": [str(group["region"])],
            "jurisdictions": ["tribal declaration"] if tribal else [],
            "multi_state_impact": False, "official_disaster_declaration": recent_at_refresh,
        }
        items.append(item)
    return items
