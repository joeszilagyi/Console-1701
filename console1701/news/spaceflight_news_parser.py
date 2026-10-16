"""Fixture-only Spaceflight News API v4 contextual article metadata."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlsplit

from console1701.news.normalize import bounded_text, normalize_timestamp

_UUID = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z")
_SENSITIVE = re.compile(r"\b(classified|secret|spy|military)\b", re.I)
_ROUTINE = re.compile(r"\b(image|photo|jellyfish|opinion|podcast|webinar)\b", re.I)


def parse_spaceflight_news_json(
    source: dict[str, Any], payload_text: str
) -> list[dict[str, Any]]:
    """Keep source-linked headlines as context, never as corroborating authority."""
    from console1701.news.parsers import NewsParserError, _normalize_item

    if (source.get("id") != "spaceflight_news_articles"
            or source.get("scope") != "ORBITAL"):
        raise NewsParserError("Spaceflight News parser requires registered ORBITAL article source")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise NewsParserError(f"Malformed Spaceflight News JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise NewsParserError("Spaceflight News JSON must be an object")
    rows = payload.get("results")
    if not isinstance(rows, list) or len(rows) > 30:
        raise NewsParserError("Spaceflight News results must be a bounded array")
    items: list[dict[str, Any]] = []
    seen: set[int] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        article_id = row.get("id")
        if (not isinstance(article_id, int) or isinstance(article_id, bool)
                or article_id < 1 or article_id in seen):
            continue
        title = bounded_text(row.get("title"), max_chars=180)
        publisher = bounded_text(row.get("news_site"), max_chars=80)
        url = str(row.get("url") or "")
        parts = urlsplit(url)
        published = normalize_timestamp(row.get("published_at"))
        if (not title or not publisher or parts.scheme != "https" or not parts.hostname
                or parts.username or parts.password or not published):
            continue
        if _SENSITIVE.search(title) or _ROUTINE.search(title) or "/image-article/" in parts.path:
            continue
        launches = row.get("launches") or []
        events = row.get("events") or []
        if not isinstance(launches, list) or not isinstance(events, list):
            continue
        linked_launches = sorted({
            value.lower() for link in launches[:10] if isinstance(link, dict)
            if (value := link.get("launch_id")) and isinstance(value, str)
            and _UUID.fullmatch(value)
        })
        linked_events = sorted({
            value for link in events[:10] if isinstance(link, dict)
            if (value := link.get("event_id")) and isinstance(value, int)
            and not isinstance(value, bool) and value > 0
        })
        if not linked_launches and not linked_events:
            continue
        # Ambiguous multi-event links are retained as metadata, not identity.
        identity: dict[str, Any] = {"public_value_class": "background"}
        if len(linked_launches) == 1 and not linked_events:
            identity.update(event_type="launch_update", launch_id=linked_launches[0])
        elif len(linked_events) == 1 and not linked_launches:
            identity.update(event_type="mission_update", object_id=str(linked_events[0]))
        else:
            identity["event_type"] = "spaceflight_article"
        seen.add(article_id)
        item = _normalize_item(source, {
            "title": title, "url": url,
            "description": bounded_text(row.get("summary"), max_chars=240),
            "published_at": published,
        }, index=index)
        item["evidence"]["spaceflight_news"] = {
            "article_id": article_id, "publisher": publisher,
            "published_at": published,
            "updated_at": normalize_timestamp(row.get("updated_at")),
            "linked_launch_ids": linked_launches,
            "linked_event_ids": linked_events,
            "source_url": "https://api.spaceflightnewsapi.net/v4/articles/",
            "authority": "aggregated_metadata_only",
        }
        item["evidence"]["orbital_identity"] = identity
        items.append(item)
    return items
