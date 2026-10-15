"""Bounded fixture-first JPL CNEOS data parsers."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from math import isfinite
from typing import Any
from urllib.parse import urlencode

from console1701.news.normalize import bounded_text

CAD_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
FIREBALL_URL = "https://ssd-api.jpl.nasa.gov/fireball.api"
AU_PER_LUNAR_DISTANCE = 0.00256955529
_CAD_REQUIRED_FIELDS = {"des", "cd", "dist", "v_rel"}
_FIREBALL_REQUIRED_FIELDS = {"date", "energy", "impact-e"}


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


def parse_jpl_fireball_json(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    """Retain recent, energetic peak-brightness records with source units intact."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    if str(source.get("scope") or "").upper() != "ORBITAL":
        raise NewsParserError("JPL fireball parser requires ORBITAL scope")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed JPL fireball JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise NewsParserError("JPL fireball JSON must be an object")
    signature = payload.get("signature")
    if not isinstance(signature, dict) or str(signature.get("version")) != "1.2":
        raise NewsParserError("JPL fireball API signature version must be 1.2")
    if payload.get("count") == 0:
        return []
    fields = payload.get("fields")
    data = payload.get("data")
    if (
        not isinstance(fields, list) or not all(isinstance(field, str) for field in fields)
        or not _FIREBALL_REQUIRED_FIELDS <= set(fields)
    ):
        raise NewsParserError("JPL fireball JSON has missing required field names")
    if not isinstance(data, list) or len(data) > 500:
        raise NewsParserError("JPL fireball JSON data must be a bounded array")
    minimum = float(source.get("min_impact_kt", 0.1))
    max_age = int(source.get("max_age_days", 30))
    now = datetime.now(UTC)
    items: list[dict[str, Any]] = []
    for index, values in enumerate(data):
        if not isinstance(values, list) or len(values) != len(fields):
            continue
        row = dict(zip(fields, values, strict=True))
        try:
            event_at = datetime.strptime(str(row.get("date") or ""), "%Y-%m-%d %H:%M:%S")
            event_at = event_at.replace(tzinfo=UTC)
        except ValueError:
            continue
        impact_kt = _finite_float(row.get("impact-e"))
        radiated = _finite_float(row.get("energy"))
        if (
            impact_kt is None or radiated is None or impact_kt < minimum
            or radiated < 0 or event_at < now - timedelta(days=max_age)
            or event_at > now + timedelta(hours=1)
        ):
            continue
        latitude = _finite_float(row.get("lat"))
        longitude = _finite_float(row.get("lon"))
        latitude_dir = row.get("lat-dir")
        longitude_dir = row.get("lon-dir")
        if latitude_dir not in {"N", "S"} or longitude_dir not in {"E", "W"}:
            latitude = longitude = None
        if latitude is not None and longitude is not None:
            latitude = abs(latitude) * (-1 if latitude_dir == "S" else 1)
            longitude = abs(longitude) * (-1 if longitude_dir == "W" else 1)
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                latitude = longitude = None
        velocity = [_finite_float(row.get(axis)) for axis in ("vx", "vy", "vz")]
        speed = (
            sum(component**2 for component in velocity) ** 0.5
            if all(component is not None for component in velocity) else None
        )
        event_iso = event_at.isoformat(timespec="seconds")
        api_time = event_at.strftime("%Y-%m-%dT%H:%M:%S")
        query = urlencode({"date-min": api_time, "date-max": api_time})
        item = _normalize_item(source, {
            "title": f"JPL fireball record: {event_at:%Y-%m-%d %H:%M} UTC",
            "url": f"{FIREBALL_URL}?{query}",
            "description": (
                f"Reported peak brightness; estimated impact energy {impact_kt:g} kt. "
                "No ground impact or damage is implied."
            ),
            "published_at": event_iso,
        }, index=index)
        item["evidence"]["jpl_fireball"] = {
            "event_time_utc": event_iso,
            "latitude": latitude,
            "longitude": longitude,
            "altitude_km": _finite_float(row.get("alt")),
            "radiated_energy_1e10_joules": radiated,
            "estimated_impact_energy_kt": impact_kt,
            "velocity_components_km_s": dict(zip(("vx", "vy", "vz"), velocity, strict=True)),
            "derived_speed_km_s": round(speed, 3) if speed is not None else None,
            "source_url": FIREBALL_URL,
            "api_version": "1.2",
            "location_basis": "source_reported_peak_brightness"
            if latitude is not None else "not_reported",
            "min_impact_kt": minimum,
            "max_age_days": max_age,
        }
        item["evidence"]["orbital_identity"] = {
            "event_type": "fireball",
            "object_id": event_iso,
        }
        items.append(item)
    return items
