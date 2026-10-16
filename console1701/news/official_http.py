"""Small, allowlisted HTTPS transport for explicit official news scans only."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http.client import HTTPException
from math import isfinite
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

from console1701.news.parsers import (
    NWS_NATIONAL_SEVERE_ALERTS_URL,
    NewsIngestError,
    PayloadTooLargeError,
    UnsupportedSourceError,
)

NWS_WASHINGTON_ALERTS_URL = "https://api.weather.gov/alerts/active?area=WA"
USGS_REGIONAL_EARTHQUAKES_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
)
USGS_GLOBAL_EARTHQUAKES_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson"
)
WSDOT_HIGHWAY_ALERTS_RSS_URL = "https://www.wsdot.wa.gov/traffic/api/HighwayAlerts/rss.aspx"
SWPC_ALERTS_URL = "https://services.swpc.noaa.gov/products/alerts.json"
SWPC_NOAA_SCALES_URL = "https://services.swpc.noaa.gov/products/noaa-scales.json"
SWPC_PLANETARY_K_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
SWPC_PLANETARY_K_1M_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
SWPC_BOULDER_K_URL = "https://services.swpc.noaa.gov/json/boulder_k_index_1m.json"
SWPC_OVATION_AURORA_URL = "https://services.swpc.noaa.gov/json/ovation_aurora_latest.json"
OFFICIAL_SOURCES = {
    ("LOCAL", "nws_active_alerts_api"): (
        NWS_WASHINGTON_ALERTS_URL, "api_json", "nws_alerts_json", "application/geo+json"
    ),
    ("REGIONAL", "nws_active_alerts_wa"): (
        NWS_WASHINGTON_ALERTS_URL, "api_json", "nws_alerts_json", "application/geo+json"
    ),
    ("NATIONAL", "nws_active_alerts_api"): (
        NWS_NATIONAL_SEVERE_ALERTS_URL, "api_json", "nws_alerts_json",
        "application/geo+json"
    ),
    ("REGIONAL", "usgs_eq_geojson"): (
        USGS_REGIONAL_EARTHQUAKES_URL, "api_json", "usgs_earthquake_geojson",
        "application/json"
    ),
    ("NATIONAL", "usgs_eq_geojson"): (
        USGS_REGIONAL_EARTHQUAKES_URL, "api_json", "usgs_earthquake_geojson",
        "application/json"
    ),
    ("GLOBAL", "usgs_eq_geojson_global"): (
        USGS_GLOBAL_EARTHQUAKES_URL, "api_json", "usgs_earthquake_geojson",
        "application/json"
    ),
    ("REGIONAL", "wsdot_highway_alerts_rss"): (
        WSDOT_HIGHWAY_ALERTS_RSS_URL, "rss", "wsdot_highway_alerts_rss", "application/rss+xml"
    ),
    ("ORBITAL", "swpc_alerts_json"): (
        SWPC_ALERTS_URL, "api_json", "swpc_alerts_json", "application/json"
    ),
    ("ORBITAL", "swpc_noaa_scales_json"): (
        SWPC_NOAA_SCALES_URL, "api_json", "swpc_noaa_scales_json", "application/json"
    ),
    ("ORBITAL", "swpc_kp_summary_json"): (
        SWPC_PLANETARY_K_URL, "api_json", "swpc_kp_json", "application/json"
    ),
    ("ORBITAL", "swpc_kp_1m_json"): (
        SWPC_PLANETARY_K_1M_URL, "api_json", "swpc_kp_json", "application/json"
    ),
    ("ORBITAL", "swpc_boulder_k_json"): (
        SWPC_BOULDER_K_URL, "api_json", "swpc_kp_json", "application/json"
    ),
    ("ORBITAL", "swpc_aurora_json"): (
        SWPC_OVATION_AURORA_URL, "api_json", "swpc_aurora_json", "application/json"
    ),
    ("ORBITAL", "nasa_rss_feeds"): (
        "https://www.nasa.gov/news-release/feed/", "rss", "nasa_orbital_rss",
        "application/rss+xml"
    ),
    ("ORBITAL", "nasa_iss_page"): (
        "https://www.nasa.gov/missions/station/feed/", "rss", "nasa_orbital_rss",
        "application/rss+xml"
    ),
    ("ORBITAL", "nasa_spacestation_blog"): (
        "https://www.nasa.gov/blogs/spacestation/feed/", "rss", "nasa_orbital_rss",
        "application/rss+xml"
    ),
    ("ORBITAL", "nasa_artemis"): (
        "https://www.nasa.gov/missions/artemis/feed/", "rss", "nasa_orbital_rss",
        "application/rss+xml"
    ),
    ("ORBITAL", "nasa_artemis_blog"): (
        "https://www.nasa.gov/blogs/artemis/feed/", "rss", "nasa_orbital_rss",
        "application/rss+xml"
    ),
    ("ORBITAL", "nasa_kennedy_blog"): (
        "https://www.nasa.gov/blogs/kennedy/feed/", "rss", "nasa_orbital_rss",
        "application/rss+xml"
    ),
    ("ORBITAL", "jpl_rss"): (
        "https://www.nasa.gov/centers-and-facilities/jpl/feed/", "rss",
        "nasa_orbital_rss", "application/rss+xml"
    ),
    ("ORBITAL", "esa_rss"): (
        "https://www.esa.int/rssfeed/Our_Activities/Space_News", "rss", "esa_orbital_rss",
        "application/rss+xml"
    ),
    ("ORBITAL", "esa_iss"): (
        "https://www.esa.int/rssfeed/Our_Activities/Human_Spaceflight", "rss",
        "esa_orbital_rss", "application/rss+xml"
    ),
    ("SYSTEM_SOLAR", "esa_space_science_feed"): (
        "https://www.esa.int/rssfeed/Our_Activities/Space_Science", "rss",
        "esa_science_rss", "application/rss+xml"
    ),
    ("SYSTEM_SOLAR", "nasa_jpl_science_feed"): (
        "https://www.nasa.gov/centers-and-facilities/jpl/feed/", "rss",
        "nasa_jpl_science_rss", "application/rss+xml"
    ),
    ("SYSTEM_SOLAR", "astronomers_telegram_rss"): (
        "https://www.astronomerstelegram.org/?rss", "rss", "atel_rss", "text/xml"
    ),
    ("SYSTEM_SOLAR", "nasa_exoplanet_ps_tap"): (
        "https://exoplanetarchive.ipac.caltech.edu/TAP/sync", "api_json",
        "exoplanet_ps_json", "application/json"
    ),
    ("SYSTEM_SOLAR", "gracedb_public_alerts"): (
        "https://gracedb.ligo.org/api/v2/superevents/", "api_json",
        "gracedb_public_alert_fixture", "application/json"
    ),
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
    """Only verified scope/source/URL/parser combinations are eligible for live ingest."""
    spec = OFFICIAL_SOURCES.get((source.get("scope"), source.get("id")))
    return (
        spec is not None
        and source.get("kind") == spec[1]
        and source.get("parser") == spec[2]
        and source.get("url") == spec[0]
        and source.get("verification_status") == "verified"
        and not source.get("auth")
        and (
            source.get("scope") != "SYSTEM_SOLAR"
            or (
                source.get("official_url") == spec[0]
                and source.get("fixture_only") is False
            )
        )
        and (
            (source.get("scope"), source.get("id")) !=
            ("SYSTEM_SOLAR", "nasa_exoplanet_ps_tap")
            or _exoplanet_live_query_safe(source)
        )
        and (
            source.get("id") != "usgs_eq_geojson"
            or _usgs_feed_covers_threshold(source.get("min_magnitude", 3.0))
        )
        and (
            (source.get("scope"), source.get("id")) !=
            ("NATIONAL", "nws_active_alerts_api")
            or (
                type(source.get("interval_minutes")) is int
                and source["interval_minutes"] >= 5
            )
        )
        and (
            (source.get("scope"), source.get("id")) != ("GLOBAL", "usgs_eq_geojson_global")
            or _usgs_feed_covers_threshold(source.get("min_magnitude", 6.0), feed_floor=4.5)
        )
        and (
            source.get("scope") != "ORBITAL"
            or source.get("id") not in {
                "swpc_kp_summary_json", "swpc_kp_1m_json", "swpc_boulder_k_json",
            }
            or _orbital_k_threshold_safe(source.get("min_k_index", 5.0))
        )
        and (
            source.get("scope") != "ORBITAL"
            or source.get("id") != "swpc_aurora_json"
            or _orbital_aurora_locations_safe(source.get("aurora_locations"))
        )
    )


def _exoplanet_live_query_safe(source: dict[str, Any]) -> bool:
    from console1701.news.science_exoplanets import live_exoplanet_query_contract

    return source.get("query_contract") == live_exoplanet_query_contract()


def _usgs_feed_covers_threshold(value: Any, *, feed_floor: float = 2.5) -> bool:
    try:
        minimum = float(value)
    except (TypeError, ValueError):
        return False
    return isfinite(minimum) and minimum >= feed_floor


def _orbital_k_threshold_safe(value: Any) -> bool:
    try:
        minimum = float(value)
    except (TypeError, ValueError):
        return False
    return isfinite(minimum) and 5.0 <= minimum <= 9.0


def _orbital_aurora_locations_safe(value: Any) -> bool:
    if not isinstance(value, list) or not 1 <= len(value) <= 8:
        return False
    try:
        return all(
            isinstance(location, dict)
            and location.get("scope") in {"LOCAL", "REGIONAL"}
            and bool(str(location.get("name") or "").strip())
            and 50 <= float(location.get("min_intensity")) <= 100
            and 0.5 <= float(location.get("radius_degrees")) <= 10
            and -90 <= float(location.get("latitude")) <= 90
            and -180 <= float(location.get("longitude")) <= 180
            for location in value
        )
    except (TypeError, ValueError):
        return False


def _bounded_header(headers: Any, name: str) -> str | None:
    value = str(headers.get(name) or "").strip()
    if not value or len(value) > 256 or "\r" in value or "\n" in value:
        return None
    return value


def _gracedb_json_get(url: str, *, user_agent: str, timeout: int, limit: int) -> tuple[Any, int]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": user_agent},
                      method="GET")
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), _NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            if int(response.status) != 200:
                raise NewsIngestError(f"GraceDB returned HTTP {response.status}.")
            content_type = str(response.headers.get("Content-Type") or "").lower()
            if content_type.split(";", 1)[0].strip() != "application/json":
                raise NewsIngestError("GraceDB returned an unexpected content type.")
            raw = response.read(limit + 1)
            if len(raw) > limit:
                raise PayloadTooLargeError("GraceDB public metadata exceeds its byte cap.")
            try:
                return json.loads(raw.decode("utf-8")), len(raw)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise NewsIngestError("GraceDB returned invalid JSON metadata.") from exc
    except HTTPError as exc:
        if exc.code == 429:
            raise RateLimitedError("GraceDB returned HTTP 429; backoff applies.") from exc
        raise NewsIngestError(f"GraceDB returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError, HTTPException) as exc:
        raise NewsIngestError(f"GraceDB transport failed: {type(exc).__name__}.") from exc


def _fetch_gracedb_public_alerts(
    *, user_agent: str, timeout: int, max_bytes: int
) -> OfficialFetchResult:
    from console1701.news.science_gracedb import public_gracedb_event_id

    endpoint = OFFICIAL_SOURCES[("SYSTEM_SOLAR", "gracedb_public_alerts")][0]
    now = datetime.now(UTC)
    start = now - timedelta(hours=48)

    def stamp(value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")

    query = (f"category: Production is_public: True created: {stamp(start)} .. {stamp(now)}")
    url = endpoint + "?" + urlencode({"query": query, "count": 10})
    list_payload, total_bytes = _gracedb_json_get(
        url, user_agent=user_agent, timeout=timeout, limit=min(max_bytes, 65_536)
    )
    rows = list_payload.get("superevents") if isinstance(list_payload, dict) else None
    num_rows = list_payload.get("numRows") if isinstance(list_payload, dict) else None
    if (not isinstance(rows, list) or type(num_rows) is not int or num_rows > 10
            or num_rows != len(rows)):
        raise NewsIngestError(
            "GraceDB query overflow or malformed public result; no partial ingest."
        )
    records = []
    for row in rows:
        event_id = row.get("superevent_id") if isinstance(row, dict) else None
        if not public_gracedb_event_id(event_id) or row.get("category") != "Production":
            raise NewsIngestError("GraceDB list contains an invalid or nonproduction event.")
        links = row.get("links") or {}
        vo_url = f"{endpoint}{event_id}/voevents/"
        if (not isinstance(links, dict) or links.get("self") != f"{endpoint}{event_id}/"
                or links.get("voevents") != vo_url):
            raise NewsIngestError("GraceDB list contains mismatched REST links.")
        remaining = min(max_bytes, 65_536) - total_bytes
        if remaining <= 0:
            raise PayloadTooLargeError("GraceDB public metadata exceeds its aggregate byte cap.")
        notices, size = _gracedb_json_get(
            vo_url, user_agent=user_agent, timeout=timeout, limit=remaining
        )
        total_bytes += size
        records.append({"superevent": row, "voevents": notices})
    assembled = json.dumps({
        "assembly_version": 1,
        "query": {"category": "Production", "is_public": True, "count": 10,
                  "created_start": stamp(start), "created_end": stamp(now)},
        "records": records,
    }, separators=(",", ":"))
    if len(assembled.encode("utf-8")) > 65_536:
        raise PayloadTooLargeError("GraceDB assembled metadata exceeds 64 KiB.")
    return OfficialFetchResult(
        text=assembled, status_code=200, etag=None, last_modified=None,
        response_bytes=total_bytes,
    )


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
        raise UnsupportedSourceError("Source is outside the verified official feed allowlist.")
    timeout = min(MAX_HTTP_TIMEOUT_SECONDS, max(1, int(timeout_seconds)))
    limit = min(MAX_HTTP_BYTES, max(1, int(max_bytes)))
    spec = OFFICIAL_SOURCES[(source["scope"], source["id"])]
    if (source["scope"], source["id"]) == ("SYSTEM_SOLAR", "gracedb_public_alerts"):
        return _fetch_gracedb_public_alerts(
            user_agent=user_agent, timeout=timeout, max_bytes=min(limit, 65_536)
        )
    headers = {"Accept": spec[3], "User-Agent": user_agent}
    if etag and _bounded_header({"ETag": etag}, "ETag"):
        headers["If-None-Match"] = etag
    if last_modified and _bounded_header({"Last-Modified": last_modified}, "Last-Modified"):
        headers["If-Modified-Since"] = last_modified
    request_url = spec[0]
    if (source["scope"], source["id"]) == ("SYSTEM_SOLAR", "nasa_exoplanet_ps_tap"):
        from console1701.news.science_exoplanets import live_exoplanet_request_url

        request_url = live_exoplanet_request_url(source)
        limit = min(limit, 65_536)
    if (source["scope"], source["id"]) == ("SYSTEM_SOLAR", "astronomers_telegram_rss"):
        limit = min(limit, 65_536)
    request = Request(request_url, headers=headers, method="GET")
    # Do not honor environment proxies or follow redirects to an unapproved host.
    opener = build_opener(ProxyHandler({}), HTTPSHandler(), _NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            status = int(response.status)
            if status != 200:
                raise NewsIngestError(f"Official feed returned HTTP {status}.")
            content_type = str(response.headers.get("Content-Type") or "").lower()
            allowed_types = (
                {"application/rss+xml"} if source["kind"] == "rss"
                else {"application/geo+json", "application/json", "application/ld+json"}
            )
            if (source["scope"], source["id"]) == ("SYSTEM_SOLAR", "astronomers_telegram_rss"):
                allowed_types = {"text/xml"}
            if content_type.split(";", 1)[0].strip() not in allowed_types:
                raise NewsIngestError("Official feed returned an unexpected content type.")
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
