"""First-pass NATIONAL attention classification from stored source metadata."""

from __future__ import annotations

import re
from typing import Any

_ROUTINE_RE = re.compile(
    r"\b(?:routine press release|weekly roundup|personnel announcement|"
    r"new deputy director|staff appointment|personnel appointment|agency anniversary|"
    r"ceremonial remarks)\b", re.I
)
_OPINION_RE = re.compile(r"\b(?:opinion|editorial|punditry|commentary)\s*:|\bpundit\b", re.I)
_POLITICS_RE = re.compile(
    r"\b(?:campaign rally|partisan fundraiser|candidate endorsement)\b", re.I
)
_COURT_ROUTINE_RE = re.compile(
    r"\b(?:routine court filing|motion to extend|docket entry|procedural filing)\b", re.I
)
_SOCIAL_FAMILIES = {"reddit", "bluesky", "x_api", "mastodon", "social"}
_ECONOMIC_FAMILIES = {"bls", "bea", "fred", "federal_reserve", "treasury_fiscal", "census"}
_AGENCY_PRESS_FAMILIES = {"agency_press", "agency_news", "federal_press"}


def classify_national_item(source: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    """Classify attention only; retain item metadata and the explanation for audit."""
    evidence = item.get("evidence") or {}
    identity = dict(evidence.get("national_identity") or {})
    title = str(item.get("title") or "")
    family = str(source.get("source_family") or "").strip().casefold()
    official_identity = source.get("official_status") == "official"
    reasons: list[str] = []
    elevated = False
    impact_score = 0
    if (nws := evidence.get("nws_alert") or {}):
        if nws.get("status") == "Actual" and str(nws.get("severity") or "") in {
            "Extreme", "Severe"
        }:
            elevated = True
            impact_score = 25 if nws.get("instruction") else 18
            reasons.append("official severe NWS alert")
    if (recall := evidence.get("nhtsa_recall") or {}):
        elevated = elevated or bool(recall.get("park_it") or recall.get("park_outside"))
        impact_score = max(impact_score, 30 if elevated else 15)
        reasons.append("official NHTSA safety recall")
    if (cpsc := evidence.get("cpsc_recall") or {}):
        risk = set(cpsc.get("risk_indicators") or [])
        elevated = elevated or bool(risk & {"death_risk", "injury_risk"})
        impact_score = max(impact_score, 25 if "death_risk" in risk else
                           18 if "injury_risk" in risk else 10)
        reasons.append("official CPSC product recall with source-stated risk")
    if evidence.get("cisa_kev"):
        elevated = True
        impact_score = max(impact_score, 12)
        reasons.append("official known-exploited vulnerability")
    if (faa := evidence.get("faa_nas_status") or {}) and faa.get("events"):
        elevated = True
        impact_score = max(impact_score, 25)
        reasons.append("official active FAA NAS disruption")
    if (federal_register := evidence.get("federal_register") or {}):
        impact_score = max(
            impact_score,
            min(25, int((federal_register.get("ranking") or {}).get("public_impact_score") or 0)),
        )
        elevated = elevated or impact_score >= 15
        reasons.append("configured Federal Register impact filter")
    if official_identity and identity.get("official_public_alert") is True:
        elevated = True
        impact_score = max(impact_score, 25)
        reasons.append("explicit official public alert")
    if official_identity and identity.get("official_disaster_declaration") is True:
        elevated = True
        impact_score = max(impact_score, 22)
        reasons.append("explicit federal disaster declaration")
    if official_identity and identity.get("public_health_action_guidance") is True:
        elevated = True
        impact_score = max(impact_score, 22)
        reasons.append("explicit public-health action guidance")
    if official_identity and identity.get("cyber_emergency_directive") is True:
        elevated = True
        impact_score = max(impact_score, 25)
        reasons.append("explicit cyber emergency directive")
    if official_identity and identity.get("high_risk_recall") is True:
        elevated = True
        impact_score = max(impact_score, 25)
        reasons.append("explicit high-risk recall classification")

    suppressed_reason: str | None = None
    if not elevated:
        if family in _ECONOMIC_FAMILIES:
            allowed = source.get("economic_release_terms") or []
            if not isinstance(allowed, list) or not any(
                isinstance(term, str) and term.strip() and term.casefold() in title.casefold()
                for term in allowed
            ):
                suppressed_reason = "economic release is not in the configured title allowlist"
        elif family in _SOCIAL_FAMILIES and not identity.get("verified_public_impact"):
            suppressed_reason = "vague social-only report without verified public impact"
        elif family in _AGENCY_PRESS_FAMILIES:
            suppressed_reason = "routine agency press item without verified public impact"
        elif _OPINION_RE.search(title):
            suppressed_reason = "opinion or commentary"
        elif _POLITICS_RE.search(title):
            suppressed_reason = "generic campaign politics"
        elif _ROUTINE_RE.search(title):
            suppressed_reason = "routine agency or personnel announcement"
        elif _COURT_ROUTINE_RE.search(title):
            suppressed_reason = "routine procedural court filing"
        elif identity.get("local_only") is True and not identity.get("national_impact"):
            suppressed_reason = "local report without national impact evidence"
        elif identity.get("public_value_class") in {"routine", "opinion", "speculation"}:
            suppressed_reason = "source-classified low public value"
    if suppressed_reason:
        reasons.append(suppressed_reason)
    return {
        "version": 1,
        "attention_state": "suppressed" if suppressed_reason else
        "elevated" if elevated else "background",
        "suppressed": bool(suppressed_reason),
        "reasons": reasons or ["no source-confirmed elevation or low-value rule"],
        "official_impact_score": impact_score,
        "headline_only_severity_inferred": False,
        "retained_for_audit": True,
    }
