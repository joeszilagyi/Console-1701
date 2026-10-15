"""Conservative sensitivity classification before ORBITAL item storage."""

from __future__ import annotations

import re
from typing import Any

_CLASSIFIED_RE = re.compile(
    r"\b(classified|spy|military)\s+(satellite|spacecraft|orbital\s+object)\b", re.I
)
_PRIVATE_TRACKING_RE = re.compile(
    r"\b(track(?:ing)?|locat(?:e|ion|ing)|monitor(?:ing)?)\s+"
    r"(?:a\s+)?private\s+(?:operator|satellite|spacecraft)\b", re.I
)
_PANIC_RE = re.compile(
    r"\b(doomsday|guaranteed\s+(?:impact|collision)|imminent\s+(?:impact|collision)|"
    r"will\s+(?:hit|strike)\s+(?:earth|a\s+city))\b", re.I
)
_RUMOR_RE = re.compile(r"\b(rumou?r(?:ed|s)?|unconfirmed|leaked|speculat(?:e|ion|ive))\b", re.I)
_HARD_FLAGS = {
    "tactical_tracking", "restricted_source", "classified_inference",
    "private_operator_monitoring", "object_surveillance",
}


def classify_orbital_item(source: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with bounded flags; redact hard-sensitive text before storage."""
    classified = dict(item)
    evidence = dict(item.get("evidence") or {})
    safety = dict(evidence.get("orbital_safety") or {})
    identity = dict(evidence.get("orbital_identity") or {})
    title = str(item.get("title") or "")
    description = str(item.get("description") or "")
    text = f"{title} {description}"[:1200]
    event_type = str(identity.get("event_type") or "").lower()
    source_class = str(source.get("source_class") or "").lower()
    verification = str(source.get("verification_status") or "").lower()
    if source_class in {"official_satellite_catalog", "official_conjunction_awareness"}:
        safety["tactical_tracking"] = True
    if source_class == "restricted_auth_candidate" or verification == "restricted_auth_required":
        safety["restricted_source"] = True
    if source_class == "social_candidate":
        safety["social_only_claim"] = True
    if _CLASSIFIED_RE.search(text):
        safety["classified_inference"] = True
    if _PRIVATE_TRACKING_RE.search(text):
        safety["private_operator_monitoring"] = True
    if _RUMOR_RE.search(text) and event_type in {
        "launch_update", "mission_update", "reentry", "orbital_debris",
    }:
        if event_type == "launch_update":
            safety["launch_rumor"] = True
        identity["rumor"] = True
        identity["public_value_class"] = "speculation"
    if _PANIC_RE.search(text):
        if event_type == "neo_close_approach":
            safety["neo_panic_language"] = True
        elif event_type == "reentry":
            safety["sensitive_reentry"] = True
        elif event_type == "orbital_debris":
            safety["debris_fear_framing"] = True
    if source_class == "official_orbital_debris" and event_type != "orbital_debris":
        # An unscoped debris source is useful as reference, not a fear ticker.
        identity["public_value_class"] = "background"
    if _HARD_FLAGS & {key for key, value in safety.items() if value is True}:
        classified["title"] = "Sensitive orbital tracking claim"
        classified["description"] = None
        safety["redacted_before_storage"] = True
    evidence["orbital_safety"] = safety
    evidence["orbital_identity"] = identity
    classified["evidence"] = evidence
    return classified
