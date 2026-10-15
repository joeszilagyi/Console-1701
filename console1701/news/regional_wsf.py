"""Fixture-only WSF Schedule API alert model, based on the official REST schema."""

from __future__ import annotations

import json
import re
from typing import Any

from console1701.news.normalize import bounded_text
from console1701.news.parsers import (
    NewsParserError,
    PayloadTooLargeError,
    _normalize_item,
    _wsdot_plain_text,
    _wsdot_timestamp,
)

API_URL = "https://www.wsdot.wa.gov/ferries/api/schedule/rest/alerts"
BULLETIN_PAGE = "https://www.wsdot.com/ferries/schedule/bulletin.aspx"
MAX_BYTES = 65_536
_CANCEL = re.compile(r"\b(cancel(?:led|ed|lation)?|out of service|suspend(?:ed|sion)?)\b", re.I)
_DELAY = re.compile(r"\b(delay(?:ed|s)?|behind schedule|wait time|one.hour wait)\b", re.I)
_NEGATED = re.compile(
    r"\b(?:no|not|without)\s+(?:\w+\s+){0,2}"
    r"(?:cancellations?|cancelled|delays?|delayed|suspensions?)\b",
    re.I,
)


def _text(value: Any, limit: int) -> str | None:
    return bounded_text(_wsdot_plain_text(str(value or "")), max_chars=limit)


def parse_wsf_alerts_fixture(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    if source.get("scope") != "REGIONAL" or source.get("id") != "wsf_bulletins":
        raise NewsParserError("WSF alerts fixture requires its REGIONAL registry source")
    if not str(source.get("url") or "").startswith("file://"):
        raise NewsParserError("WSF alerts are fixture-only until API access is reviewed")
    if source.get("official_url") != API_URL:
        raise NewsParserError("WSF fixture requires the exact documented alerts operation")
    if len(payload_text.encode("utf-8")) > MAX_BYTES:
        raise PayloadTooLargeError("WSF alerts fixture exceeds 64 KiB")
    try:
        rows = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError("Malformed WSF alerts JSON fixture") from exc
    if not isinstance(rows, list) or len(rows) > 100:
        raise NewsParserError("WSF alerts response must be a bounded JSON array")
    seen: set[int] = set()
    items: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"WSF alert {index} must be an object")
        bulletin_id = row.get("BulletinID")
        if type(bulletin_id) is not int or bulletin_id <= 0 or bulletin_id in seen:
            raise NewsParserError(f"WSF alert {index} has invalid or repeated BulletinID")
        seen.add(bulletin_id)
        if row.get("BulletinFlag") is not True:
            continue
        title = _text(row.get("AlertFullTitle"), 240)
        published = _wsdot_timestamp(row.get("PublishDate"))
        if not title or not published:
            raise NewsParserError(f"WSF bulletin {bulletin_id} needs title and PublishDate")
        route_ids = row.get("AffectedRouteIDs")
        if route_ids is None:
            route_ids = []
        if not isinstance(route_ids, list) or len(route_ids) > 30 or any(
            type(route_id) is not int or route_id <= 0 for route_id in route_ids
        ):
            raise NewsParserError(f"WSF bulletin {bulletin_id} has invalid routes")
        route_ids = list(dict.fromkeys(route_ids))
        all_routes = row.get("AllRoutesFlag") is True
        if not route_ids and not all_routes:
            continue
        disruption = _text(row.get("DisruptionDescription"), 300)
        bulletin = _text(row.get("BulletinText"), 300)
        text = _NEGATED.sub("", " ".join((title, disruption or "", bulletin or "")))
        impact = (
            "cancellation" if _CANCEL.search(text) else
            "delay" if _DELAY.search(text) else "notice"
        )
        impact_score = {"cancellation": 25, "delay": 15, "notice": 0}[impact]
        # The public bulletin page has no verified per-alert URL. The query is an
        # internal dedupe key only; item URL stays the real public bulletin page.
        identity_url = f"{BULLETIN_PAGE}?fixture_bulletin_id={bulletin_id}"
        item = _normalize_item(source, {
            "title": title,
            "url": BULLETIN_PAGE,
            "canonical_url": identity_url,
            "description": disruption or bulletin,
            "published_at": published,
            "tags": ["official", "regional", "ferry", "wsf", impact],
        }, index=index)
        item["evidence"]["wsf_alert"] = {
            "bulletin_id": bulletin_id,
            "bulletin_flag": True,
            "alert_type": _text(row.get("AlertType"), 80),
            "affected_route_ids": route_ids,
            "all_routes": all_routes,
            "terminal": None,
            "vessel": None,
            "status": impact,
            "published_at": published,
            "start_at": None,
            "end_at": None,
            "source_url": BULLETIN_PAGE,
            "api_operation": API_URL,
            "canonical_url_basis": "synthetic_fixture_dedupe_key_not_official_per_alert_link",
            "ranking": {"public_impact_score": impact_score,
                        "basis": "bounded bulletin cancellation/delay text"},
        }
        item["evidence"]["regional_identity"] = {
            "ferry_route": [f"wsf-route:{route_id}" for route_id in route_ids],
        }
        items.append(item)
    return items
