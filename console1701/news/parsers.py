from __future__ import annotations

import json
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urljoin, urlsplit

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


class ArchiveFirehoseBlockedError(NewsParserError):
    """Raised when a science archive request or response exceeds its narrow contract."""


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
_NWS_US_ZONE_RE = re.compile(r"\b([A-Z]{2})[ZC]\d{3}\b")
_NATIONAL_USGS_REGIONS = (
    ("contiguous_us", -125.0, -66.0, 24.0, 50.0),
    ("alaska", -180.0, -129.0, 50.0, 72.0),
    ("aleutians", 170.0, 180.0, 50.0, 55.0),
    ("hawaii", -161.5, -154.0, 18.0, 23.0),
    ("puerto_rico_usvi", -68.5, -64.0, 17.0, 19.0),
    ("guam_nmi", 143.0, 147.0, 13.0, 21.0),
    ("american_samoa", -172.0, -168.0, -15.0, -10.0),
)
_FOREIGN_USGS_PLACE_SUFFIX = re.compile(
    r",\s*(?:Canada|Mexico|Cuba|The Bahamas|Bahamas|Guatemala|Belize|Honduras|"
    r"Haiti|Dominican Republic|Jamaica)\s*$", re.I
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

    if parser_name == "swpc_alerts_json":
        from console1701.news.orbital_parsers import parse_swpc_alerts_json

        return parse_swpc_alerts_json(source, payload_text)
    if parser_name == "swpc_noaa_scales_json":
        from console1701.news.orbital_parsers import parse_swpc_noaa_scales_json

        return parse_swpc_noaa_scales_json(source, payload_text)
    if parser_name == "swpc_kp_json":
        from console1701.news.orbital_parsers import parse_swpc_kp_json

        return parse_swpc_kp_json(source, payload_text)
    if parser_name == "swpc_aurora_json":
        from console1701.news.orbital_parsers import parse_swpc_aurora_json

        return parse_swpc_aurora_json(source, payload_text)
    if parser_name == "jpl_cad_json":
        from console1701.news.cneos_parsers import parse_jpl_cad_json

        return parse_jpl_cad_json(source, payload_text)
    if parser_name == "jpl_fireball_json":
        from console1701.news.cneos_parsers import parse_jpl_fireball_json

        return parse_jpl_fireball_json(source, payload_text)
    if parser_name == "nasa_orbital_rss":
        from console1701.news.orbital_rss import parse_nasa_orbital_rss

        return parse_nasa_orbital_rss(source, payload_text)
    if parser_name == "esa_orbital_rss":
        from console1701.news.orbital_rss import parse_esa_orbital_rss

        return parse_esa_orbital_rss(source, payload_text)
    if parser_name == "nasa_jpl_science_rss":
        from console1701.news.science_rss import parse_nasa_jpl_science_rss

        return parse_nasa_jpl_science_rss(source, payload_text)
    if parser_name == "nasa_science_news_fixture":
        from console1701.news.science_rss import parse_nasa_science_news_fixture

        return parse_nasa_science_news_fixture(source, payload_text)
    if parser_name == "atel_rss":
        from console1701.news.science_atel import parse_atel_rss

        return parse_atel_rss(source, payload_text)
    if parser_name == "esa_science_rss":
        from console1701.news.science_rss import parse_esa_science_rss

        return parse_esa_science_rss(source, payload_text)
    if parser_name == "esa_telescope_science_rss":
        from console1701.news.science_rss import parse_esa_telescope_science_rss

        return parse_esa_telescope_science_rss(source, payload_text)
    if parser_name == "exoplanet_ps_json":
        from console1701.news.science_exoplanets import parse_exoplanet_ps_json

        return parse_exoplanet_ps_json(source, payload_text)
    if parser_name == "mast_caom_tiny_json":
        from console1701.news.science_mast import parse_mast_caom_tiny_json

        return parse_mast_caom_tiny_json(source, payload_text)
    if parser_name == "pds_collection_metadata":
        from console1701.news.science_pds import parse_pds_collection_metadata

        return parse_pds_collection_metadata(source, payload_text)
    if parser_name == "gcn_notice_fixture":
        from console1701.news.science_gcn import parse_gcn_notice_fixture

        return parse_gcn_notice_fixture(source, payload_text)
    if parser_name == "gcn_circular_fixture":
        from console1701.news.science_circular import parse_gcn_circular_fixture

        return parse_gcn_circular_fixture(source, payload_text)
    if parser_name == "gracedb_public_alert_fixture":
        from console1701.news.science_gracedb import parse_gracedb_public_alert_fixture

        return parse_gracedb_public_alert_fixture(source, payload_text)
    if parser_name == "cpsc_recalls_json":
        from console1701.news.cpsc_recalls import parse_cpsc_recalls_json

        return parse_cpsc_recalls_json(source, payload_text)
    if parser_name == "cisa_advisories_rss":
        from console1701.news.cisa_advisories import parse_cisa_advisories_rss

        return parse_cisa_advisories_rss(source, payload_text)
    if parser_name == "swpc_xray_flares_json":
        from console1701.news.orbital_flares import parse_swpc_xray_flares_json

        return parse_swpc_xray_flares_json(source, payload_text)

    if parser_name == "nws_alerts_json":
        return _parse_nws_alerts_json(source, payload_text)
    if parser_name == "usgs_earthquake_geojson":
        return _parse_usgs_earthquake_geojson(source, payload_text)
    if parser_name == "usgs_water_latest_fixture":
        from console1701.news.regional_water import parse_usgs_water_latest_fixture

        return parse_usgs_water_latest_fixture(source, payload_text)
    if parser_name == "wsf_alerts_fixture":
        from console1701.news.regional_wsf import parse_wsf_alerts_fixture

        return parse_wsf_alerts_fixture(source, payload_text)
    if parser_name == "nwcc_atom_fixture":
        from console1701.news.regional_nwcc import parse_nwcc_atom_fixture

        return parse_nwcc_atom_fixture(source, payload_text)
    if parser_name == "ecology_aqi_fixture":
        from console1701.news.regional_aqi import parse_ecology_aqi_fixture

        return parse_ecology_aqi_fixture(source, payload_text)
    if parser_name == "gdacs_rss":
        return _parse_gdacs_rss(source, payload_text)
    if parser_name == "ecdc_rss":
        return _parse_ecdc_rss(source, payload_text)
    if parser_name == "nhc_basin_rss":
        return _parse_nhc_basin_rss(source, payload_text)
    if parser_name == "un_news_rss":
        return _parse_un_news_rss(source, payload_text)
    if parser_name == "gdacs_geojson":
        return _parse_gdacs_geojson(source, payload_text)
    if parser_name == "reliefweb_disasters_json":
        return _parse_reliefweb_disasters_json(source, payload_text)
    if parser_name == "reliefweb_reports_json":
        return _parse_reliefweb_reports_json(source, payload_text)
    if parser_name == "who_don_json":
        return _parse_who_don_json(source, payload_text)
    if parser_name == "wsdot_highway_alerts_rss":
        return _parse_wsdot_highway_alerts_rss(source, payload_text)
    if parser_name == "king_county_emergency_rss":
        return _parse_king_county_emergency_rss(source, payload_text)
    if parser_name == "pierce_road_rss_fixture":
        from console1701.news.regional_pierce import parse_pierce_road_rss_fixture

        return parse_pierce_road_rss_fixture(source, payload_text)
    if parser_name == "nhtsa_recalls_json":
        return _parse_nhtsa_recalls_json(source, payload_text)
    if parser_name == "cisa_kev_json":
        return _parse_cisa_kev_json(source, payload_text)
    if parser_name == "faa_nas_status_xml":
        return _parse_faa_nas_status_xml(source, payload_text)
    if parser_name == "federal_register_documents_json":
        return _parse_federal_register_documents_json(source, payload_text)
    if parser_name == "govinfo_collection_rss":
        return _parse_govinfo_collection_rss(source, payload_text)
    if parser_name == "fda_recalls_rss":
        return _parse_fda_recalls_rss(source, payload_text)
    if parser_name == "un_press_rss":
        return _parse_un_press_rss(source, payload_text)
    if parser_name == "iaea_rss":
        return _parse_iaea_rss(source, payload_text)
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


_GDACS_NS = "http://www.gdacs.org"
_GDACS_GEO_NS = "http://www.w3.org/2003/01/geo/wgs84_pos#"
_GDACS_ALERT_WEIGHTS = {"green": 8, "orange": 24, "red": 40}


def _gdacs_official_url(value: Any, *, index: int) -> str:
    url = normalize_url(value)
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in {"gdacs.org", "www.gdacs.org"}:
        raise NewsParserError(f"GDACS item {index} has no official HTTPS report URL.")
    return url


def _gdacs_number(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _gdacs_point(latitude: Any, longitude: Any) -> list[float] | None:
    lat, lon = _gdacs_number(latitude), _gdacs_number(longitude)
    if lat is None or lon is None or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        return None
    return [lon, lat]


def _gdacs_bbox(value: Any) -> list[float] | None:
    if isinstance(value, str):
        parts = value.split()
        # RSS explicitly documents lon-min, lon-max, lat-min, lat-max.
        if len(parts) != 4:
            return None
        numbers = [_gdacs_number(part) for part in parts]
        if any(number is None for number in numbers):
            return None
        lon_min, lon_max, lat_min, lat_max = numbers
        value = [lon_min, lat_min, lon_max, lat_max]
    if not isinstance(value, list) or len(value) != 4:
        return None
    numbers = [_gdacs_number(part) for part in value]
    if any(number is None for number in numbers):
        return None
    west, south, east, north = numbers
    if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
        return None
    return [west, south, east, north]


def _gdacs_item(
    source: dict[str, Any], *, index: int, data: dict[str, Any]
) -> dict[str, Any]:
    if str(source.get("scope") or "").upper() != "GLOBAL":
        raise NewsParserError("GDACS parser requires GLOBAL scope.")
    event_type = bounded_text(data.get("event_type"), max_chars=12)
    event_id = bounded_text(data.get("event_id"), max_chars=32)
    alert_level = bounded_text(data.get("alert_level"), max_chars=16)
    alert_key = str(alert_level or "").lower()
    published_at = normalize_timestamp(data.get("published_at"))
    updated_at = normalize_timestamp(data.get("updated_at"))
    if not event_type or not event_id or alert_key not in _GDACS_ALERT_WEIGHTS:
        raise NewsParserError(f"GDACS item {index} is missing event identity or alert level.")
    if not published_at:
        raise NewsParserError(f"GDACS item {index} has no valid event time.")
    url = _gdacs_official_url(data.get("url"), index=index)
    name = bounded_text(data.get("name"), max_chars=MAX_TITLE_LENGTH)
    country = bounded_text(data.get("country"), max_chars=120)
    title = bounded_text(data.get("title"), max_chars=MAX_TITLE_LENGTH)
    title = title or name or f"{alert_level} {event_type} in {country or 'unknown region'}"
    item = _normalize_item(
        source,
        {
            "title": title,
            "url": url,
            "description": data.get("description"),
            "published_at": published_at,
            "tags": ["official", "gdacs", "global", "disaster", alert_key, event_type.lower()],
        },
        index=index,
    )
    item["evidence"]["gdacs"] = {
        "event_id": event_id,
        "episode_id": bounded_text(data.get("episode_id"), max_chars=32),
        "event_type": event_type,
        "event_name": name,
        "alert_level": alert_level,
        "alert_score": _gdacs_number(data.get("alert_score")),
        "severity": _gdacs_number(data.get("severity")),
        "severity_unit": bounded_text(data.get("severity_unit"), max_chars=32),
        "severity_text": bounded_text(data.get("severity_text"), max_chars=240),
        "country": country,
        "iso3": bounded_text(data.get("iso3"), max_chars=3),
        "affected_countries": _unique_texts(data.get("affected_countries") or [], max_chars=120),
        "coordinates": data.get("coordinates"),
        "bbox": data.get("bbox"),
        "raw_bbox": data.get("raw_bbox"),
        "geometry_type": bounded_text(data.get("geometry_type"), max_chars=32),
        "start_at": normalize_timestamp(data.get("start_at")),
        "updated_at": updated_at,
        "source_url": url,
        "source_format": data.get("source_format"),
        "source_health": {"source": "official_gdacs", "fixture_parser": True},
        "ranking": {
            "official_alert": True,
            "alert_level_weight": _GDACS_ALERT_WEIGHTS[alert_key],
            "basis": "GDACS alert level; independent impact scoring pending",
        },
    }
    return item


def _parse_ecdc_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "GLOBAL":
        raise NewsParserError("ECDC RSS parser requires GLOBAL scope.")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed ECDC RSS fixture: {exc}") from exc
    if _local_name(root.tag) != "rss":
        raise NewsParserError("ECDC fixture must have an rss root.")
    channel = root.find("./channel")
    if channel is None:
        raise NewsParserError("ECDC RSS fixture is missing a channel.")
    items: list[dict[str, Any]] = []
    for index, element in enumerate(channel.findall("./item")):
        url = _element_text(element.find("./link"))
        try:
            parts = urlsplit(url or "")
        except ValueError as exc:
            raise NewsParserError(f"ECDC item {index} has an invalid URL.") from exc
        if parts.scheme != "https" or parts.hostname not in {
            "www.ecdc.europa.eu", "ecdc.europa.eu"
        }:
            raise NewsParserError(f"ECDC item {index} has no official HTTPS article URL.")
        published = normalize_timestamp(_element_text(element.find("./pubDate")))
        if not published:
            raise NewsParserError(f"ECDC item {index} has no valid publication time.")
        categories = _unique_texts(
            [_element_text(node) for node in element.findall("./category")], max_chars=64
        )
        creator = _element_text(element.find("{http://purl.org/dc/elements/1.1/}creator"))
        guid = _element_text(element.find("./guid"))
        item = _normalize_item(
            source,
            {
                "title": _element_text(element.find("./title")),
                "url": url,
                "description": _wsdot_plain_text(_element_text(element.find("./description"))),
                "published_at": published,
                "tags": ["official", "ecdc", "public-health", "europe-context", "global",
                         *categories],
            },
            index=index,
        )
        item["evidence"]["ecdc_rss"] = {
            "categories": categories,
            "creator": bounded_text(creator, max_chars=120),
            "guid": bounded_text(guid, max_chars=500),
            "published_at": published,
            "source_url": item["url"],
            "source_region_scope": "Europe",
            "impact_geography_assessed": False,
            "summary_bounded": True,
            "ranking": {
                "official_public_health": True,
                "source_weight": "below_who_don_until_convergence_or_severity",
            },
        }
        items.append(item)
    return items


_NHC_BASINS = {
    "NHC Atlantic": "atlantic",
    "NHC Eastern North Pacific": "eastern_pacific",
    "CPHC Central North Pacific": "central_pacific",
}
_NHC_ATCF_RE = re.compile(r"\b(?:AL|EP|CP)\d{2}20\d{2}\b")
_NHC_ADVISORY_RE = re.compile(
    r"^(?P<storm_type>.+?) (?P<name>[A-Z][A-Za-z0-9-]+) "
    r"Public Advisory Number (?P<number>\d+[a-z]?)$"
)
_NHC_WATCH_RE = re.compile(
    r"\b(Hurricane|Tropical Storm) (Watch|Warning) is in effect\b", re.IGNORECASE
)


def _parse_nhc_basin_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "GLOBAL":
        raise NewsParserError("NHC basin RSS parser requires GLOBAL scope.")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed NHC basin RSS fixture: {exc}") from exc
    channel = root.find("./channel") if _local_name(root.tag) == "rss" else None
    basin = _NHC_BASINS.get(_element_text(channel.find("./title"))) if channel is not None else None
    if not basin:
        raise NewsParserError("NHC basin RSS fixture has an unknown channel/basin.")
    rows = channel.findall("./item")
    summaries: dict[str, dict[str, str | None]] = {}
    for row in rows:
        title = _element_text(row.find("./title")) or ""
        cyclone = row.find("{https://www.nhc.noaa.gov}Cyclone")
        if not title.startswith("Summary for ") or cyclone is None:
            continue
        url = _element_text(row.find("./link"))
        if not url:
            continue
        storm_id = _element_text(cyclone.find("{https://www.nhc.noaa.gov}atcf"))
        summaries[url] = {
            "storm_id": storm_id if storm_id and _NHC_ATCF_RE.fullmatch(storm_id) else None,
            "storm_name": _element_text(cyclone.find("{https://www.nhc.noaa.gov}name")),
            "storm_type": _element_text(cyclone.find("{https://www.nhc.noaa.gov}type")),
            "wallet": _element_text(cyclone.find("{https://www.nhc.noaa.gov}wallet")),
        }
    items: list[dict[str, Any]] = []
    advisory_urls: set[str] = set()
    for index, row in enumerate(rows):
        title = _element_text(row.find("./title")) or ""
        match = _NHC_ADVISORY_RE.fullmatch(title)
        if match is None:
            continue  # Outlooks, graphics, and inactive placeholders are not advisories.
        url = _element_text(row.find("./link"))
        try:
            parts = urlsplit(url or "")
        except ValueError as exc:
            raise NewsParserError(f"NHC advisory {index} has an invalid URL.") from exc
        if parts.scheme != "https" or parts.hostname != "www.nhc.noaa.gov":
            raise NewsParserError(f"NHC advisory {index} lacks an official HTTPS URL.")
        published = normalize_timestamp(_element_text(row.find("./pubDate")))
        if not published:
            raise NewsParserError(f"NHC advisory {index} lacks a valid publication time.")
        raw_description = _element_text(row.find("./description")) or ""
        summary = summaries.get(url or "") or {}
        storm_id = summary.get("storm_id") or (
            (_NHC_ATCF_RE.search(raw_description) or [None])[0]
        )
        if storm_id and not _NHC_ATCF_RE.fullmatch(storm_id):
            storm_id = None
        watch_terms = sorted({
            f"{kind.title()} {state.title()}"
            for kind, state in _NHC_WATCH_RE.findall(raw_description)
        })
        item = _normalize_item(source, {
            "title": title,
            "url": url,
            "description": _wsdot_plain_text(raw_description),
            "published_at": published,
            "tags": ["official", "nhc", "tropical-cyclone", basin],
        }, index=index)
        item["evidence"]["nhc_rss"] = {
            "basin": basin,
            "storm_id": storm_id,
            "storm_name": summary.get("storm_name") or match.group("name"),
            "storm_type": summary.get("storm_type") or match.group("storm_type"),
            "wallet": summary.get("wallet"),
            "advisory_type": "public_advisory",
            "advisory_number": match.group("number"),
            "watch_warning_terms": watch_terms,
            "watch_warning_geography_verified": False,
            "guid": bounded_text(_element_text(row.find("./guid")), max_chars=500),
            "published_at": published,
            "source_url": item["url"],
        }
        item["evidence"]["global_identity"] = {
            "basin": basin,
            "storm_id": storm_id,
        }
        advisory_urls.add(url or "")
        items.append(item)
    for index, row in enumerate(rows):
        title = _element_text(row.find("./title")) or ""
        url = _element_text(row.find("./link"))
        if not title.startswith("Summary for ") or not url or url in advisory_urls:
            continue
        summary = summaries.get(url)
        if not summary:
            continue
        try:
            parts = urlsplit(url)
        except ValueError as exc:
            raise NewsParserError(f"NHC summary {index} has an invalid URL.") from exc
        published = normalize_timestamp(_element_text(row.find("./pubDate")))
        if parts.scheme != "https" or parts.hostname != "www.nhc.noaa.gov" or not published:
            raise NewsParserError(f"NHC summary {index} lacks an official URL or time.")
        item = _normalize_item(source, {
            "title": title,
            "url": url,
            "description": _wsdot_plain_text(_element_text(row.find("./description"))),
            "published_at": published,
            "tags": ["official", "nhc", "tropical-cyclone", basin],
        }, index=index)
        item["evidence"]["nhc_rss"] = {
            **summary, "basin": basin, "advisory_type": "storm_summary",
            "advisory_number": None, "watch_warning_terms": [],
            "watch_warning_geography_verified": False,
            "guid": bounded_text(_element_text(row.find("./guid")), max_chars=500),
            "published_at": published, "source_url": item["url"],
        }
        item["evidence"]["global_identity"] = {
            "basin": basin, "storm_id": summary.get("storm_id"),
        }
        items.append(item)
    return items


_UN_NEWS_LOW_VALUE_PREFIXES = (
    "world news in brief:", "un news in brief:", "in pictures:",
    "photo story:", "interview:", "podcast:", "opening remarks:",
    "secretary-general's remarks:",
)
_UN_NEWS_LOW_VALUE_CATEGORIES = {
    "feature", "features", "podcast", "interview", "photo story",
}


def _parse_un_news_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "GLOBAL":
        raise NewsParserError("UN News RSS parser requires GLOBAL scope.")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed UN News RSS fixture: {exc}") from exc
    channel = root.find("./channel") if _local_name(root.tag) == "rss" else None
    if channel is None or not (_element_text(channel.find("./title")) or "").startswith(
        "UN News"
    ):
        raise NewsParserError("UN News fixture must have the official RSS channel.")
    items: list[dict[str, Any]] = []
    for index, element in enumerate(channel.findall("./item")):
        title = _element_text(element.find("./title")) or ""
        categories = _unique_texts(
            [_element_text(node) for node in element.findall("./category")], max_chars=64
        )
        if title.casefold().startswith(_UN_NEWS_LOW_VALUE_PREFIXES) or any(
            category.casefold() in _UN_NEWS_LOW_VALUE_CATEGORIES for category in categories
        ):
            continue
        feed_link = _element_text(element.find("./link"))
        guid = _element_text(element.find("./guid"))
        try:
            feed_parts = urlsplit(feed_link or "")
            story_parts = urlsplit(guid or "")
        except ValueError as exc:
            raise NewsParserError(f"UN News item {index} has an invalid URL.") from exc
        if (
            feed_parts.scheme != "https" or feed_parts.hostname != "news.un.org"
            or story_parts.scheme != "https" or story_parts.hostname != "news.un.org"
            or not story_parts.path.startswith("/en/story/")
        ):
            raise NewsParserError(f"UN News item {index} lacks an official story URL.")
        published = normalize_timestamp(_element_text(element.find("./pubDate")))
        if not published:
            raise NewsParserError(f"UN News item {index} lacks a valid publication time.")
        item = _normalize_item(source, {
            "title": title,
            "url": guid,
            "description": _wsdot_plain_text(_element_text(element.find("./description"))),
            "published_at": published,
            "tags": ["official", "un-news", "global", *categories],
        }, index=index)
        item["evidence"]["un_news_rss"] = {
            "categories": categories,
            "feed_link": bounded_text(feed_link, max_chars=500),
            "guid": bounded_text(guid, max_chars=500),
            "source_label": bounded_text(_element_text(element.find("./source")), max_chars=120),
            "published_at": published,
            "source_url": item["url"],
            "institution": "United Nations",
            "impact_geography_assessed": False,
            "ranking": {
                "official_institution_source": True,
                "impact_requires_other_evidence": True,
            },
        }
        item["evidence"]["global_identity"] = {"institution": "United Nations"}
        items.append(item)
    return items


_UN_PRESS_ACTION_TERMS = (
    "adopts", "adopted", "sanctions", "ceasefire", "emergency session",
    "humanitarian crisis", "peacekeeping mandate", "resolution",
)
_UN_PRESS_LOW_VALUE_RE = re.compile(
    r"\b(message for|remarks at|to hold|will hold|schedule of|briefing schedule)\b", re.I
)


def _parse_un_press_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "GLOBAL":
        raise NewsParserError("UN Press RSS parser requires GLOBAL scope.")
    crisis_terms = [
        value.casefold()
        for value in _configured_texts(source.get("active_crisis_terms"), default=[])
    ]
    if not crisis_terms:
        raise NewsParserError("UN Press RSS requires configured active_crisis_terms.")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", payload_text, re.I):
        raise NewsParserError("UN Press RSS must not contain DTD or entity declarations.")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed UN Press RSS: {exc}") from exc
    channel = root.find("channel") if root.tag == "rss" else None
    if channel is None or _element_text(channel.find("title")) != (
        "UN Meetings Coverage and Press Releases"
    ):
        raise NewsParserError("UN Press RSS has an unexpected channel.")
    items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for index, row in enumerate(channel.findall("item")[:100]):
        title = bounded_text(_wsdot_plain_text(_element_text(row.find("title"))), max_chars=280)
        url = str(_element_text(row.find("link")) or "").strip()
        guid = str(_element_text(row.find("guid")) or "").strip()
        parts = urlsplit(url)
        if (
            not title or url != guid or url in seen_urls
            or parts.scheme != "https" or parts.hostname != "press.un.org"
            or not parts.path.startswith("/en/")
        ):
            raise NewsParserError(f"UN Press RSS item {index} has invalid official identity.")
        seen_urls.add(url)
        published = normalize_timestamp(_element_text(row.find("pubDate")))
        if not published:
            raise NewsParserError(f"UN Press RSS item {index} lacks publication time.")
        title_folded = title.casefold()
        organ = (
            "security_council" if "security council" in title_folded else
            "general_assembly" if "general assembly" in title_folded else None
        )
        matched_crises = [term for term in crisis_terms if term in title_folded]
        matched_actions = [term for term in _UN_PRESS_ACTION_TERMS if term in title_folded]
        if (
            _UN_PRESS_LOW_VALUE_RE.search(title)
            or not (organ or "humanitarian" in title_folded or "peacekeeping" in title_folded)
            or not (matched_crises or matched_actions)
        ):
            continue
        description = bounded_text(
            _wsdot_plain_text(_element_text(row.find("description"))), max_chars=500
        )
        item = _normalize_item(source, {
            "title": title,
            "url": url,
            "description": description,
            "published_at": published,
            "tags": ["official", "un-press", "institution", "global"],
        }, index=index)
        item["evidence"]["un_press"] = {
            "organ": organ,
            "organ_basis": "title_only_unverified" if organ else "not_provided",
            "matched_crisis_terms": matched_crises[:10],
            "matched_action_terms": matched_actions[:10],
            "feed_creator": bounded_text(
                _element_text(row.find("{http://purl.org/dc/elements/1.1/}creator")),
                max_chars=100,
            ),
            "guid": guid,
            "source_url": url,
            "published_at": published,
            "decision_or_outcome_inferred": False,
            "body_stored": False,
        }
        item["evidence"]["global_identity"] = {"institution": "United Nations"}
        items.append(item)
    return items


_IAEA_URGENT_RE = re.compile(
    r"\b(?:nuclear|radiological|radiation)\s+(?:emergency|incident|accident|leak)\b"
    r"|\b(?:emergency|incident|accident|leak)\s+(?:at|involving)\s+[^.]{0,80}\bnuclear\b",
    re.I,
)
_IAEA_ROUTINE_RE = re.compile(
    r"\b(?:training|course|workshop|conference|forum|careers|scholarship|"
    r"invited|press arrangements|meeting schedule|how nuclear science|"
    r"technologies in space)\b", re.I
)
_IAEA_FEED_DATE_RE = re.compile(r"^(\d{2})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})$")


def _parse_iaea_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "GLOBAL":
        raise NewsParserError("IAEA RSS parser requires GLOBAL scope.")
    crisis_terms = [
        value.casefold()
        for value in _configured_texts(source.get("active_crisis_terms"), default=[])
    ]
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", payload_text, re.I):
        raise NewsParserError("IAEA RSS must not contain DTD or entity declarations.")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed IAEA RSS: {exc}") from exc
    channel = root.find("channel") if root.tag == "rss" else None
    if channel is None or _element_text(channel.find("title")) != "IAEA Top News":
        raise NewsParserError("IAEA RSS has an unexpected channel.")
    items: list[dict[str, Any]] = []
    seen_guids: set[str] = set()
    for index, row in enumerate(channel.findall("item")[:100]):
        title = bounded_text(_wsdot_plain_text(_element_text(row.find("title"))), max_chars=280)
        feed_url = str(_element_text(row.find("link")) or "").strip()
        guid = str(_element_text(row.find("guid")) or "").strip()
        parts = urlsplit(feed_url)
        if (
            not title or not guid.isdecimal() or guid in seen_guids
            or parts.scheme not in {"http", "https"} or parts.hostname != "www.iaea.org"
            or not (parts.path.startswith("/news/") or parts.path.startswith("/newscenter/"))
            or parts.username or parts.password or parts.port or parts.query or parts.fragment
        ):
            raise NewsParserError(f"IAEA RSS item {index} has invalid official identity.")
        seen_guids.add(guid)
        feed_date = bounded_text(_element_text(row.find("pubDate")), max_chars=40)
        match = _IAEA_FEED_DATE_RE.fullmatch(feed_date or "")
        if not match:
            raise NewsParserError(f"IAEA RSS item {index} has invalid publication date.")
        year, month, day, hour, minute = map(int, match.groups())
        try:
            # The feed has no timezone: store only the calendar day for recency.
            published = datetime(2000 + year, month, day, hour, minute).date().isoformat()
        except ValueError as exc:
            raise NewsParserError(f"IAEA RSS item {index} has invalid publication date.") from exc
        title_folded = title.casefold()
        matched_crises = [term for term in crisis_terms if term in title_folded]
        urgent = bool(_IAEA_URGENT_RE.search(title))
        situation_update = bool(re.search(
            r"\b(?:director general statement|update \d+)\b.*\bsituation in\b", title, re.I
        ))
        if _IAEA_ROUTINE_RE.search(title) or not (urgent or (situation_update and matched_crises)):
            continue
        url = normalize_url(feed_url.replace("http://", "https://", 1))
        categories = _unique_texts(
            [_element_text(node) for node in row.findall("category")], max_chars=64
        )
        item = _normalize_item(source, {
            "title": title,
            "url": url,
            "description": _wsdot_plain_text(_element_text(row.find("description"))),
            "published_at": published,
            "tags": ["official", "iaea", "nuclear-safety", "global", *categories],
        }, index=index)
        item["evidence"]["iaea"] = {
            "feed_url": feed_url,
            "guid": guid,
            "source_url": url,
            "feed_pub_date": feed_date,
            "publication_date": published,
            "publication_precision": "day; feed time has no timezone",
            "categories": categories,
            "matched_crisis_terms": matched_crises[:10],
            "urgent_title_phrase": urgent,
            "situation_update_title": situation_update,
            "severity_confirmed": False,
            "ranking": {
                "official_nuclear_safety_source": True,
                "urgent_title_signal": urgent,
                "active_crisis_context": bool(matched_crises),
                "impact_requires_other_evidence": True,
            },
            "body_stored": False,
        }
        item["evidence"]["global_identity"] = {"institution": "IAEA"}
        items.append(item)
    return items


def _parse_gdacs_rss(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed GDACS RSS fixture: {exc}") from exc
    if _local_name(root.tag) != "rss":
        raise NewsParserError("GDACS RSS fixture must have an rss root.")
    rows = root.findall("./channel/item")
    if not rows:
        raise NewsParserError("GDACS RSS fixture has no item rows.")
    items = []
    for index, row in enumerate(rows):
        def field(key: str, current_row: ET.Element = row) -> str | None:
            return current_row.findtext(f"{{{_GDACS_NS}}}{key}")
        severity = row.find(f"{{{_GDACS_NS}}}severity")
        geo = row.find(f"{{{_GDACS_GEO_NS}}}Point")
        items.append(_gdacs_item(source, index=index, data={
            "event_type": field("eventtype"),
            "event_id": field("eventid"),
            "episode_id": field("episodeid"),
            "alert_level": field("alertlevel"),
            "alert_score": field("alertscore"),
            "severity": severity.get("value") if severity is not None else None,
            "severity_unit": severity.get("unit") if severity is not None else None,
            "severity_text": severity.text if severity is not None else None,
            "country": field("country"),
            "iso3": field("iso3"),
            "coordinates": _gdacs_point(
                geo.findtext(f"{{{_GDACS_GEO_NS}}}lat") if geo is not None else None,
                geo.findtext(f"{{{_GDACS_GEO_NS}}}long") if geo is not None else None,
            ),
            "bbox": _gdacs_bbox(field("bbox")),
            "raw_bbox": bounded_text(field("bbox"), max_chars=160),
            "geometry_type": "Point" if geo is not None else None,
            "title": row.findtext("title"),
            "name": field("eventname"),
            "description": row.findtext("description"),
            "url": row.findtext("link"),
            "published_at": row.findtext("pubDate"),
            "start_at": field("fromdate"),
            "updated_at": field("datemodified"),
            "source_format": "rss",
        }))
    return items


def _parse_gdacs_geojson(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed GDACS GeoJSON fixture: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise NewsParserError("GDACS API fixture must be a GeoJSON FeatureCollection.")
    features = payload.get("features")
    if not isinstance(features, list):
        raise NewsParserError("GDACS API fixture must have features.")
    items = []
    for index, feature in enumerate(features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise NewsParserError(f"GDACS feature {index} must be a GeoJSON Feature.")
        props = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(props, dict) or not isinstance(geometry, dict):
            raise NewsParserError(f"GDACS feature {index} lacks properties or geometry.")
        urls = props.get("url")
        severity = props.get("severitydata") or {}
        if not isinstance(urls, dict) or not isinstance(severity, dict):
            raise NewsParserError(f"GDACS feature {index} has invalid URL or severity data.")
        affected = props.get("affectedcountries") or []
        if not isinstance(affected, list):
            raise NewsParserError(f"GDACS feature {index} has invalid affected countries.")
        countries = [row.get("countryname") for row in affected if isinstance(row, dict)]
        coords = geometry.get("coordinates")
        point = (
            _gdacs_point(coords[1], coords[0])
            if geometry.get("type") == "Point" and isinstance(coords, list) and len(coords) >= 2
            else None
        )
        items.append(_gdacs_item(source, index=index, data={
            "event_type": props.get("eventtype"),
            "event_id": props.get("eventid"),
            "episode_id": props.get("episodeid"),
            "alert_level": props.get("alertlevel"),
            "alert_score": props.get("alertscore"),
            "severity": severity.get("severity"),
            "severity_unit": severity.get("severityunit"),
            "severity_text": severity.get("severitytext"),
            "country": props.get("country"),
            "iso3": props.get("iso3"),
            "affected_countries": countries,
            "coordinates": point,
            "bbox": _gdacs_bbox(feature.get("bbox")),
            "raw_bbox": feature.get("bbox") if isinstance(feature.get("bbox"), list) else None,
            "geometry_type": geometry.get("type"),
            "title": props.get("name"),
            "name": props.get("eventname"),
            "description": props.get("description"),
            "url": urls.get("report"),
            "published_at": props.get("fromdate"),
            "start_at": props.get("fromdate"),
            "updated_at": props.get("datemodified"),
            "source_format": "geojson",
        }))
    return items


def _reliefweb_names(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return _unique_texts(
        [row.get("name") for row in value if isinstance(row, dict)], max_chars=120
    )


def _reliefweb_config_set(source: dict[str, Any], key: str) -> set[str]:
    raw = source.get(key)
    if not isinstance(raw, list) or not raw:
        raise NewsParserError(f"ReliefWeb reports require configured {key}.")
    values = {str(value).strip().casefold() for value in raw if str(value).strip()}
    if not values:
        raise NewsParserError(f"ReliefWeb reports require configured {key}.")
    return values


def _parse_reliefweb_reports_json(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "GLOBAL":
        raise NewsParserError("ReliefWeb reports parser requires GLOBAL scope.")
    active_ids = _reliefweb_config_set(source, "active_disaster_ids")
    official_sources = _reliefweb_config_set(source, "official_source_names")
    themes = _reliefweb_config_set(source, "humanitarian_theme_names")
    max_items = source.get("max_items", 10)
    if isinstance(max_items, bool) or not isinstance(max_items, int) or not 1 <= max_items <= 25:
        raise NewsParserError("ReliefWeb reports max_items must be 1..25.")
    retention_days = source.get("retention_days")
    if (
        isinstance(retention_days, bool)
        or not isinstance(retention_days, int)
        or not 1 <= retention_days <= 7
    ):
        raise NewsParserError("ReliefWeb reports require retention_days of 1..7.")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed ReliefWeb reports fixture: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise NewsParserError("ReliefWeb reports fixture must have a data list.")
    items = []
    for index, row in enumerate(payload["data"]):
        if not isinstance(row, dict) or not isinstance(row.get("fields"), dict):
            raise NewsParserError(f"ReliefWeb report {index} lacks fields.")
        fields = row["fields"]
        disaster_rows = fields.get("disaster") or []
        if not isinstance(disaster_rows, list):
            raise NewsParserError(f"ReliefWeb report {index} has invalid disasters.")
        matched_disasters = [
            entry for entry in disaster_rows
            if isinstance(entry, dict) and str(entry.get("id") or "").casefold() in active_ids
        ]
        source_names = _reliefweb_names(fields.get("source"))
        matched_sources = [name for name in source_names if name.casefold() in official_sources]
        theme_names = _reliefweb_names(fields.get("theme"))
        matched_themes = [name for name in theme_names if name.casefold() in themes]
        if not (matched_disasters and matched_sources and matched_themes):
            continue
        report_id = bounded_text(row.get("id") or fields.get("id"), max_chars=32)
        title = bounded_text(fields.get("title"), max_chars=MAX_TITLE_LENGTH)
        url = normalize_url(fields.get("url"))
        parts = urlsplit(url)
        if not report_id or not title or parts.scheme != "https" or parts.hostname not in {
            "reliefweb.int", "www.reliefweb.int"
        }:
            raise NewsParserError(f"ReliefWeb report {index} lacks official identity or URL.")
        date = fields.get("date") or {}
        if not isinstance(date, dict):
            raise NewsParserError(f"ReliefWeb report {index} has invalid dates.")
        published_at = normalize_timestamp(date.get("original") or date.get("created"))
        if not published_at:
            raise NewsParserError(f"ReliefWeb report {index} has no publication date.")
        headline = fields.get("headline")
        summary = headline.get("summary") if isinstance(headline, dict) else None
        countries = _reliefweb_names(fields.get("country"))
        item = _normalize_item(
            source,
            {
                "title": title,
                "url": url,
                "description": summary,
                "published_at": published_at,
                "tags": ["reliefweb", "global", "humanitarian", "report"],
            },
            index=index,
        )
        item["evidence"]["reliefweb_report"] = {
            "id": report_id,
            "disaster_ids": [str(entry["id"]) for entry in matched_disasters],
            "disaster_names": _reliefweb_names(matched_disasters),
            "sources": matched_sources,
            "countries": countries,
            "themes": matched_themes,
            "published_at": published_at,
            "updated_at": normalize_timestamp(date.get("changed")),
            "source_url": url,
            "filter": {
                "configured_active_disaster_match": True,
                "official_source_match": True,
                "humanitarian_theme_match": True,
                "max_items": max_items,
                "retention_days": retention_days,
            },
            "ranking": {"humanitarian_source": True, "report_volume_capped": True},
        }
        items.append(item)
        if len(items) >= max_items:
            break
    return items


def _parse_reliefweb_disasters_json(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "GLOBAL":
        raise NewsParserError("ReliefWeb disaster parser requires GLOBAL scope.")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed ReliefWeb disaster fixture: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise NewsParserError("ReliefWeb disaster fixture must have a data list.")
    items = []
    for index, row in enumerate(payload["data"]):
        if not isinstance(row, dict) or not isinstance(row.get("fields"), dict):
            raise NewsParserError(f"ReliefWeb disaster {index} lacks fields.")
        fields = row["fields"]
        date = fields.get("date") or {}
        if not isinstance(date, dict):
            raise NewsParserError(f"ReliefWeb disaster {index} has invalid dates.")
        disaster_id = bounded_text(row.get("id") or fields.get("id"), max_chars=32)
        name = bounded_text(fields.get("name"), max_chars=MAX_TITLE_LENGTH)
        url = normalize_url(fields.get("url"))
        parts = urlsplit(url)
        if not disaster_id or not name or parts.scheme != "https" or parts.hostname not in {
            "reliefweb.int", "www.reliefweb.int"
        }:
            raise NewsParserError(f"ReliefWeb disaster {index} lacks official identity or URL.")
        country = _reliefweb_names(fields.get("country"))
        primary_country = fields.get("primary_country")
        if isinstance(primary_country, dict):
            primary_country = bounded_text(primary_country.get("name"), max_chars=120)
        else:
            primary_country = None
        disaster_type = _reliefweb_names(fields.get("type"))
        primary_type = fields.get("primary_type")
        if isinstance(primary_type, dict):
            primary_type = bounded_text(primary_type.get("name"), max_chars=120)
        else:
            primary_type = None
        event_date = normalize_timestamp(date.get("event"))
        created_at = normalize_timestamp(date.get("created"))
        changed_at = normalize_timestamp(date.get("changed"))
        if not (event_date or created_at):
            raise NewsParserError(f"ReliefWeb disaster {index} lacks event or creation date.")
        reports_count = fields.get("reports_count")
        if isinstance(reports_count, bool) or not isinstance(reports_count, int):
            reports_count = None
        item = _normalize_item(
            source,
            {
                "title": name,
                "url": url,
                "description": fields.get("description"),
                "published_at": event_date or created_at,
                "tags": ["reliefweb", "global", "humanitarian", "disaster"],
            },
            index=index,
        )
        item["evidence"]["reliefweb_disaster"] = {
            "id": disaster_id,
            "name": name,
            "status": bounded_text(fields.get("status"), max_chars=32),
            "countries": country,
            "primary_country": primary_country,
            "types": disaster_type,
            "primary_type": primary_type,
            "event_date": event_date,
            "created_at": created_at,
            "updated_at": changed_at,
            "source_url": url,
            "reports_count": reports_count,
            "glide": bounded_text(fields.get("glide"), max_chars=64),
            "ranking": {
                "humanitarian_source": True,
                "active": fields.get("status") in {"current", "alert"},
                "featured": fields.get("featured") is True,
            },
        }
        items.append(item)
    return items


_WHO_DON_SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{1,120}$")


def _parse_who_don_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "GLOBAL":
        raise NewsParserError("WHO DON parser requires GLOBAL scope.")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed WHO DON fixture: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("value"), list):
        raise NewsParserError("WHO DON fixture must have an OData value list.")
    items = []
    for index, row in enumerate(payload["value"]):
        if not isinstance(row, dict):
            raise NewsParserError(f"WHO DON row {index} must be an object.")
        slug = str(row.get("UrlName") or "").strip()
        if not slug:
            path = str(row.get("ItemDefaultUrl") or "").strip()
            slug = path.rsplit("/", 1)[-1]
        if not _WHO_DON_SLUG_RE.fullmatch(slug):
            raise NewsParserError(f"WHO DON row {index} has no safe article slug.")
        title_value = row.get("OverrideTitle") if row.get("UseOverrideTitle") is True else None
        title = bounded_text(title_value or row.get("Title"), max_chars=MAX_TITLE_LENGTH)
        published_at = normalize_timestamp(
            row.get("PublicationDateAndTime") or row.get("PublicationDate")
        )
        if not title or not published_at:
            raise NewsParserError(f"WHO DON row {index} lacks title or publication date.")
        url = f"https://www.who.int/emergencies/disease-outbreak-news/item/{slug}"
        hazard_label, geography_label = title, None
        for separator in (" - ", " – "):
            if separator in title:
                hazard_label, geography_label = title.rsplit(separator, 1)
                break
        item = _normalize_item(
            source,
            {
                "title": title,
                "url": url,
                "description": row.get("Summary"),
                "published_at": published_at,
                "tags": ["official", "who", "global", "public-health", "outbreak-news"],
            },
            index=index,
        )
        item["evidence"]["who_don"] = {
            "id": bounded_text(row.get("Id"), max_chars=64),
            "don_id": bounded_text(row.get("DonId") or slug, max_chars=120),
            "hazard_label": bounded_text(hazard_label, max_chars=160),
            "geography_label": bounded_text(geography_label, max_chars=160),
            "geography_basis": "title_suffix_unverified" if geography_label else "not_provided",
            "published_at": published_at,
            "updated_at": normalize_timestamp(row.get("LastModified")),
            "source_url": url,
            "summary_bounded": True,
            "case_counts_extracted": False,
            "ranking": {"official_public_health": True, "who_don": True},
        }
        items.append(item)
    return items


def _usgs_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _global_usgs_filter(source: dict[str, Any]) -> dict[str, Any]:
    defaults = {
        "min_magnitude": 6.0,
        "min_depth_km": -100.0,
        "max_depth_km": 1000.0,
        "min_felt": 0.0,
        "min_mmi": 0.0,
    }
    values: dict[str, Any] = {}
    for key, default in defaults.items():
        value = _usgs_number(source.get(key, default))
        if value is None:
            raise NewsParserError(f"GLOBAL USGS {key} must be a finite number.")
        values[key] = value
    if not (
        values["min_magnitude"] >= 0
        and -100 <= values["min_depth_km"] <= values["max_depth_km"] <= 1000
        and values["min_felt"] >= 0
        and 0 <= values["min_mmi"] <= 12
    ):
        raise NewsParserError("GLOBAL USGS magnitude, depth, felt, or intensity filter is invalid.")
    max_age = source.get("max_age_hours")
    if max_age is not None:
        max_age = _usgs_number(max_age)
        if max_age is None or not 1 <= max_age <= 24 * 31:
            raise NewsParserError("GLOBAL USGS max_age_hours must be 1..744.")
    values["max_age_hours"] = max_age
    if not isinstance(source.get("tsunami_only", False), bool):
        raise NewsParserError("GLOBAL USGS tsunami_only must be a boolean.")
    values["tsunami_only"] = source.get("tsunami_only", False)
    for key in ("country_terms", "region_terms"):
        raw = source.get(key, [])
        if not isinstance(raw, list) or len(raw) > 20 or any(
            not isinstance(term, str) or not 1 <= len(term.strip()) <= 80 for term in raw
        ):
            raise NewsParserError(f"GLOBAL USGS {key} must have at most 20 bounded labels.")
        values[key] = list(dict.fromkeys(term.strip().casefold() for term in raw))
    return values


def _usgs_filter(source: dict[str, Any]) -> dict[str, Any]:
    if str(source.get("scope") or "").upper() == "GLOBAL":
        return _global_usgs_filter(source)
    if str(source.get("scope") or "").upper() == "NATIONAL":
        magnitude = _usgs_number(source.get("min_magnitude", 5.0))
        if magnitude is None or magnitude < 0:
            raise NewsParserError(
                "NATIONAL USGS min_magnitude must be a finite nonnegative number."
            )
        return {"min_magnitude": magnitude}
    defaults = {
        "min_longitude": -130.0,
        "max_longitude": -116.5,
        "min_latitude": 45.0,
        "max_latitude": 50.0,
        "min_magnitude": 3.0,
    }
    values: dict[str, float] = {}
    for key, default in defaults.items():
        value = _usgs_number(source.get(key, default))
        if value is None:
            raise NewsParserError(f"USGS source {key} must be a finite number.")
        values[key] = value
    if not (
        -180 <= values["min_longitude"] < values["max_longitude"] <= 180
        and -90 <= values["min_latitude"] < values["max_latitude"] <= 90
        and values["min_magnitude"] >= 0
    ):
        raise NewsParserError("USGS source coordinate bounds or magnitude threshold are invalid.")
    radius_keys = ("center_latitude", "center_longitude", "radius_km")
    if any(source.get(key) is not None for key in radius_keys):
        if any(source.get(key) is None for key in radius_keys):
            raise NewsParserError("USGS radius filter requires center latitude, longitude, and km.")
        for key in radius_keys:
            value = _usgs_number(source[key])
            if value is None:
                raise NewsParserError(f"USGS {key} must be a finite number.")
            values[key] = value
        if not (
            -90 <= values["center_latitude"] <= 90
            and -180 <= values["center_longitude"] <= 180
            and 0 < values["radius_km"] <= 3000
        ):
            raise NewsParserError("USGS radius center or distance is invalid.")
    return values


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat_delta = math.radians(lat2 - lat1)
    lon_delta = math.radians(lon2 - lon1)
    arc = (
        math.sin(lat_delta / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
        * math.sin(lon_delta / 2) ** 2
    )
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(arc)))


def _national_usgs_region(longitude: float, latitude: float) -> str | None:
    for name, min_lon, max_lon, min_lat, max_lat in _NATIONAL_USGS_REGIONS:
        if min_lon <= longitude <= max_lon and min_lat <= latitude <= max_lat:
            return name
    return None


def _usgs_timestamp(value: Any) -> str | None:
    milliseconds = _usgs_number(value)
    if milliseconds is None:
        return None
    try:
        return datetime.fromtimestamp(milliseconds / 1000, tz=UTC).isoformat(
            timespec="seconds"
        )
    except (ValueError, OverflowError, OSError):
        return None


def _parse_usgs_earthquake_geojson(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed USGS GeoJSON fixture: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise NewsParserError("USGS fixture must be a GeoJSON FeatureCollection.")
    features = payload.get("features")
    if not isinstance(features, list):
        raise NewsParserError("USGS fixture must contain a features list.")
    geo_filter = _usgs_filter(source)
    global_scope = str(source.get("scope") or "").upper() == "GLOBAL"
    normalized: list[dict[str, Any]] = []
    for index, feature in enumerate(features):
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise NewsParserError(f"USGS feature {index} must be a GeoJSON Feature.")
        properties = feature.get("properties")
        geometry = feature.get("geometry")
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            raise NewsParserError(f"USGS feature {index} is missing properties or geometry.")
        if str(properties.get("type") or "earthquake").strip().lower() != "earthquake":
            continue
        coords = geometry.get("coordinates")
        if geometry.get("type") != "Point" or not isinstance(coords, list) or len(coords) < 2:
            raise NewsParserError(f"USGS feature {index} must have Point coordinates.")
        longitude = _usgs_number(coords[0])
        latitude = _usgs_number(coords[1])
        magnitude = _usgs_number(properties.get("mag"))
        if longitude is None or latitude is None or magnitude is None:
            continue
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            continue
        national = str(source.get("scope") or "").upper() == "NATIONAL"
        national_region = _national_usgs_region(longitude, latitude) if national else None
        source_place = str(properties.get("place") or "").strip()
        # The broad U.S. coordinate boxes include foreign land. A country suffix
        # in USGS's own place label is a useful exclusion, not proof of a U.S.
        # epicenter or a multi-state impact for labels that remain.
        foreign_place_label = bool(_FOREIGN_USGS_PLACE_SUFFIX.search(source_place))
        radius_distance = (
            _distance_km(
                geo_filter["center_latitude"], geo_filter["center_longitude"],
                latitude, longitude,
            ) if "radius_km" in geo_filter and not (national or global_scope) else None
        )
        matches_geography = (
            True if global_scope else (
                national_region is not None and not foreign_place_label
            ) if national else
            geo_filter["min_longitude"] <= longitude <= geo_filter["max_longitude"]
            and geo_filter["min_latitude"] <= latitude <= geo_filter["max_latitude"]
        )
        if radius_distance is not None:
            matches_geography = matches_geography and radius_distance <= geo_filter["radius_km"]
        if not matches_geography or magnitude < geo_filter["min_magnitude"]:
            continue
        event_id = bounded_text(feature.get("id"), max_chars=120)
        if global_scope and not event_id:
            raise NewsParserError(f"GLOBAL USGS feature {index} has no event id.")
        published_at = _usgs_timestamp(properties.get("time"))
        if published_at is None:
            raise NewsParserError(f"USGS feature {index} has no valid event time.")
        url = str(properties.get("url") or "")
        try:
            parts = urlsplit(url)
        except ValueError as exc:
            raise NewsParserError(f"USGS feature {index} has an invalid event URL.") from exc
        if parts.scheme != "https" or parts.hostname != "earthquake.usgs.gov":
            raise NewsParserError(f"USGS feature {index} has no official HTTPS event URL.")
        place = bounded_text(source_place, max_chars=180) or (
            "World" if global_scope else "U.S. region" if national else "Washington region"
        )
        title = bounded_text(properties.get("title"), max_chars=MAX_TITLE_LENGTH)
        title = title or f"M {magnitude:.1f} - {place}"
        felt = _int_value(properties.get("felt")) or 0
        alert = bounded_text(properties.get("alert"), max_chars=32)
        depth_km = _usgs_number(coords[2]) if len(coords) > 2 else None
        if global_scope:
            mmi = _usgs_number(properties.get("mmi"))
            if (
                depth_km is None or
                not geo_filter["min_depth_km"] <= depth_km <= geo_filter["max_depth_km"] or
                felt < geo_filter["min_felt"] or
                (geo_filter["min_mmi"] > 0 and (mmi is None or mmi < geo_filter["min_mmi"])) or
                (geo_filter["tsunami_only"] and properties.get("tsunami") != 1)
            ):
                continue
            if geo_filter["max_age_hours"] is not None:
                age_hours = (
                    datetime.now(UTC) - datetime.fromisoformat(published_at)
                ).total_seconds() / 3600
                if age_hours < -1 or age_hours > geo_filter["max_age_hours"]:
                    continue
            place_terms = geo_filter["country_terms"] + geo_filter["region_terms"]
            if place_terms and not any(
                re.search(rf"\b{re.escape(term)}\b", place.casefold())
                for term in place_terms
            ):
                continue
        magnitude_weight = min(35, max(0, round((magnitude - 2.5) * 8)))
        felt_weight = min(10, max(0, felt // 10))
        alert_weight = {"red": 30, "orange": 20, "yellow": 10, "green": 3}.get(
            str(alert or "").lower(), 0
        )
        seismic_weight = min(55, magnitude_weight + felt_weight + alert_weight)
        item = _normalize_item(
            source,
            {
                "title": title,
                "url": url,
                "canonical_url": url,
                "description": f"Magnitude {magnitude:.1f} earthquake near {place}.",
                "published_at": published_at,
                "tags": _unique_texts(
                    [
                        "official",
                        "usgs",
                        "earthquake",
                        "seismic",
                        "global" if global_scope else "national" if national else "regional",
                        "public-impact" if (
                            magnitude >= (6.5 if global_scope else 4.5) or felt >= 10
                        ) else None,
                        "tsunami" if properties.get("tsunami") == 1 else None,
                    ],
                    max_chars=64,
                ),
            },
            index=index,
        )
        item["evidence"]["usgs_earthquake"] = {
            "id": event_id,
            "magnitude": magnitude,
            "magnitude_type": bounded_text(properties.get("magType"), max_chars=32),
            "place": place,
            "depth_km": depth_km,
            "longitude": longitude,
            "latitude": latitude,
            "time": published_at,
            "updated": _usgs_timestamp(properties.get("updated")),
            "felt": felt,
            "cdi": _usgs_number(properties.get("cdi")),
            "mmi": _usgs_number(properties.get("mmi")),
            "alert": alert,
            "tsunami": properties.get("tsunami") == 1,
            "significance": _int_value(properties.get("sig")),
            "status": bounded_text(properties.get("status"), max_chars=32),
            "event_type": "earthquake",
            "source_url": url,
            "filter": {
                **geo_filter,
                "matched": True,
                "geography_basis": (
                    "source_place_label" if global_scope else
                    "coarse_us_region_coordinates" if national else
                    "configured_radius_and_bounds" if radius_distance is not None else
                    "configured_bounds"
                ),
                "distance_km": round(radius_distance, 1) if radius_distance is not None else None,
                "region": national_region,
                "foreign_place_label_guard": bool(national),
                "place_label": place if global_scope else None,
            },
            "ranking": {
                "magnitude_weight": magnitude_weight,
                "felt_weight": felt_weight,
                "alert_weight": alert_weight,
                "regional_seismic_weight": seismic_weight,
                **({
                    "national_severity_score": min(45, magnitude_weight + alert_weight),
                    "national_felt_impact_score": min(25, felt_weight * 2),
                } if national else {}),
            },
        }
        if national:
            item["evidence"]["national_identity"] = {
                "event_type": "earthquake",
                "agency": "USGS",
                "official_event_ids": [f"usgs:{event_id}"] if event_id else [],
                "local_regional_impact_score": min(20, max(
                    magnitude_weight // 2, felt_weight * 2,
                )),
                "multi_state_impact": False,
                "impact_scope_basis": (
                    "USGS summary felt count has no verified state distribution; "
                    "coarse epicenter region does not prove multi-state impact"
                ),
            }
        if global_scope:
            item["evidence"]["global_identity"] = {
                "earthquake_id": item["evidence"]["usgs_earthquake"]["id"],
                "impact_tags": ["tsunami"] if properties.get("tsunami") == 1 else [],
            }
        normalized.append(item)
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
    privacy = _sfd_privacy_decision(
        incident_type=incident_type,
        unit_count=unit_count,
        neighborhood=neighborhood,
        address=address,
    )
    location_tokens = _sfd_location_tokens(
        row, address=address, neighborhood=neighborhood,
        suppress_exact=privacy["exact_location_suppressed"],
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
    suppress_exact: bool,
) -> list[str]:
    tokens = _unique_texts(
        [
            neighborhood,
            _street_only(address),
            None if suppress_exact else _first_value(row, "cross_street", "intersection"),
            _first_value(row, "zone", "beat"),
        ],
        max_chars=120,
    )
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
        rows = next(
            (payload[key] for key in ("alerts", "items", "data") if key in payload), None
        )
    else:
        rows = payload
    if not isinstance(rows, list):
        raise NewsParserError("WSDOT fixture must be a list or object with alert list.")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"WSDOT alert row {index} must be an object.")
        if not _wsdot_alert_matches_scope(source, row):
            continue
        item = _normalize_wsdot_alert(source, row, index=index)
        alert_id = item["evidence"]["wsdot_alert"]["alert_id"]
        if alert_id in seen_ids:
            raise NewsParserError(f"WSDOT JSON alert row {index} duplicates alert ID {alert_id}.")
        seen_ids.add(alert_id)
        normalized.append(item)
    return normalized


class _WsdotPlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _wsdot_plain_text(value: str | None) -> str:
    parser = _WsdotPlainText()
    parser.feed(value or "")
    return " ".join(" ".join(parser.parts).split())


def _parse_wsdot_highway_alerts_rss(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed WSDOT RSS: {exc}") from exc
    channel = root.find("./channel") if _local_name(root.tag) == "rss" else None
    if channel is None or _element_text(channel.find("./title")) != "WA State Highway Alerts":
        raise NewsParserError("WSDOT RSS must contain the official Highway Alerts channel.")
    rows = channel.findall("./item")
    if not rows:
        raise NewsParserError("WSDOT RSS has no alert rows; keep the prior snapshot.")
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, element in enumerate(rows):
        alert_id = str(_element_text(element.find("./guid")) or "")
        title = _wsdot_plain_text(_element_text(element.find("./title")))
        description = _wsdot_plain_text(_element_text(element.find("./description")))
        updated = _element_text(element.find("./{http://www.w3.org/2005/Atom}updated"))
        raw_link = str(_element_text(element.find("./link")) or "")
        try:
            parts = urlsplit(raw_link)
        except ValueError as exc:
            raise NewsParserError(f"WSDOT RSS alert row {index} has an invalid URL.") from exc
        refnum = parse_qs(parts.query).get("refnum", [])
        if (
            not alert_id.isdigit() or len(alert_id) > 12 or alert_id in seen_ids
            or not title or not normalize_timestamp(updated)
            or parts.scheme not in {"http", "https"}
            or parts.hostname != "www.wsdot.wa.gov"
            or parts.path.lower() != "/traffic/trafficalerts/default.aspx"
            or refnum != [alert_id]
        ):
            raise NewsParserError(f"WSDOT RSS alert row {index} has invalid identity or fields.")
        seen_ids.add(alert_id)
        official_link = normalize_url(parts._replace(scheme="https").geturl())
        priority_match = re.search(r"\b(highest|high|medium|low) impact\b", description, re.I)
        item = _normalize_wsdot_alert(
            source,
            {
                "AlertID": alert_id,
                "Headline": title,
                "Description": description,
                "LastUpdatedTime": updated,
                "url": official_link,
                "Priority": priority_match.group(1).title() if priority_match else None,
            },
            index=index,
        )
        item["evidence"]["wsdot_alert"]["feed_url"] = str(source.get("url") or "")
        item["evidence"]["wsdot_alert"]["link_note"] = (
            "WSDOT's per-alert legacy link currently redirects to its general alerts page."
        )
        normalized.append(item)
    return normalized


def _parse_king_county_emergency_rss(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "REGIONAL":
        raise NewsParserError("King County Emergency News parser requires REGIONAL scope.")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed King County Emergency News RSS: {exc}") from exc
    channel = root.find("./channel") if _local_name(root.tag) == "rss" else None
    if channel is None or _element_text(channel.find("./title")) != "King County Emergency News":
        raise NewsParserError("King County Emergency News RSS has an unexpected channel.")
    items = _parse_rss_feed(source, root)
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        parts = urlsplit(str(item["url"]))
        if parts.scheme != "https" or parts.hostname != "kcemergency.com":
            raise NewsParserError(f"King County Emergency News item {index} has no official URL.")
        if not item.get("source_published_at"):
            raise NewsParserError(
                f"King County Emergency News item {index} has no publication time."
            )
        item["description"] = bounded_text(
            _wsdot_plain_text(item.get("description") or ""), max_chars=500
        )
        categories = list(item.get("tags") or [])
        classification, impact_score = _king_county_emergency_classification(
            str(item["title"]), categories
        )
        item["tags"] = _unique_texts(
            ["official", "county-emergency", *categories,
             "public-impact" if classification == "emergency_alert" else None],
            max_chars=64,
        )
        item["evidence"]["king_county_emergency"] = {
            "publisher": "King County Emergency Management",
            "county": "King County",
            "geography_basis": "publisher_jurisdiction_only",
            "source_url": item["url"],
            "published_at": item["source_published_at"],
            "categories": categories,
            "classification": classification,
            "ranking": {"public_impact_score": impact_score},
            "body_stored": False,
        }
        normalized.append(item)
    return normalized


def _king_county_emergency_classification(
    title: str, categories: list[str]
) -> tuple[str, int]:
    text = " ".join([title, *categories]).casefold()
    if re.search(r"\b(test|exercise|drill|semi-annual)\b", text):
        return "test", 0
    if re.search(r"\b(recovery|assistance|fema funding)\b", text) and not re.search(
        r"\b(evacuation|shelter in place|warning)\b", text
    ):
        return "recovery", 6
    if re.search(
        r"\b(evacuation|shelter in place|emergency|flood warning|boil water|alert)\b",
        text,
    ):
        return "emergency_alert", 30
    return "county_notice", 4


_NHTSA_CAMPAIGN_RE = re.compile(r"\d{2}[A-Z]\d{6}\Z")
_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,19}\Z")


def _parse_cisa_kev_json(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "NATIONAL":
        raise NewsParserError("CISA KEV parser requires NATIONAL scope.")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed CISA KEV JSON: {exc}") from exc
    rows = payload.get("vulnerabilities") if isinstance(payload, dict) else None
    count = payload.get("count") if isinstance(payload, dict) else None
    if (
        not isinstance(rows, list) or not rows
        or not isinstance(count, int) or isinstance(count, bool) or count != len(rows)
        or not bounded_text(payload.get("catalogVersion"), max_chars=64)
        or not normalize_timestamp(payload.get("dateReleased"))
    ):
        raise NewsParserError("CISA KEV catalog needs a nonempty, matching snapshot envelope.")
    seen_cves: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"CISA KEV row {index} is not an object.")
        cve = str(row.get("cveID") or "").strip().upper()
        if not _CVE_RE.fullmatch(cve) or cve in seen_cves:
            raise NewsParserError(f"CISA KEV row {index} has invalid or duplicate CVE.")
        seen_cves.add(cve)
        try:
            added = datetime.strptime(str(row.get("dateAdded") or ""), "%Y-%m-%d").date()
            due = datetime.strptime(str(row.get("dueDate") or ""), "%Y-%m-%d").date()
        except ValueError as exc:
            raise NewsParserError(f"CISA KEV row {index} has invalid calendar dates.") from exc
        vendor = bounded_text(row.get("vendorProject"), max_chars=100)
        product = bounded_text(row.get("product"), max_chars=100)
        name = bounded_text(row.get("vulnerabilityName"), max_chars=180)
        description = bounded_text(row.get("shortDescription"), max_chars=500)
        action = bounded_text(row.get("requiredAction"), max_chars=500)
        if not all((vendor, product, name, description, action)):
            raise NewsParserError(f"CISA KEV row {index} lacks required fields.")
        ransomware = str(row.get("knownRansomwareCampaignUse") or "Unknown").strip()
        if ransomware not in {"Known", "Unknown"}:
            raise NewsParserError(f"CISA KEV row {index} has invalid ransomware evidence.")
        triage = str(row.get("forensicTriage") or "No").strip()
        if triage not in {"Yes", "No"}:
            raise NewsParserError(f"CISA KEV row {index} has invalid triage evidence.")
        cwes = row.get("cwes") or []
        if not isinstance(cwes, list):
            raise NewsParserError(f"CISA KEV row {index} has invalid CWE values.")
        cwes = [str(value) for value in cwes[:20] if re.fullmatch(r"CWE-\d+", str(value))]
        catalog_url = "https://www.cisa.gov/known-exploited-vulnerabilities-catalog"
        search_url = catalog_url + "?search_api_fulltext=" + quote(cve)
        score = 10 + (8 if ransomware == "Known" else 0) + (4 if triage == "Yes" else 0)
        item = _normalize_item(source, {
            "title": f"CISA KEV {cve}: {name}",
            "url": search_url,
            "description": description,
            "published_at": added.isoformat(),
            "tags": ["official", "cybersecurity", "known-exploited", "cisa"],
        }, index=index)
        item["evidence"]["cisa_kev"] = {
            "cve_id": cve,
            "vendor_project": vendor,
            "product": product,
            "vulnerability_name": name,
            "date_added": added.isoformat(),
            "due_date": due.isoformat(),
            "date_precision": "day",
            "due_date_applies_to": "federal_civilian_executive_branch",
            "required_action": action,
            "known_ransomware_campaign_use": ransomware,
            "forensic_triage": triage,
            "cwes": cwes,
            "source_url": catalog_url,
            "item_url_kind": "catalog_search",
            "catalog_version": bounded_text(payload["catalogVersion"], max_chars=64),
            "catalog_released_at": normalize_timestamp(payload["dateReleased"]),
            "local_applicability": "unknown",
            "ranking": {"cyber_score": score},
            "body_stored": False,
        }
        normalized.append(item)
    return normalized


_FAA_NAS_GROUPS = {
    "Ground_Delay_List": ("Ground_Delay", "ground_delay", 34),
    "Ground_Stop_List": ("Ground_Stop", "ground_stop", 40),
    "Arrival_Departure_Delay_List": ("Delay", "arrival_departure_delay", 24),
    "Airport_Closure_List": ("Airport", "closure_notice", 30),
}


def _parse_faa_nas_status_xml(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "NATIONAL":
        raise NewsParserError("FAA NAS XML parser requires NATIONAL scope.")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", payload_text, re.I):
        raise NewsParserError("FAA NAS XML must not contain a DTD or entity declaration.")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed FAA NAS XML: {exc}") from exc
    if root.tag != "AIRPORT_STATUS_INFORMATION":
        raise NewsParserError("FAA NAS XML has an unexpected root.")
    update_text = str(_element_text(root.find("Update_Time")) or "").strip()
    try:
        updated_at = datetime.strptime(update_text, "%a %b %d %H:%M:%S %Y GMT").replace(
            tzinfo=UTC
        ).isoformat(timespec="seconds")
    except ValueError as exc:
        raise NewsParserError("FAA NAS XML has an invalid Update_Time.") from exc
    selected_codes = [
        _normalize_airport_code(value)
        for value in _configured_texts(source.get("airport_codes"), default=[])
    ]
    selected_codes = [
        value for value in selected_codes if value and re.fullmatch(r"[A-Z]{3}", value)
    ]
    if not selected_codes:
        raise NewsParserError("NATIONAL FAA NAS XML needs a verified airport_codes allowlist.")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for delay_type in root.findall("Delay_type"):
        group_name = bounded_text(_element_text(delay_type.find("Name")), max_chars=100)
        unknown_lists = [
            child.tag for child in delay_type
            if child.tag.endswith("_List") and child.tag not in _FAA_NAS_GROUPS and len(child)
        ]
        if unknown_lists:
            raise NewsParserError(f"FAA NAS XML has unsupported active list: {unknown_lists[0]}.")
        for list_name, (row_name, event_type, base_weight) in _FAA_NAS_GROUPS.items():
            event_list = delay_type.find(list_name)
            if event_list is None:
                continue
            for row in event_list.findall(row_name):
                code = _normalize_airport_code(_element_text(row.find("ARPT")))
                if not code or not re.fullmatch(r"[A-Z]{3}", code):
                    raise NewsParserError("FAA NAS event has an invalid airport code.")
                if code not in selected_codes:
                    continue
                direction_element = row.find("Arrival_Departure")
                direction = (
                    bounded_text(direction_element.get("Type"), max_chars=30)
                    if direction_element is not None else None
                )
                average = bounded_text(_element_text(row.find("Avg")), max_chars=80)
                maximum = bounded_text(_element_text(row.find("Max")), max_chars=80)
                minimum = (
                    bounded_text(_element_text(direction_element.find("Min")), max_chars=80)
                    if direction_element is not None else None
                )
                if direction_element is not None:
                    maximum = maximum or bounded_text(
                        _element_text(direction_element.find("Max")), max_chars=80
                    )
                delay_minutes = _duration_minutes(average or minimum or maximum) or 0
                event = {
                    "event_type": event_type,
                    "group_name": group_name,
                    "direction": direction,
                    "reason": bounded_text(_element_text(row.find("Reason")), max_chars=300),
                    "average_delay": average,
                    "minimum_delay": minimum,
                    "maximum_delay": maximum,
                    "delay_minutes": delay_minutes,
                    "start_text": bounded_text(_element_text(row.find("Start")), max_chars=80),
                    "end_text": bounded_text(_element_text(row.find("Reopen")), max_chars=80),
                    "time_precision": (
                        "source_text_without_year" if event_type == "closure_notice" else None
                    ),
                    "impact_score": min(50, base_weight + min(10, delay_minutes // 10)),
                }
                grouped.setdefault(code, []).append(event)
    source_url = "https://nasstatus.faa.gov/api/airport-status-information"
    normalized: list[dict[str, Any]] = []
    for index, (code, events) in enumerate(grouped.items()):
        event_count = len(events)
        events = events[:25]
        lead = max(events, key=lambda event: event["impact_score"])
        airport_url = f"https://www.faa.gov/airport-status/{code}"
        item = _normalize_item(source, {
            "title": f"FAA NAS {code}: {lead['event_type'].replace('_', ' ').title()}",
            "url": airport_url,
            "description": lead["reason"] or lead["group_name"],
            "published_at": updated_at,
            "tags": ["official", "faa", "aviation", "airport-status", code.lower()],
        }, index=index)
        item["evidence"]["faa_nas_status"] = {
            "airport_code": code,
            "events": events,
            "event_count": event_count,
            "events_truncated": event_count > len(events),
            "source_update_at": updated_at,
            "source_url": source_url,
            "airport_status_url": airport_url,
            "geography_basis": "airport_code_only_not_country_verified",
            "ranking": {"aviation_impact_score": lead["impact_score"]},
            "body_stored": False,
        }
        normalized.append(item)
    return normalized


_FEDERAL_REGISTER_LOW_VALUE_RE = re.compile(
    r"\b(information collection|notice of meeting|combined notice of filings|"
    r"privacy act of 1974; system of records|submission for omb review)\b", re.I
)
_FEDERAL_REGISTER_DOC_RE = re.compile(r"\d{4}-\d{4,6}\Z")


def _parse_federal_register_documents_json(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "NATIONAL":
        raise NewsParserError("Federal Register parser requires NATIONAL scope.")
    agency_slugs = [
        value.casefold() for value in _configured_texts(source.get("agency_slugs"), default=[])
    ]
    document_types = [
        value.casefold() for value in _configured_texts(source.get("document_types"), default=[])
    ]
    impact_terms = [
        value.casefold() for value in _configured_texts(source.get("impact_terms"), default=[])
    ]
    if not agency_slugs or not document_types or not impact_terms:
        raise NewsParserError(
            "Federal Register parser requires agency, type and impact allowlists."
        )
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed Federal Register JSON: {exc}") from exc
    rows = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or len(rows) > 100:
        raise NewsParserError("Federal Register response needs at most 100 results.")
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"Federal Register row {index} is not an object.")
        document_number = str(row.get("document_number") or "").strip()
        if not _FEDERAL_REGISTER_DOC_RE.fullmatch(document_number) or document_number in seen_ids:
            raise NewsParserError(f"Federal Register row {index} has invalid document identity.")
        seen_ids.add(document_number)
        title = bounded_text(row.get("title"), max_chars=280)
        doc_type = bounded_text(row.get("type"), max_chars=80)
        agencies = row.get("agencies")
        if not title or not doc_type or not isinstance(agencies, list):
            raise NewsParserError(f"Federal Register row {index} lacks required metadata.")
        matched_agencies = [
            bounded_text(agency.get("slug"), max_chars=100)
            for agency in agencies if isinstance(agency, dict)
            and str(agency.get("slug") or "").casefold() in agency_slugs
        ]
        if not matched_agencies or doc_type.casefold() not in document_types:
            continue
        matched_terms = [term for term in impact_terms if term in title.casefold()]
        if not matched_terms or _FEDERAL_REGISTER_LOW_VALUE_RE.search(title):
            continue
        published = str(row.get("publication_date") or "")
        try:
            published_date = datetime.strptime(published, "%Y-%m-%d").date()
        except ValueError as exc:
            raise NewsParserError(
                f"Federal Register row {index} has invalid publication date."
            ) from exc
        url = str(row.get("html_url") or "").strip()
        parts = urlsplit(url)
        if (
            parts.scheme != "https" or parts.hostname != "www.federalregister.gov"
            or not parts.path.startswith(f"/documents/{published_date:%Y/%m/%d}/{document_number}/")
        ):
            raise NewsParserError(f"Federal Register row {index} has invalid document URL.")
        comment_end = _federal_register_date(row.get("comment_end_date"), index)
        effective_on = _federal_register_date(row.get("effective_on"), index)
        item = _normalize_item(source, {
            "title": title,
            "url": url,
            "description": bounded_text(row.get("abstract"), max_chars=500),
            "published_at": published_date.isoformat(),
            "tags": ["official", "federal-register", doc_type.lower().replace(" ", "-")],
        }, index=index)
        impact_score = min(25, 12 + (5 if doc_type.casefold() == "rule" else 0)
                           + (3 if comment_end else 0))
        item["evidence"]["federal_register"] = {
            "document_number": document_number,
            "document_type": doc_type,
            "agency_slugs": matched_agencies[:10],
            "matched_impact_terms": matched_terms[:10],
            "publication_date": published_date.isoformat(),
            "date_precision": "day",
            "comment_end_date": comment_end,
            "effective_on": effective_on,
            "action": bounded_text(row.get("action"), max_chars=300),
            "source_url": url,
            "legal_status": "informational_xml_rendition_verify_official_pdf",
            "ranking": {"public_impact_score": impact_score},
            "body_stored": False,
        }
        normalized.append(item)
    return normalized


def _federal_register_date(value: Any, index: int) -> str | None:
    if value in (None, ""):
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise NewsParserError(f"Federal Register row {index} has invalid action date.") from exc


_GOVINFO_COLLECTIONS = {
    "BILLS": ("Congressional Bills- Enrolled - New items on GovInfo", "enrolled_bill"),
    "PLAW": ("Public and Private Laws - New items on GovInfo", "public_law"),
    "FR": ("Federal Register - New items on GovInfo", "federal_register_issue"),
}


def _parse_govinfo_collection_rss(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "NATIONAL":
        raise NewsParserError("GovInfo RSS parser requires NATIONAL scope.")
    collection = str(source.get("collection") or "").strip().upper()
    if collection not in _GOVINFO_COLLECTIONS:
        raise NewsParserError("GovInfo RSS parser needs an allowlisted collection.")
    impact_terms = [
        value.casefold() for value in _configured_texts(source.get("impact_terms"), default=[])
    ]
    if not impact_terms:
        raise NewsParserError("GovInfo RSS parser needs impact_terms filtering.")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", payload_text, re.I):
        raise NewsParserError("GovInfo RSS must not contain DTD or entity declarations.")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed GovInfo RSS: {exc}") from exc
    channel = root.find("channel") if root.tag == "rss" else None
    expected_title, publication_stage = _GOVINFO_COLLECTIONS[collection]
    if channel is None or _element_text(channel.find("title")) != expected_title:
        raise NewsParserError("GovInfo RSS has an unexpected collection channel.")
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(channel.findall("item")[:100]):
        identifier = str(_element_text(row.find("guid")) or "").strip()
        if not identifier.startswith(collection + "-") or not re.fullmatch(
            r"[A-Za-z0-9-]{6,100}", identifier
        ) or identifier in seen_ids:
            raise NewsParserError(f"GovInfo RSS item {index} has invalid identity.")
        seen_ids.add(identifier)
        title = bounded_text(_wsdot_plain_text(_element_text(row.find("title"))), max_chars=280)
        published = normalize_timestamp(_element_text(row.find("pubDate")))
        url = str(_element_text(row.find("link")) or "").strip()
        if (
            not title or not published
            or url != f"https://www.govinfo.gov/app/details/{identifier}"
        ):
            raise NewsParserError(f"GovInfo RSS item {index} has invalid fields or URL.")
        matched_terms = [term for term in impact_terms if term in title.casefold()]
        if not matched_terms:
            continue
        description = bounded_text(
            _wsdot_plain_text(_element_text(row.find("description"))), max_chars=250
        )
        item = _normalize_item(source, {
            "title": title,
            "url": url,
            "description": description,
            "published_at": published,
            "tags": ["official", "govinfo", collection.lower(), "publication"],
        }, index=index)
        feed_name = "bills-enr" if collection == "BILLS" else collection.lower()
        item["evidence"]["govinfo_publication"] = {
            "collection": collection,
            "document_id": identifier,
            "publication_stage": publication_stage,
            "feed_published_at": published,
            "feed_timestamp_meaning": "govinfo_feed_item_not_document_effective_date",
            "source_url": url,
            "feed_url": f"https://www.govinfo.gov/rss/{feed_name}.xml",
            "matched_impact_terms": matched_terms[:10],
            "legal_effect_inferred": False,
            "ranking": {"publication_score": 8},
            "body_stored": False,
        }
        normalized.append(item)
    return normalized


def _parse_fda_recalls_rss(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "NATIONAL":
        raise NewsParserError("FDA recalls RSS parser requires NATIONAL scope.")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", payload_text, re.I):
        raise NewsParserError("FDA recalls RSS must not contain DTD or entity declarations.")
    try:
        root = ET.fromstring(payload_text)
    except ET.ParseError as exc:
        raise NewsParserError(f"Malformed FDA recalls RSS: {exc}") from exc
    channel = root.find("channel") if root.tag == "rss" else None
    if channel is None or _element_text(channel.find("title")) != (
        "Food and Drugs Administration--Recalls/Safety Alerts"
    ):
        raise NewsParserError("FDA recalls RSS has an unexpected channel.")
    normalized: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for index, row in enumerate(channel.findall("item")[:100]):
        title = bounded_text(_wsdot_plain_text(_element_text(row.find("title"))), max_chars=280)
        link = str(_element_text(row.find("link")) or "").strip()
        guid = str(_element_text(row.find("guid")) or "").strip()
        if not title or not link or not guid or link != guid:
            raise NewsParserError(f"FDA recalls RSS item {index} lacks identity or title.")
        parts = urlsplit(link)
        if (
            parts.scheme not in {"http", "https"}
            or parts.hostname != "www.fda.gov"
            or not parts.path.startswith("/safety/recalls-market-withdrawals-safety-alerts/")
        ):
            raise NewsParserError(f"FDA recalls RSS item {index} has no official recall URL.")
        url = normalize_url(parts._replace(scheme="https").geturl())
        if url in seen_urls:
            raise NewsParserError(f"FDA recalls RSS item {index} duplicates an official URL.")
        seen_urls.add(url)
        published = normalize_timestamp(_element_text(row.find("pubDate")))
        if not published:
            raise NewsParserError(f"FDA recalls RSS item {index} lacks publication time.")
        description = bounded_text(
            _wsdot_plain_text(_element_text(row.find("description"))), max_chars=500
        )
        creator = bounded_text(
            _element_text(row.find("{http://purl.org/dc/elements/1.1/}creator")),
            max_chars=100,
        )
        item = _normalize_item(source, {
            "title": title,
            "url": url,
            "description": description,
            "published_at": published,
            "tags": ["official", "fda-hosted", "recall-notice"],
        }, index=index)
        item["evidence"]["fda_recall_notice"] = {
            "feed_name": "Recalls/Safety Alerts",
            "feed_url": (
                "https://www.fda.gov/about-fda/contact-fda/stay-informed/"
                "rss-feeds/recalls/rss.xml"
            ),
            "guid": guid,
            "source_url": url,
            "feed_creator": creator,
            "hosted_by": "FDA",
            "severity": "not_in_feed",
            "distribution_geography": "not_in_feed",
            "recall_classification": "not_in_feed",
            "translation_relationship": "unverified",
            "ranking": {"public_hazard_score": 0},
            "body_stored": False,
        }
        normalized.append(item)
    return normalized


def _parse_nhtsa_recalls_json(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if str(source.get("scope") or "").upper() != "NATIONAL":
        raise NewsParserError("NHTSA recall parser requires NATIONAL scope.")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed NHTSA recall JSON: {exc}") from exc
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("Count"), int)
        or isinstance(payload.get("Count"), bool)
        or not isinstance(payload.get("results"), list)
        or payload["Count"] != len(payload["results"])
    ):
        raise NewsParserError("NHTSA recall response needs matching Count and results.")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for index, row in enumerate(payload["results"]):
        if not isinstance(row, dict):
            raise NewsParserError(f"NHTSA recall row {index} is not an object.")
        campaign = str(row.get("NHTSACampaignNumber") or "").strip().upper()
        if not _NHTSA_CAMPAIGN_RE.fullmatch(campaign):
            raise NewsParserError(f"NHTSA recall row {index} has no valid campaign number.")
        grouped.setdefault(campaign, []).append(row)

    normalized: list[dict[str, Any]] = []
    for index, (campaign, rows) in enumerate(grouped.items()):
        first = rows[0]
        report_date = str(first.get("ReportReceivedDate") or "").strip()
        try:
            published_at = datetime.strptime(report_date, "%m/%d/%Y").replace(
                tzinfo=UTC
            ).isoformat(timespec="seconds")
        except ValueError as exc:
            raise NewsParserError(f"NHTSA campaign {campaign} has invalid report date.") from exc
        component = bounded_text(first.get("Component"), max_chars=140)
        manufacturer = bounded_text(first.get("Manufacturer"), max_chars=140)
        if not component or not manufacturer:
            raise NewsParserError(f"NHTSA campaign {campaign} lacks manufacturer or component.")
        for row in rows[1:]:
            if (
                str(row.get("ReportReceivedDate") or "").strip() != report_date
                or bounded_text(row.get("Component"), max_chars=140) != component
                or bounded_text(row.get("Manufacturer"), max_chars=140) != manufacturer
            ):
                raise NewsParserError(f"NHTSA campaign {campaign} has conflicting rows.")
        vehicles = []
        for row in rows:
            vehicle = {
                "model_year": bounded_text(row.get("ModelYear"), max_chars=8),
                "make": bounded_text(row.get("Make"), max_chars=80),
                "model": bounded_text(row.get("Model"), max_chars=100),
            }
            if vehicle not in vehicles:
                vehicles.append(vehicle)
        units = []
        for row in rows:
            raw = row.get("PotentialNumberofUnitsAffected")
            try:
                value = int(str(raw).replace(",", "")) if raw not in (None, "") else None
            except ValueError as exc:
                raise NewsParserError(f"NHTSA campaign {campaign} has invalid units.") from exc
            if value is not None and value >= 0:
                units.append(value)
        affected_units = max(units) if units else None
        park_it = any(str(row.get("parkIt") or "").strip().lower() in {"yes", "true", "1"}
                      for row in rows)
        park_outside = any(str(row.get("parkOutSide") or "").strip().lower() in {"yes", "true", "1"}
                           for row in rows)
        score = min(35, (20 if park_it else 0) + (15 if park_outside else 0)
                    + (10 if affected_units is not None and affected_units >= 100_000 else 0))
        campaign_url = (
            "https://api.nhtsa.gov/recalls/campaignNumber?campaignNumber="
            + quote(campaign)
        )
        item = _normalize_item(source, {
            "title": f"NHTSA recall {campaign}: {manufacturer} {component}",
            "url": campaign_url,
            "description": bounded_text(first.get("Summary"), max_chars=500),
            "published_at": published_at,
            "tags": ["official", "vehicle-safety", "recall", "nhtsa"],
        }, index=index)
        item["evidence"]["nhtsa_recall"] = {
            "campaign_number": campaign,
            "manufacturer": manufacturer,
            "component": component,
            "vehicles": vehicles[:50],
            "vehicles_truncated": len(vehicles) > 50,
            "report_received_date": report_date,
            "date_precision": "day",
            "potential_units_affected": affected_units,
            "summary": bounded_text(first.get("Summary"), max_chars=500),
            "consequence": bounded_text(first.get("Consequence"), max_chars=500),
            "remedy": bounded_text(first.get("Remedy"), max_chars=500),
            "park_it": park_it,
            "park_outside": park_outside,
            "source_url": campaign_url,
            "instruction_url": "https://www.nhtsa.gov/recalls",
            "ranking": {"vehicle_safety_score": score},
            "body_stored": False,
        }
        normalized.append(item)
    return normalized


def _normalize_wsdot_alert(
    source: dict[str, Any],
    row: dict[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    alert_id = bounded_text(_first_value(row, "alert_id", "AlertID", "id", "ID"), max_chars=120)
    raw_title = _first_value(row, "headline", "Headline", "HeadlineDescription", "title", "Title")
    title = bounded_text(_wsdot_plain_text(str(raw_title or "")), max_chars=MAX_TITLE_LENGTH)
    raw_description = _first_value(
        row,
        "description",
        "Description",
        "ExtendedDescription",
        "extended_description",
    )
    description = bounded_text(
        _wsdot_plain_text(str(raw_description or "")),
        max_chars=MAX_DESCRIPTION_LENGTH,
    )
    published_at = _wsdot_timestamp(
        _first_value(row, "last_updated", "LastUpdatedTime", "published_at", "StartTime")
    )
    if not alert_id or not alert_id.isdigit() or not title or not published_at:
        raise NewsParserError(
            f"WSDOT alert row {index} is missing numeric ID, title, or timestamp."
        )
    source_url = _wsdot_source_url(source, alert_id or str(index), row)
    route_tokens = _wsdot_route_tokens(row)
    facility_tokens = _wsdot_facility_tokens(source, row)
    impact = _wsdot_impact(row)
    start_location = _wsdot_roadway_location(row.get("StartRoadwayLocation"))
    end_location = _wsdot_roadway_location(row.get("EndRoadwayLocation"))
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
        "event_category": bounded_text(row.get("EventCategory"), max_chars=100),
        "event_status": bounded_text(row.get("EventStatus"), max_chars=64),
        "start_time": _wsdot_timestamp(row.get("StartTime")),
        "end_time": _wsdot_timestamp(row.get("EndTime")),
        "start_roadway_location": start_location,
        "end_roadway_location": end_location,
        "priority": bounded_text(_first_value(row, "priority", "Priority"), max_chars=64),
        "county": bounded_text(_first_value(row, "county", "County"), max_chars=120),
        "region": bounded_text(_first_value(row, "region", "Region"), max_chars=120),
        "published_at": published_at,
        "source_url": source_url,
        "source_url_basis": (
            "payload_url" if _first_value(row, "url", "Url", "link", "Link")
            else "official_rss_refnum_link"
        ),
        "ranking": {
            "route_token_count": len(route_tokens),
            "facility_token_count": len(facility_tokens),
            "impact_weight": impact["weight"],
            "public_impact_score": (
                0 if impact["label"] == "resolved"
                else min(60, impact["weight"] + len(route_tokens) * 6)
            ),
        },
        "filter": _wsdot_filter_evidence(source, row),
    }
    return item


_WSDOT_DOTNET_DATE_RE = re.compile(r"^/Date\((-?\d{1,15})(?:[+-]\d{4})?\)/$")


def _wsdot_timestamp(value: Any) -> str | None:
    normalized = normalize_timestamp(value)
    if normalized:
        return normalized
    match = _WSDOT_DOTNET_DATE_RE.fullmatch(str(value or ""))
    if match is None:
        return None
    try:
        return datetime.fromtimestamp(int(match.group(1)) / 1000, tz=UTC).isoformat(
            timespec="seconds"
        )
    except (ValueError, OverflowError, OSError):
        return None


def _wsdot_roadway_location(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    milepost = _usgs_number(value.get("MilePost"))
    return {
        "description": bounded_text(value.get("Description"), max_chars=120),
        "direction": bounded_text(value.get("Direction"), max_chars=40),
        "milepost": milepost if milepost is not None and 0 <= milepost <= 1000 else None,
        "road_name": bounded_text(value.get("RoadName"), max_chars=80),
    }


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
    for key in ("StartRoadwayLocation", "EndRoadwayLocation"):
        location = row.get(key)
        if isinstance(location, dict):
            values.extend([location.get("RoadName"), location.get("Description")])
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
    if str(row.get("EventStatus") or "").strip().lower() == "closed":
        return {"label": "resolved", "weight": 0}
    text = _wsdot_row_text(row).lower()
    priority = str(row.get("Priority") or row.get("priority") or "").lower()
    if any(word in text for word in ("closed", "closure", "blocked all lanes")):
        return {"label": "closure", "weight": 32}
    if priority == "highest":
        return {"label": "highest_impact", "weight": 30}
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
    return normalize_url(
        f"https://www.wsdot.wa.gov/traffic/trafficalerts/default.aspx?refnum={quote(str(row_key))}"
    )


def _wsdot_row_text(row: dict[str, Any]) -> str:
    values = [
        row.get(key)
        for key in (
            "headline",
            "Headline",
            "HeadlineDescription",
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
            "EventCategory",
        )
    ]
    for key in ("StartRoadwayLocation", "EndRoadwayLocation"):
        location = row.get(key)
        if isinstance(location, dict):
            values.extend([location.get("RoadName"), location.get("Description")])
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
    ugc = _string_list(geocode.get("UGC"), max_chars=32)
    same_codes = _string_list(geocode.get("SAME"), max_chars=16)
    county_codes = [code for code in same_codes if re.fullmatch(r"0?53\d{3}", code)]
    county_area_labels = [
        segment.strip() for segment in area_desc.split(";")
        if re.search(r"\bCounty\b", segment, re.IGNORECASE)
    ]
    affected_states = sorted({
        match.group(1)
        for value in [*affected_zones, *ugc]
        for match in _NWS_US_ZONE_RE.finditer(value.upper())
    } | ({"WA"} if county_codes else set()))
    instruction = bounded_text(properties.get("instruction"), max_chars=500)
    instruction_url = _nws_official_instruction_url(
        properties.get("instructionUrl") or properties.get("web")
    )
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
        "county_codes": county_codes,
        "county_area_labels": county_area_labels,
        "affected_states": affected_states,
        "geography_basis": (
            "official_ugc_zone_ids" if any(
                _NWS_US_ZONE_RE.search(value.upper()) for value in [*affected_zones, *ugc]
            ) else "official_same_county_codes" if county_codes else "area_description_only"
        ),
        "instruction": instruction,
        "instruction_url": instruction_url,
        "source_url": item["url"],
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


def _nws_official_instruction_url(value: Any) -> str | None:
    if not value:
        return None
    try:
        parts = urlsplit(str(value).strip())
    except ValueError:
        return None
    host = (parts.hostname or "").lower()
    if parts.scheme.lower() != "https" or not (
        host == "weather.gov" or host.endswith(".weather.gov")
    ):
        return None
    return normalize_url(value)


def _nws_alert_matches_scope(source: dict[str, Any], properties: dict[str, Any]) -> bool:
    scope = str(source.get("scope") or "").upper()
    if scope == "REGIONAL":
        affected_zones = _string_list(properties.get("affectedZones"), max_chars=240)
        geocode = properties.get("geocode") if isinstance(properties.get("geocode"), dict) else {}
        ugc = _string_list(geocode.get("UGC"), max_chars=32)
        same_codes = _string_list(geocode.get("SAME"), max_chars=16)
        zone_text = " ".join([*affected_zones, *ugc]).upper()
        in_washington = bool(re.search(r"\bWA[ZC]\d{3}\b", zone_text)) or (
            "washington" in str(properties.get("areaDesc") or "").lower()
        ) or any(re.fullmatch(r"0?53\d{3}", code) for code in same_codes)
        if not in_washington:
            return False
        filters = _nws_filter_evidence(source, properties)
        if not any((source.get("zone_ids"), source.get("county_codes"),
                    source.get("county_keywords"), source.get("area_keywords"))):
            return True
        return bool(
            filters["matched_zone_ids"] or filters["matched_county_codes"]
            or filters["matched_county_keywords"] or filters["matched_keywords"]
        )
    if scope != "LOCAL":
        return True
    evidence = _nws_filter_evidence(source, properties)
    return bool(evidence["matched_keywords"] or evidence["matched_zone_ids"])


def _nws_filter_evidence(source: dict[str, Any], properties: dict[str, Any]) -> dict[str, Any]:
    regional = str(source.get("scope") or "").upper() == "REGIONAL"
    area_keywords = _configured_texts(
        source.get("area_keywords"),
        default=[] if regional else ["Seattle", "King County", "Puget Sound"],
    )
    zone_ids = _configured_texts(source.get("zone_ids"), default=[])
    county_codes = _configured_texts(source.get("county_codes"), default=[])
    county_keywords = _configured_texts(source.get("county_keywords"), default=[])
    area_desc = str(properties.get("areaDesc") or "")
    affected_zones = _string_list(properties.get("affectedZones"), max_chars=240)
    geocode = properties.get("geocode") if isinstance(properties.get("geocode"), dict) else {}
    same_codes = _string_list(geocode.get("SAME"), max_chars=16)
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
        "county_codes": county_codes,
        "county_keywords": county_keywords,
        "matched_keywords": matched_keywords,
        "matched_county_codes": [code for code in county_codes if code in same_codes],
        "matched_county_keywords": [
            county for county in county_keywords if county.lower() in area_lower
        ],
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
        if not signal["public_impact"]:
            route_tokens = []
        matched_neighborhoods = _matched_keywords(text, neighborhoods)
        privacy = _spd_privacy_decision(
            text=text,
            preliminary_report=signal["preliminary"],
            public_impact=signal["public_impact"],
            neighborhoods=matched_neighborhoods,
            route_tokens=route_tokens,
        )
        if privacy["exact_location_suppressed"]:
            item["title"] = f"SPD {signal['incident_label']} near {privacy['display_location']}"
            item["description"] = (
                "SPD reports a private incident. Exact location and narrative are withheld "
                "by LOCAL privacy rules."
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
                "low_public_value_private": privacy["low_public_value_private"],
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
            "low_public_value_private": privacy["low_public_value_private"],
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
    suppress_exact = not public_impact
    if low_acuity and suppress_exact:
        reason = "Low-acuity or private SPD report without public-impact justification."
    elif suppress_exact:
        reason = "Minor SPD report without public-impact justification."
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
        "low_public_value_private": suppress_exact,
        "public_impact_justified": public_impact,
        "preliminary_report": preliminary_report,
        "overdose_related": overdose_related,
        "privacy_category": (
            "overdose" if overdose_related else "low_acuity" if low_acuity
            else "minor_police" if suppress_exact else "none"
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
