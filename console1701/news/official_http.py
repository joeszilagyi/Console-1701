"""Small, allowlisted HTTPS transport for explicit official news scans only."""

from __future__ import annotations

from dataclasses import dataclass
from http.client import HTTPException
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

from console1701.news.parsers import NewsIngestError, PayloadTooLargeError, UnsupportedSourceError

NWS_WASHINGTON_ALERTS_URL = "https://api.weather.gov/alerts/active?area=WA"
NWS_WASHINGTON_SOURCE_KEYS = {
    ("LOCAL", "nws_active_alerts_api"),
    ("REGIONAL", "nws_active_alerts_wa"),
}
MAX_HTTP_BYTES = 4 * 1024 * 1024
MAX_HTTP_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class OfficialFetchResult:
    text: str | None
    status_code: int
    etag: str | None
    last_modified: str | None
    response_bytes: int


class RateLimitedError(NewsIngestError):
    """An official feed has asked this scanner to back off."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def is_supported_official_source(source: dict[str, Any]) -> bool:
    """Only the documented Washington alerts endpoint and its two scoped identities."""
    return (
        (source.get("scope"), source.get("id")) in NWS_WASHINGTON_SOURCE_KEYS
        and source.get("kind") == "api_json"
        and source.get("parser") == "nws_alerts_json"
        and source.get("url") == NWS_WASHINGTON_ALERTS_URL
        and source.get("verification_status") == "verified"
        and not source.get("auth")
    )


def _bounded_header(headers: Any, name: str) -> str | None:
    value = str(headers.get(name) or "").strip()
    if not value or len(value) > 256 or "\r" in value or "\n" in value:
        return None
    return value


def fetch_official_text(
    source: dict[str, Any],
    *,
    user_agent: str,
    timeout_seconds: int,
    max_bytes: int,
    etag: str | None = None,
    last_modified: str | None = None,
) -> OfficialFetchResult:
    if not is_supported_official_source(source):
        raise UnsupportedSourceError("Only the verified Washington NWS alerts URL is allowed.")
    timeout = min(MAX_HTTP_TIMEOUT_SECONDS, max(1, int(timeout_seconds)))
    limit = min(MAX_HTTP_BYTES, max(1, int(max_bytes)))
    headers = {"Accept": "application/geo+json", "User-Agent": user_agent}
    if etag and _bounded_header({"ETag": etag}, "ETag"):
        headers["If-None-Match"] = etag
    if last_modified and _bounded_header({"Last-Modified": last_modified}, "Last-Modified"):
        headers["If-Modified-Since"] = last_modified
    request = Request(NWS_WASHINGTON_ALERTS_URL, headers=headers, method="GET")
    # Do not honor environment proxies or follow redirects to an unapproved host.
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), _NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            status = int(response.status)
            if status != 200:
                raise NewsIngestError(f"Official feed returned HTTP {status}.")
            content_type = str(response.headers.get("Content-Type") or "").lower()
            if content_type.split(";", 1)[0].strip() not in {
                "application/geo+json",
                "application/json",
                "application/ld+json",
            }:
                raise NewsIngestError("Official feed did not return JSON content.")
            payload = response.read(limit + 1)
            if len(payload) > limit:
                raise PayloadTooLargeError(f"Official feed exceeds {limit} bytes.")
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise NewsIngestError("Official feed is not valid UTF-8.") from exc
            return OfficialFetchResult(
                text=text,
                status_code=status,
                etag=_bounded_header(response.headers, "ETag"),
                last_modified=_bounded_header(response.headers, "Last-Modified"),
                response_bytes=len(payload),
            )
    except HTTPError as exc:
        if exc.code == 304:
            return OfficialFetchResult(
                text=None,
                status_code=304,
                etag=_bounded_header(exc.headers, "ETag") or etag,
                last_modified=_bounded_header(exc.headers, "Last-Modified") or last_modified,
                response_bytes=0,
            )
        if exc.code == 429:
            raise RateLimitedError("Official feed returned HTTP 429; backoff applies.") from exc
        raise NewsIngestError(f"Official feed returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError, HTTPException) as exc:
        raise NewsIngestError(f"Official feed transport failed: {type(exc).__name__}.") from exc
