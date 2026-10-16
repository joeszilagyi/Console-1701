"""Offline CDC HAN index metadata and bounded official-page observations."""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

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
_PAGE_BADGE_TYPES = {
    "CDC Health Advisory": "Health Advisory",
    "This is an official CDC health update": "Health Update",
}
_OBSERVED_TYPE_PHRASES = {
    "Health Alert Network (HAN) Health Advisory": "Health Advisory",
    "This Health Advisory": "Health Advisory",
    "is issuing this Health Advisory": "Health Advisory",
    "Health Alert Network (HAN) Health Update": "Health Update",
}
_EASTERN = ZoneInfo("America/New_York")


def _distribution_instant(detail: dict[str, str | None] | None) -> str | None:
    """Convert a printed ET wall time only when its distribution date is known."""
    if not detail or not detail["date"] or not detail["time"]:
        return None
    local_date = date.fromisoformat(detail["date"])
    local_time = datetime.strptime(detail["time"], "%I:%M %p ET").time()
    return datetime.combine(local_date, local_time, _EASTERN).astimezone(UTC).isoformat()


class _NoticeSummary(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.badges: list[tuple[str, str]] = []
        self.anchors: list[dict[str, str | None]] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.text.append(value)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "img":
            attributes = dict(attrs)
            self.badges.append((attributes.get("src") or "", attributes.get("alt") or ""))
        elif tag == "a":
            self.anchors.append(dict(attrs))


def _page_summary(summary: Any, lead: Any, anchor: Any,
                  notice_id: str) -> tuple[str, str, str | None]:
    if (not isinstance(summary, str) or len(summary.encode("utf-8")) > 4096
            or summary.count('data-section="cdc_health_alert_summary"') != 1):
        raise NewsParserError("CDC HAN notice summary lacks bounded page provenance")
    parsed = _NoticeSummary()
    parsed.feed(summary)
    if (len(parsed.text) != 4 or parsed.text[:2] != [
        "At a glance", "Distributed via the CDC Health Alert Network"
    ] or parsed.text[3] != notice_id or len(parsed.badges) != 1):
        raise NewsParserError("CDC HAN notice summary lacks distribution fields")
    try:
        distribution_date = datetime.strptime(parsed.text[2], "%B %d, %Y").date().isoformat()
    except ValueError as exc:
        raise NewsParserError("CDC HAN notice summary has invalid distribution date") from exc
    badge_src, badge_alt = parsed.badges[0]
    badge_type = _PAGE_BADGE_TYPES.get(badge_alt)
    if (not badge_src.startswith("/han/media/images/") or ".." in badge_src
            or not badge_type):
        raise NewsParserError("CDC HAN notice summary has unverified message type")
    if not isinstance(lead, str) or len(lead.encode("utf-8")) > 4096:
        raise NewsParserError("CDC HAN notice summary lead is invalid")
    parsed_lead = _NoticeSummary()
    parsed_lead.feed(lead)
    lead_text = re.sub(r"\s+", " ", " ".join(parsed_lead.text))
    if (not lead.lstrip().startswith("<p>") or not lead.rstrip().endswith("</p>")
            or ("The Centers for Disease Control and Prevention (CDC) is issuing this "
                f"Health Alert Network (HAN) {badge_type}") not in lead_text):
        raise NewsParserError("CDC HAN notice lead conflicts with message type")
    public_anchor = None
    if anchor is not None:
        if (not isinstance(anchor, str) or len(anchor.encode("utf-8")) > 512
                or not anchor.lstrip().startswith("<a ")
                or not anchor.rstrip().endswith("</a>")):
            raise NewsParserError("CDC HAN public recommendation anchor is invalid")
        parsed_anchor = _NoticeSummary()
        parsed_anchor.feed(anchor)
        if (len(parsed_anchor.anchors) != 1 or parsed_anchor.text or parsed_anchor.badges
                or parsed_anchor.anchors[0].get("class") != "onThisPageAnchor"
                or parsed_anchor.anchors[0].get("id") !=
                "cdc_health_alert_section_5-recommendations-for-the-public"
                or parsed_anchor.anchors[0].get("title") != "Recommendations for the Public"
                or parsed_anchor.anchors[0].get("href")):
            raise NewsParserError("CDC HAN public recommendation anchor is invalid")
        public_anchor = "cdc_health_alert_section_5-recommendations-for-the-public"
    return distribution_date, badge_type, public_anchor


def _rendered_page_observation(row: dict[str, Any], notice_id: str) -> tuple[
    str | None, str, str | None
]:
    """Validate a bounded, manually transcribed official page observation.

    This is an offline research snapshot, not a raw HTML response or live parser.
    """
    observed_at = row.get("observed_at")
    if (set(row) != {"permalink", "at_a_glance", "summary_type_phrase", "observed_at"}
            or not isinstance(observed_at, str)
            or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", observed_at)
            or not isinstance(row["at_a_glance"], list)):
        raise NewsParserError("CDC HAN rendered observation lacks provenance")
    try:
        date.fromisoformat(observed_at)
    except ValueError as exc:
        raise NewsParserError("CDC HAN rendered observation lacks provenance") from exc
    glance = row["at_a_glance"]
    if (len(glance) not in {1, 3}
            or any(not isinstance(value, str) or len(value) > 100 for value in glance)
            or glance[0] != "Distributed via the CDC Health Alert Network"
            or (len(glance) == 3 and glance[2] != notice_id)):
        raise NewsParserError("CDC HAN rendered observation lacks distribution fields")
    phrase = row["summary_type_phrase"]
    message_type = _OBSERVED_TYPE_PHRASES.get(phrase)
    if not message_type:
        raise NewsParserError("CDC HAN rendered observation lacks summary message type")
    if len(glance) == 1:
        return None, message_type, None
    # Date-only labels include one comma between day and year. Split a time
    # suffix only after the four-digit year.
    date_match = re.fullmatch(r"([A-Za-z]+ \d{1,2}, \d{4})(?:, (\d{1,2}:\d{2} [AP]M ET))?",
                              glance[1])
    if not date_match:
        raise NewsParserError("CDC HAN rendered observation has invalid distribution date")
    try:
        distribution_date = datetime.strptime(date_match.group(1), "%B %d, %Y").date()
        if date_match.group(2):
            datetime.strptime(date_match.group(2), "%I:%M %p ET")
    except ValueError as exc:
        raise NewsParserError("CDC HAN rendered observation has invalid distribution date") from exc
    return distribution_date.isoformat(), message_type, date_match.group(2)


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
    summaries = payload.get("notice_summaries", [])
    if not isinstance(summaries, list) or len(summaries) > 20:
        raise NewsParserError("CDC HAN fixture has unbounded notice summaries")
    by_url: dict[str, dict[str, str | None]] = {}
    for summary in summaries:
        if not isinstance(summary, dict) or not isinstance(summary.get("permalink"), str):
            raise NewsParserError("CDC HAN notice summary lacks a permalink")
        summary_url = summary["permalink"]
        try:
            parts = urlsplit(summary_url)
            port = parts.port
        except ValueError as exc:
            raise NewsParserError("CDC HAN notice summary has invalid URL") from exc
        match = _NOTICE_PATH.fullmatch(parts.path)
        if (parts.scheme != "https" or parts.hostname != "www.cdc.gov"
                or parts.username or parts.password or port or parts.query or parts.fragment
                or not match or summary_url in by_url):
            raise NewsParserError("CDC HAN notice summary has invalid or duplicate URL")
        date, message_type, anchor = _page_summary(
            summary.get("page_summary_html"), summary.get("summary_lead_html"),
            summary.get("recommendation_anchor_html"),
            f"CDCHAN-{match.group(1)}"
        )
        by_url[summary_url] = {
            "date": date, "type": message_type, "anchor": anchor, "time": None,
            "type_basis": "official_notice_page_badge_and_summary_lead",
            "date_basis": "official_notice_page_at_a_glance",
            "observed_at": None,
        }
    observations = payload.get("notice_observations", [])
    if not isinstance(observations, list) or len(observations) > 20:
        raise NewsParserError("CDC HAN fixture has unbounded rendered observations")
    for observation in observations:
        if not isinstance(observation, dict):
            raise NewsParserError("CDC HAN rendered observation must be an object")
        observation_url = observation.get("permalink")
        if not isinstance(observation_url, str):
            raise NewsParserError("CDC HAN rendered observation lacks a permalink")
        try:
            parts = urlsplit(observation_url)
            port = parts.port
        except ValueError as exc:
            raise NewsParserError("CDC HAN rendered observation has invalid URL") from exc
        match = _NOTICE_PATH.fullmatch(parts.path)
        if (parts.scheme != "https" or parts.hostname != "www.cdc.gov"
                or parts.username or parts.password or port or parts.query or parts.fragment
                or not match or observation_url in by_url):
            raise NewsParserError("CDC HAN rendered observation has invalid or duplicate URL")
        date, message_type, local_time = _rendered_page_observation(
            observation, f"CDCHAN-{match.group(1)}"
        )
        by_url[observation_url] = {
            "date": date, "type": message_type, "anchor": None,
            "time": local_time,
            "type_basis": "official_notice_page_rendered_summary_phrase",
            "date_basis": "official_notice_page_rendered_at_a_glance" if date else None,
            "observed_at": observation["observed_at"],
        }
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
        detail = by_url.pop(url, None)
        if detail and message_type_hint and detail["type"] != message_type_hint:
            raise NewsParserError(f"CDC HAN row {index} conflicts with its notice summary")
        distribution_instant = _distribution_instant(detail)
        item = _normalize_item(source, {
            "title": title, "url": url, "description": excerpt,
            "published_at": distribution_instant or reviewed,
            "tags": ["official", "cdc", "han", "public-health", "notice-metadata"],
        }, index=index)
        item["evidence"]["cdc_han"] = {
            "notice_id": notice_id, "archive_url": ARCHIVE_URL,
            "search_url": SEARCH_URL, "notice_url": url,
            "index_last_reviewed_at": reviewed, "index_article_date_at": article_date,
            "date_basis": (
                "official_notice_page_ET_distribution_time_converted_to_UTC"
                if distribution_instant else
                "CDC search index last-reviewed date; distribution time unverified"
            ),
            "message_type": detail["type"] if detail else None,
            "message_type_basis": detail["type_basis"] if detail else None,
            "notice_page_observed_at": detail["observed_at"] if detail else None,
            "message_type_hint": message_type_hint,
            "message_type_hint_basis": (
                "index badge filename; separate from notice-page verification"
            ),
            "distribution_date": detail["date"] if detail else None,
            "distribution_time": detail["time"] if detail else None,
            "distribution_instant_utc": distribution_instant,
            "distribution_date_basis": detail["date_basis"] if detail else None,
            "distribution_time_basis": (
                "official_notice_page_rendered_at_a_glance_ET"
                if detail and detail["time"] else None
            ),
            "affected_population": None, "jurisdiction": None,
            "public_instruction_url": (
                f"{url}#{detail['anchor']}" if detail and detail["anchor"] else None
            ),
            "preliminary_status": "unverified",
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
    if by_url:
        raise NewsParserError("CDC HAN notice summary has no matching search row")
    return items
