"""Bounded fixture parser for the official CPSC recall retrieval service."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

CPSC_RECALL_SERVICE = "https://www.saferproducts.gov/RestWebServices/Recall"


def _names(row: dict[str, Any], key: str, *, limit: int = 3) -> list[str]:
    values = row.get(key)
    if not isinstance(values, list):
        return []
    return [text for entry in values[:limit] if isinstance(entry, dict)
            if (text := bounded_text(entry.get("Name"), max_chars=180))]


def parse_cpsc_recalls_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    if source.get("scope") != "NATIONAL" or source.get("id") != "cpsc_recalls_api":
        raise NewsParserError("CPSC parser requires its exact NATIONAL source")
    fixture_url = str(source.get("url") or "")
    official_fixture = (
        urlsplit(fixture_url).scheme == "file"
        and source.get("official_url") == CPSC_RECALL_SERVICE
    )
    if not source.get("fixture_only") or not (
        fixture_url == CPSC_RECALL_SERVICE or official_fixture
    ):
        raise NewsParserError("CPSC parser requires the official fixture-only service")
    query = source.get("query_contract")
    if not isinstance(query, dict) or set(query) != {"recall_date_start", "recall_date_end",
                                                  "format", "timeout_seconds"}:
        raise NewsParserError("CPSC parser requires a bounded recall-date query")
    try:
        start = date.fromisoformat(query["recall_date_start"])
        end = date.fromisoformat(query["recall_date_end"])
    except (TypeError, ValueError) as exc:
        raise NewsParserError("CPSC parser requires ISO recall-date bounds") from exc
    if (query["format"] != "json" or type(query["timeout_seconds"]) is not int
            or not 1 <= query["timeout_seconds"] <= 15
            or not start <= end <= start + timedelta(days=7)):
        raise NewsParserError("CPSC parser query is outside the bounded allowlist")
    if len(payload_text.encode("utf-8")) > 1_048_576:
        raise PayloadTooLargeError("CPSC recall response exceeds the 1 MiB parser cap")
    try:
        rows = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed CPSC recall JSON: {exc}") from exc
    if not isinstance(rows, list) or len(rows) > 100:
        raise NewsParserError("CPSC recall response exceeds the 100-row cap")
    items: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or type(row.get("RecallID")) is not int:
            raise NewsParserError(f"CPSC row {index} lacks a recall ID")
        recall_id = row["RecallID"]
        if recall_id in seen_ids:
            raise NewsParserError(f"CPSC row {index} duplicates a recall ID")
        seen_ids.add(recall_id)
        recall_number = bounded_text(row.get("RecallNumber"), max_chars=30)
        title = bounded_text(row.get("Title"), max_chars=280)
        url = str(row.get("URL") or "")
        parts = urlsplit(url)
        recall_time = normalize_timestamp(row.get("RecallDate"))
        if (recall_id <= 0 or not recall_number or not title or not recall_time
                or parts.scheme != "https" or parts.hostname not in {"cpsc.gov", "www.cpsc.gov"}
                or not parts.path.startswith("/Recalls/")
                or not start <= date.fromisoformat(recall_time[:10]) <= end):
            raise NewsParserError(f"CPSC row {index} is outside the official recall contract")
        products = _names(row, "Products")
        hazards = _names(row, "Hazards")
        injuries = _names(row, "Injuries")
        remedies = _names(row, "Remedies")
        firms = _names(row, "Manufacturers") or _names(row, "Importers")
        retailers = _names(row, "Retailers", limit=2)
        hazard_text = " ".join((title, *hazards)).casefold()
        risk = (["death_risk"] if "death" in hazard_text else [])
        if "serious injury" in hazard_text or "injuries" in hazard_text:
            risk.append("injury_risk")
        score = 25 if "death_risk" in risk else 18 if "injury_risk" in risk else 10
        item = _normalize_item(source, {
            "title": title, "url": url,
            "description": "; ".join(hazards[:2]) or "CPSC consumer product recall.",
            "published_at": recall_time,
            "tags": ["official", "cpsc", "consumer_safety", "recall"],
        }, index=index)
        item["evidence"]["cpsc_recall"] = {
            "recall_id": recall_id,
            "recall_number": recall_number,
            "recall_date": recall_time,
            "last_publish_date": normalize_timestamp(row.get("LastPublishDate")),
            "products": products,
            "firm_names": firms,
            "hazards": hazards,
            "injury_report_text": injuries,
            "risk_indicators": risk,
            "remedies": remedies,
            "retailer_text": retailers,
            "distribution_scope": "not_structured_in_api",
            "public_instruction_url": url,
            "source_url": url,
            "query_bounds": dict(query),
            "fixture_only": True,
            "images_downloaded": False,
            "ranking": {"consumer_safety_score": score,
                        "basis": "CPSC title and source-provided hazard risk language"},
        }
        item["evidence"]["national_identity"] = {
            "event_type": "consumer_product_recall",
            "agency": "CPSC",
            "official_event_ids": [f"cpsc:{recall_id}"],
            "affected_states": [],
            "distribution_areas": [],
            "multi_state_impact": False,
            "distribution_basis": "not_structured_in_api",
        }
        items.append(item)
    return items
