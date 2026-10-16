"""Conservative, deterministic grouping of stored science metadata."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

_TOKENS = re.compile(r"[a-z0-9]+")
_STOP = {"a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "the",
         "to", "with", "new", "latest", "update", "science", "nasa", "esa"}
MATCH_WINDOW_HOURS = 96
_EXCLUSIVE_EVENT_ID_PREFIXES = ("gcn_event:", "gracedb:")


def _value(value: Any) -> str:
    return " ".join(_TOKENS.findall(str(value or "").casefold()))


def _time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _family(value: Any) -> str:
    family = _value(value).replace(" ", "_")
    if family.startswith(("nasa_", "jpl_")):
        return "nasa"
    if family.startswith("esa_"):
        return "esa"
    return family or "unknown"


def science_item_signature(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence") or {}
    source = evidence.get("source") or {}
    source_family = _value(source.get("source_family")).replace(" ", "_")
    rss = evidence.get("science_rss") or {}
    planet = (
        evidence.get("exoplanet_archive") or {}
    ) if source_family == "nasa_exoplanet_archive" else {}
    mast = (evidence.get("mast_caom") or {}) if source_family == "mast" else {}
    pds = (evidence.get("pds_collection") or {}) if source_family == "nasa_pds" else {}
    gcn_family = source_family in {"gcn", "nasa_gcn"}
    gcn = (evidence.get("gcn_notice") or {}) if gcn_family else {}
    circular = (evidence.get("gcn_circular") or {}) if gcn_family else {}
    identity = evidence.get("science_identity") or {}
    if gcn or circular:
        kind = "transient"
    elif planet:
        kind = "exoplanet"
    elif pds:
        kind = "planetary_archive"
    elif mast:
        kind = "telescope_observation"
    elif rss.get("telescope"):
        kind = "telescope_release"
    else:
        kind = _value(identity.get("event_type") or "science_release").replace(" ", "_")
    identifiers: set[str] = set()
    for field, value in (
        ("gcn_event", gcn.get("event_name") or gcn.get("event_id")),
        ("gcn_trigger", gcn.get("trigger_id")),
        ("gcn_event", circular.get("event_id")),
        ("gcn_circular", circular.get("circular_id")),
        ("planet", planet.get("planet_name")),
        ("mast_observation", mast.get("observation_id")),
        ("mast_dataset", mast.get("dataset_id")),
        ("pds_collection", pds.get("collection_lid")),
        ("telescope_release", rss.get("release_id")),
        ("atel", identity.get("atel_number")),
        ("tns", identity.get("tns_name")),
        ("gracedb", identity.get("gracedb_superevent_id")),
        ("doi", identity.get("doi")),
        ("bibcode", identity.get("bibcode")),
        ("dataset", identity.get("dataset_id")),
    ):
        normalized = _value(value)
        if normalized:
            identifiers.add(f"{field}:{normalized}")
    # A planet or mission name alone can recur in unrelated releases. Keep it
    # as context, never as an event identifier.
    context = {
        key: _value(value) for key, value in (
            ("mission", identity.get("mission") or rss.get("mission_label")
             or pds.get("mission") or gcn.get("mission") or mast.get("mission")),
            ("telescope", identity.get("telescope") or rss.get("telescope")),
            ("instrument", identity.get("instrument") or gcn.get("instrument")
             or mast.get("instrument") or rss.get("instrument")),
            ("object", identity.get("object_name") or mast.get("target_name")),
            ("body", identity.get("solar_system_body") or pds.get("target_body")),
            ("system", identity.get("exoplanet_system") or planet.get("host_star")),
            ("coordinates", identity.get("coordinates_icrs_deg")
             or gcn.get("coordinates_icrs_deg")),
        ) if value
    }
    return {
        "id": int(item["id"]), "kind": kind, "identifiers": identifiers,
        "context": context,
        "tokens": set(_TOKENS.findall(str(item.get("title") or "").casefold())) - _STOP,
        "published_at": _time(item.get("source_published_at") or item.get("first_seen_at")),
        "family": _family(source_family),
        "source_key": str(source.get("source_key") or ""),
    }


def science_match_basis(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    if left["kind"] != right["kind"] or not left["published_at"] or not right["published_at"]:
        return []
    # One Circular ID can be reassigned to another event in a correction.
    # The explicit transient IDs take precedence over shared publication ID.
    for prefix in _EXCLUSIVE_EVENT_ID_PREFIXES:
        left_ids = {value for value in left["identifiers"] if value.startswith(prefix)}
        right_ids = {value for value in right["identifiers"] if value.startswith(prefix)}
        if left_ids and right_ids and not left_ids & right_ids:
            return []
    hours = abs((left["published_at"] - right["published_at"]).total_seconds()) / 3600
    if hours > MATCH_WINDOW_HOURS:
        return []
    if left["identifiers"] & right["identifiers"]:
        return ["event_kind", "shared_event_id", "time_window"]
    if left["family"] in {"unknown", right["family"]} or right["family"] == "unknown":
        return []
    shared_context = sorted(key for key, value in left["context"].items()
                            if value and value == right["context"].get(key))
    shared_tokens = left["tokens"] & right["tokens"]
    if not shared_context or len(shared_tokens) < 3:
        return []
    return ["event_kind", *shared_context, "title_tokens", "time_window",
            "independent_family"]


def correlate_science_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group by complete-link matches so one broad headline cannot bridge events."""
    signatures = [science_item_signature(item) for item in items
                  if item.get("scope") == "SYSTEM_SOLAR"]
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
            basis = science_match_basis(signatures[left], signatures[right])
            if not basis:
                continue
            left_root, right_root = root(left), root(right)
            if left_root != right_root:
                if not all(science_match_basis(signatures[a], signatures[b])
                           for a in members[left_root] for b in members[right_root]):
                    continue
                parents[right_root] = left_root
                members[left_root].extend(members.pop(right_root))
            matches.append({"item_ids": [signatures[left]["id"], signatures[right]["id"]],
                            "basis": basis})
    groups: dict[int, list[dict[str, Any]]] = {}
    for index, signature in enumerate(signatures):
        groups.setdefault(root(index), []).append(signature)
    result = []
    for group in groups.values():
        ids = sorted(member["id"] for member in group)
        families = sorted({member["family"] for member in group
                           if member["family"] != "unknown"})
        group_matches = [match for match in matches if set(match["item_ids"]) <= set(ids)]
        result.append({
            "event_key": f"science:item:{ids[0]}", "item_ids": ids,
            "source_keys": sorted({member["source_key"] for member in group
                                   if member["source_key"]}),
            "families": families,
            "event_kinds": sorted({member["kind"] for member in group}),
            "identifiers": sorted(set().union(*(member["identifiers"] for member in group))),
            "matches": group_matches,
            "corroborated": len(families) >= 2 and any(
                "independent_family" in match["basis"] for match in group_matches),
        })
    return sorted(result, key=lambda group: group["item_ids"][0])
