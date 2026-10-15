"""Evidence-backed impact tags; canonical scope remains ORBITAL."""

from __future__ import annotations

from typing import Any

ORBITAL_IMPACT_TAGS = frozenset({
    "GLOBAL_IMPACT", "NATIONAL_IMPACT", "REGIONAL_IMPACT", "LOCAL_IMPACT",
    "SKY", "RADIO", "GPS", "AVIATION", "SATELLITE", "POWER", "AURORA",
    "CREWED", "NEO", "REENTRY", "DEBRIS",
})
_SYSTEM_TAGS = {
    "radio": "RADIO", "hf radio": "RADIO", "hf": "RADIO",
    "gps": "GPS", "navigation": "GPS", "aviation": "AVIATION",
    "spacecraft": "SATELLITE", "satellite": "SATELLITE",
    "power": "POWER", "aurora": "AURORA",
}


def derive_orbital_impact(item: dict[str, Any]) -> dict[str, Any]:
    """Use parsed official fields, not headline guesses or implied geographic reach."""
    evidence = item.get("evidence") or {}
    identity = evidence.get("orbital_identity") or {}
    event_type = str(identity.get("event_type") or "").lower()
    basis: dict[str, list[str]] = {}

    def add(tag: str, reason: str) -> None:
        if tag in ORBITAL_IMPACT_TAGS:
            basis.setdefault(tag, []).append(reason)

    aurora = evidence.get("swpc_aurora") or {}
    if aurora.get("model_only") is True and aurora.get("grid_match_basis") == (
        "configured_coordinate_box"
    ):
        add("SKY", "swpc_aurora.model_only")
        add("AURORA", "swpc_aurora.model_value")
        scope = str(aurora.get("location_scope") or "").upper()
        if scope in {"LOCAL", "REGIONAL"}:
            add(f"{scope}_IMPACT", "swpc_aurora.configured_location_scope")

    alert = evidence.get("swpc_alert") or {}
    for impact in alert.get("potential_impacts") or []:
        if not isinstance(impact, dict):
            continue
        system = str(impact.get("system") or "").lower().strip()
        if tag := _SYSTEM_TAGS.get(system):
            add(tag, f"swpc_alert.potential_impacts.{system}")
    # An official source may explicitly classify geographic reach. A radio,
    # aviation, or power impact alone does not establish national/global reach.
    source_scope = str(identity.get("source_reported_impact_scope") or "").upper()
    if source_scope in {"GLOBAL", "NATIONAL", "REGIONAL", "LOCAL"}:
        add(f"{source_scope}_IMPACT", "orbital_identity.source_reported_impact_scope")

    if event_type == "neo_close_approach" and evidence.get("jpl_close_approach"):
        add("NEO", "jpl_close_approach.designation")
    if event_type == "fireball" and evidence.get("jpl_fireball"):
        add("SKY", "jpl_fireball.event_time_utc")
    if event_type in {"iss_update", "crewed_mission_update"} and (
        evidence.get("nasa_rss") or evidence.get("esa_rss")
    ):
        add("CREWED", "official_agency_rss.story_type")
    if event_type == "reentry" and evidence.get("official_reentry"):
        add("REENTRY", "official_reentry.event_type")
    if event_type == "orbital_debris" and evidence.get("official_debris"):
        add("DEBRIS", "official_debris.event_type")
    return {
        "tags": sorted(basis),
        "basis": {tag: sorted(set(reasons)) for tag, reasons in sorted(basis.items())},
        "geography_inferred": False,
    }
