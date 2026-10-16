"""Fixture-only Minor Planet Center MPEC search-result metadata."""

from __future__ import annotations

import json
import re
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text

MPEC_API_URL = "https://data.minorplanetcenter.net/api/mpecs"
_MPEC_ID = re.compile(r"20\d{2}-[A-Z]\d{1,3}\Z")
_OBJECT_TITLE = re.compile(r"20\d{2} [A-Z]{1,2}\d{0,3}\Z")
_ROUTINE = re.compile(r"\b(daily orbit update|monthly list|observable objects)\b", re.I)


def parse_mpc_mpec_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Preserve publication identity without reading or storing circular bodies."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    if source.get("id") != "mpc_mpecs_api" or source.get("scope") != "ORBITAL":
        raise NewsParserError("MPC MPEC parser requires registered ORBITAL API identity")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed MPC MPEC JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise NewsParserError("MPC MPEC JSON must be an object")
    request = payload.get("request")
    results = payload.get("results")
    terms = request.get("terms") if isinstance(request, dict) else None
    if (not isinstance(terms, list) or len(terms) != 1
            or not isinstance(terms[0], str) or not 1 <= len(terms[0]) <= 40
            or any(character in terms[0] for character in ("%", "*"))
            or not isinstance(results, dict) or set(results) != {terms[0]}):
        raise NewsParserError("MPC MPEC fixture requires one exact bounded search term")
    rows = results[terms[0]]
    if not isinstance(rows, list) or len(rows) > 20:
        raise NewsParserError("MPC MPEC search results must be a bounded array")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        mpec_id = bounded_text(row.get("fullname"), max_chars=20)
        title = bounded_text(row.get("title"), max_chars=120)
        url = str(row.get("link") or "")
        parts = urlsplit(url)
        if (not mpec_id or not _MPEC_ID.fullmatch(mpec_id) or mpec_id in seen
                or not title or _ROUTINE.search(title)
                or parts.scheme != "https"
                or parts.hostname not in {"minorplanetcenter.net", "www.minorplanetcenter.net"}
                or not parts.path.startswith("/mpec/") or parts.username or parts.password):
            continue
        try:
            published = parsedate_to_datetime(str(row.get("pubdate") or ""))
        except (TypeError, ValueError):
            continue
        if published.tzinfo is None:
            continue
        published_at = published.isoformat()
        seen.add(mpec_id)
        item = _normalize_item(source, {
            "title": f"MPC MPEC {mpec_id}: {title}",
            "url": url,
            "description": "MPC publication metadata; no close approach or impact implied.",
            "published_at": published_at,
        }, index=index)
        item["evidence"]["mpc_mpec"] = {
            "mpec_id": mpec_id,
            "notice_title": title,
            "published_at": published_at,
            "source_url": MPEC_API_URL,
            "circular_url": url,
            "body_stored": False,
            "risk_framing": "publication_not_impact_prediction",
        }
        item["evidence"]["orbital_identity"] = {
            "event_type": "minor_planet_notice",
            "object_id": mpec_id,
            "mpc_designation": title if _OBJECT_TITLE.fullmatch(title) else None,
            "public_value_class": "background",
        }
        items.append(item)
    return items
