"""Conservative ORBITAL event matching using only stored, source-backed facts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "the",
    "to", "with", "nasa", "esa", "swpc", "space", "new", "update", "latest",
}
MATCH_WINDOW_HOURS = 96


def _normalized(value: Any) -> str:
    return " ".join(_TOKEN_RE.findall(str(value or "").lower()))


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def orbital_independent_family(value: Any) -> str:
    family = _normalized(value).replace(" ", "_")
    if family in {"nasa", "jpl"} or family.startswith(("nasa_", "jpl_")):
        return "nasa"
    if family == "esa" or family.startswith("esa_"):
        return "esa"
    return family or "unknown"


def orbital_item_signature(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence") or {}
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
        "reentry_object_id", "safe_satellite_id",
    ):
        value = _normalized(identity.get(field))
        if value:
            identifiers.add(f"{field}:{value}")
    cad = evidence.get("jpl_close_approach") or {}
    designation = _normalized(cad.get("designation"))
    approach = _normalized(cad.get("approach_time_tdb"))
    if designation and approach:
        identifiers.add(f"cad:{designation}:{approach}")
    fireball = evidence.get("jpl_fireball") or {}
    fireball_time = _normalized(fireball.get("event_time_utc"))
    if fireball_time:
        identifiers.add(f"fireball:{fireball_time}")
    context = {
        field: _normalized(identity.get(field)) for field in (
            "mission_name", "launch_vehicle", "payload", "provider", "neo_designation",
            "reentry_object", "noaa_scale", "kp_window", "fireball_location",
        )
    }
    swpc = evidence.get("swpc_alert") or {}
    swpc_scale = evidence.get("swpc_noaa_scale") or {}
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
            (evidence.get("source") or {}).get("source_family")
        ),
        "source_key": str((evidence.get("source") or {}).get("source_key") or ""),
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
    }


def orbital_match_basis(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    if not left["published_at"] or not right["published_at"]:
        return []
    hours = abs((left["published_at"] - right["published_at"]).total_seconds()) / 3600
    if hours > MATCH_WINDOW_HOURS:
        return []
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
    if not left["event_type"] or left["event_type"] != right["event_type"]:
        return []
    if left["identifiers"] & right["identifiers"]:
        return ["event_type", "shared_event_id", "time_window"]
    if left["family"] == "unknown" or left["family"] == right["family"]:
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
