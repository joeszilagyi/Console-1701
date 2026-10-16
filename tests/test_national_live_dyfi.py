from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from urllib.error import HTTPError

import pytest
import yaml

from console1701.config import ConfigError, load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import (
    USGS_REGIONAL_EARTHQUAKES_URL,
    OfficialFetchResult,
    RateLimitedError,
    _usgs_dyfi_get,
    fetch_national_usgs_dyfi,
)
from console1701.news.parsers import (
    NewsIngestError,
    NewsParserError,
    PayloadTooLargeError,
    parse_fixture_items,
)
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/national_usgs_redwood_dyfi.json"
OBSERVED = json.loads(FIXTURE.read_text())
EVENT_ID = "nc75382936"
DETAIL_URL = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{EVENT_ID}.geojson"
PRODUCT_URL = OBSERVED["fixture_dyfi"]["product_url"]


def _source() -> dict:
    return {
        "scope": "NATIONAL", "id": "usgs_eq_geojson", "kind": "api_json",
        "parser": "usgs_earthquake_geojson", "url": USGS_REGIONAL_EARTHQUAKES_URL,
        "verification_status": "verified", "min_magnitude": 5.0,
        "interval_minutes": 60, "dyfi_state_enrichment": True,
    }


def _summary() -> str:
    payload = deepcopy(OBSERVED)
    payload.pop("fixture_dyfi")
    payload["features"][0]["properties"]["detail"] = DETAIL_URL
    return json.dumps(payload)


def _detail(event_id: str = EVENT_ID) -> bytes:
    product_url = PRODUCT_URL.replace(EVENT_ID, event_id)
    return json.dumps({
        "type": "Feature", "id": event_id,
        "properties": {
            "url": f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}",
            "products": {"dyfi": [
                {"source": "us", "status": "UPDATE", "preferredWeight": 8,
                 "updateTime": 1784832964337, "contents": {}},
                {"source": "us", "status": "UPDATE", "preferredWeight": 53,
                 "updateTime": 1790984474973, "contents": {"cdi_zip.xml": {
                     "contentType": "application/xml", "length": 84498,
                     "url": product_url,
                 }}},
            ]},
        },
    }).encode()


def _config(path: Path, *, interval: int = 60) -> Path:
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {"enabled": True, "fetch_policy": {"allow_official_http": True},
                 "scopes": {"NATIONAL": {"enabled": True, "sources": [{
                     "id": "usgs_eq_geojson", "enabled": True,
                     "interval_minutes": interval, "dyfi_state_enrichment": True,
                 }]}}},
    }))
    return path


def test_dyfi_live_opt_in_requires_sixty_minute_exact_source(tmp_path):
    with pytest.raises(ConfigError, match="interval_minutes"):
        load_config(_config(tmp_path / "too-often.yml", interval=30))
    source = load_config(_config(tmp_path / "allowed.yml"))["news"]["scopes"][
        "NATIONAL"
    ]["sources"][0]
    assert source["dyfi_state_enrichment"] is True
    assert source["interval_minutes"] == 60
    with pytest.raises(NewsParserError, match="matching detail URL"):
        parse_fixture_items(
            _source(), _summary().replace(DETAIL_URL, DETAIL_URL + "?other=1")
        )


def test_dyfi_transport_selects_preferred_product_and_reuses_version(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs["max_bytes"]))
        body = _detail() if url == DETAIL_URL else OBSERVED["fixture_dyfi"]["xml"].encode()
        return body, len(body)

    monkeypatch.setattr("console1701.news.official_http._usgs_dyfi_get", fake_get)
    sidecar, cached, size, state = fetch_national_usgs_dyfi(
        _source(), event_id=EVENT_ID, detail_url=DETAIL_URL, user_agent="console-1701 test",
    )
    assert state == "downloaded_product" and cached is None
    assert sidecar["product_url"] == PRODUCT_URL
    assert size == len(_detail()) + 84498
    assert calls == [(DETAIL_URL, 262144), (PRODUCT_URL, 131072)]
    calls.clear()
    summary = {"event_id": EVENT_ID, "product_url": PRODUCT_URL, "fixture_only": False}
    sidecar, cached, size, state = fetch_national_usgs_dyfi(
        _source(), event_id=EVENT_ID, detail_url=DETAIL_URL,
        user_agent="console-1701 test", cached=summary,
    )
    assert sidecar is None and cached == summary and state == "cached_product"
    assert calls == [(DETAIL_URL, 262144)]
    with pytest.raises(NewsIngestError, match="does not match"):
        monkeypatch.setattr(
            "console1701.news.official_http._usgs_dyfi_get",
            lambda *args, **kwargs: (b'{"type":"Feature","id":"other","properties":{}}', 51),
        )
        fetch_national_usgs_dyfi(
            _source(), event_id=EVENT_ID, detail_url=DETAIL_URL,
            user_agent="console-1701 test",
        )


def test_dyfi_transport_does_not_follow_changed_product_url(monkeypatch):
    detail = json.loads(_detail())
    detail["properties"]["products"]["dyfi"][1]["contents"]["cdi_zip.xml"][
        "url"
    ] = "https://example.org/zip.xml"
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        body = json.dumps(detail).encode()
        return body, len(body)

    monkeypatch.setattr("console1701.news.official_http._usgs_dyfi_get", fake_get)
    sidecar, cached, size, state = fetch_national_usgs_dyfi(
        _source(), event_id=EVENT_ID, detail_url=DETAIL_URL, user_agent="console-1701 test",
    )
    assert sidecar is None and cached is None and state == "unsupported_zip_product"
    assert size == len(json.dumps(detail).encode())
    assert calls == [DETAIL_URL]

    detail["properties"]["products"].pop("dyfi")
    sidecar, cached, size, state = fetch_national_usgs_dyfi(
        _source(), event_id=EVENT_ID, detail_url=DETAIL_URL, user_agent="console-1701 test",
    )
    assert sidecar is None and cached is None and state == "no_product"
    assert calls == [DETAIL_URL, DETAIL_URL]


def test_dyfi_http_transport_rejects_wrong_type_oversize_and_rate_limit(monkeypatch):
    observed = {}

    class Response:
        status = 200

        def __init__(self, body, content_type):
            self.body = body
            self.headers = {"Content-Type": content_type}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, limit):
            return self.body[:limit]

    class Opener:
        def __init__(self, response):
            self.response = response

        def open(self, request, *, timeout):
            observed["url"] = request.full_url
            observed["accept"] = request.get_header("Accept")
            observed["timeout"] = timeout
            return self.response

    monkeypatch.setattr(
        "console1701.news.official_http.build_opener",
        lambda *handlers: Opener(Response(b"{}", "application/json")),
    )
    body, size = _usgs_dyfi_get(
        DETAIL_URL, user_agent="console-1701 test", accept="application/json",
        allowed_types={"application/json"}, max_bytes=10,
    )
    assert body == b"{}" and size == 2
    assert observed == {"url": DETAIL_URL, "accept": "application/json", "timeout": 8}
    monkeypatch.setattr(
        "console1701.news.official_http.build_opener",
        lambda *handlers: Opener(Response(b"{}", "text/html")),
    )
    with pytest.raises(NewsIngestError, match="content type"):
        _usgs_dyfi_get(DETAIL_URL, user_agent="test", accept="application/json",
                       allowed_types={"application/json"}, max_bytes=10)
    monkeypatch.setattr(
        "console1701.news.official_http.build_opener",
        lambda *handlers: Opener(Response(b"x" * 11, "application/json")),
    )
    with pytest.raises(PayloadTooLargeError):
        _usgs_dyfi_get(DETAIL_URL, user_agent="test", accept="application/json",
                       allowed_types={"application/json"}, max_bytes=10)

    class LimitedOpener:
        def open(self, request, *, timeout):
            raise HTTPError(request.full_url, 429, "rate limited", {}, None)

    monkeypatch.setattr(
        "console1701.news.official_http.build_opener", lambda *handlers: LimitedOpener()
    )
    with pytest.raises(RateLimitedError):
        _usgs_dyfi_get(DETAIL_URL, user_agent="test", accept="application/json",
                       allowed_types={"application/json"}, max_bytes=10)


def test_live_dyfi_scan_stores_only_state_totals_and_reuses_product(tmp_path, monkeypatch):
    summary = _summary()
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: OfficialFetchResult(summary, 200, None, None, len(summary)),
    )
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        body = _detail() if url == DETAIL_URL else OBSERVED["fixture_dyfi"]["xml"].encode()
        return body, len(body)

    monkeypatch.setattr("console1701.news.official_http._usgs_dyfi_get", fake_get)
    path = _config(tmp_path / "live.yml")
    result = run_news_scan(path)
    assert result["status"] == "complete" and result["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        item = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchone()
        run = conn.execute(
            "SELECT evidence_json FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
        conn.commit()
    evidence = json_loads(item["evidence_json"], {})
    assert evidence["usgs_earthquake"]["dyfi_state_evidence"]["fixture_only"] is False
    assert evidence["national_identity"]["affected_states"] == ["CA", "NV"]
    assert evidence["national_identity"]["multi_state_impact"] is True
    assert "<location" not in item["evidence_json"]
    assert json_loads(run["evidence_json"], {})["dyfi_state"]["state"] == (
        "downloaded_product"
    )
    run_news_scan(path)
    assert calls == [DETAIL_URL, PRODUCT_URL, DETAIL_URL]
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute(
            "SELECT evidence_json FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert json_loads(run["evidence_json"], {})["dyfi_state"]["state"] == (
        "cached_product"
    )


def test_live_dyfi_is_capped_to_one_event_and_backs_off_rate_limit(tmp_path, monkeypatch):
    payload = json.loads(_summary())
    second = deepcopy(payload["features"][0])
    second["id"] = "nc75382937"
    second["properties"]["url"] = (
        "https://earthquake.usgs.gov/earthquakes/eventpage/nc75382937"
    )
    second["properties"]["detail"] = (
        "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/nc75382937.geojson"
    )
    second["properties"]["felt"] = 100
    payload["features"].append(second)
    summary = json.dumps(payload)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: OfficialFetchResult(summary, 200, None, None, len(summary)),
    )
    calls = []

    def rate_limited(url, **kwargs):
        calls.append(url)
        raise RateLimitedError("USGS DYFI returned HTTP 429")

    monkeypatch.setattr("console1701.news.official_http._usgs_dyfi_get", rate_limited)
    path = _config(tmp_path / "rate.yml")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute(
            "SELECT evidence_json FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
        conn.commit()
    first_evidence = json_loads(run["evidence_json"], {})["dyfi_state"]
    assert first_evidence["state"] == "rate_limited"
    assert first_evidence["eligible_count"] == 2
    assert calls == [DETAIL_URL]
    run_news_scan(path)
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute(
            "SELECT evidence_json FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    second_evidence = json_loads(run["evidence_json"], {})["dyfi_state"]
    assert second_evidence["state"] == "rate_backoff"
    assert second_evidence["events_attempted"] == 0
    assert calls == [DETAIL_URL]


def test_next_scan_enriches_second_event_and_keeps_unchanged_first(tmp_path, monkeypatch):
    payload = json.loads(_summary())
    second_id = "nc75382937"
    second = deepcopy(payload["features"][0])
    second["id"] = second_id
    second["properties"]["url"] = (
        f"https://earthquake.usgs.gov/earthquakes/eventpage/{second_id}"
    )
    second["properties"]["detail"] = (
        f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{second_id}.geojson"
    )
    second["properties"]["felt"] = 100
    payload["features"].append(second)
    summary = json.dumps(payload)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: OfficialFetchResult(summary, 200, None, None, len(summary)),
    )
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        if "/detail/" in url:
            event_id = url.rsplit("/", 1)[-1].removesuffix(".geojson")
            body = _detail(event_id)
        else:
            body = OBSERVED["fixture_dyfi"]["xml"].encode()
        return body, len(body)

    monkeypatch.setattr("console1701.news.official_http._usgs_dyfi_get", fake_get)
    path = _config(tmp_path / "two.yml")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        conn.execute("UPDATE news_fetch_runs SET started_at='2026-01-01T00:00:00+00:00'")
        conn.commit()
    run_news_scan(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchall()
        run = conn.execute(
            "SELECT evidence_json FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    by_id = {
        (evidence := json_loads(row["evidence_json"], {}))["usgs_earthquake"]["id"]: evidence
        for row in rows
    }
    assert set(by_id) == {EVENT_ID, second_id}
    assert all(
        row["national_identity"]["affected_states"] == ["CA", "NV"]
        for row in by_id.values()
    )
    assert json_loads(run["evidence_json"], {})["dyfi_state"]["cached_events_reused"] == 1
    assert len(calls) == 4  # One detail and one product GET per scan.


def test_geoserve_and_dyfi_opt_ins_preserve_both_evidence_paths(tmp_path, monkeypatch):
    summary = _summary()
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: OfficialFetchResult(summary, 200, None, None, len(summary)),
    )
    admin = {
        "metadata": {"request": (
            "https://earthquake.usgs.gov/ws/geoserve/regions.json?"
            "latitude=39.362333&longitude=-123.228833&type=admin"
        ), "types": ["admin"]},
        "admin": {"type": "FeatureCollection", "count": 1, "features": [{
            "type": "Feature", "geometry": None,
            "properties": {"iso": "USA", "country": "United States", "region": "California"},
        }]},
    }
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_national_usgs_geoserve_admin",
        lambda *args, **kwargs: (admin, len(json.dumps(admin))),
    )

    def fake_get(url, **kwargs):
        body = _detail() if url == DETAIL_URL else OBSERVED["fixture_dyfi"]["xml"].encode()
        return body, len(body)

    monkeypatch.setattr("console1701.news.official_http._usgs_dyfi_get", fake_get)
    path = _config(tmp_path / "both.yml")
    cfg = yaml.safe_load(path.read_text())
    cfg["news"]["scopes"]["NATIONAL"]["sources"][0][
        "geoserve_admin_enrichment"
    ] = True
    path.write_text(yaml.safe_dump(cfg))
    assert run_news_scan(path)["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        item = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchone()
    evidence = json_loads(item["evidence_json"], {})
    quake = evidence["usgs_earthquake"]
    assert quake["filter"]["geoserve_admin"]["region"] == "California"
    assert quake["filter"]["geography_basis"] == "usgs_geoserve_admin_live"
    assert quake["dyfi_state_evidence"]["reported_states_at_threshold"] == ["CA", "NV"]
