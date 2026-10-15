"""Bounded fixture-first JPL CNEOS data parsers."""

from __future__ import annotations

import json
from datetime import datetime
from math import isfinite
from typing import Any
from urllib.parse import urlencode

from console1701.news.normalize import bounded_text

CAD_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
AU_PER_LUNAR_DISTANCE = 0.00256955529
_CAD_REQUIRED_FIELDS = {"des", "cd", "dist", "v_rel"}


def _finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def parse_jpl_cad_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Preserve approach geometry without making an impact-risk assertion."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    if str(source.get("scope") or "").upper() != "ORBITAL":
        raise NewsParserError("JPL CAD parser requires ORBITAL scope")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed JPL CAD JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise NewsParserError("JPL CAD JSON must be an object")
    signature = payload.get("signature")
    if not isinstance(signature, dict) or str(signature.get("version")) != "1.5":
        raise NewsParserError("JPL CAD API signature version must be 1.5")
    if payload.get("count") == 0:
        return []
    fields = payload.get("fields")
    data = payload.get("data")
    if (
        not isinstance(fields, list) or not all(isinstance(field, str) for field in fields)
        or not _CAD_REQUIRED_FIELDS <= set(fields)
    ):
        raise NewsParserError("JPL CAD JSON has missing required field names")
    if not isinstance(data, list) or len(data) > 500:
        raise NewsParserError("JPL CAD JSON data must be a bounded array")
    max_ld = float(source.get("max_lunar_distance", 5.0))
    min_diameter = float(source.get("min_diameter_km", 0.05))
    items: list[dict[str, Any]] = []
    for index, values in enumerate(data):
        if not isinstance(values, list) or len(values) != len(fields):
            continue
        row = dict(zip(fields, values, strict=True))
        if row.get("body") not in (None, "Earth"):
            continue
        designation = bounded_text(row.get("des"), max_chars=80)
        approach_tdb = bounded_text(row.get("cd"), max_chars=40)
        try:
            approach_date = datetime.strptime(approach_tdb or "", "%Y-%b-%d %H:%M").date()
        except ValueError:
            continue
        distance_au = _finite_float(row.get("dist"))
        velocity = _finite_float(row.get("v_rel"))
        if (
            not designation or not approach_tdb or distance_au is None
            or velocity is None or distance_au <= 0 or velocity < 0
        ):
            continue
        distance_ld = distance_au / AU_PER_LUNAR_DISTANCE
        diameter = _finite_float(row.get("diameter"))
        if distance_ld > max_ld or (
            distance_ld > 1 and diameter is not None and diameter < min_diameter
        ):
            continue
        # Unknown diameter is retained only inside one lunar distance.
        if distance_ld > 1 and diameter is None:
            continue
        query = urlencode({
            "des": designation, "date-min": approach_date.isoformat(),
            "date-max": approach_date.isoformat(),
        })
        name = bounded_text(row.get("fullname") or designation, max_chars=100)
        item = _normalize_item(source, {
            "title": f"JPL close approach: {name}",
            "url": f"{CAD_URL}?{query}",
            "description": (
                f"Predicted Earth close approach at {distance_ld:.2f} lunar distances. "
                "This feed alone does not establish impact risk."
            ),
        }, index=index)
        item["evidence"]["jpl_close_approach"] = {
            "designation": designation,
            "full_name": name,
            "orbit_id": row.get("orbit_id"),
            "approach_time_tdb": approach_tdb,
            "time_scale": "TDB",
            "distance_au": distance_au,
            "distance_min_au": _finite_float(row.get("dist_min")),
            "distance_max_au": _finite_float(row.get("dist_max")),
            "distance_lunar": round(distance_ld, 3),
            "relative_velocity_km_s": velocity,
            "diameter_km": diameter,
            "diameter_sigma_km": _finite_float(row.get("diameter_sigma")),
            "absolute_magnitude_h": _finite_float(row.get("h")),
            "source_url": CAD_URL,
            "api_version": "1.5",
            "risk_framing": "close_approach_not_impact_prediction",
            "threshold_lunar_distance": max_ld,
            "threshold_diameter_km": min_diameter,
        }
        item["evidence"]["orbital_identity"] = {
            "event_type": "neo_close_approach",
            "object_id": designation,
        }
        items.append(item)
    return items
