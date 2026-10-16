"""Fixture-only FSIS recall metadata from the published API response shape."""

from __future__ import annotations

import json
import re
from html import unescape
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

FSIS_API_URL = "https://www.fsis.usda.gov/fsis/api/recall/v/1"
_RECALL_NUMBER = re.compile(r"(?:\d{3}(?:-\d{3})?-\d{4}(?:-EXP)?|PHA-\d{8}-\d{2})\Z")
_HTML_TAG = re.compile(r"<[^>]+>")
_STATE_LABEL = re.compile(r"[A-Za-z][A-Za-z .'-]{1,40}\Z")


def _boolean(value: Any) -> bool | None:
    if value is True or value == "True":
        return True
    if value is False or value == "False":
        return False
    return None


def _text(value: Any, *, max_chars: int) -> str | None:
    if not isinstance(value, str):
        return None
    return bounded_text(unescape(_HTML_TAG.sub(" ", value)), max_chars=max_chars)


def _list_text(value: Any, *, max_items: int, max_chars: int) -> list[str]:
    if not isinstance(value, list) or len(value) > max_items:
        return []
    return [text for raw in value if (text := _text(raw, max_chars=max_chars))]


def _notice_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return None
    if (parts.scheme not in {"http", "https"} or parts.hostname != "www.fsis.usda.gov"
            or parts.username or parts.password or port or parts.query or parts.fragment
            or not parts.path.startswith("/recalls-alerts/")):
        return None
    return urlunsplit(("https", "www.fsis.usda.gov", parts.path, "", ""))


def parse_fsis_recalls_json(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Parse bounded local records without inferring a detail URL or consumer action."""
    if (source.get("scope") != "NATIONAL" or source.get("id") != "fsis_recall_api"
            or source.get("parser") != "fsis_recalls_json"):
        raise NewsParserError("FSIS parser requires its exact NATIONAL source")
    url = str(source.get("url") or "")
    file_fixture = urlsplit(url).scheme == "file" and source.get("official_url") == FSIS_API_URL
    if not source.get("fixture_only") or not (url == FSIS_API_URL or file_fixture):
        raise NewsParserError("FSIS parser requires the official fixture-only API")
    if len(payload_text.encode("utf-8")) > 262_144:
        raise PayloadTooLargeError("FSIS fixture exceeds 256 KiB")
    try:
        rows = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed FSIS JSON: {exc}") from exc
    if not isinstance(rows, list) or len(rows) > 50:
        raise NewsParserError("FSIS fixture requires a list of at most 50 records")
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"FSIS row {index} must be an object")
        language = row.get("langcode")
        if language == "Spanish":
            continue
        if language != "English":
            raise NewsParserError(f"FSIS row {index} has an unverified language")
        number = _text(row.get("field_recall_number"), max_chars=30)
        title = _text(row.get("field_title"), max_chars=280)
        date = normalize_timestamp(row.get("field_recall_date"))
        detail_url = _notice_url(row.get("field_recall_url"))
        if (not number or not _RECALL_NUMBER.fullmatch(number) or number in seen
                or not title or not date or not detail_url
                or row.get("field_recall_number_export") != number):
            raise NewsParserError(f"FSIS row {index} lacks stable recall identity")
        seen.add(number)
        classification = _text(row.get("field_recall_classification"), max_chars=20)
        if classification not in {None, "Class I", "Class II", "Class III",
                                  "Public Health Alert"}:
            raise NewsParserError(f"FSIS row {index} has an unknown recall class")
        risk = _text(row.get("field_risk_level"), max_chars=40)
        if risk and risk not in {"High - Class I", "Medium - Class I", "Low - Class II",
                                 "Marginal - Class III", "Public Health Alert"}:
            raise NewsParserError(f"FSIS row {index} has an unknown risk label")
        if risk and classification and not risk.endswith(classification):
            raise NewsParserError(f"FSIS row {index} has conflicting risk and class")
        raw_states = row.get("field_states")
        if not isinstance(raw_states, list) or len(raw_states) > 20 or any(
            not isinstance(label, str) or "<" in label or ">" in label
            for label in raw_states
        ):
            raise NewsParserError(f"FSIS row {index} has invalid state labels")
        state_labels = [label.strip() for label in raw_states]
        if any(not _STATE_LABEL.fullmatch(label) for label in state_labels):
            raise NewsParserError(f"FSIS row {index} has invalid state labels")
        state_labels = list(dict.fromkeys(state_labels))
        active = _boolean(row.get("field_active_notice"))
        archived = _boolean(row.get("field_archive_recall"))
        if active is None or archived is None:
            raise NewsParserError(f"FSIS row {index} lacks lifecycle flags")
        recall_type = _text(row.get("field_recall_type"), max_chars=60)
        if recall_type not in {"Active Recall", "Closed Recall", "Public Health Alert"}:
            raise NewsParserError(f"FSIS row {index} has an unknown recall type")
        lifecycle_conflict = (
            (recall_type == "Closed Recall" and not archived)
            or (recall_type == "Active Recall" and archived)
            or (active and archived)
        )
        current_notice = not lifecycle_conflict and not archived and (
            recall_type == "Active Recall"
            or (recall_type == "Public Health Alert" and active)
        )
        products = _list_text(row.get("field_product_items"), max_items=50, max_chars=180)[:3]
        reasons = _list_text(row.get("field_recall_reason"), max_items=10, max_chars=120)[:3]
        firms = _list_text(row.get("field_establishment"), max_items=10, max_chars=120)[:3]
        source_url = FSIS_API_URL + "?" + urlencode({"field_recall_number": number})
        item = _normalize_item(source, {
            "title": title, "url": detail_url, "published_at": date,
            "description": "; ".join(reasons),
            "tags": ["official", "fsis", "food-safety",
                     "public-health-alert" if recall_type == "Public Health Alert" else "recall"],
        }, index=index)
        item["evidence"]["fsis_recall"] = {
            "recall_number": number,
            "recall_date": date,
            "last_modified_date": normalize_timestamp(row.get("field_last_modified_date")),
            "recall_type": recall_type,
            "recall_classification": classification,
            "risk_level": risk,
            "recall_reasons": reasons,
            "product_items": products,
            "establishment_names": firms,
            "distribution_state_labels": state_labels,
            "active_notice": active,
            "archive_recall": archived,
            "lifecycle_conflict": lifecycle_conflict,
            "current_notice": current_notice,
            "closed_date": normalize_timestamp(row.get("field_closed_date")),
            "closed_year": _text(row.get("field_closed_year"), max_chars=4),
            "source_record_query_url": source_url,
            "source_url": detail_url,
            "public_instruction_url": detail_url,
            "detail_url_verified": True,
            "instruction_content_parsed": False,
            "summary_html_stored": False,
            "company_contact_stored": False,
            "fixture_only": True,
        }
        item["evidence"]["national_identity"] = {
            "event_type": (
                "food_public_health_alert" if recall_type == "Public Health Alert"
                else "food_recall"
            ),
            "agency": "FSIS",
            "official_event_ids": [f"fsis:{number.lower()}"],
            "affected_states": [],
            "distribution_areas": state_labels,
            "multi_state_impact": False,
            "multi_state_distribution": len(state_labels) > 1,
            "distribution_basis": "FSIS field_states; distribution, not confirmed consumption",
            "high_risk_recall": current_notice and classification == "Class I",
            "official_public_alert": current_notice and recall_type == "Public Health Alert",
            "official_severity_score": (
                25 if current_notice and classification == "Class I" else 0
            ),
        }
        items.append(item)
    return items
