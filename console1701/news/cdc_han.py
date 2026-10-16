"""Offline CDC HAN notice metadata from the archive's first-party JSON search view."""

from __future__ import annotations

import json
import re
from html import unescape
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, _normalize_item

SEARCH_URL = "https://search.cdc.gov/srch/internet_wcms/select"
ARCHIVE_URL = "https://www.cdc.gov/han/php/notices/index.html"
QUERY = {
    "q": "*:*",
    "fq": "permalink:*han/php/notices/*",
    "rows": "20",
    "sort": "cdc_last_reviewed_date_dt desc",
    "fl": (
        "id,title_txt,permalink,cdc_last_reviewed_date_dt,cdc_article_date_dt,"
        "cdc_dfe_template_str,excerpt_txt,cdc_related_image_str"
    ),
    "wt": "json",
}
_NOTICE_PATH = re.compile(r"/han/php/notices/han(\d{5})\.html\Z")
_BADGE_TYPES = {
    "HAN-Health-Alert.png": "Health Alert",
    "HAN-Health-Advisory.png": "Health Advisory",
    "logo-han-health-update.png": "Health Update",
}


def _plain(value: Any, *, max_chars: int) -> str | None:
    if not isinstance(value, str):
        return None
    text = unescape(re.sub(r"</?em>", "", value, flags=re.I))
    if "<" in text or ">" in text:
        return None
    return bounded_text(text, max_chars=max_chars)


def parse_cdc_han_search_fixture(source: dict[str, Any], payload_text: str) -> list[dict[str, Any]]:
    """Store notice index metadata; badges are hints, never alert or impact proof."""
    if (source.get("scope") != "NATIONAL" or source.get("id") != "cdc_han_notices"
            or source.get("source_family") != "cdc"
            or source.get("official_status") != "official"
            or source.get("official_url") != SEARCH_URL
            or not str(source.get("url") or "").startswith("file://")
            or source.get("query_contract") != QUERY):
        raise NewsParserError("CDC HAN fixture requires its exact official search contract")
    if len(payload_text.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("CDC HAN fixture exceeds 64 KiB")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed CDC HAN search JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise NewsParserError("CDC HAN search response must be an object")
    header = payload.get("responseHeader") or {}
    response = payload.get("response") or {}
    rows = response.get("docs")
    if (not isinstance(header, dict) or header.get("status") != 0
            or header.get("params") != QUERY or not isinstance(response, dict)
            or response.get("start") != 0 or not isinstance(rows, list)
            or len(rows) > 20 or not isinstance(response.get("numFound"), int)
            or response["numFound"] < len(rows)):
        raise NewsParserError("CDC HAN fixture lacks its bounded search response shape")
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise NewsParserError(f"CDC HAN row {index} is not an object")
        url = row.get("permalink")
        try:
            parts = urlsplit(str(url or ""))
            port = parts.port
        except ValueError as exc:
            raise NewsParserError(f"CDC HAN row {index} has an invalid URL") from exc
        if (parts.scheme != "https" or parts.hostname != "www.cdc.gov"
                or parts.username or parts.password or port or parts.query or parts.fragment):
            raise NewsParserError(f"CDC HAN row {index} has an invalid CDC URL")
        match = _NOTICE_PATH.fullmatch(parts.path)
        if not match:
            if parts.path == "/han/php/notices/index.html":
                continue
            raise NewsParserError(f"CDC HAN row {index} is outside the notice collection")
        notice_id = f"CDCHAN-{match.group(1)}"
        title = _plain(row.get("title_txt"), max_chars=280)
        excerpt = _plain(row.get("excerpt_txt"), max_chars=320)
        reviewed = normalize_timestamp(row.get("cdc_last_reviewed_date_dt"))
        article_date = normalize_timestamp(row.get("cdc_article_date_dt"))
        badge_urls = row.get("cdc_related_image_str")
        if (not title or not reviewed or not article_date or notice_id in seen
                or row.get("cdc_dfe_template_str") != ["cdc_health_alert"]
                or not isinstance(badge_urls, list) or len(badge_urls) > 2):
            raise NewsParserError(f"CDC HAN row {index} lacks stable notice metadata")
        seen.add(notice_id)
        badge = badge_urls[0] if len(badge_urls) == 1 else None
        badge_name = urlsplit(str(badge or "")).path.rsplit("/", 1)[-1]
        message_type_hint = (
            _BADGE_TYPES.get(badge_name)
            if isinstance(badge, str)
            and badge.startswith("https://www.cdc.gov/han/media/images/") else None
        )
        item = _normalize_item(source, {
            "title": title, "url": url, "description": excerpt,
            "published_at": reviewed,
            "tags": ["official", "cdc", "han", "public-health", "notice-metadata"],
        }, index=index)
        item["evidence"]["cdc_han"] = {
            "notice_id": notice_id, "archive_url": ARCHIVE_URL,
            "search_url": SEARCH_URL, "notice_url": url,
            "index_last_reviewed_at": reviewed, "index_article_date_at": article_date,
            "date_basis": "CDC search index last-reviewed date; distribution time unverified",
            "message_type": None, "message_type_hint": message_type_hint,
            "message_type_hint_basis": "index badge filename; notice body not fetched",
            "affected_population": None, "jurisdiction": None,
            "public_instruction_url": None, "preliminary_status": "unverified",
            "active_alert_verified": False, "public_impact_verified": False,
            "body_stored": False,
        }
        item["evidence"]["national_identity"] = {
            "event_type": "public_health_notice", "agency": "CDC",
            "official_event_ids": [f"cdc_han:{notice_id.casefold()}"],
            "national_impact": False, "multi_state_impact": False,
            "impact_scope_basis": (
                "HAN archive listing does not verify affected geography or public impact"
            ),
        }
        items.append(item)
    return items
