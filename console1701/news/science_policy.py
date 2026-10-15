"""Conservative COSMIC attention rules applied before local persistence."""

from __future__ import annotations

import re
from typing import Any

_UFO_RE = re.compile(r"\b(?:ufo|ufos|uap|uaps|unidentified flying object)\b", re.I)
_ALIEN_CLAIM_RE = re.compile(
    r"\b(?:alien|extraterrestrial)\s+life\s+(?:found|discovered|confirmed|proven)\b|"
    r"\b(?:found|discovered|confirmed|proven)\s+(?:alien|extraterrestrial)\s+life\b|"
    r"\b(?:nasa|esa)\s+(?:confirms?|proves?)\s+aliens?\b|"
    r"\blife\s+(?:found|discovered|confirmed)\s+(?:on|beyond|outside)\s+(?:earth|mars|"
    r"the solar system)\b",
    re.I,
)
_RUMOR_RE = re.compile(r"\b(?:unverified|unconfirmed|social media)\s+(?:rumor|claim)\b", re.I)
_HYPE_RE = re.compile(
    r"\b(?:shocking|mind[- ]blowing|scientists? baffled|you won't believe)\b", re.I
)
_IMAGE_RE = re.compile(r"\b(?:stunning image|photo gallery|see (?:these )?photos)\b", re.I)
_EXPLAINER_RE = re.compile(r"\b(?:what is|how to|beginner'?s guide|explained:)\b", re.I)
_OLD_PAPER_RE = re.compile(r"\b(?:old|archival|previous)\s+(?:study|paper|research)\b", re.I)
_UNREVIEWED_RE = re.compile(
    r"\b(?:unreviewed|not peer[- ]reviewed)\s+preprint\b|"
    r"\bpreprint\s+(?:claims?|purports?|suggests?)\b", re.I
)


def classify_science_item(source: dict[str, Any], item: dict[str, Any]) -> dict[str, Any] | None:
    """Drop explicit unsupported claims; label low-value metadata without inferring discovery."""
    if source.get("scope") != "SYSTEM_SOLAR" or item.get("scope") != "SYSTEM_SOLAR":
        return item
    title = str(item.get("title") or "")
    description = str(item.get("description") or "")
    text = f"{title} {description}"
    if _UFO_RE.search(text) or _ALIEN_CLAIM_RE.search(text) or _RUMOR_RE.search(text):
        return None
    reasons: list[str] = []
    if _HYPE_RE.search(title):
        reasons.append("sensational headline language")
    if _IMAGE_RE.search(title):
        reasons.append("image-led headline without an explicit science result")
    if _EXPLAINER_RE.search(title):
        reasons.append("generic explainer")
    if _OLD_PAPER_RE.search(title):
        reasons.append("old or archival study described as current")
    if _UNREVIEWED_RE.search(text):
        reasons.append("unreviewed preprint claim")
    output = dict(item)
    evidence = dict(item.get("evidence") or {})
    if (evidence.get("gracedb_public_alert") or {}).get("status") == "retracted":
        reasons.append("official GraceDB VOEvent retraction")
    if (
        evidence.get("exoplanet_archive") or evidence.get("mast_caom")
        or evidence.get("pds_collection") or "archive_metadata" in (item.get("tags") or [])
    ):
        reasons.append("archive metadata update without a source-backed science release")
    identity = dict(evidence.get("science_identity") or {})
    if reasons:
        identity["public_value_class"] = "background"
    evidence["science_identity"] = identity
    evidence["science_safety"] = {
        "attention_state": "background" if reasons else "eligible",
        "reasons": reasons or ["no explicit hype or low-value signal in bounded metadata"],
        "scientific_meaning_inferred_from_headline": False,
    }
    output["evidence"] = evidence
    return output
