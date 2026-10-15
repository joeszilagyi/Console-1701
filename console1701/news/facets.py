"""Indexed, bounded facets derived from persisted GLOBAL item evidence."""

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
