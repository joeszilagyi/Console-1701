from __future__ import annotations

from urllib.error import HTTPError

import pytest

from console1701.news.official_http import (
    NWS_WASHINGTON_ALERTS_URL,
    RateLimitedError,
    fetch_official_text,
    is_supported_official_source,
)
from console1701.news.parsers import PayloadTooLargeError, UnsupportedSourceError


def _source() -> dict:
    return {
        "id": "nws_active_alerts_api",
        "scope": "LOCAL",
        "kind": "api_json",
        "parser": "nws_alerts_json",
        "url": NWS_WASHINGTON_ALERTS_URL,
        "verification_status": "verified",
    }


class _Response:
    status = 200
    headers = {
        "Content-Type": "application/geo+json; charset=utf-8",
        "ETag": '"current"',
    }

    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]


def test_official_http_requires_exact_verified_nws_endpoint():
    source = _source()
    assert is_supported_official_source(source)
    for changed in (
        {"url": "https://api.weather.gov/alerts/active?area=OR"},
        {"url": "https://example.org/alerts/active?area=WA"},
        {"verification_status": "candidate_needs_verification"},
        {"parser": "generic_json_items"},
        {"auth": {"token": "not-allowed"}},
    ):
        assert not is_supported_official_source({**source, **changed})
    with pytest.raises(UnsupportedSourceError):
        fetch_official_text(
            {**source, "url": "https://example.org/alerts/active?area=WA"},
            user_agent="console-1701 test", timeout_seconds=5, max_bytes=100,
        )


def test_official_http_is_bounded_and_sends_conditional_headers(monkeypatch):
    observed = {}

    class _Opener:
        def open(self, request, *, timeout):
            observed["request"] = request
            observed["timeout"] = timeout
            return _Response(b'{"features":[]}')

    monkeypatch.setattr("console1701.news.official_http.build_opener", lambda *handlers: _Opener())
    result = fetch_official_text(
        _source(), user_agent="console-1701 test", timeout_seconds=999,
        max_bytes=100, etag='"previous"',
    )

    assert result.text == '{"features":[]}'
    assert result.etag == '"current"'
    assert observed["timeout"] == 30
    assert observed["request"].get_header("If-none-match") == '"previous"'
    assert observed["request"].get_header("User-agent") == "console-1701 test"

    class _OversizedOpener:
        def open(self, request, *, timeout):
            return _Response(b"x" * 11)

    monkeypatch.setattr(
        "console1701.news.official_http.build_opener", lambda *handlers: _OversizedOpener()
    )
    with pytest.raises(PayloadTooLargeError):
        fetch_official_text(
            _source(), user_agent="console-1701 test", timeout_seconds=5, max_bytes=10
        )


@pytest.mark.parametrize("status,expected", [(304, None), (429, RateLimitedError)])
def test_official_http_handles_not_modified_and_rate_limit(monkeypatch, status, expected):
    class _Opener:
        def open(self, request, *, timeout):
            raise HTTPError(NWS_WASHINGTON_ALERTS_URL, status, "HTTP error", {"ETag": '"e"'}, None)

    monkeypatch.setattr("console1701.news.official_http.build_opener", lambda *handlers: _Opener())
    if expected is None:
        result = fetch_official_text(
            _source(), user_agent="console-1701 test", timeout_seconds=5, max_bytes=100
        )
        assert result.status_code == 304
        assert result.text is None
        assert result.etag == '"e"'
    else:
        with pytest.raises(expected):
            fetch_official_text(
                _source(), user_agent="console-1701 test", timeout_seconds=5, max_bytes=100
            )
