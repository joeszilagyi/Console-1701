"""Conservative, deterministic GLOBAL event identity from stored metadata."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_GLIDE_RE = re.compile(r"[A-Z]{2}-\d{4}-\d{6}-[A-Z]{3}\Z")
_STOPWORDS = {
    "a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "the", "to",
    "with", "after", "amid", "new", "update", "report", "reports", "global",
}
_TYPE_ALIASES = {
    "eq": "earthquake",
    "tc": "tropical_cyclone",
    "tropical cyclone": "tropical_cyclone",
    "fl": "flood",
    "flood": "flood",
    "vo": "volcano",
    "volcanic eruption": "volcano",
}
MATCH_WINDOW_HOURS = 96


def _normalized(value: Any) -> str:
    return " ".join(_TOKEN_RE.findall(str(value or "").lower()))


def _glide_identifier(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip().upper()
    return f"glide:{candidate.lower()}" if _GLIDE_RE.fullmatch(candidate) else None


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def global_item_signature(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence") or {}
    contract = evidence.get("global") or {}
    gdacs = evidence.get("gdacs") or {}
    disaster = evidence.get("reliefweb_disaster") or {}
    report = evidence.get("reliefweb_report") or {}
    who = evidence.get("who_don") or {}
    identity = evidence.get("global_identity") or {}
    identifiers: set[str] = set()
    if gdacs.get("event_id") and gdacs.get("event_type"):
        identifiers.add(
            f"gdacs:{_normalized(gdacs['event_type'])}:{_normalized(gdacs['event_id'])}"
        )
    if disaster.get("id"):
        identifiers.add(f"reliefweb_disaster:{_normalized(disaster['id'])}")
    for glide in (gdacs.get("glide"), disaster.get("glide")):
        if identifier := _glide_identifier(glide):
            identifiers.add(identifier)
    identifiers.update(
        f"reliefweb_disaster:{_normalized(value)}"
        for value in report.get("disaster_ids") or [] if _normalized(value)
    )
    for glide in report.get("disaster_glides") or []:
        if identifier := _glide_identifier(glide):
            identifiers.add(identifier)
    if who.get("don_id"):
        identifiers.add(f"who_don:{_normalized(who['don_id'])}")
    if (evidence.get("usgs_earthquake") or {}).get("id"):
        identifiers.add(
            f"usgs_earthquake:{_normalized(evidence['usgs_earthquake']['id'])}"
        )
    for field in ("storm_id", "earthquake_id", "cyber_incident_id"):
        if identity.get(field):
            identifiers.add(f"{field}:{_normalized(identity[field])}")
    event_type = _normalized(contract.get("event_type"))
    event_type = _TYPE_ALIASES.get(event_type, event_type.replace(" ", "_"))
    countries = {
        _normalized(value) for value in contract.get("affected_countries") or []
        if _normalized(value)
    }
    if contract.get("geography_basis") != "official_source_fields":
        countries = set()
    regions = {
        _normalized(value) for value in contract.get("affected_regions") or []
        if _normalized(value)
    }
    if contract.get("geography_basis") != "official_source_fields":
        regions = set()
    return {
        "id": int(item["id"]),
        "identifiers": identifiers,
        "event_type": event_type,
        "countries": countries,
        "regions": regions,
        "basins": {_normalized(identity["basin"])} if identity.get("basin") else set(),
        "volcanoes": (
            {_normalized(identity["volcano_name"])} if identity.get("volcano_name") else set()
        ),
        "diseases": {_normalized(identity["disease"])} if identity.get("disease") else set(),
        "institutions": (
            {_normalized(identity["institution"])} if identity.get("institution") else set()
        ),
        "transport_sectors": (
            {_normalized(identity["transport_sector"])}
            if identity.get("transport_sector") else set()
        ),
        "cyber_identifiers": {
            _normalized(value) for value in identity.get("cyber_identifiers") or []
            if _normalized(value)
        },
        "impact_tags": {
            _normalized(value) for value in contract.get("impact_tags") or []
            if _normalized(value)
        },
        "tokens": set(_TOKEN_RE.findall(str(item.get("title") or "").lower())) - _STOPWORDS,
        "published_at": _time(item.get("source_published_at") or item.get("first_seen_at")),
        "family": _normalized((evidence.get("source") or {}).get("source_family")) or "unknown",
        "source_key": str((evidence.get("source") or {}).get("source_key") or ""),
        "official": (evidence.get("source") or {}).get("official_status") == "official",
        "article_url": str(item.get("canonical_url") or item.get("url") or "").strip(),
        "syndication_id": _normalized(identity.get("syndication_id")),
    }


def global_match_basis(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    left_glides = {value for value in left["identifiers"] if value.startswith("glide:")}
    right_glides = {value for value in right["identifiers"] if value.startswith("glide:")}
    if left_glides and right_glides and not left_glides & right_glides:
        return []
    if left["identifiers"] & right["identifiers"]:
        return ["shared_event_id"]
    if (left["article_url"] and left["article_url"] == right["article_url"]
            and len(left["tokens"] & right["tokens"]) >= 2
            and (not left["event_type"] or not right["event_type"]
                 or left["event_type"] == right["event_type"])):
        return ["same_article_url"]
    if (left["syndication_id"] and left["syndication_id"] == right["syndication_id"]
            and (not left["event_type"] or not right["event_type"]
                 or left["event_type"] == right["event_type"])):
        return ["same_syndication_id"]
    if left["family"] == "unknown" or left["family"] == right["family"]:
        return []
    if not left["event_type"] or left["event_type"] != right["event_type"]:
        return []
    geography = [
        label for field, label in (
            ("countries", "country"), ("regions", "region"),
            ("basins", "basin"), ("volcanoes", "volcano_name"),
        ) if left[field] & right[field]
    ]
    if not geography:
        return []
    if len(left["tokens"] & right["tokens"]) < 2:
        return []
    if not left["published_at"] or not right["published_at"]:
        return []
    hours = abs((left["published_at"] - right["published_at"]).total_seconds()) / 3600
    if hours > MATCH_WINDOW_HOURS:
        return []
    context = [
        label for field, label in (
            ("diseases", "disease"), ("institutions", "institution"),
            ("transport_sectors", "transport_sector"),
            ("cyber_identifiers", "cyber_identifier"), ("impact_tags", "impact_tag"),
        ) if left[field] & right[field]
    ]
    return [
        "event_type", *geography, *context, "title_tokens", "time_window",
        "independent_family",
    ]


def correlate_global_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return groups of GLOBAL item ids with auditable pairwise match reasons."""
    signatures = [global_item_signature(item) for item in items if item.get("scope") == "GLOBAL"]
    parents = list(range(len(signatures)))
    component_members = {index: [index] for index in range(len(signatures))}

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    matches: list[dict[str, Any]] = []
    for left in range(len(signatures)):
        for right in range(left + 1, len(signatures)):
            basis = global_match_basis(signatures[left], signatures[right])
            if basis:
                left_root = root(left)
                right_root = root(right)
                if left_root != right_root:
                    if not all(
                        global_match_basis(signatures[a], signatures[b])
                        for a in component_members[left_root]
                        for b in component_members[right_root]
                    ):
                        continue
                    parents[right_root] = left_root
                    component_members[left_root].extend(component_members.pop(right_root))
                matches.append({
                    "item_ids": [signatures[left]["id"], signatures[right]["id"]],
                    "basis": basis,
                    "shared_tokens": sorted(
                        signatures[left]["tokens"] & signatures[right]["tokens"]
                    ),
                })

    groups: dict[int, list[dict[str, Any]]] = {}
    for index, signature in enumerate(signatures):
        groups.setdefault(root(index), []).append(signature)
    result = []
    for members in groups.values():
        ids = sorted(member["id"] for member in members)
        families = sorted({member["family"] for member in members if member["family"] != "unknown"})
        credited: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        seen_syndication: set[str] = set()
        for member in sorted(members, key=lambda entry: entry["id"]):
            url = member["article_url"]
            syndication = member["syndication_id"]
            duplicate = bool(
                (url and url in seen_urls)
                or (syndication and syndication in seen_syndication)
            )
            if url:
                seen_urls.add(url)
            if syndication:
                seen_syndication.add(syndication)
            if not duplicate:
                credited.append(member)
        credited_families = sorted({
            entry["family"] for entry in credited if entry["family"] != "unknown"
        })
        group_matches = [entry for entry in matches if set(entry["item_ids"]) <= set(ids)]
        result.append({
            "event_key": f"global:item:{ids[0]}",
            "item_ids": ids,
            "source_keys": sorted({
                member["source_key"] for member in members if member["source_key"]
            }),
            "families": families,
            "credited_families": credited_families,
            "credited_official_families": sorted({
                entry["family"] for entry in credited
                if entry["official"] and entry["family"] != "unknown"
            }),
            "syndicated_duplicate_count": len(members) - len(credited),
            "event_types": sorted({
                member["event_type"] for member in members if member["event_type"]
            }),
            "countries": sorted(set().union(*(member["countries"] for member in members))),
            "identifiers": sorted(set().union(*(member["identifiers"] for member in members))),
            "matches": group_matches,
            "corroborated": len(credited_families) >= 2 and any(
                "independent_family" in match["basis"]
                or "shared_event_id" in match["basis"] for match in group_matches
            ),
        })
    return sorted(result, key=lambda group: group["item_ids"][0])
