from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

MAX_TITLE_LENGTH = 280
MAX_DESCRIPTION_LENGTH = 1200
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def bounded_text(value: Any, *, max_chars: int) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).split()).strip()
    if not text:
        return None
    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return text[:max_chars]
    return text[: max_chars - 1].rstrip() + "…"


def normalize_timestamp(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None

    for candidate in (text, text.replace("Z", "+00:00")):
        try:
            parsed = datetime.fromisoformat(candidate)
            break
        except ValueError:
            parsed = None
    if parsed is None:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError, IndexError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat(timespec="seconds")


def normalize_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith("file://"):
        return text
    parts = urlsplit(text)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path or "/"
    query = urlencode(sorted(parse_qsl(parts.query, keep_blank_values=True)))
    return urlunsplit((scheme, netloc, path, query, ""))


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def url_hash(url: str) -> str:
    return hash_text(normalize_url(url))


def content_hash(title: str, description: str | None) -> str:
    return hash_text(f"{title}\n{description or ''}")


def expires_at(seen_at: str, retention_days: int) -> str:
    parsed = datetime.fromisoformat(seen_at)
    return (parsed + timedelta(days=max(1, retention_days))).isoformat(timespec="seconds")


def rank_score(
    source_priority: int,
    source_published_at: str | None,
    *,
    seen_at: str,
    tag_count: int,
) -> int:
    score = int(source_priority)
    published = source_published_at or seen_at
    try:
        age = datetime.fromisoformat(seen_at) - datetime.fromisoformat(published)
    except ValueError:
        age = timedelta(0)
    age_hours = max(0, int(age.total_seconds() // 3600))
    recency_bonus = max(0, 72 - min(age_hours, 72))
    return score + recency_bonus + min(tag_count, 10)


def cluster_key(title: str, hashed_url: str) -> str:
    tokens = _TOKEN_RE.findall(title.lower())
    if tokens:
        return "-".join(tokens[:8])
    return hashed_url[:16]
