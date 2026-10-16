"""Conservative NATIONAL event matching from explicit source metadata."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {"a", "an", "and", "at", "by", "for", "from", "in", "of", "on",
              "the", "to", "with", "after", "new", "update", "reports", "national"}
_WINDOW_HOURS = 72


def _tokens(value: Any) -> set[str]:
    return set(_TOKEN_RE.findall(str(value or "").casefold()))


def _values(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {" ".join(_TOKEN_RE.findall(str(entry).casefold())) for entry in value[:40]
            if _TOKEN_RE.findall(str(entry).casefold())}


def _time(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def national_item_signature(item: dict[str, Any]) -> dict[str, Any]:
    evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
    identity = evidence.get("national_identity") or {}
    source = evidence.get("source") or {}
    identifiers: set[str] = set()
    for evidence_key, field, namespace in (
        ("usgs_earthquake", "id", "usgs"),
        ("nws_alert", "id", "nws"),
        ("nhtsa_recall", "campaign_number", "nhtsa_campaign"),
        ("cpsc_recall", "recall_id", "cpsc"),
        ("openfema_declaration", "declaration", "fema"),
        ("cisa_kev", "cve_id", "cve"),
        ("federal_register", "document_number", "fr_document"),
        ("govinfo_publication", "document_id", "govinfo_document"),
    ):
        payload = evidence.get(evidence_key) or {}
        if payload.get(field):
            identifiers.add(f"{namespace}:{str(payload[field]).strip().casefold()}")
    for entry in identity.get("official_event_ids") or []:
        if isinstance(entry, str) and ":" in entry and len(entry) <= 120:
            identifiers.add(entry.casefold())
    nws = evidence.get("nws_alert") or {}
    geocode = nws.get("geocode") or {}
    zones = _values(geocode.get("UGC"))
    states = _values(identity.get("affected_states"))
    states.update(zone[:2] for zone in zones if re.fullmatch(r"[a-z]{2}[cz]\d{3}", zone))
    faa = evidence.get("faa_nas_status") or {}
    airports = _values(identity.get("affected_airports"))
    if faa.get("airport_code"):
        airports.add(str(faa["airport_code"]).casefold())
    return {
        "id": int(item["id"]),
        "identifiers": identifiers,
        "event_type": str(identity.get("event_type") or (
            "earthquake" if evidence.get("usgs_earthquake") else
            "weather_alert" if nws else
            "vehicle_recall" if evidence.get("nhtsa_recall") else
            "consumer_product_recall" if evidence.get("cpsc_recall") else
            "fda_recall_notice" if evidence.get("fda_recall_notice") else
            "cyber_vulnerability" if evidence.get("cisa_kev") else
            "aviation_disruption" if faa else
            "federal_action" if evidence.get("federal_register") else
            "federal_publication" if evidence.get("govinfo_publication") else ""
        )).strip().casefold(),
        "agency": str(identity.get("agency") or (
            "CPSC" if evidence.get("cpsc_recall") else
            "FDA" if evidence.get("fda_recall_notice") else ""
        )).strip().casefold(),
        "affected_states": states,
        "affected_territories": _values(identity.get("affected_territories")),
        "fema_regions": _values(identity.get("fema_regions")),
        "nws_regions": _values(identity.get("nws_regions")),
        "storm_basins": _values(identity.get("storm_basins")),
        "affected_airports": airports,
        "distribution_areas": _values(identity.get("distribution_areas")),
        "infrastructure_sectors": _values(identity.get("infrastructure_sectors")),
        "population_groups": _values(identity.get("population_groups")),
        "jurisdictions": _values(identity.get("jurisdictions")),
        "national_impact": bool(identity.get("national_impact")),
        "multi_state_impact": bool(identity.get("multi_state_impact")) or len(states) >= 2,
        "tokens": _tokens(item.get("title")) - _STOPWORDS,
        "published_at": _time(item.get("source_published_at") or item.get("first_seen_at")),
        "family": str(source.get("source_family") or "unknown").strip().casefold(),
        "official": source.get("official_status") == "official",
        "source_key": str(source.get("source_key") or "").strip(),
        "article_url": str(item.get("canonical_url") or item.get("url") or "").strip(),
        "syndication_id": str(identity.get("syndication_id") or "").strip().casefold(),
    }


_CONTEXT_FIELDS = (
    "affected_states", "affected_territories", "fema_regions", "nws_regions",
    "storm_basins", "affected_airports", "distribution_areas",
    "infrastructure_sectors", "population_groups", "jurisdictions",
)


def national_match_basis(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    # An article or broad title may mention several official events. When both
    # items carry IDs from the same authority, disjoint IDs rule out a match.
    namespaces = {
        value.split(":", 1)[0] for value in left["identifiers"]
    } & {
        value.split(":", 1)[0] for value in right["identifiers"]
    }
    for namespace in namespaces:
        prefix = f"{namespace}:"
        left_ids = {value for value in left["identifiers"] if value.startswith(prefix)}
        right_ids = {value for value in right["identifiers"] if value.startswith(prefix)}
        if not left_ids & right_ids:
            return []
    shared_ids = left["identifiers"] & right["identifiers"]
    if shared_ids and all(value.startswith("cve:") for value in shared_ids):
        if (left["family"] != "cisa" or right["family"] != "cisa"
                or not left["official"] or not right["official"]
                or left["agency"] != "cisa" or right["agency"] != "cisa"
                or not left["published_at"] or not right["published_at"]
                or abs((left["published_at"] - right["published_at"]).total_seconds())
                > _WINDOW_HOURS * 3600):
            return []
        return ["shared_cve", "same_authority", "time_window"]
    if shared_ids:
        return ["shared_official_event_id"]
    compatible_type = (
        not left["event_type"] or not right["event_type"]
        or left["event_type"] == right["event_type"]
    )
    if (left["article_url"] and left["article_url"] == right["article_url"]
            and compatible_type and len(left["tokens"] & right["tokens"]) >= 2):
        return ["same_article_url"]
    if (left["syndication_id"] and left["syndication_id"] == right["syndication_id"]
            and compatible_type):
        return ["same_syndication_id"]
    if left["family"] == "unknown" or left["family"] == right["family"]:
        return []
    if not left["event_type"] or left["event_type"] != right["event_type"]:
        return []
    if left["agency"] and right["agency"] and left["agency"] != right["agency"]:
        return []
    context = [field for field in _CONTEXT_FIELDS if left[field] & right[field]]
    if not context or len(left["tokens"] & right["tokens"]) < 3:
        return []
    if not left["published_at"] or not right["published_at"]:
        return []
    hours = abs((left["published_at"] - right["published_at"]).total_seconds()) / 3600
    if hours > _WINDOW_HOURS:
        return []
    return ["event_type", *context, "title_tokens", "time_window", "independent_family"]


def correlate_national_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signatures = [
        national_item_signature(item) for item in items if item.get("scope") == "NATIONAL"
    ]
    parents = list(range(len(signatures)))
    components = {index: [index] for index in range(len(signatures))}

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    matches: list[dict[str, Any]] = []
    for left in range(len(signatures)):
        for right in range(left + 1, len(signatures)):
            basis = national_match_basis(signatures[left], signatures[right])
            if not basis:
                continue
            a, b = root(left), root(right)
            if a != b:
                if not all(national_match_basis(signatures[x], signatures[y])
                           for x in components[a] for y in components[b]):
                    continue
                parents[b] = a
                components[a].extend(components.pop(b))
            matches.append({"item_ids": [signatures[left]["id"], signatures[right]["id"]],
                            "basis": basis,
                            "shared_tokens": sorted(signatures[left]["tokens"] &
                                                    signatures[right]["tokens"])})
    grouped: dict[int, list[dict[str, Any]]] = {}
    for index, signature in enumerate(signatures):
        grouped.setdefault(root(index), []).append(signature)
    result: list[dict[str, Any]] = []
    for members in grouped.values():
        ids = sorted(member["id"] for member in members)
        family_set = {member["family"] for member in members if member["family"] != "unknown"}
        result.append({
            "event_key": f"national:item:{ids[0]}",
            "item_ids": ids,
            "families": sorted(family_set),
            "source_keys": sorted({member["source_key"] for member in members
                                   if member["source_key"]}),
            "event_types": sorted({member["event_type"] for member in members
                                   if member["event_type"]}),
            "identifiers": sorted(set().union(*(member["identifiers"] for member in members))),
            "affected_states": sorted(set().union(*(
                member["affected_states"] for member in members
            ))),
            "affected_territories": sorted(set().union(*(
                member["affected_territories"] for member in members
            ))),
            "affected_airports": sorted(set().union(*(
                member["affected_airports"] for member in members
            ))),
            "national_impact": any(member["national_impact"] for member in members),
            "multi_state_impact": any(member["multi_state_impact"] for member in members),
            "matches": [match for match in matches if set(match["item_ids"]) <= set(ids)],
            "corroborated": len(family_set) >= 2 and any(
                "independent_family" in match["basis"]
                for match in matches if set(match["item_ids"]) <= set(ids)
            ),
        })
    return sorted(result, key=lambda group: group["item_ids"][0])
