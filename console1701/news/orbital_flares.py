"""Bounded fixture parser for SWPC's GOES X-ray flare event list."""

from __future__ import annotations

import json
import math
import re
from typing import Any
from urllib.parse import urlencode

from console1701.news.normalize import normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

FLARES_URL = "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json"
_CLASS = re.compile(r"^([MX])(\d{1,2}(?:\.\d{1,2})?)$")


def _time(value: Any) -> str | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    return normalize_timestamp(value)


def parse_swpc_xray_flares_json(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if (source.get("scope") != "ORBITAL" or source.get("id") != "swpc_xray_flux_summary"
            or source.get("kind") != "api_json"
            or source.get("official_url", FLARES_URL) != FLARES_URL):
        raise NewsParserError("SWPC flare parser requires its exact ORBITAL product")
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("SWPC flare metadata exceeds 64 KiB")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError("Malformed SWPC flare JSON") from exc
    if not isinstance(payload, list) or len(payload) > 200:
        raise NewsParserError("SWPC flare metadata needs a bounded array")
    items: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()
    for index, row in enumerate(payload):
        if not isinstance(row, dict):
            raise NewsParserError("SWPC flare row must be an object")
        raw_class = str(row.get("max_class") or "").upper()
        match = _CLASS.fullmatch(raw_class)
        if match is None:
            if raw_class.startswith(("M", "X")):
                raise NewsParserError(f"SWPC flare row {index} has invalid peak class")
            # B/C-class observations and source rows without a peak class are background.
            continue
        class_value = float(match.group(2))
        if class_value < 1:
            continue
        satellite = row.get("satellite")
        begin = _time(row.get("begin_time"))
        peak = _time(row.get("max_time"))
        end = _time(row.get("end_time")) if row.get("end_time") is not None else None
        flux = row.get("max_xrlong")
        if (type(satellite) is not int or not 1 <= satellite <= 99
                or not begin or not peak or peak < begin
                or (row.get("end_time") is not None and not end)
                or (end and end < peak)
                or isinstance(flux, bool) or not isinstance(flux, (int, float))
                or not math.isfinite(flux) or not 0 < flux <= 0.01):
            raise NewsParserError(f"SWPC flare row {index} has invalid event metadata")
        key = satellite, begin
        if key in seen:
            raise NewsParserError("SWPC flare metadata has a duplicate event identity")
        seen.add(key)
        query = urlencode({"begin_time": begin, "satellite": satellite})
        item = _normalize_item(source, {
            "title": f"SWPC GOES {raw_class} X-ray flare observed",
            "url": f"{FLARES_URL}?{query}",
            "description": "GOES X-ray flare measurement; Earth impact is not established.",
            "published_at": peak,
            "tags": ["official", "swpc", "solar-flare", "measurement"],
        }, index=index)
        item["evidence"]["swpc_xray_flare"] = {
            "begin_time": begin, "max_time": peak, "end_time": end,
            "max_class": raw_class, "max_xrlong_watts_m2": flux,
            "satellite": satellite, "source_url": FLARES_URL,
            "link_note": "Query parameters are local identity, not a source deep link.",
            "earth_impact_inferred": False, "operational_impact_inferred": False,
        }
        item["evidence"]["orbital_identity"] = {
            "event_type": "solar_flare", "object_id": f"goes:{satellite}:{begin}",
            "flare_class": raw_class,
        }
        item["evidence"]["orbital_safety"] = {"official_alert": False}
        items.append(item)
    return items
