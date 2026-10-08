from __future__ import annotations

from urllib.error import HTTPError

import pytest

from console1701.news.official_http import (
    NWS_WASHINGTON_ALERTS_URL,
    USGS_REGIONAL_EARTHQUAKES_URL,
    WSDOT_HIGHWAY_ALERTS_RSS_URL,
    RateLimitedError,
    fetch_official_text,
    is_supported_official_source,
)
from console1701.news.parsers import NewsIngestError, PayloadTooLargeError, UnsupportedSourceError


def _source() -> dict:
    return {
        "id": "nws_active_alerts_api",
        "scope": "LOCAL",
        "kind": "api_json",
        "parser": "nws_alerts_json",
        "url": NWS_WASHINGTON_ALERTS_URL,
        "verification_status": "verified",
    }


def _usgs_source() -> dict:
    return {
        "id": "usgs_eq_geojson",
        "scope": "REGIONAL",
        "kind": "api_json",
        "parser": "usgs_earthquake_geojson",
        "url": USGS_REGIONAL_EARTHQUAKES_URL,
        "verification_status": "verified",
    }


def _wsdot_source() -> dict:
    return {
        "id": "wsdot_highway_alerts_rss",
        "scope": "REGIONAL",
        "kind": "rss",
        "parser": "wsdot_highway_alerts_rss",
        "url": WSDOT_HIGHWAY_ALERTS_RSS_URL,
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
    assert is_supported_official_source(
        {**source, "scope": "REGIONAL", "id": "nws_active_alerts_wa"}
    )
    for changed in (
        {"scope": "REGIONAL"},
        {"id": "nws_active_alerts_wa"},
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


def test_official_http_requires_exact_verified_usgs_feed(monkeypatch):
    source = _usgs_source()
    assert is_supported_official_source(source)
    for changed in (
        {"scope": "GLOBAL"},
        {"id": "usgs_earthquake_geojson"},
        {"url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson"},
        {"parser": "generic_json_items"},
        {"verification_status": "official_page_seen"},
        {"auth": {"token": "not-allowed"}},
        {"min_magnitude": 2.0},
    ):
        assert not is_supported_official_source({**source, **changed})

    observed = {}

    class _UsGsResponse(_Response):
        headers = {"Content-Type": "application/json; charset=utf-8", "Last-Modified": "today"}

    class _Opener:
        def open(self, request, *, timeout):
            observed["url"] = request.full_url
            observed["accept"] = request.get_header("Accept")
            return _UsGsResponse(b'{"type":"FeatureCollection","features":[]}')

    monkeypatch.setattr("console1701.news.official_http.build_opener", lambda *handlers: _Opener())
    result = fetch_official_text(
        source, user_agent="console-1701 test", timeout_seconds=5, max_bytes=100
    )

    assert result.status_code == 200
    assert result.last_modified == "today"
    assert observed == {"url": USGS_REGIONAL_EARTHQUAKES_URL, "accept": "application/json"}


def test_official_http_requires_exact_wsdot_rss_and_rss_content_type(monkeypatch):
    source = _wsdot_source()
    assert is_supported_official_source(source)
    for changed in (
        {"scope": "LOCAL"},
        {"id": "wsdot_traveler_api"},
        {"url": "https://www.wsdot.wa.gov/traffic/api/HighwayAlerts/rss.aspx?x=1"},
        {"kind": "api_json"},
        {"parser": "generic_json_items"},
        {"verification_status": "official_page_seen"},
        {"auth": {"code": "secret"}},
    ):
        assert not is_supported_official_source({**source, **changed})

    observed = {}

    class _RssResponse(_Response):
        headers = {"Content-Type": "application/rss+xml; charset=utf-8"}

    class _Opener:
        def open(self, request, *, timeout):
            observed["url"] = request.full_url
            observed["accept"] = request.get_header("Accept")
            return _RssResponse(b"<rss/>")

    monkeypatch.setattr("console1701.news.official_http.build_opener", lambda *handlers: _Opener())
    result = fetch_official_text(
        source, user_agent="console-1701 test", timeout_seconds=5, max_bytes=100
    )
    assert result.text == "<rss/>"
    assert observed == {"url": WSDOT_HIGHWAY_ALERTS_RSS_URL, "accept": "application/rss+xml"}

    class _WrongTypeResponse(_RssResponse):
        headers = {"Content-Type": "text/html"}

    class _WrongTypeOpener:
        def open(self, request, *, timeout):
            return _WrongTypeResponse(b"<rss/>")

    monkeypatch.setattr(
        "console1701.news.official_http.build_opener", lambda *handlers: _WrongTypeOpener()
    )
    with pytest.raises(NewsIngestError, match="content type"):
        fetch_official_text(source, user_agent="console-1701 test", timeout_seconds=5,
                            max_bytes=100)


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
