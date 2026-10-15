"""Deterministic GLOBAL attention rules based on source and bounded metadata."""

from __future__ import annotations

import re
from typing import Any

_ROUTINE_RE = re.compile(
    r"\b(?:routine diplomatic statement|courtesy call|weekly institutional roundup|"
    r"staff appointment|ceremonial remarks|routine economic release|economic calendar)\b", re.I
)
_OPINION_RE = re.compile(r"\b(?:opinion|editorial|punditry|commentary)\s*:", re.I)
_DOMESTIC_RE = re.compile(
    r"\b(?:campaign rally|candidate endorsement|partisan fundraiser|domestic election)\b",
    re.I,
)
_RUMOR_RE = re.compile(r"\b(?:unconfirmed rumor|unverified claim|social media rumor)\b", re.I)
_GRAPHIC_RE = re.compile(r"\b(?:graphic footage|graphic video|graphic images)\b", re.I)
_PRIVATE_RE = re.compile(r"\b(?:private distress|identify private victim|home address of)\b", re.I)
_SOCIAL_FAMILIES = {"reddit", "bluesky", "x_api", "mastodon", "social"}


def classify_global_item(source: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    """Set explicit low-value/sensitivity evidence before persistence and event ranking."""
    if source.get("scope") != "GLOBAL" or item.get("scope") != "GLOBAL":
        return item
    output = dict(item)
    evidence = dict(item.get("evidence") or {})
    identity = dict(evidence.get("global_identity") or {})
    sensitivity = dict(evidence.get("sensitivity") or {})
    title = str(item.get("title") or "")
    family = str(source.get("source_family") or "").casefold()
    official_alert = bool(
        (evidence.get("gdacs") or {}).get("alert_level") in {"Red", "Orange"}
        or (evidence.get("usgs_earthquake") or {}).get("tsunami") is True
        or (evidence.get("nhc_rss") or {}).get("watch_warning_terms")
        or (evidence.get("reliefweb_disaster") or {}).get("status") in {"current", "alert"}
    )
    reasons: list[str] = []
    if _GRAPHIC_RE.search(title):
        sensitivity["graphic_violence"] = True
        reasons.append("explicit graphic-content headline")
    if _PRIVATE_RE.search(title):
        sensitivity["private_distress"] = True
        reasons.append("explicit private-person headline")
    if _RUMOR_RE.search(title) and not official_alert:
        identity["rumor"] = True
        reasons.append("explicit unverified claim")
    if family in _SOCIAL_FAMILIES and not official_alert:
        identity.setdefault("public_value_class", "background")
        reasons.append("single social source has no verified public impact")
    if not official_alert and not identity.get("public_value_class"):
        if _ROUTINE_RE.search(title):
            identity["public_value_class"] = "routine"
            reasons.append("routine institutional or economic headline")
        elif _OPINION_RE.search(title):
            identity["public_value_class"] = "opinion"
            reasons.append("opinion or punditry headline")
        elif _DOMESTIC_RE.search(title) and not identity.get("international_impact"):
            identity["public_value_class"] = "generic_politics"
            identity["out_of_scope"] = True
            reasons.append("domestic politics without international impact evidence")
    evidence["global_identity"] = identity
    evidence["sensitivity"] = sensitivity
    evidence["global_attention_policy"] = {
        "version": 1,
        "official_alert_evidence": official_alert,
        "attention_state": "suppressed" if any(sensitivity.get(key) for key in (
            "graphic_violence", "private_distress", "doxxing", "targeted_person_tracking",
        )) else "background" if identity.get("public_value_class") or identity.get("rumor")
        else "eligible",
        "reasons": reasons or ["no low-value or sensitive signal in stored metadata"],
        "impact_from_headline_inferred": False,
    }
    output["evidence"] = evidence
    return output
