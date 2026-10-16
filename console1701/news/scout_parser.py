"""Fixture-only NASA/JPL Scout summary metadata parser."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

from console1701.news.normalize import bounded_text

SCOUT_URL = "https://ssd-api.jpl.nasa.gov/scout.api"
_DESIGNATION = re.compile(r"[A-Za-z0-9]{3,24}\Z")


def parse_jpl_scout_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Keep provisional object identity; never promote Scout scores to risk."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    if (str(source.get("scope") or "").upper() != "ORBITAL"
            or source.get("id") != "jpl_scout_api"):
        raise NewsParserError("JPL Scout parser requires its ORBITAL source identity")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed JPL Scout JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise NewsParserError("JPL Scout JSON must be an object")
    signature = payload.get("signature")
    if (not isinstance(signature, dict)
            or signature.get("source") != "NASA/JPL Scout API"
            or str(signature.get("version")) != "1.3"):
        raise NewsParserError("JPL Scout signature must identify API version 1.3")
    try:
        count = int(payload.get("count"))
    except (TypeError, ValueError) as exc:
        raise NewsParserError("JPL Scout count must be an integer") from exc
    rows = payload.get("data", [])
    if (count < 0 or count > 200 or not isinstance(rows, list)
            or len(rows) != count):
        raise NewsParserError("JPL Scout summary data must be a bounded count-matched array")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        designation = bounded_text(row.get("objectName"), max_chars=24)
        if not designation or not _DESIGNATION.fullmatch(designation) or designation in seen:
            continue
        try:
            observations = int(row.get("nObs"))
        except (TypeError, ValueError):
            continue
        if observations < 1 or observations > 100000:
            continue
        last_run = bounded_text(row.get("lastRun"), max_chars=32)
        if not last_run or not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?", last_run):
            continue
        try:
            datetime.strptime(
                last_run, "%Y-%m-%d %H:%M:%S" if len(last_run) == 19 else "%Y-%m-%d %H:%M"
            )
        except ValueError:
            continue
        seen.add(designation)
        item = _normalize_item(source, {
            "title": f"JPL Scout provisional object: {designation}",
            "url": f"{SCOUT_URL}?{urlencode({'tdes': designation})}",
            "description": (
                f"Scout summary lists {observations} observations for this provisional object. "
                "This entry does not establish an Earth impact prediction."
            ),
        }, index=index)
        item["evidence"]["jpl_scout"] = {
            "provisional_designation": designation,
            "observation_count": observations,
            "source_last_run": last_run,
            "source_last_run_timezone": "unspecified",
            "source_url": SCOUT_URL,
            "api_version": "1.3",
            "risk_framing": "provisional_candidate_not_impact_prediction",
        }
        item["evidence"]["orbital_identity"] = {
            "event_type": "neo_candidate",
            "object_id": designation,
            "public_value_class": "background",
        }
        items.append(item)
    return items
