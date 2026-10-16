"""Conservative REGIONAL correlation using stored, source-backed fields only."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

_WORDS = re.compile(r"[a-z0-9]+")
_STOP = {"a", "an", "and", "at", "by", "for", "from", "in", "of", "on",
         "the", "to", "with", "alert", "update", "regional", "washington"}
_GEO_FIELDS = (
    "county", "city", "route", "mountain_pass", "ferry_route", "airport", "port",
    "river_basin", "weather_zone", "fire_incident", "volcano", "seismic_region",
    "aqi_station", "public_health_jurisdiction",
)
MATCH_WINDOW_HOURS = 48
_WASHINGTON_ZONE = ZoneInfo("America/Los_Angeles")


def _value(value: Any) -> str:
    return " ".join(_WORDS.findall(str(value or "").casefold()))


def _values(value: Any) -> set[str]:
    entries = value if isinstance(value, list) else [value]
    return {_value(entry) for entry in entries[:40] if _value(entry)}


def _county_values(value: Any) -> set[str]:
    return {county.removesuffix(" county") for county in _values(value)
            if county.removesuffix(" county")}


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def regional_item_signature(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence") or {}
    event = evidence.get("regional_event") or {}
    geography = event.get("geography") or {}
    source = evidence.get("source") or {}
    identity = evidence.get("regional_identity") or {}
    fields: dict[str, set[str]] = {field: set() for field in _GEO_FIELDS}
    fire_start_date = None
    # Parser-derived geography has a known provenance. Optional future identity fields
    # are admitted only for official, high-confidence, geographically matched items.
    if (event.get("confidence") == "high" and geography.get("matched")
            and source.get("official_status") == "official"):
        for field in _GEO_FIELDS:
            fields[field] = (
                _county_values(identity.get(field)) if field == "county"
                else _values(identity.get(field))
            )
        fields["county"].update(_county_values(geography.get("county")))
        fields["route"].update(_values(geography.get("routes")))
        fields["weather_zone"].update(_values(geography.get("zone_ids")))
        # Facility names are not assumed to identify an airport, port, or pass.
        if source.get("source_key") == "wa_dnr_fire_statistics":
            fire_start_date = (evidence.get("wa_dnr_fire_statistics") or {}).get(
                "discovery_date"
            )
        elif source.get("source_key") == "nwcc_large_fire_wa":
            fire_start_date = (evidence.get("nwcc_large_fire") or {}).get("start_date")
        elif source.get("source_key") == "nwcc_point_daily_wa":
            fire_start_date = (evidence.get("nwcc_point_daily") or {}).get("start_date")
        elif source.get("source_key") == "nifc_wfigs_current_wa":
            discovery = (evidence.get("nifc_wfigs") or {}).get("discovery_at")
            if isinstance(discovery, str) and discovery.endswith(("+00:00", "Z")):
                observed = _time(discovery)
                if observed:
                    fire_start_date = observed.astimezone(
                        _WASHINGTON_ZONE
                    ).date().isoformat()
    return {
        "id": int(item["id"]),
        "event_key": str(event.get("event_key") or ""),
        "event_type": str(event.get("event_type") or "").casefold(),
        "fields": fields,
        "tokens": set(_WORDS.findall(str(item.get("title") or "").casefold())) - _STOP,
        "published_at": _time(item.get("source_published_at") or item.get("first_seen_at")),
        "family": str(source.get("source_family") or "").casefold(),
        "source_key": str(source.get("source_key") or ""),
        "official": source.get("official_status") == "official",
        "fire_start_date": fire_start_date,
    }


def regional_match_basis(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    if left["event_key"] and left["event_key"] == right["event_key"]:
        return ["shared_official_event_id"] if left["official"] and right["official"] else []
    if not left["family"] or left["family"] == right["family"]:
        return []
    if not left["official"] or not right["official"]:
        return []
    if (not left["event_type"] or left["event_type"] == "regional_headline"
            or left["event_type"] != right["event_type"]):
        return []
    if (left["event_type"] == "wildfire_update"
            and {left["source_key"], right["source_key"]} == {
                "wa_dnr_fire_statistics", "nifc_wfigs_current_wa",
            }):
        if (left["fields"]["fire_incident"]
                and left["fields"]["fire_incident"] == right["fields"]["fire_incident"]
                and left["fields"]["county"]
                and left["fields"]["county"] == right["fields"]["county"]
                and left["fire_start_date"]
                and left["fire_start_date"] == right["fire_start_date"]):
            return ["event_type", "fire_incident", "county", "pacific_discovery_day",
                    "independent_family"]
        return []
    if (left["event_type"] == "wildfire_update"
            and {left["source_key"], right["source_key"]} == {
                "wa_dnr_fire_statistics", "nwcc_large_fire_wa",
            }
            and left["fields"]["fire_incident"]
            and left["fields"]["fire_incident"] == right["fields"]["fire_incident"]
            and left["fire_start_date"]
            and left["fire_start_date"] == right["fire_start_date"]):
        return ["event_type", "fire_incident", "source_start_date", "independent_family"]
    shared = [field for field in _GEO_FIELDS if left["fields"][field] & right["fields"][field]]
    if not shared or len(left["tokens"] & right["tokens"]) < 3:
        return []
    if not left["published_at"] or not right["published_at"]:
        return []
    delta = abs((left["published_at"] - right["published_at"]).total_seconds()) / 3600
    if delta > MATCH_WINDOW_HOURS:
        return []
    return ["event_type", *shared, "title_tokens", "time_window", "independent_family"]


def correlate_regional_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signatures = [
        regional_item_signature(item) for item in items if item.get("scope") == "REGIONAL"
    ]
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
            basis = regional_match_basis(signatures[left], signatures[right])
            if not basis:
                continue
            a, b = root(left), root(right)
            if a != b:
                # Require every pair to match; a broad middle report cannot bridge
                # two distinct incidents into one cluster.
                if not all(regional_match_basis(signatures[x], signatures[y])
                           for x in members[a] for y in members[b]):
                    continue
                parents[b] = a
                members[a].extend(members.pop(b))
            matches.append({
                "item_ids": [signatures[left]["id"], signatures[right]["id"]],
                "basis": basis,
                "shared_tokens": sorted(signatures[left]["tokens"] & signatures[right]["tokens"]),
            })
    groups: dict[int, list[dict[str, Any]]] = {}
    for index, signature in enumerate(signatures):
        groups.setdefault(root(index), []).append(signature)
    result = []
    for group in groups.values():
        ids = sorted(entry["id"] for entry in group)
        keys = sorted({entry["event_key"] for entry in group if entry["event_key"]})
        group_matches = [match for match in matches if set(match["item_ids"]) <= set(ids)]
        families = sorted({entry["family"] for entry in group if entry["family"]})
        result.append({
            "event_key": keys[0] if keys else f"regional:item:{ids[0]}",
            "item_ids": ids,
            "families": families,
            "source_keys": sorted({entry["source_key"] for entry in group if entry["source_key"]}),
            "event_types": sorted({entry["event_type"] for entry in group if entry["event_type"]}),
            "matches": group_matches,
            "corroborated": len(families) >= 2 and any(
                "independent_family" in match["basis"] for match in group_matches
            ),
        })
    return sorted(result, key=lambda group: group["item_ids"][0])
