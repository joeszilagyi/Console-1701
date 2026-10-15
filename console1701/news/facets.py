"""Indexed, bounded facets derived from persisted scoped item evidence."""

from __future__ import annotations

import sqlite3
from typing import Any


def global_item_facets(evidence: dict[str, Any], tags: list[Any]) -> set[tuple[str, str]]:
    facets: set[tuple[str, str]] = set()

    def add(kind: str, value: Any) -> None:
        if not isinstance(value, str):
            return
        text = value.strip().casefold()
        if text and len(text) <= 120:
            facets.add((kind, text))

    source = evidence.get("source") or {}
    if isinstance(source, dict):
        add("source_family", source.get("source_family"))
    gdacs = evidence.get("gdacs") or {}
    if isinstance(gdacs, dict):
        add("event_type", gdacs.get("event_type"))
        add("country", gdacs.get("country"))
        for country in _list_values(gdacs.get("affected_countries")):
            add("country", country)
    disaster = evidence.get("reliefweb_disaster") or {}
    if isinstance(disaster, dict):
        for country in _list_values(disaster.get("countries")):
            add("country", country)
        for event_type in _list_values(disaster.get("types")):
            add("event_type", event_type)
    report = evidence.get("reliefweb_report") or {}
    if isinstance(report, dict):
        for country in _list_values(report.get("countries")):
            add("country", country)
    geography = evidence.get("geography") or {}
    if isinstance(geography, dict):
        for region in _list_values(geography.get("verified_regions")):
            add("region", region)
    sensitivity = evidence.get("sensitivity") or {}
    if isinstance(sensitivity, dict):
        for key, enabled in sensitivity.items():
            if enabled is True:
                add("sensitivity", key)
    for tag in tags:
        if isinstance(tag, str) and tag in {
            "local-impact", "us-impact", "conflict-humanitarian"
        }:
            add("impact_tag", tag)
    return facets


def _list_values(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def national_item_facets(evidence: dict[str, Any]) -> set[tuple[str, str]]:
    """Use official parser fields for query labels; never infer a state from prose."""
    facets: set[tuple[str, str]] = set()

    def add(kind: str, value: Any) -> None:
        if not isinstance(value, str):
            return
        text = value.strip().casefold()
        if text and len(text) <= 120:
            facets.add((kind, text))

    source = evidence.get("source") or {}
    if isinstance(source, dict):
        add("source_family", source.get("source_family"))
    nws = evidence.get("nws_alert") or {}
    if isinstance(nws, dict):
        add("agency", "nws")
        add("sector", "weather")
        for state in _list_values(nws.get("affected_states"))[:16]:
            add("state", state)
    usgs = evidence.get("usgs_earthquake") or {}
    if isinstance(usgs, dict):
        add("agency", "usgs")
        add("sector", "seismic")
    nhtsa = evidence.get("nhtsa_recall") or {}
    if isinstance(nhtsa, dict):
        add("agency", "nhtsa")
        add("sector", "transportation")
    kev = evidence.get("cisa_kev") or {}
    if isinstance(kev, dict):
        add("agency", "cisa")
        add("sector", "cybersecurity")
    nas = evidence.get("faa_nas_status") or {}
    if isinstance(nas, dict):
        add("agency", "faa")
        add("sector", "aviation")
    return facets


def replace_national_item_facets(
    conn: sqlite3.Connection,
    item_id: int,
    evidence: dict[str, Any],
) -> None:
    conn.execute("DELETE FROM news_item_facets WHERE item_id = ?", (item_id,))
    conn.executemany(
        "INSERT INTO news_item_facets (item_id, scope, facet_kind, facet_value) "
        "VALUES (?, 'NATIONAL', ?, ?)",
        [(item_id, kind, value) for kind, value in sorted(national_item_facets(evidence))],
    )


def regional_item_facets(evidence: dict[str, Any]) -> set[tuple[str, str]]:
    facets: set[tuple[str, str]] = set()

    def add(kind: str, value: Any) -> None:
        if not isinstance(value, str):
            return
        text = value.strip().casefold()
        if text and len(text) <= 120:
            facets.add((kind, text))

    event = evidence.get("regional_event") or {}
    if not isinstance(event, dict):
        return facets
    add("event_type", event.get("event_type"))
    add("source_family", event.get("source_family"))
    geography = event.get("geography") or {}
    if not isinstance(geography, dict) or not geography.get("matched"):
        return facets
    basis = geography.get("basis")
    if basis == "official_affected_zones":
        for zone in _list_values(geography.get("zone_ids"))[:8]:
            add("zone", zone)
    elif basis == "official_route_county_facility":
        for route in _list_values(geography.get("routes"))[:8]:
            add("route", route)
        for facility in _list_values(geography.get("facilities"))[:8]:
            add("facility", facility)
        add("county", geography.get("county"))
        add("region", geography.get("region"))
    # USGS coordinates prove a point, not a county or regional impact label.
    return facets


def replace_regional_item_facets(
    conn: sqlite3.Connection,
    item_id: int,
    evidence: dict[str, Any],
) -> None:
    conn.execute("DELETE FROM news_item_facets WHERE item_id = ?", (item_id,))
    conn.executemany(
        "INSERT INTO news_item_facets (item_id, scope, facet_kind, facet_value) "
        "VALUES (?, 'REGIONAL', ?, ?)",
        [(item_id, kind, value) for kind, value in sorted(regional_item_facets(evidence))],
    )


def replace_global_item_facets(
    conn: sqlite3.Connection,
    item_id: int,
    evidence: dict[str, Any],
    tags: list[Any],
) -> None:
    conn.execute("DELETE FROM news_item_facets WHERE item_id = ?", (item_id,))
    conn.executemany(
        "INSERT INTO news_item_facets (item_id, scope, facet_kind, facet_value) "
        "VALUES (?, 'GLOBAL', ?, ?)",
        [(item_id, kind, value) for kind, value in sorted(global_item_facets(evidence, tags))],
    )
