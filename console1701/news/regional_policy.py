"""Conservative privacy and public-impact rules for REGIONAL metadata."""

from __future__ import annotations

import re
from typing import Any

_ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+(?:(?:N|S|E|W|NE|NW|SE|SW)\s+)?"
    r"(?:[A-Za-z0-9][A-Za-z0-9.'-]*\s+){1,5}"
    r"(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Blvd|Boulevard|"
    r"Way|Place|Pl)\b\.?(?:\s+(?:Apt|Unit|Suite|#)\s*[A-Za-z0-9-]+)?",
    re.I,
)
_LOW_ACUITY_RE = re.compile(
    r"\b(?:routine|minor|small|isolated|single.home|residential|neighborhood)\b", re.I
)
_OUTAGE_RE = re.compile(r"\b(?:outage|power loss|power restored|service interruption)\b", re.I)
_PUBLIC_IMPACT_RE = re.compile(
    r"\b(?:evacuat\w*|major closure|widespread|countywide|regional emergency|"
    r"boil water|shelter in place|multiple counties)\b", re.I
)
_SOCIAL_FAMILIES = {"reddit", "bluesky", "x_api", "mastodon", "social"}


def _score(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        return _ADDRESS_RE.sub("[street address withheld]", value)
    if isinstance(value, list):
        return [_redact(entry) for entry in value]
    if isinstance(value, dict):
        return {key: _redact(entry) for key, entry in value.items()}
    return value


def apply_regional_privacy_policy(
    source: dict[str, Any], item: dict[str, Any]
) -> dict[str, Any]:
    """Redact exact addresses before storage and explain low-value attention limits."""
    if source.get("scope") != "REGIONAL" or item.get("scope") != "REGIONAL":
        return item
    evidence = item.get("evidence") or {}
    nws = evidence.get("nws_alert") or {}
    wsdot = evidence.get("wsdot_alert") or {}
    usgs = evidence.get("usgs_earthquake") or {}
    county = evidence.get("king_county_emergency") or {}
    title = str(item.get("title") or "")
    description = str(item.get("description") or "")
    text = f"{title} {description}"
    family = str(source.get("source_family") or "").casefold()
    official_impact = bool(
        _score((nws.get("ranking") or {}).get("total_alert_weight")) >= 20
        or _score((wsdot.get("ranking") or {}).get("public_impact_score")) >= 15
        or _score((usgs.get("ranking") or {}).get("regional_seismic_weight")) >= 25
        or _score((county.get("ranking") or {}).get("public_impact_score")) >= 15
    )
    public_claim = bool(_PUBLIC_IMPACT_RE.search(text))
    verified_impact = official_impact
    outage_low_value = bool(_OUTAGE_RE.search(text) and _LOW_ACUITY_RE.search(text))
    social_only = family in _SOCIAL_FAMILIES
    routine_safety = bool(_LOW_ACUITY_RE.search(text) and family in {
        "public_safety", "police", "fire", "regional_news",
    })
    low_acuity_private = bool(
        not verified_impact and (outage_low_value or routine_safety or social_only)
    )
    redacted = _redact({
        "title": item.get("title"), "description": item.get("description"),
        "tags": item.get("tags"), "evidence": evidence,
    })
    changed = redacted["title"] != item.get("title") or (
        redacted["description"] != item.get("description")
        or redacted["evidence"] != evidence or redacted["tags"] != item.get("tags")
    )
    output = dict(item)
    output.update(redacted)
    output["evidence"] = dict(output["evidence"])
    output["evidence"]["privacy"] = {
        **dict(output["evidence"].get("privacy") or {}),
        "redaction_applied": changed,
        "redaction_basis": "exact_street_address" if changed else None,
        "low_acuity_private": low_acuity_private,
        "attention_state": "background" if low_acuity_private else "eligible",
        "public_impact_basis": "official_alert_metadata" if official_impact else
        "headline_claim_only" if public_claim else "none",
        "social_only": social_only,
        "residential_outage_below_threshold": outage_low_value and not verified_impact,
        "address_pattern_redacted": changed,
    }
    return output
