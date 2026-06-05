from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin

from console1701.news.normalize import (
    MAX_DESCRIPTION_LENGTH,
    MAX_TITLE_LENGTH,
    bounded_text,
    normalize_timestamp,
    normalize_url,
)


class NewsIngestError(RuntimeError):
    """Base error for fixture ingest failures."""


class PayloadTooLargeError(NewsIngestError):
    """Raised when a local fixture exceeds the configured size cap."""


class UnsupportedSourceError(NewsIngestError):
    """Raised when a source is outside the local fixture-only phase."""


class NewsParserError(NewsIngestError):
    """Raised when a source fixture cannot be parsed."""


_METRO_ROUTES_RE = re.compile(
    r"\bRoutes\s+([A-Z0-9,\s/&-]+?)(?=\s+(?:are|will|rerouted|delayed|"
    r"canceled|cancelled|suspended|near|in|on|due|with)\b|[.;:]|$)",
    re.IGNORECASE,
)
_METRO_ROUTE_RE = re.compile(r"\bRoute\s+([A-Z]?\d{1,3}[A-Z]?)\b", re.IGNORECASE)
_METRO_ROUTE_TOKEN_RE = re.compile(r"\b[A-Z]?\d{1,3}[A-Z]?\b")
_SFD_LOW_ACUITY_RE = re.compile(
    r"\b(aid|basic life support|medical|medic|overdose|psychiatric|sick person)\b",
    re.IGNORECASE,
)
_SFD_PUBLIC_IMPACT_RE = re.compile(
    r"\b(fire|hazmat|rescue|water rescue|motor vehicle|collision|marine|"
    r"structure|brush|explosion|natural gas)\b",
    re.IGNORECASE,
)
_WSDOT_ROUTE_RE = re.compile(r"\b(?:I-\d+|US\s?\d+|SR\s?\d+|WA\s?\d+)\b", re.IGNORECASE)
_SPD_IMPACT_RE = re.compile(
    r"\b(incident|shooting|fatal|homicide|explosion|fire|crash|collision|arrest|evacuation|missing|"
    r"robbery|assault|significant)\b",
    re.IGNORECASE,
)
_SPD_MAJOR_IMPACT_RE = re.compile(r"\b(critical|major|severe|fatal|homicide|shooting|explosion)\b")
_SPD_PRELIMINARY_RE = re.compile(r"\b(preliminary|prelim|investigating|update)\b", re.IGNORECASE)
_SPD_LOW_ACUITY_RE = re.compile(
    r"\b(aid|assistance|medical|medic|overdose|psychiatric|sick|suicide|domestic|mental|welfare)\b",
    re.IGNORECASE,
)
_SPD_OVERDOSE_RE = re.compile(r"\boverdose\b", re.IGNORECASE)
_SDOT_BLOG_IMPACT_RE = re.compile(
    r"\b(bridge|highway|freeway|transit|bus|light rail|road|street|"
    r"flood|storm|closure|delay|accident)\b",
    re.IGNORECASE,
)


def resolve_file_url(url: str, *, config_dir: Path) -> Path:
    if not url.startswith("file://"):
        raise UnsupportedSourceError("Only file:// sources are allowed during fixture ingest.")
    raw_path = url[len("file://") :]
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (config_dir / path).resolve()
    return path


def load_fixture_text(
    source: dict[str, Any],
    *,
    config_dir: Path,
    max_bytes: int,
) -> tuple[str, Path]:
    path = resolve_file_url(str(source.get("url") or ""), config_dir=config_dir)
    try:
        size = path.stat().st_size
    except FileNotFoundError as exc:
        raise NewsIngestError(f"Fixture file not found: {path}") from exc
    if size > max_bytes:
        raise PayloadTooLargeError(
            f"Fixture exceeds max_response_bytes: {size} > {max_bytes} for {path.name}"
        )
    return path.read_text(encoding="utf-8"), path


def parse_fixture_items(
    source: dict[str, Any],
    payload_text: str,
) -> list[dict[str, Any]]:
    parser_name = str(source.get("parser") or "").strip().lower()
    kind = str(source.get("kind") or "").strip().lower()

    if parser_name == "nws_alerts_json":
        return _parse_nws_alerts_json(source, payload_text)
    if parser_name == "alertseattle_rss":
        return _parse_alertseattle_rss_feed(source, payload_text)
    if parser_name == "metro_rss":
        return _parse_metro_rss_feed(source, payload_text)
    if parser_name == "local_blog_rss":
        return _parse_local_blog_rss_feed(source, payload_text)
    if parser_name in {"spd_blotter_rss", "spd_blotter_feed"}:
        return _parse_spd_blotter_rss_feed(source, payload_text)
    if parser_name in {"sdot_blog_rss", "sdot_blog_feed"}:
        return _parse_sdot_blog_rss_feed(source, payload_text)
    if parser_name in {"local_news_rss", "regional_news_rss"}:
        return _parse_local_news_rss_feed(source, payload_text)
    if parser_name == "sfd_fire_911_socrata":
        return _parse_sfd_fire_911_socrata(source, payload_text)
    if parser_name == "wsdot_travel_alerts_json":
        return _parse_wsdot_travel_alerts_json(source, payload_text)
    if parser_name == "city_light_outages_json":
        return _parse_city_light_outages_json(source, payload_text)
    if parser_name == "faa_airport_status_json":
        return _parse_faa_airport_status_json(source, payload_text)
    if parser_name == "generic_json_items" or kind in {
        "local_file_json",
        "api_json",
        "open_data_json",
    }:
        return _parse_json_items(source, payload_text)
    if parser_name == "homepage_selectors" or kind == "homepage_headlines":
        return _parse_homepage_items(source, payload_text)
    if kind in {"local_file_rss", "rss", "atom"}:
        return _parse_xml_feed(source, payload_text)
    raise UnsupportedSourceError(f"Unsupported fixture parser for source kind: {kind}")


def _normalize_item(
    source: dict[str, Any],
    raw_item: dict[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    title = bounded_text(raw_item.get("title"), max_chars=MAX_TITLE_LENGTH)
    url = normalize_url(raw_item.get("url") or raw_item.get("link"))
    if not title or not url:
        raise NewsParserError(f"Item {index} is missing a title or URL.")
    description = bounded_text(
        raw_item.get("description") or raw_item.get("summary"),
        max_chars=MAX_DESCRIPTION_LENGTH,
    )

    raw_tags = raw_item.get("tags") or raw_item.get("categories") or []
    tags: list[str] = []
    if isinstance(raw_tags, list):
        for value in raw_tags:
            text = bounded_text(value, max_chars=64)
            if text and text not in tags:
                tags.append(text)
    elif isinstance(raw_tags, str):
        text = bounded_text(raw_tags, max_chars=64)
        if text:
            tags.append(text)

    return {
        "scope": source["scope"],
        "title": title,
        "url": url,
        "canonical_url": normalize_url(raw_item.get("canonical_url") or url),
        "description": description,
        "source_published_at": normalize_timestamp(
            raw_item.get("published_at")
            or raw_item.get("published")
            or raw_item.get("updated")
            or raw_item.get("pub_date")
            or raw_item.get("date")
        ),
        "tags": tags,
        "evidence": {
            "parser": str(source.get("parser") or source.get("kind") or "unknown"),
            "raw_index": index,
        },
    }


def _parse_json_items(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed JSON fixture: {exc}") from exc
    if isinstance(payload, dict):
        items = payload.get("items")
    else:
        items = payload
    if not isinstance(items, list):
        raise NewsParserError("JSON fixture must be a list or an object with an items list.")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise NewsParserError(f"JSON item {index} must be an object.")
        normalized.append(_normalize_item(source, item, index=index))
    return normalized


def _parse_sfd_fire_911_socrata(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed SFD Socrata JSON fixture: {exc}") from exc
    if isinstance(payload, dict):
        rows = payload.get("items") or payload.get("rows") or payload.get("data")
    else:
        rows = payload
    if not isinstance(rows, list):
        raise NewsParserError("SFD Socrata fixture must be a list or object with row list.")

    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"SFD Socrata row {index} must be an object.")
        normalized.append(_normalize_sfd_fire_911_row(source, row, index=index))
    return normalized


def _normalize_sfd_fire_911_row(
    source: dict[str, Any],
    row: dict[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    dataset_id = str(source.get("dataset_id") or "kzjm-xkqj")
    row_id = bounded_text(
        _first_value(row, ":id", "row_id", "id", "sid", "incident_number", "incident_num"),
        max_chars=120,
    )
    incident_number = bounded_text(
        _first_value(row, "incident_number", "incident_num", "incident_no", "cad_event_number"),
        max_chars=120,
    )
    incident_type = bounded_text(
        _first_value(row, "type", "incident_type", "call_type", "event_type"),
        max_chars=160,
    )
    observed_at = normalize_timestamp(
        _first_value(row, "datetime", "date_time", "event_time", "observed_at", "alarm_datetime")
    )
    if not incident_type or not observed_at:
        raise NewsParserError(f"SFD Socrata row {index} is missing incident type or timestamp.")
    unit_count = _int_value(
        _first_value(row, "unit_count", "units", "units_dispatched", "unit_count_total")
    )
    address = bounded_text(_first_value(row, "address", "address_raw"), max_chars=240)
    neighborhood = bounded_text(
        _first_value(row, "neighborhood", "neighborhood_district"),
        max_chars=120,
    )
    location_tokens = _sfd_location_tokens(row, address=address, neighborhood=neighborhood)
    privacy = _sfd_privacy_decision(
        incident_type=incident_type,
        unit_count=unit_count,
        neighborhood=neighborhood,
        address=address,
    )
    display_location = privacy["display_location"]
    source_url = _sfd_source_url(source, row_id or incident_number or str(index))
    title = f"SFD {incident_type} near {display_location}"
    description = _sfd_description(
        incident_type=incident_type,
        unit_count=unit_count,
        privacy=privacy,
    )
    public_impact = _sfd_public_impact(incident_type=incident_type, unit_count=unit_count)
    tags = _unique_texts(
        [
            "official",
            "sfd",
            "fire_911",
            incident_type.lower(),
            "public-impact" if public_impact["elevated"] else None,
            "privacy-redacted" if privacy["exact_location_suppressed"] else None,
        ],
        max_chars=64,
    )
    item = _normalize_item(
        source,
        {
            "title": title,
            "url": source_url,
            "canonical_url": source_url,
            "description": description,
            "published_at": observed_at,
            "tags": tags,
        },
        index=index,
    )
    item["evidence"]["sfd_fire_911"] = {
        "dataset_id": dataset_id,
        "row_id": row_id,
        "incident_number": incident_number,
        "incident_type": incident_type,
        "observed_at": observed_at,
        "unit_count": unit_count,
        "source_url": source_url,
        "location_tokens": location_tokens,
        "location_basis": privacy["location_basis"],
        "public_impact": public_impact,
    }
    item["evidence"]["privacy"] = {
        "exact_location_suppressed": privacy["exact_location_suppressed"],
        "redaction_applied": privacy["exact_location_suppressed"],
        "redaction_reason": privacy["redaction_reason"],
        "display_location": display_location,
        "raw_address_stored": False,
        "low_acuity_private": privacy["low_acuity_private"],
        "overdose_related": privacy["overdose_related"],
        "privacy_category": privacy["privacy_category"],
    }
    return item


def _first_value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def _int_value(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _sfd_source_url(source: dict[str, Any], row_key: str) -> str:
    explicit = str(source.get("homepage_url") or source.get("url") or "").strip()
    base_url = (
        explicit
        or "https://data.seattle.gov/Public-Safety/Seattle-Real-Time-Fire-911-Calls/kzjm-xkqj"
    )
    separator = "&" if "?" in base_url else "?"
    return normalize_url(f"{base_url}{separator}row_id={quote(str(row_key))}")


def _sfd_location_tokens(
    row: dict[str, Any],
    *,
    address: str | None,
    neighborhood: str | None,
) -> list[str]:
    tokens = _unique_texts(
        [
            neighborhood,
            _street_only(address),
            _first_value(row, "cross_street", "intersection"),
            _first_value(row, "zone", "beat"),
        ],
        max_chars=120,
    )
    location = row.get("report_location") or row.get("location")
    if isinstance(location, dict):
        for key in ("human_address", "address"):
            text = bounded_text(location.get(key), max_chars=120)
            if text and text not in tokens:
                tokens.append(text)
    return tokens


def _sfd_privacy_decision(
    *,
    incident_type: str,
    unit_count: int | None,
    neighborhood: str | None,
    address: str | None,
) -> dict[str, Any]:
    low_acuity = bool(_SFD_LOW_ACUITY_RE.search(incident_type))
    public_impact = _sfd_public_impact(incident_type=incident_type, unit_count=unit_count)
    overdose_related = bool(_SPD_OVERDOSE_RE.search(incident_type))
    suppress_exact = low_acuity and not public_impact["elevated"]
    street_only = _street_only(address)
    if suppress_exact:
        display_location = neighborhood or street_only or "Seattle"
        reason = "Low-acuity or private medical call without public-impact signal."
        basis = "neighborhood" if neighborhood else "street_token" if street_only else "city"
    else:
        display_location = street_only or neighborhood or "Seattle"
        reason = "Exact private address is not stored; public display uses privacy-safe tokens."
        basis = "street_token" if street_only else "neighborhood" if neighborhood else "city"
    return {
        "exact_location_suppressed": suppress_exact,
        "redaction_reason": reason,
        "display_location": display_location,
        "location_basis": basis,
        "low_acuity_private": low_acuity,
        "overdose_related": overdose_related,
        "privacy_category": (
            "overdose" if overdose_related else "low_acuity" if low_acuity else "none"
        ),
    }


def _sfd_public_impact(*, incident_type: str, unit_count: int | None) -> dict[str, Any]:
    type_signal = bool(_SFD_PUBLIC_IMPACT_RE.search(incident_type))
    unit_signal = unit_count is not None and unit_count >= 5
    elevated = bool(type_signal or unit_signal)
    if unit_signal:
        reason = "unit_count_at_or_above_major_threshold"
    elif type_signal:
        reason = "incident_type_public_impact"
    else:
        reason = "no_public_impact_signal"
    return {
        "elevated": elevated,
        "unit_count": unit_count,
        "unit_threshold": 5,
        "type_signal": type_signal,
        "reason": reason,
        "public_impact_score": (
            (20 if type_signal else 0) + (min(unit_count or 0, 10) * 2) if elevated else 0
        ),
    }


def _sfd_description(
    *,
    incident_type: str,
    unit_count: int | None,
    privacy: dict[str, Any],
) -> str:
    unit_text = f" with {unit_count} reported unit(s)" if unit_count is not None else ""
    if privacy["exact_location_suppressed"]:
        return (
            f"SFD reported {incident_type}{unit_text}. Exact location suppressed by "
            "LOCAL privacy rules."
        )
    return f"SFD reported {incident_type}{unit_text} near {privacy['display_location']}."


def _street_only(address: str | None) -> str | None:
    if not address:
        return None
    text = re.sub(r"^\s*\d+[A-Z]?\s+", "", address).strip()
    text = re.sub(r"\b(?:Apt|Apartment|Unit|Suite|Ste)\s+\w+\b", "", text, flags=re.IGNORECASE)
    text = " ".join(text.split()).strip(" ,")
    return bounded_text(text, max_chars=120)


def _parse_wsdot_travel_alerts_json(
    source: dict[str, Any],
    payload_text: str,
) -> list[dict[str, Any]]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed WSDOT JSON fixture: {exc}") from exc
    if isinstance(payload, dict):
        rows = payload.get("alerts") or payload.get("items") or payload.get("data")
    else:
        rows = payload
    if not isinstance(rows, list):
        raise NewsParserError("WSDOT fixture must be a list or object with alert list.")

    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"WSDOT alert row {index} must be an object.")
        if not _wsdot_alert_matches_scope(source, row):
            continue
        normalized.append(_normalize_wsdot_alert(source, row, index=index))
    return normalized


def _normalize_wsdot_alert(
    source: dict[str, Any],
    row: dict[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    alert_id = bounded_text(_first_value(row, "alert_id", "AlertID", "id", "ID"), max_chars=120)
    title = bounded_text(
        _first_value(row, "headline", "Headline", "title", "Title"),
        max_chars=MAX_TITLE_LENGTH,
    )
    description = bounded_text(
        _first_value(
            row,
            "description",
            "Description",
            "extended_description",
            "ExtendedDescription",
        ),
        max_chars=MAX_DESCRIPTION_LENGTH,
    )
    published_at = normalize_timestamp(
        _first_value(row, "last_updated", "LastUpdatedTime", "published_at", "StartTime")
    )
    if not title or not published_at:
        raise NewsParserError(f"WSDOT alert row {index} is missing title or timestamp.")
    source_url = _wsdot_source_url(source, alert_id or str(index), row)
    route_tokens = _wsdot_route_tokens(row)
    facility_tokens = _wsdot_facility_tokens(source, row)
    impact = _wsdot_impact(row)
    tags = _unique_texts(
        [
            "official",
            "transport",
            "wsdot",
            impact["label"],
            *[route.lower().replace(" ", "-") for route in route_tokens],
        ],
        max_chars=64,
    )
    item = _normalize_item(
        source,
        {
            "title": title,
            "url": source_url,
            "canonical_url": source_url,
            "description": description,
            "published_at": published_at,
            "tags": tags,
        },
        index=index,
    )
    item["evidence"]["wsdot_alert"] = {
        "alert_id": alert_id,
        "route_tokens": route_tokens,
        "facility_tokens": facility_tokens,
        "impact": impact["label"],
        "impact_weight": impact["weight"],
        "priority": bounded_text(_first_value(row, "priority", "Priority"), max_chars=64),
        "county": bounded_text(_first_value(row, "county", "County"), max_chars=120),
        "region": bounded_text(_first_value(row, "region", "Region"), max_chars=120),
        "published_at": published_at,
        "source_url": source_url,
        "ranking": {
            "route_token_count": len(route_tokens),
            "facility_token_count": len(facility_tokens),
            "impact_weight": impact["weight"],
            "public_impact_score": min(60, impact["weight"] + len(route_tokens) * 6),
        },
        "filter": _wsdot_filter_evidence(source, row),
    }
    return item


def _wsdot_alert_matches_scope(source: dict[str, Any], row: dict[str, Any]) -> bool:
    if str(source.get("scope") or "").upper() != "LOCAL":
        return True
    evidence = _wsdot_filter_evidence(source, row)
    return bool(
        evidence["matched_route_tokens"]
        or evidence["matched_facility_keywords"]
        or evidence["matched_area_keywords"]
    )


def _wsdot_filter_evidence(source: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    route_allowlist = _configured_texts(
        source.get("route_keywords"),
        default=["I-5", "I-90", "SR 99", "SR 520", "SR 509", "SR 599"],
    )
    facility_keywords = _configured_texts(
        source.get("facility_keywords"),
        default=["West Seattle Bridge", "Aurora Bridge", "Lake Washington Bridge"],
    )
    area_keywords = _configured_texts(
        source.get("area_keywords"),
        default=["Seattle", "King County", "Downtown", "Ballard", "West Seattle"],
    )
    route_tokens = _wsdot_route_tokens(row)
    text = _wsdot_row_text(row)
    matched_routes = [
        route
        for route in route_allowlist
        if any(
            route.lower().replace(" ", "") == token.lower().replace(" ", "")
            for token in route_tokens
        )
    ]
    return {
        "route_keywords": route_allowlist,
        "facility_keywords": facility_keywords,
        "area_keywords": area_keywords,
        "matched_route_tokens": matched_routes,
        "matched_facility_keywords": _matched_keywords(text, facility_keywords),
        "matched_area_keywords": _matched_keywords(text, area_keywords),
    }


def _wsdot_route_tokens(row: dict[str, Any]) -> list[str]:
    values: list[Any] = [
        _first_value(row, "route", "Route", "road_name", "RoadName", "roadway", "Roadway"),
    ]
    affected = _first_value(row, "affected_routes", "AffectedRoutes", "routes", "Routes")
    if isinstance(affected, list):
        values.extend(affected)
    else:
        values.append(affected)
    values.append(_wsdot_row_text(row))
    tokens: list[str] = []
    for value in values:
        text = str(value or "")
        for match in _WSDOT_ROUTE_RE.findall(text):
            token = " ".join(match.upper().replace("SR", "SR ").replace("US", "US ").split())
            token = token.replace("I ", "I-")
            if token not in tokens:
                tokens.append(token)
    return tokens


def _wsdot_facility_tokens(source: dict[str, Any], row: dict[str, Any]) -> list[str]:
    facility_keywords = _configured_texts(
        source.get("facility_keywords"),
        default=["West Seattle Bridge", "Aurora Bridge", "Lake Washington Bridge"],
    )
    return _matched_keywords(_wsdot_row_text(row), facility_keywords)


def _wsdot_impact(row: dict[str, Any]) -> dict[str, Any]:
    text = _wsdot_row_text(row).lower()
    if any(word in text for word in ("closed", "closure", "blocked all lanes")):
        return {"label": "closure", "weight": 32}
    if any(word in text for word in ("blocked", "lane closed", "lane closure")):
        return {"label": "lane_blocked", "weight": 22}
    if any(word in text for word in ("delay", "delayed", "backup")):
        return {"label": "delay", "weight": 14}
    if any(word in text for word in ("construction", "maintenance", "roadwork")):
        return {"label": "roadwork", "weight": 8}
    return {"label": "traveler_alert", "weight": 4}


def _wsdot_source_url(source: dict[str, Any], row_key: str, row: dict[str, Any]) -> str:
    explicit = _first_value(row, "url", "Url", "link", "Link")
    if explicit:
        return normalize_url(explicit)
    base_url = str(source.get("homepage_url") or source.get("url") or "").strip()
    if not base_url:
        base_url = "https://wsdot.wa.gov/traffic/api/"
    separator = "&" if "?" in base_url else "?"
    return normalize_url(f"{base_url}{separator}alert_id={quote(str(row_key))}")


def _wsdot_row_text(row: dict[str, Any]) -> str:
    values = [
        row.get(key)
        for key in (
            "headline",
            "Headline",
            "title",
            "Title",
            "description",
            "Description",
            "extended_description",
            "ExtendedDescription",
            "road_name",
            "RoadName",
            "county",
            "County",
            "region",
            "Region",
        )
    ]
    return " ".join(str(value) for value in values if value)


def _parse_city_light_outages_json(
    source: dict[str, Any],
    payload_text: str,
) -> list[dict[str, Any]]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed City Light outage JSON fixture: {exc}") from exc
    if isinstance(payload, dict):
        rows = payload.get("outages") or payload.get("items") or payload.get("data")
    else:
        rows = payload
    if not isinstance(rows, list):
        raise NewsParserError("City Light outage fixture must be a list or object with outages.")

    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"City Light outage row {index} must be an object.")
        if not _city_light_outage_matches_scope(source, row):
            continue
        normalized.append(_normalize_city_light_outage(source, row, index=index))
    return normalized


def _normalize_city_light_outage(
    source: dict[str, Any],
    row: dict[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    outage_id = bounded_text(
        _first_value(row, "outage_id", "outageId", "id", "event_id", "eventId"),
        max_chars=120,
    )
    area = bounded_text(
        _first_value(row, "area", "neighborhood", "location", "impacted_area", "city"),
        max_chars=160,
    )
    status = (
        bounded_text(
            _first_value(row, "status", "outage_status", "state"),
            max_chars=80,
        )
        or "reported"
    )
    customers_affected = _int_value(
        _first_value(
            row,
            "customers_affected",
            "customersAffected",
            "customer_count",
            "affected_customers",
        )
    )
    started_at = normalize_timestamp(
        _first_value(row, "started_at", "start_time", "reported_at", "outage_start")
    )
    updated_at = normalize_timestamp(
        _first_value(row, "updated_at", "last_updated", "lastUpdated", "observed_at")
    )
    observed_at = started_at or updated_at
    if not area or not observed_at:
        raise NewsParserError(
            f"City Light outage row {index} is missing area or observed timestamp."
        )

    cause = bounded_text(_first_value(row, "cause", "estimated_cause"), max_chars=160)
    crew_status = bounded_text(
        _first_value(row, "crew_status", "crewStatus", "crew"),
        max_chars=160,
    )
    estimated_restoration_at = normalize_timestamp(
        _first_value(
            row,
            "estimated_restoration_at",
            "estimatedRestorationAt",
            "estimated_restore_time",
            "etor",
        )
    )
    source_url = _city_light_source_url(source, outage_id or str(index), row)
    filter_evidence = _city_light_filter_evidence(source, row)
    impact = _city_light_impact(
        status=status,
        customers_affected=customers_affected,
        row=row,
        matched_area_count=len(filter_evidence["matched_area_keywords"]),
    )
    customer_text = (
        f" affecting {customers_affected} customer(s)" if customers_affected is not None else ""
    )
    description_parts = [
        f"Seattle City Light reports a {status.lower()} outage{customer_text} in {area}.",
    ]
    if estimated_restoration_at:
        description_parts.append(f"Estimated restoration: {estimated_restoration_at}.")
    if cause:
        description_parts.append(f"Cause: {cause}.")
    tags = _unique_texts(
        [
            "official",
            "utility",
            "city-light",
            "power-outage",
            impact["label"],
            area.lower().replace(" ", "-"),
        ],
        max_chars=64,
    )
    item = _normalize_item(
        source,
        {
            "title": f"City Light outage affecting {area}",
            "url": source_url,
            "canonical_url": source_url,
            "description": " ".join(description_parts),
            "published_at": observed_at,
            "tags": tags,
        },
        index=index,
    )
    item["evidence"]["city_light_outage"] = {
        "outage_id": outage_id,
        "area": area,
        "status": status,
        "customers_affected": customers_affected,
        "started_at": started_at,
        "updated_at": updated_at,
        "estimated_restoration_at": estimated_restoration_at,
        "cause": cause,
        "crew_status": crew_status,
        "source_url": source_url,
        "filter": filter_evidence,
        "ranking": {
            "impact_label": impact["label"],
            "customer_impact_weight": impact["customer_weight"],
            "status_weight": impact["status_weight"],
            "area_match_weight": impact["area_match_weight"],
            "utility_impact_score": impact["utility_impact_score"],
        },
    }
    return item


def _city_light_outage_matches_scope(source: dict[str, Any], row: dict[str, Any]) -> bool:
    if str(source.get("scope") or "").upper() != "LOCAL":
        return True
    evidence = _city_light_filter_evidence(source, row)
    return bool(evidence["matched_area_keywords"])


def _city_light_filter_evidence(source: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    area_keywords = _configured_texts(
        source.get("area_keywords"),
        default=[
            "Seattle",
            "Capitol Hill",
            "Downtown",
            "First Hill",
            "University District",
            "Ballard",
            "West Seattle",
            "Rainier Valley",
            "Beacon Hill",
            "Queen Anne",
        ],
    )
    values = [
        _first_value(row, "area", "neighborhood", "location", "impacted_area", "city"),
        _first_value(row, "description", "summary", "cause"),
    ]
    text = " ".join(str(value) for value in values if value)
    return {
        "area_keywords": area_keywords,
        "matched_area_keywords": _matched_keywords(text, area_keywords),
    }


def _city_light_impact(
    *,
    status: str,
    customers_affected: int | None,
    row: dict[str, Any],
    matched_area_count: int,
) -> dict[str, Any]:
    text = " ".join(
        str(value)
        for value in (
            status,
            _first_value(row, "description", "summary", "cause", "crew_status", "crewStatus"),
        )
        if value
    ).lower()
    if customers_affected is None:
        customer_weight = 0
    elif customers_affected >= 10000:
        customer_weight = 40
    elif customers_affected >= 5000:
        customer_weight = 32
    elif customers_affected >= 1000:
        customer_weight = 24
    elif customers_affected >= 100:
        customer_weight = 12
    elif customers_affected > 0:
        customer_weight = 6
    else:
        customer_weight = 0

    if any(word in text for word in ("downed", "wire", "emergency")):
        status_weight = 20
    elif any(word in text for word in ("investigating", "repair", "dispatched", "active")):
        status_weight = 12
    elif any(word in text for word in ("planned", "scheduled")):
        status_weight = 4
    elif any(word in text for word in ("restored", "resolved")):
        status_weight = -8
    else:
        status_weight = 6

    area_match_weight = min(9, matched_area_count * 3)
    score = max(0, min(55, customer_weight + status_weight + area_match_weight))
    if customers_affected is not None and customers_affected >= 1000:
        label = "major_outage"
    elif score > 0:
        label = "active_outage"
    else:
        label = "outage_status"
    return {
        "label": label,
        "customer_weight": customer_weight,
        "status_weight": status_weight,
        "area_match_weight": area_match_weight,
        "utility_impact_score": score,
    }


def _city_light_source_url(source: dict[str, Any], row_key: str, row: dict[str, Any]) -> str:
    explicit = _first_value(row, "url", "source_url", "link")
    if explicit:
        return normalize_url(explicit)
    base_url = str(source.get("homepage_url") or source.get("url") or "").strip()
    if not base_url or base_url.startswith("file://"):
        base_url = "https://www.seattle.gov/city-light/outages"
    separator = "&" if "?" in base_url else "?"
    return normalize_url(f"{base_url}{separator}outage_id={quote(str(row_key))}")


def _parse_faa_airport_status_json(
    source: dict[str, Any],
    payload_text: str,
) -> list[dict[str, Any]]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed FAA airport status JSON fixture: {exc}") from exc
    rows = _faa_airport_rows(payload)
    if rows is None:
        raise NewsParserError(
            "FAA airport status fixture must be an object or list of airport rows."
        )

    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"FAA airport status row {index} must be an object.")
        if not _faa_airport_matches_scope(source, row):
            continue
        normalized.append(_normalize_faa_airport_status(source, row, index=index))
    return normalized


def _faa_airport_rows(payload: Any) -> list[dict[str, Any]] | None:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return None
    for key in ("airports", "airport_statuses", "items", "data"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return rows
    events = payload.get("events")
    if isinstance(events, list):
        airport = payload.get("airport") if isinstance(payload.get("airport"), dict) else {}
        return [{**airport, **event} for event in events if isinstance(event, dict)]
    return [payload]


def _normalize_faa_airport_status(
    source: dict[str, Any],
    row: dict[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    airport_code = _faa_airport_code(row)
    airport_name = bounded_text(
        _first_value(row, "airport_name", "airportName", "name"),
        max_chars=160,
    )
    location = bounded_text(_first_value(row, "location", "city", "city_state"), max_chars=160)
    status = (
        bounded_text(
            _first_value(row, "status", "delay_type", "delayType", "event_type", "type"),
            max_chars=120,
        )
        or "On Time"
    )
    observed_at = normalize_timestamp(
        _first_value(
            row,
            "updated_at",
            "updateTimeUtc",
            "observed_at",
            "published_at",
            "start_time",
            "startTime",
        )
    )
    if not airport_code or not observed_at:
        raise NewsParserError(
            f"FAA airport status row {index} is missing airport code or timestamp."
        )
    reason = bounded_text(_first_value(row, "reason", "description", "summary"), max_chars=240)
    average_delay = bounded_text(
        _first_value(row, "average_delay", "averageDelay", "avg_delay", "avgDelay"),
        max_chars=120,
    )
    max_delay = bounded_text(
        _first_value(row, "max_delay", "maxDelay"),
        max_chars=120,
    )
    start_time = normalize_timestamp(_first_value(row, "start_time", "startTime"))
    end_time = normalize_timestamp(_first_value(row, "end_time", "endTime", "closureReopen"))
    impact = _faa_airport_impact(
        status=status,
        reason=reason,
        delay_minutes=_faa_delay_minutes(row, average_delay=average_delay, max_delay=max_delay),
    )
    source_url = _faa_airport_source_url(source, airport_code, row)
    description_parts = [f"FAA reports {airport_code} airport status as {status}."]
    if average_delay:
        description_parts.append(f"Average delay: {average_delay}.")
    if max_delay:
        description_parts.append(f"Maximum delay: {max_delay}.")
    if reason:
        description_parts.append(f"Reason: {reason}.")
    tags = _unique_texts(
        [
            "official",
            "airport",
            "faa",
            airport_code.lower(),
            impact["label"],
        ],
        max_chars=64,
    )
    item = _normalize_item(
        source,
        {
            "title": f"FAA {airport_code} airport status: {status}",
            "url": source_url,
            "canonical_url": source_url,
            "description": " ".join(description_parts),
            "published_at": observed_at,
            "tags": tags,
        },
        index=index,
    )
    item["evidence"]["faa_airport_status"] = {
        "airport_code": airport_code,
        "airport_name": airport_name,
        "location": location,
        "status": status,
        "reason": reason,
        "average_delay": average_delay,
        "max_delay": max_delay,
        "start_time": start_time,
        "end_time": end_time,
        "observed_at": observed_at,
        "source_url": source_url,
        "weather": {
            "conditions": bounded_text(
                _first_value(row, "weather", "weather_conditions", "conditions"),
                max_chars=120,
            ),
            "temperature": bounded_text(
                _first_value(row, "temperature", "temperature_f", "temperatureF"),
                max_chars=80,
            ),
            "wind": bounded_text(_first_value(row, "wind", "wind_speed"), max_chars=120),
        },
        "ranking": {
            "impact_label": impact["label"],
            "event_weight": impact["event_weight"],
            "delay_minutes": impact["delay_minutes"],
            "delay_weight": impact["delay_weight"],
            "airport_impact_score": impact["airport_impact_score"],
        },
        "filter": _faa_airport_filter_evidence(source, row),
    }
    return item


def _faa_airport_matches_scope(source: dict[str, Any], row: dict[str, Any]) -> bool:
    if str(source.get("scope") or "").upper() != "LOCAL":
        return True
    evidence = _faa_airport_filter_evidence(source, row)
    return bool(evidence["matched_airport_codes"])


def _faa_airport_filter_evidence(source: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    airport_codes = [
        _normalize_airport_code(value)
        for value in _configured_texts(source.get("airport_codes"), default=["SEA"])
    ]
    airport_codes = [value for value in airport_codes if value]
    row_code = _faa_airport_code(row)
    return {
        "airport_codes": airport_codes,
        "matched_airport_codes": [
            airport_code for airport_code in airport_codes if row_code and airport_code == row_code
        ],
    }


def _faa_airport_code(row: dict[str, Any]) -> str | None:
    airport = row.get("airport")
    value = None
    if isinstance(airport, dict):
        value = _first_value(airport, "code", "iata", "faa", "airport_code", "airportCode")
    if value is None:
        value = _first_value(row, "airport_code", "airportCode", "code", "iata", "faa")
    return _normalize_airport_code(value)


def _normalize_airport_code(value: Any) -> str | None:
    text = bounded_text(value, max_chars=8)
    if not text:
        return None
    code = text.upper().strip()
    if len(code) == 4 and code.startswith("K"):
        code = code[1:]
    return code


def _faa_airport_impact(
    *,
    status: str,
    reason: str | None,
    delay_minutes: int,
) -> dict[str, Any]:
    text = f"{status} {reason or ''}".lower()
    if "closure" in text or "closed" in text:
        label = "airport_closure"
        event_weight = 45
    elif "ground stop" in text:
        label = "ground_stop"
        event_weight = 40
    elif "ground delay" in text:
        label = "ground_delay"
        event_weight = 34
    elif "arrival delay" in text or "departure delay" in text:
        label = "airport_delay"
        event_weight = 24
    elif "delay" in text:
        label = "airport_delay"
        event_weight = 18
    elif "on time" in text or "no delay" in text or "no delays" in text:
        label = "on_time"
        event_weight = 0
    else:
        label = "airport_status"
        event_weight = 8
    delay_weight = min(12, max(0, delay_minutes // 5))
    return {
        "label": label,
        "event_weight": event_weight,
        "delay_minutes": delay_minutes,
        "delay_weight": delay_weight,
        "airport_impact_score": min(55, event_weight + delay_weight),
    }


def _faa_delay_minutes(
    row: dict[str, Any],
    *,
    average_delay: str | None,
    max_delay: str | None,
) -> int:
    explicit = _int_value(
        _first_value(row, "delay_minutes", "delayMinutes", "average_delay_minutes")
    )
    if explicit is not None:
        return explicit
    for text in (average_delay, max_delay):
        parsed = _duration_minutes(text)
        if parsed is not None:
            return parsed
    return 0


def _duration_minutes(value: Any) -> int | None:
    if value in (None, ""):
        return None
    text = str(value).lower()
    hours = 0
    minutes = 0
    hour_match = re.search(r"(\d+)\s*(?:hour|hr)", text)
    minute_match = re.search(r"(\d+)\s*(?:minute|min)", text)
    if hour_match:
        hours = int(hour_match.group(1))
    if minute_match:
        minutes = int(minute_match.group(1))
    if hours or minutes:
        return hours * 60 + minutes
    first_number = re.search(r"\d+", text)
    return int(first_number.group(0)) if first_number else None


def _faa_airport_source_url(source: dict[str, Any], airport_code: str, row: dict[str, Any]) -> str:
    explicit = _first_value(row, "url", "source_url", "sourceUrl", "link")
    if explicit:
        return normalize_url(explicit)
    base_url = str(source.get("homepage_url") or source.get("url") or "").strip()
    if not base_url or base_url.startswith("file://"):
        base_url = f"https://www.faa.gov/airport-status/{airport_code}"
    return normalize_url(base_url)


def _parse_nws_alerts_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed NWS alert JSON fixture: {exc}") from exc
    if not isinstance(payload, dict):
        raise NewsParserError("NWS alert fixture must be a GeoJSON feature collection object.")
    features = payload.get("features")
    if not isinstance(features, list):
        raise NewsParserError("NWS alert fixture must contain a features list.")

    normalized: list[dict[str, Any]] = []
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            raise NewsParserError(f"NWS alert feature {index} must be an object.")
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise NewsParserError(f"NWS alert feature {index} is missing properties.")
        if not _nws_alert_matches_scope(source, properties):
            continue
        normalized.append(_normalize_nws_alert(source, feature, properties, index=index))
    return normalized


def _normalize_nws_alert(
    source: dict[str, Any],
    feature: dict[str, Any],
    properties: dict[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    event = bounded_text(properties.get("event"), max_chars=120) or "Weather alert"
    area_desc = bounded_text(properties.get("areaDesc"), max_chars=220)
    headline = bounded_text(properties.get("headline"), max_chars=MAX_TITLE_LENGTH)
    title = headline or (f"{event} for {area_desc}" if area_desc else event)
    url = (
        properties.get("@id") or properties.get("uri") or properties.get("id") or feature.get("id")
    )
    if not url:
        raise NewsParserError(f"NWS alert feature {index} is missing an alert URL.")
    description = bounded_text(
        properties.get("description")
        or properties.get("instruction")
        or properties.get("headline"),
        max_chars=MAX_DESCRIPTION_LENGTH,
    )
    published_at = normalize_timestamp(
        properties.get("effective") or properties.get("sent") or properties.get("onset")
    )
    severity = bounded_text(properties.get("severity"), max_chars=64)
    urgency = bounded_text(properties.get("urgency"), max_chars=64)
    certainty = bounded_text(properties.get("certainty"), max_chars=64)
    status = bounded_text(properties.get("status"), max_chars=64)
    affected_zones = _string_list(properties.get("affectedZones"), max_chars=240)
    geocode = properties.get("geocode") if isinstance(properties.get("geocode"), dict) else {}
    references = properties.get("references")
    reference_count = len(references) if isinstance(references, list) else 0
    ranking = _nws_alert_ranking_evidence(
        severity=severity,
        urgency=urgency,
        certainty=certainty,
        status=status,
    )
    tags = _unique_texts(
        [
            "official",
            "weather",
            "alert",
            "nws",
            event.lower(),
            severity.lower() if severity else None,
            urgency.lower() if urgency else None,
            certainty.lower() if certainty else None,
        ],
        max_chars=64,
    )
    item = _normalize_item(
        source,
        {
            "title": title,
            "url": url,
            "canonical_url": url,
            "description": description,
            "published_at": published_at,
            "tags": tags,
        },
        index=index,
    )
    item["evidence"]["nws_alert"] = {
        "id": properties.get("id") or feature.get("id"),
        "event": event,
        "severity": severity,
        "urgency": urgency,
        "certainty": certainty,
        "status": status,
        "message_type": properties.get("messageType"),
        "category": properties.get("category"),
        "area_desc": area_desc,
        "affected_zones": affected_zones,
        "sent": normalize_timestamp(properties.get("sent")),
        "effective": normalize_timestamp(properties.get("effective")),
        "onset": normalize_timestamp(properties.get("onset")),
        "expires": normalize_timestamp(properties.get("expires")),
        "ends": normalize_timestamp(properties.get("ends")),
        "sender_name": properties.get("senderName"),
        "geocode": geocode,
        "reference_count": reference_count,
        "ranking": ranking,
        "filter": _nws_filter_evidence(source, properties),
    }
    return item


def _nws_alert_matches_scope(source: dict[str, Any], properties: dict[str, Any]) -> bool:
    if str(source.get("scope") or "").upper() != "LOCAL":
        return True
    evidence = _nws_filter_evidence(source, properties)
    return bool(evidence["matched_keywords"] or evidence["matched_zone_ids"])


def _nws_filter_evidence(source: dict[str, Any], properties: dict[str, Any]) -> dict[str, Any]:
    area_keywords = _configured_texts(
        source.get("area_keywords"),
        default=["Seattle", "King County", "Puget Sound"],
    )
    zone_ids = _configured_texts(source.get("zone_ids"), default=[])
    area_desc = str(properties.get("areaDesc") or "")
    affected_zones = _string_list(properties.get("affectedZones"), max_chars=240)
    area_lower = area_desc.lower()
    matched_keywords = [keyword for keyword in area_keywords if keyword.lower() in area_lower]
    matched_zone_ids = [
        zone_id
        for zone_id in zone_ids
        if any(zone_id.lower() in zone.lower() for zone in affected_zones)
    ]
    return {
        "area_keywords": area_keywords,
        "zone_ids": zone_ids,
        "matched_keywords": matched_keywords,
        "matched_zone_ids": matched_zone_ids,
    }


def _nws_alert_ranking_evidence(
    *,
    severity: str | None,
    urgency: str | None,
    certainty: str | None,
    status: str | None,
) -> dict[str, Any]:
    severity_weight = {
        "extreme": 40,
        "severe": 30,
        "moderate": 18,
        "minor": 8,
        "unknown": 0,
    }.get(str(severity or "").lower(), 0)
    urgency_weight = {
        "immediate": 24,
        "expected": 16,
        "future": 8,
        "past": -8,
        "unknown": 0,
    }.get(str(urgency or "").lower(), 0)
    certainty_weight = {
        "observed": 16,
        "likely": 12,
        "possible": 5,
        "unlikely": -5,
        "unknown": 0,
    }.get(str(certainty or "").lower(), 0)
    active = str(status or "").lower() == "actual"
    return {
        "active_alert": active,
        "severity_weight": severity_weight,
        "urgency_weight": urgency_weight,
        "certainty_weight": certainty_weight,
        "total_alert_weight": severity_weight + urgency_weight + certainty_weight,
    }


def _configured_texts(value: Any, *, default: list[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        return list(default)
    return _unique_texts(values, max_chars=120)


def _string_list(value: Any, *, max_chars: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return _unique_texts(value, max_chars=max_chars)


def _unique_texts(values: list[Any], *, max_chars: int) -> list[str]:
    texts: list[str] = []
    for value in values:
        text = bounded_text(value, max_chars=max_chars)
        if text and text not in texts:
            texts.append(text)
    return texts


def _parse_xml_feed(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed XML fixture: {exc}") from exc

    tag = _local_name(root.tag)
    if tag == "rss":
        return _parse_rss_feed(source, root)
    if tag == "feed":
        return _parse_atom_feed(source, root)
    raise NewsParserError(f"Unsupported feed root: {tag}")


def _parse_alertseattle_rss_feed(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    items = _parse_xml_feed(source, payload_text)
    enriched: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        text = " ".join(
            value
            for value in (
                item.get("title"),
                item.get("description"),
                " ".join(item.get("tags") or []),
            )
            if value
        )
        event_type = _alertseattle_event_type(text)
        severity = _alertseattle_severity(text, event_type=event_type)
        tags = list(item.get("tags") or [])
        for tag in ["official", "alertseattle", "city-alert", event_type, severity["label"]]:
            if tag not in tags:
                tags.append(tag)
        evidence = dict(item.get("evidence") or {})
        evidence["parser"] = str(source.get("parser") or "alertseattle_rss")
        evidence["raw_index"] = index
        evidence["alertseattle"] = {
            "event_type": event_type,
            "severity": severity["label"],
            "severity_weight": severity["weight"],
            "official_city_alert": True,
            "source_url": item.get("url"),
            "published_at": item.get("source_published_at"),
            "ranking": {
                "official_alert_weight": 24,
                "severity_weight": severity["weight"],
                "city_alert_score": 24 + severity["weight"],
            },
        }
        item["tags"] = tags
        item["evidence"] = evidence
        enriched.append(item)
    return enriched


def _alertseattle_event_type(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("evacuation", "shelter", "emergency")):
        return "emergency"
    if any(word in lowered for word in ("power", "outage", "utility")):
        return "utility"
    if any(word in lowered for word in ("smoke", "air quality", "weather", "wind", "heat")):
        return "weather_hazard"
    if any(word in lowered for word in ("road", "bridge", "traffic", "closure")):
        return "transport"
    return "city_notice"


def _alertseattle_severity(text: str, *, event_type: str) -> dict[str, Any]:
    lowered = text.lower()
    if any(word in lowered for word in ("evacuation", "shelter in place", "emergency")):
        return {"label": "severe", "weight": 30}
    if event_type in {"utility", "weather_hazard", "transport"}:
        return {"label": "moderate", "weight": 18}
    if any(word in lowered for word in ("advisory", "notice", "update")):
        return {"label": "minor", "weight": 8}
    return {"label": "unknown", "weight": 0}


def _parse_metro_rss_feed(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    items = _parse_xml_feed(source, payload_text)
    enriched: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        text = " ".join(
            value
            for value in (
                item.get("title"),
                item.get("description"),
                " ".join(item.get("tags") or []),
            )
            if value
        )
        route_ids = _metro_route_ids(text)
        service_areas = _matched_keywords(
            text,
            _configured_texts(
                source.get("service_area_keywords"),
                default=[
                    "Seattle",
                    "Downtown",
                    "Capitol Hill",
                    "West Seattle",
                    "Ballard",
                    "University District",
                    "Rainier Valley",
                ],
            ),
        )
        impact = _metro_impact(text)
        ranking = {
            "route_count": len(route_ids),
            "service_area_count": len(service_areas),
            "impact_weight": impact["weight"],
            "transit_impact_score": min(40, len(route_ids) * 5 + len(service_areas) * 4)
            + impact["weight"],
        }
        tags = list(item.get("tags") or [])
        for tag in ["official", "transit", "metro", *[f"route-{route}" for route in route_ids]]:
            if tag not in tags:
                tags.append(tag)
        evidence = dict(item.get("evidence") or {})
        evidence["parser"] = str(source.get("parser") or "metro_rss")
        evidence["raw_index"] = index
        evidence["metro_advisory"] = {
            "route_ids": route_ids,
            "affected_service_areas": service_areas,
            "impact": impact["label"],
            "ranking": ranking,
            "source_url": item.get("url"),
            "advisory_title": item.get("title"),
        }
        item["tags"] = tags
        item["evidence"] = evidence
        enriched.append(item)
    return enriched


def _parse_local_blog_rss_feed(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    items = _parse_xml_feed(source, payload_text)
    neighborhood_keywords = _configured_texts(
        source.get("neighborhood_keywords"),
        default=["West Seattle", "Capitol Hill", "Ballard", "Downtown", "Rainier Valley"],
    )
    enriched: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        text = " ".join(
            value
            for value in (
                item.get("title"),
                item.get("description"),
                " ".join(item.get("tags") or []),
            )
            if value
        )
        neighborhoods = _matched_keywords(text, neighborhood_keywords)
        signal = _local_blog_signal(text)
        tags = list(item.get("tags") or [])
        for tag in [
            "local-news",
            "neighborhood-blog",
            signal["label"],
            *[value.lower().replace(" ", "-") for value in neighborhoods],
        ]:
            if tag not in tags:
                tags.append(tag)
        evidence = dict(item.get("evidence") or {})
        evidence["parser"] = str(source.get("parser") or "local_blog_rss")
        evidence["raw_index"] = index
        evidence["local_blog"] = {
            "publisher_family": source.get("source_family") or source.get("id"),
            "neighborhoods": neighborhoods,
            "signal_type": signal["label"],
            "signal_weight": signal["weight"],
            "source_url": item.get("url"),
            "published_at": item.get("source_published_at"),
            "storage": {
                "article_body_stored": False,
                "headline_metadata_only": True,
            },
            "ranking": {
                "neighborhood_count": len(neighborhoods),
                "signal_weight": signal["weight"],
                "local_blog_score": min(30, signal["weight"] + len(neighborhoods) * 4),
            },
        }
        item["tags"] = tags
        item["evidence"] = evidence
        enriched.append(item)
    return enriched


def _parse_spd_blotter_rss_feed(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    items = _parse_xml_feed(source, payload_text)
    enriched: list[dict[str, Any]] = []
    neighborhoods = _configured_texts(
        source.get("neighborhood_keywords"),
        default=[
            "West Seattle",
            "Capitol Hill",
            "Downtown",
            "Rainier Valley",
            "Ballard",
            "Beacon Hill",
            "University District",
        ],
    )
    for index, item in enumerate(items):
        text = " ".join(
            value
            for value in (
                item.get("title"),
                item.get("description"),
                " ".join(item.get("tags") or []),
            )
            if value
        )
        signal = _spd_blotter_signal(text)
        route_tokens = _local_route_tokens(text)
        matched_neighborhoods = _matched_keywords(text, neighborhoods)
        privacy = _spd_privacy_decision(
            text=text,
            preliminary_report=signal["preliminary"],
            public_impact=signal["public_impact"],
            neighborhoods=matched_neighborhoods,
            route_tokens=route_tokens,
        )
        incident_score = int(signal["score"])
        if privacy["exact_location_suppressed"]:
            incident_score = min(incident_score, 10)
        tags = list(item.get("tags") or [])
        for tag in [
            "official",
            "local-news",
            "spd",
            "safety-alert",
            signal["incident_type"],
        ]:
            if tag not in tags:
                tags.append(tag)
        if privacy["exact_location_suppressed"] and "privacy-redacted" not in tags:
            tags.append("privacy-redacted")
        evidence = dict(item.get("evidence") or {})
        evidence["parser"] = str(source.get("parser") or "spd_blotter_rss")
        evidence["raw_index"] = index
        evidence["spd_blotter"] = {
            "source_url": item.get("url"),
            "published_at": item.get("source_published_at"),
            "incident_type": signal["incident_type"],
            "incident_label": signal["incident_label"],
            "severity": signal["severity_label"],
            "preliminary_report": signal["preliminary"],
            "preliminary_signal": signal["preliminary_signal"],
            "neighborhoods": matched_neighborhoods,
            "route_tokens": route_tokens,
            "ranking": {
                "incident_score": incident_score,
                "severity_weight": signal["severity_weight"],
                "route_impact": len(route_tokens),
            },
            "privacy": {
                "low_acuity_private": privacy["low_acuity_private"],
                "exact_location_suppressed": privacy["exact_location_suppressed"],
                "public_impact_justified": privacy["public_impact_justified"],
                "redaction_reason": privacy["redaction_reason"],
                "display_location": privacy["display_location"],
                "location_basis": privacy["location_basis"],
                "overdose_related": privacy["overdose_related"],
                "privacy_category": privacy["privacy_category"],
            },
            "filter": {
                "neighborhood_keywords": neighborhoods,
                "matched_neighborhoods": matched_neighborhoods,
                "matched_route_tokens": route_tokens,
            },
        }
        evidence["privacy"] = {
            "exact_location_suppressed": privacy["exact_location_suppressed"],
            "redaction_applied": privacy["exact_location_suppressed"],
            "redaction_reason": privacy["redaction_reason"],
            "display_location": privacy["display_location"],
            "location_basis": privacy["location_basis"],
            "raw_address_stored": False,
            "low_acuity_private": privacy["low_acuity_private"],
            "public_impact_justified": privacy["public_impact_justified"],
            "overdose_related": privacy["overdose_related"],
            "privacy_category": privacy["privacy_category"],
        }
        item["tags"] = tags
        item["evidence"] = evidence
        enriched.append(item)
    return enriched


def _parse_sdot_blog_rss_feed(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    items = _parse_xml_feed(source, payload_text)
    enriched: list[dict[str, Any]] = []
    service_areas = _configured_texts(
        source.get("service_area_keywords"),
        default=[
            "Seattle",
            "Downtown",
            "Capitol Hill",
            "East Seattle",
            "West Seattle",
            "Ballard",
            "University District",
            "Seattle Center",
        ],
    )
    for index, item in enumerate(items):
        text = " ".join(
            value
            for value in (
                item.get("title"),
                item.get("description"),
                " ".join(item.get("tags") or []),
            )
            if value
        )
        signal = _sdot_blog_signal(text)
        route_tokens = _local_route_tokens(text)
        areas = _matched_keywords(text, service_areas)
        tags = list(item.get("tags") or [])
        for tag in [
            "official",
            "local-news",
            "sdot",
            signal["incident_type"],
            signal["impact_label"],
        ]:
            if tag not in tags:
                tags.append(tag)
        evidence = dict(item.get("evidence") or {})
        evidence["parser"] = str(source.get("parser") or "sdot_blog_rss")
        evidence["raw_index"] = index
        signal_score = int(signal["score"])
        service_area_count = len(areas)
        route_count = len(route_tokens)
        evidence["sdot_blog"] = {
            "source_url": item.get("url"),
            "published_at": item.get("source_published_at"),
            "incident_type": signal["incident_type"],
            "impact_label": signal["impact_label"],
            "impact_score": signal_score,
            "route_tokens": route_tokens,
            "service_areas": areas,
            "route_count": route_count,
            "service_area_count": service_area_count,
            "ranking": {
                "route_count": route_count,
                "area_count": service_area_count,
                "traffic_impact_score": signal_score + route_count + service_area_count,
            },
        }
        item["tags"] = tags
        item["evidence"] = evidence
        enriched.append(item)
    return enriched


def _parse_local_news_rss_feed(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    items = _parse_xml_feed(source, payload_text)
    enriched: list[dict[str, Any]] = []
    service_areas = _configured_texts(
        source.get("service_area_keywords"),
        default=[
            "Seattle",
            "Downtown",
            "Capitol Hill",
            "Ballard",
            "West Seattle",
            "University District",
            "Rainier Valley",
        ],
    )
    for index, item in enumerate(items):
        text = " ".join(
            value
            for value in (
                item.get("title"),
                item.get("description"),
                " ".join(item.get("tags") or []),
            )
            if value
        )
        signal = _local_news_signal(text)
        route_tokens = _local_route_tokens(text)
        matched_areas = _matched_keywords(text, service_areas)
        score = signal["score"] + len(route_tokens) * 3 + len(matched_areas) * 2
        traffic_related = bool(signal["traffic_related"])
        tags = list(item.get("tags") or [])
        for tag in [
            "local-news",
            "news",
            signal["news_type"],
            signal["impact_label"],
        ]:
            if tag not in tags:
                tags.append(tag)
        for route in route_tokens:
            route_tag = f"route-{route}"
            if route_tag not in tags:
                tags.append(route_tag)
            if route not in tags:
                tags.append(route)
        for area in matched_areas:
            normalized = str(area).lower().replace(" ", "-")
            if normalized not in tags:
                tags.append(normalized)
        evidence = dict(item.get("evidence") or {})
        evidence["parser"] = str(source.get("parser") or "local_news_rss")
        evidence["raw_index"] = index
        evidence["local_news"] = {
            "source_url": item.get("url"),
            "published_at": item.get("source_published_at"),
            "news_type": signal["news_type"],
            "impact_label": signal["impact_label"],
            "traffic_related": traffic_related,
            "route_tokens": route_tokens,
            "service_areas": matched_areas,
            "public_impact_score": score,
            "ranking": {
                "local_news_score": score,
                "route_count": len(route_tokens),
                "service_area_count": len(matched_areas),
            },
        }
        item["tags"] = tags
        item["evidence"] = evidence
        enriched.append(item)
    return enriched


def _spd_blotter_signal(text: str) -> dict[str, Any]:
    lowered = text.lower()
    preliminary = bool(_SPD_PRELIMINARY_RE.search(text))
    impact = bool(_SPD_IMPACT_RE.search(text))
    major = bool(_SPD_MAJOR_IMPACT_RE.search(text))
    if any(term in lowered for term in ("shooting", "homicide", "fatal")):
        incident_type = "law_enforcement_major_incident"
        label = "major incident"
        severity_label = "severe"
        severity_weight = 38 if major else 26
    elif "significant" in lowered and impact:
        incident_type = "law_enforcement_significant"
        label = "significant report"
        severity_label = "moderate"
        severity_weight = 28
    elif any(term in lowered for term in ("collision", "crash", "accident")):
        incident_type = "traffic_incident"
        label = "traffic incident"
        severity_label = "moderate"
        severity_weight = 22
    elif impact:
        incident_type = "incident_report"
        label = "incident report"
        severity_label = "notice"
        severity_weight = 12
    else:
        incident_type = "incident_report"
        label = "incident update"
        severity_label = "notice"
        severity_weight = 6
    public_impact = incident_type in {
        "law_enforcement_major_incident",
        "law_enforcement_significant",
        "traffic_incident",
    }
    score = max(
        5,
        severity_weight + (8 if preliminary else 0) + (12 if major else 0),
    )
    return {
        "incident_type": incident_type,
        "incident_label": label,
        "severity_label": severity_label,
        "severity_weight": severity_weight,
        "public_impact": public_impact,
        "preliminary": preliminary,
        "preliminary_signal": "preliminary" if preliminary else "official",
        "score": min(50, score),
    }


def _spd_privacy_decision(
    *,
    text: str,
    preliminary_report: bool,
    public_impact: bool,
    neighborhoods: list[str],
    route_tokens: list[str],
) -> dict[str, Any]:
    lowered = str(text).lower()
    low_acuity = bool(_SPD_LOW_ACUITY_RE.search(lowered))
    overdose_related = bool(_SPD_OVERDOSE_RE.search(lowered))
    suppress_exact = low_acuity and not public_impact
    if suppress_exact:
        reason = "Low-acuity or private SPD report without public-impact justification."
    elif low_acuity and public_impact:
        reason = "SPD item is low-acuity/private but elevated by public-impact evidence."
    else:
        reason = "Exact private location is not stored; privacy-safe tokens are used."
    if neighborhoods:
        display_location = neighborhoods[0]
        basis = "neighborhood"
    elif route_tokens:
        display_location = route_tokens[0]
        basis = "route_token"
    else:
        display_location = "Seattle"
        basis = "city"
    if suppress_exact:
        display_location = display_location if basis != "city" else "Seattle"
    return {
        "exact_location_suppressed": suppress_exact,
        "redaction_reason": reason,
        "display_location": display_location,
        "location_basis": basis,
        "low_acuity_private": low_acuity,
        "public_impact_justified": public_impact,
        "preliminary_report": preliminary_report,
        "overdose_related": overdose_related,
        "privacy_category": (
            "overdose" if overdose_related else "low_acuity" if low_acuity else "none"
        ),
        "raw_address_stored": False,
    }


def _sdot_blog_signal(text: str) -> dict[str, Any]:
    lowered = text.lower()
    traffic_related = bool(_SDOT_BLOG_IMPACT_RE.search(text))
    if any(term in lowered for term in ("collision", "crash", "pileup", "accident", "fatal")):
        incident_type = "traffic_collision"
        impact_label = "traffic_collision"
        score = 24
    elif any(term in lowered for term in ("closure", "closed", "detour", "shutdown", "outage")):
        incident_type = "transit_disruption"
        impact_label = "closure_or_detour"
        score = 30
    elif any(term in lowered for term in ("delay", "delayed", "slow")):
        incident_type = "service_disruption"
        impact_label = "delay"
        score = 18
    elif traffic_related:
        incident_type = "transit_update"
        impact_label = "transit_related"
        score = 14
    else:
        incident_type = "news_story"
        impact_label = "informational"
        score = 8
    return {
        "incident_type": incident_type,
        "impact_label": impact_label,
        "traffic_related": traffic_related,
        "score": score,
    }


def _local_news_signal(text: str) -> dict[str, Any]:
    lowered = text.lower()
    if any(
        term in lowered
        for term in (
            "road",
            "traffic",
            "transit",
            "bridge",
            "highway",
            "flood",
            "closure",
            "lane",
        )
    ):
        impact_label = "transit_or_infrastructure"
        score = 12
        traffic_related = True
    elif any(
        term in lowered
        for term in ("accident", "crash", "collision", "evacuation", "incident", "fire")
    ):
        impact_label = "public_safety"
        score = 10
        traffic_related = False
    else:
        impact_label = "general_news"
        score = 4
        traffic_related = False
    return {
        "news_type": "local_news",
        "impact_label": impact_label,
        "traffic_related": traffic_related,
        "score": score,
    }


def _local_route_tokens(value: str) -> list[str]:
    text = str(value or "")
    route_tokens: list[str] = []
    for match in _WSDOT_ROUTE_RE.findall(text):
        token = " ".join(str(match).upper().replace("SR", "SR ").replace("US", "US ").split())
        token = token.replace("I ", "I-")
        if token and token not in route_tokens:
            route_tokens.append(token)
    for match in _METRO_ROUTE_TOKEN_RE.findall(text):
        token = str(match).upper().strip()
        if token and token not in route_tokens:
            route_tokens.append(token)
    return route_tokens


def _local_blog_signal(text: str) -> dict[str, Any]:
    lowered = text.lower()
    if any(word in lowered for word in ("closed", "closure", "blocked", "collision")):
        return {"label": "disruption", "weight": 18}
    if any(word in lowered for word in ("power outage", "outage", "fire", "police")):
        return {"label": "incident", "weight": 16}
    if any(word in lowered for word in ("meeting", "council", "open house")):
        return {"label": "civic", "weight": 8}
    return {"label": "local_context", "weight": 4}


def _metro_route_ids(text: str) -> list[str]:
    routes: list[str] = []
    for match in _METRO_ROUTES_RE.finditer(text):
        route_text = match.group(1)
        for token in _METRO_ROUTE_TOKEN_RE.findall(route_text):
            if token not in routes:
                routes.append(token)
    for token in _METRO_ROUTE_RE.findall(text):
        if token not in routes:
            routes.append(token)
    return routes


def _metro_impact(text: str) -> dict[str, Any]:
    lowered = text.lower()
    if any(word in lowered for word in ("canceled", "cancelled", "suspended")):
        return {"label": "cancellation", "weight": 24}
    if any(word in lowered for word in ("reroute", "rerouted", "detour")):
        return {"label": "reroute", "weight": 18}
    if any(word in lowered for word in ("delay", "delayed", "late")):
        return {"label": "delay", "weight": 12}
    if any(word in lowered for word in ("stop closure", "stop closed", "closed stop")):
        return {"label": "stop_closure", "weight": 10}
    return {"label": "advisory", "weight": 4}


def _matched_keywords(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    return [keyword for keyword in keywords if keyword.lower() in lowered]


def _parse_rss_feed(source: dict[str, Any], root: ET.Element) -> list[dict[str, Any]]:
    channel = root.find("./channel")
    if channel is None:
        raise NewsParserError("RSS fixture is missing a channel element.")
    items: list[dict[str, Any]] = []
    for index, element in enumerate(channel.findall("./item")):
        tags = [
            text for text in (_element_text(node) for node in element.findall("./category")) if text
        ]
        items.append(
            _normalize_item(
                source,
                {
                    "title": _element_text(element.find("./title")),
                    "url": _element_text(element.find("./link")),
                    "description": _element_text(element.find("./description")),
                    "published_at": _element_text(element.find("./pubDate")),
                    "tags": tags,
                },
                index=index,
            )
        )
    return items


def _parse_atom_feed(source: dict[str, Any], root: ET.Element) -> list[dict[str, Any]]:
    namespace = ""
    if root.tag.startswith("{") and "}" in root.tag:
        namespace = root.tag.split("}", 1)[0] + "}"
    items: list[dict[str, Any]] = []
    for index, element in enumerate(root.findall(f"./{namespace}entry")):
        url = ""
        for link in element.findall(f"./{namespace}link"):
            href = (link.attrib.get("href") or "").strip()
            rel = (link.attrib.get("rel") or "alternate").strip()
            if href and rel == "alternate":
                url = href
                break
            if href and not url:
                url = href
        tags = [
            link.attrib.get("term", "").strip()
            for link in element.findall(f"./{namespace}category")
        ]
        items.append(
            _normalize_item(
                source,
                {
                    "title": _element_text(element.find(f"./{namespace}title")),
                    "url": url,
                    "description": _element_text(element.find(f"./{namespace}summary"))
                    or _element_text(element.find(f"./{namespace}content")),
                    "published_at": _element_text(element.find(f"./{namespace}published"))
                    or _element_text(element.find(f"./{namespace}updated")),
                    "tags": [tag for tag in tags if tag],
                },
                index=index,
            )
        )
    return items


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    children: list[_Node] = field(default_factory=list)
    text_parts: list[str] = field(default_factory=list)

    def text_content(self) -> str:
        parts = [part.strip() for part in self.text_parts if part.strip()]
        for child in self.children:
            text = child.text_content()
            if text:
                parts.append(text)
        return " ".join(parts).strip()


class _DOMBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("document", {})
        self._stack: list[_Node] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag.lower(), {key.lower(): value or "" for key, value in attrs})
        self._stack[-1].children.append(node)
        self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        if len(self._stack) > 1:
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if data:
            self._stack[-1].text_parts.append(data)


def _parse_homepage_items(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    selectors = source.get("selectors") or {}
    item_selector = str(selectors.get("item") or "").strip()
    title_selector = str(selectors.get("title") or "").strip()
    url_selector = str(selectors.get("url") or "").strip()
    description_selector = str(selectors.get("description") or "").strip()
    if not all((item_selector, title_selector, url_selector)):
        raise NewsParserError("Homepage fixtures require item, title, and url selectors.")

    builder = _DOMBuilder()
    builder.feed(payload_text)
    base_url = str(source.get("homepage_url") or source.get("url") or "")

    items: list[dict[str, Any]] = []
    for index, node in enumerate(_find_matching_nodes(builder.root, item_selector)):
        title_node = _first_matching_descendant(node, title_selector)
        url_node = _first_matching_descendant(node, url_selector)
        description_node = (
            _first_matching_descendant(node, description_selector) if description_selector else None
        )
        href = ""
        if url_node is not None:
            href = (url_node.attrs.get("href") or "").strip()
        items.append(
            _normalize_item(
                source,
                {
                    "title": title_node.text_content() if title_node else None,
                    "url": urljoin(base_url, href),
                    "description": description_node.text_content() if description_node else None,
                },
                index=index,
            )
        )
    return items


def _element_text(element: ET.Element | None) -> str | None:
    if element is None:
        return None
    if element.text is None:
        return None
    text = " ".join(element.text.split()).strip()
    return text or None


def _local_name(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _find_matching_nodes(root: _Node, selector_text: str) -> list[_Node]:
    selectors = [_parse_simple_selector(part) for part in selector_text.split(",") if part.strip()]
    matches: list[_Node] = []

    def visit(node: _Node) -> None:
        if any(_matches_selector(node, selector) for selector in selectors):
            matches.append(node)
        for child in node.children:
            visit(child)

    for child in root.children:
        visit(child)
    return matches


def _first_matching_descendant(root: _Node, selector_text: str) -> _Node | None:
    matches = _find_matching_nodes(root, selector_text)
    return matches[0] if matches else None


def _parse_simple_selector(text: str) -> dict[str, str | None]:
    text = text.strip()
    selector = {"tag": None, "id": None, "class": None}
    if not text:
        return selector

    tag = text
    if "#" in tag:
        tag, selector_id = tag.split("#", 1)
        selector["id"] = selector_id.strip() or None
    if "." in tag:
        tag, selector_class = tag.split(".", 1)
        selector["class"] = selector_class.strip() or None
    tag = tag.strip()
    selector["tag"] = tag.lower() or None
    return selector


def _matches_selector(node: _Node, selector: dict[str, str | None]) -> bool:
    tag = selector["tag"]
    selector_id = selector["id"]
    selector_class = selector["class"]
    if tag and node.tag != tag:
        return False
    if selector_id and (node.attrs.get("id") or "").strip() != selector_id:
        return False
    if selector_class:
        classes = {part for part in (node.attrs.get("class") or "").split() if part}
        if selector_class not in classes:
            return False
    return True
