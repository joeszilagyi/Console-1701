"""Conservative ORBITAL event matching using only stored, source-backed facts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from math import isfinite
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "the",
    "to", "with", "nasa", "esa", "swpc", "space", "new", "update", "latest",
}
MATCH_WINDOW_HOURS = 96
_EXCLUSIVE_EVENT_ID_FIELDS = (
    "launch_id", "launch_library_event_id", "cneos_event_id", "mpc_designation",
    "reentry_object_id", "safe_satellite_id",
)


def _normalized(value: Any) -> str:
    return " ".join(_TOKEN_RE.findall(str(value or "").lower()))


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


def orbital_independent_family(value: Any) -> str:
    family = _normalized(value).replace(" ", "_")
    if family == "spaceflight_news_api":
        # SNAPI aggregates publishers and imports Launch Library links. Its
        # article metadata must not count as another independent observation.
        return "unknown"
    if family in {"nasa", "jpl"} or family.startswith(("nasa_", "jpl_")):
        return "nasa"
    if family == "esa" or family.startswith("esa_"):
        return "esa"
    return family or "unknown"


def orbital_item_signature(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence") or {}
    source = evidence.get("source") or {}
    source_family = _normalized(source.get("source_family")).replace(" ", "_")
    identity = evidence.get("orbital_identity") or {}
    event_type = _normalized(identity.get("event_type")).replace(" ", "_")
    identifiers: set[str] = set()
    # The object's identity is scoped by event type. A designation alone is not
    # enough to merge distinct close approaches on different dates.
    object_id = _normalized(identity.get("object_id"))
    if object_id and event_type and event_type != "neo_close_approach":
        identifiers.add(f"{event_type}:{object_id}")
    for field in (
        "product_id", "launch_id", "cneos_event_id", "mpc_designation",
        "reentry_object_id", "safe_satellite_id", "launch_library_event_id",
    ):
        value = _normalized(identity.get(field))
        if value:
            identifiers.add(f"{field}:{value}")
    cad = (evidence.get("jpl_close_approach") or {}) if source_family == "jpl_cneos" else {}
    designation = _normalized(cad.get("designation"))
    approach = _normalized(cad.get("approach_time_tdb"))
    if designation and approach:
        identifiers.add(f"cad:{designation}:{approach}")
    fireball = (evidence.get("jpl_fireball") or {}) if source_family == "jpl_cneos" else {}
    fireball_at = _time(fireball.get("event_time_utc"))
    fireball_location_identity = None
    fireball_energy_identity = None
    if event_type == "fireball" and fireball_at:
        latitude = _number(fireball.get("latitude"))
        longitude = _number(fireball.get("longitude"))
        if (latitude is not None and longitude is not None
                and -90 <= latitude <= 90 and -180 <= longitude <= 180):
            fireball_location_identity = (
                f"{fireball_at.isoformat()}:geo:{latitude:g}:{longitude:g}"
            )
        radiated = _number(fireball.get("radiated_energy_1e10_joules"))
        impact = _number(fireball.get("estimated_impact_energy_kt"))
        if radiated is not None and impact is not None:
            fireball_energy_identity = (
                f"{fireball_at.isoformat()}:energy:{radiated:g}:{impact:g}"
            )
        for value in (fireball_location_identity, fireball_energy_identity):
            if value:
                identifiers.add(f"fireball:{value}")
    context = {
        field: _normalized(identity.get(field)) for field in (
            "mission_name", "launch_vehicle", "payload", "provider", "neo_designation",
            "reentry_object", "noaa_scale", "kp_window", "fireball_location", "iss_action",
        )
    }
    swpc = (evidence.get("swpc_alert") or {}) if source_family == "swpc" else {}
    swpc_scale = (evidence.get("swpc_noaa_scale") or {}) if source_family == "swpc" else {}
    swpc_kp = (evidence.get("swpc_k_index") or {}) if source_family == "swpc" else {}
    launch_library = (
        evidence.get("launch_library") or {}
    ) if source_family == "launch_library" else {}
    if swpc.get("noaa_scale"):
        context["noaa_scale"] = _normalized(swpc["noaa_scale"])
    if swpc_scale.get("scale"):
        context["noaa_scale"] = _normalized(swpc_scale["scale"])
    return {
        "id": int(item["id"]),
        "event_type": event_type,
        "identifiers": identifiers,
        "context": {key: value for key, value in context.items() if value},
        "tokens": set(_TOKEN_RE.findall(str(item.get("title") or "").lower())) - _STOPWORDS,
        "published_at": _time(item.get("source_published_at") or item.get("first_seen_at")),
        "family": orbital_independent_family(
            source_family
        ),
        "source_key": str(source.get("source_key") or ""),
        "swpc_alert": {
            "kind": swpc.get("message_type"),
            "cancelled": swpc.get("cancelled") is True,
            "valid_from": _time(swpc.get("valid_from")),
            "valid_until": _time(swpc.get("valid_until")),
        } if swpc else {},
        "swpc_scale": {
            "period_kind": swpc_scale.get("period_kind"),
            "observed_at": _time(swpc_scale.get("timestamp")),
        } if swpc_scale else {},
        "swpc_kp": {
            "source_kind": swpc_kp.get("source_kind"),
            "observation_type": swpc_kp.get("observation_type"),
            "observed_at": _time(swpc_kp.get("observed_at")),
        } if swpc_kp else {},
        "launch_at": _time(launch_library.get("net")),
        "ll_event_at": _time(launch_library.get("event_time")),
        "fireball_location_identity": fireball_location_identity,
        "fireball_energy_identity": fireball_energy_identity,
    }


def orbital_match_basis(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    if not left["published_at"] or not right["published_at"]:
        return []
    hours = abs((left["published_at"] - right["published_at"]).total_seconds()) / 3600
    same_mpec_notice = False
    if left["event_type"] == right["event_type"] == "minor_planet_notice":
        # The MPEC designation names an object, while each circular has its
        # own publication ID. A corrected title can retain one circular ID.
        prefix = "minor_planet_notice:"
        left_notices = {value for value in left["identifiers"] if value.startswith(prefix)}
        right_notices = {value for value in right["identifiers"] if value.startswith(prefix)}
        if left_notices and right_notices:
            if not left_notices & right_notices:
                return []
            same_mpec_notice = True
    # Two reports can share a mission name and headline while referring to
    # distinct launches, objects, or Launch Library events. Explicit IDs from
    # the same namespace take precedence over broad context convergence.
    for field in _EXCLUSIVE_EVENT_ID_FIELDS:
        if field == "mpc_designation" and same_mpec_notice:
            continue
        prefix = f"{field}:"
        left_ids = {value for value in left["identifiers"] if value.startswith(prefix)}
        right_ids = {value for value in right["identifiers"] if value.startswith(prefix)}
        if left_ids and right_ids and not left_ids & right_ids:
            return []
    shared_ids = left["identifiers"] & right["identifiers"]
    shared_launch_id = any(value.startswith("launch_id:") for value in shared_ids)
    shared_ll_event_id = any(
        value.startswith("launch_library_event_id:") for value in shared_ids
    )
    near_source_launch = bool(shared_launch_id and (
        left["launch_at"] and abs(
            (left["launch_at"] - right["published_at"]).total_seconds()
        ) <= MATCH_WINDOW_HOURS * 3600
        or right["launch_at"] and abs(
            (right["launch_at"] - left["published_at"]).total_seconds()
        ) <= MATCH_WINDOW_HOURS * 3600
    ))
    ll_event, ll_article = (
        (left, right) if left["source_key"] == "launch_library_events" else (right, left)
    )
    near_source_event = bool(
        shared_ll_event_id
        and ll_event["source_key"] == "launch_library_events"
        and ll_article["source_key"] == "spaceflight_news_articles"
        and ll_event["event_type"] in {"iss_update", "mission_update"}
        and ll_article["event_type"] == "mission_update"
        and ll_event["ll_event_at"]
        and abs((ll_event["ll_event_at"] - ll_article["published_at"]).total_seconds())
        <= MATCH_WINDOW_HOURS * 3600
    )
    if hours > MATCH_WINDOW_HOURS and not near_source_launch and not near_source_event:
        return []
    if left["event_type"] == right["event_type"] == "fireball":
        left_location = left["fireball_location_identity"]
        right_location = right["fireball_location_identity"]
        if left_location and right_location:
            return ["fireball_time_location_or_energy", "time_window"] if (
                left_location == right_location
            ) else []
        left_energy = left["fireball_energy_identity"]
        right_energy = right["fireball_energy_identity"]
        return ["fireball_time_energy_missing_location", "time_window"] if (
            left_energy and left_energy == right_energy
        ) else []
    if near_source_event:
        return ["linked_launch_library_event_id", "event_window"]
    if {left["event_type"], right["event_type"]} == {
        "space_weather_alert", "space_weather_scale",
    }:
        alert, scale = (left, right) if left["event_type"] == "space_weather_alert" else (
            right, left
        )
        valid = alert["swpc_alert"]
        observed = scale["swpc_scale"]
        if (alert["family"] == scale["family"] == "swpc"
                and valid.get("kind") in {"ALERT", "WARNING", "EXTENDED WARNING"}
                and not valid.get("cancelled")
                and observed.get("period_kind") == "current"
                and alert["context"].get("noaa_scale")
                == scale["context"].get("noaa_scale")
                and valid.get("valid_from") and valid.get("valid_until")
                and observed.get("observed_at")
                and valid["valid_from"] <= observed["observed_at"] <= valid["valid_until"]):
            return ["same_noaa_scale", "alert_valid_window", "current_scale_observation"]
        return []
    if {left["event_type"], right["event_type"]} == {
        "space_weather_alert", "geomagnetic_k_index",
    }:
        alert, kp = (left, right) if left["event_type"] == "space_weather_alert" else (
            right, left
        )
        valid = alert["swpc_alert"]
        observation = kp["swpc_kp"]
        scale = alert["context"].get("noaa_scale")
        if (alert["family"] == kp["family"] == "swpc"
                and valid.get("kind") in {"ALERT", "WARNING", "EXTENDED WARNING"}
                and not valid.get("cancelled")
                and scale and scale.startswith("g")
                and scale == kp["context"].get("noaa_scale")
                and observation.get("source_kind") == "planetary"
                and observation.get("observation_type") == "observed_3h_summary"
                and valid.get("valid_from") and valid.get("valid_until")
                and observation.get("observed_at")
                and valid["valid_from"] <= observation["observed_at"] <= valid["valid_until"]):
            return ["same_noaa_geomagnetic_scale", "alert_valid_window",
                    "planetary_kp_observation"]
        return []
    if {left["event_type"], right["event_type"]} == {
        "space_weather_scale", "geomagnetic_k_index",
    }:
        scale, kp = (left, right) if left["event_type"] == "space_weather_scale" else (
            right, left
        )
        scale_at = scale["swpc_scale"].get("observed_at")
        kp_at = kp["swpc_kp"].get("observed_at")
        scale_level = scale["context"].get("noaa_scale")
        if (scale["family"] == kp["family"] == "swpc"
                and scale["swpc_scale"].get("period_kind") == "current"
                and kp["swpc_kp"].get("source_kind") == "planetary"
                and kp["swpc_kp"].get("observation_type") == "observed_3h_summary"
                and scale_level and scale_level.startswith("g")
                and scale_level == kp["context"].get("noaa_scale")
                and scale_at and kp_at
                and abs((scale_at - kp_at).total_seconds()) <= 3 * 3600):
            return ["same_noaa_geomagnetic_scale", "current_scale_observation",
                    "nearby_planetary_kp_3h_observation"]
        return []
    if not left["event_type"] or left["event_type"] != right["event_type"]:
        return []
    if shared_ids:
        return [
            "event_type", "shared_event_id",
            "launch_window" if hours > MATCH_WINDOW_HOURS else "time_window",
        ]
    if left["family"] == "unknown" or left["family"] == right["family"]:
        return []
    if left["event_type"] == "iss_update" and (
        not left["context"].get("iss_action")
        or left["context"].get("iss_action") != right["context"].get("iss_action")
    ):
        return []
    shared_context = [
        field for field, value in left["context"].items()
        if value == right["context"].get(field)
    ]
    shared_tokens = left["tokens"] & right["tokens"]
    if len(shared_tokens) < (3 if shared_context else 4):
        return []
    return [
        "event_type", *shared_context, "title_tokens", "time_window", "independent_family",
    ]


def correlate_orbital_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return complete-link groups; a broad headline cannot bridge separate events."""
    signatures = [orbital_item_signature(item) for item in items if item.get("scope") == "ORBITAL"]
    parents = list(range(len(signatures)))
    members = {index: [index] for index in range(len(signatures))}

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    matches: list[dict[str, Any]] = []
    for left in range(len(signatures)):
        for right in range(left + 1, len(signatures)):
            basis = orbital_match_basis(signatures[left], signatures[right])
            if not basis:
                continue
            left_root, right_root = root(left), root(right)
            if left_root != right_root:
                if not all(
                    orbital_match_basis(signatures[a], signatures[b])
                    for a in members[left_root] for b in members[right_root]
                ):
                    continue
                parents[right_root] = left_root
                members[left_root].extend(members.pop(right_root))
            matches.append({
                "item_ids": [signatures[left]["id"], signatures[right]["id"]],
                "basis": basis,
                "shared_tokens": sorted(signatures[left]["tokens"] & signatures[right]["tokens"]),
            })

    groups: dict[int, list[dict[str, Any]]] = {}
    for index, signature in enumerate(signatures):
        groups.setdefault(root(index), []).append(signature)
    result = []
    for group_members in groups.values():
        ids = sorted(member["id"] for member in group_members)
        families = sorted({
            member["family"] for member in group_members if member["family"] != "unknown"
        })
        result.append({
            "event_key": f"orbital:item:{ids[0]}",
            "item_ids": ids,
            "source_keys": sorted({
                member["source_key"] for member in group_members if member["source_key"]
            }),
            "families": families,
            "event_types": sorted({member["event_type"] for member in group_members}),
            "identifiers": sorted(set().union(*(
                member["identifiers"] for member in group_members
            ))),
            "matches": [entry for entry in matches if set(entry["item_ids"]) <= set(ids)],
            "corroborated": len(families) >= 2 and any(
                "independent_family" in entry["basis"]
                for entry in matches if set(entry["item_ids"]) <= set(ids)
            ),
        })
    return sorted(result, key=lambda group: group["item_ids"][0])
