from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import pytest
import yaml
from starlette.requests import Request

from console1701 import config as config_module
from console1701.api import build_router
from console1701.config import ConfigError, load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import OfficialFetchResult, is_supported_official_source
from console1701.news.scanner import run_news_scan
from console1701.news.science_rss import ESA_SPACE_SCIENCE_FEED


def _config(tmp_path, monkeypatch, *, allow_http=True, source_override=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    source = {
        "id": "esa_space_science_feed", "name": "ESA Space Science", "kind": "rss",
        "parser": "esa_science_rss", "enabled": True, "fixture_only": False,
        "official_url": ESA_SPACE_SCIENCE_FEED, "url": ESA_SPACE_SCIENCE_FEED,
    }
    source.update(source_override or {})
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "solar_system_beyond": {"enabled": True},
        "news": {"enabled": True, "fetch_policy": {
            "allow_official_http": allow_http, "max_response_bytes": 4_194_304,
        },
                 "scopes": {"SYSTEM_SOLAR": {"enabled": True, "sources": [source]}}},
    }))
    return path


def _payload(*, age_days=0):
    published = format_datetime(datetime.now(UTC) - timedelta(days=age_days))
    return f"""<rss><channel><title>ESA Space Science</title>
      <item><title>Solar Orbiter maps magnetic switchbacks</title>
      <link>https://www.esa.int/Science_Exploration/Space_Science/Solar_Orbiter/magnetic_switchbacks</link>
      <pubDate>{published}</pubDate><description>Solar physics finding.</description></item>
      <item><title>ESA mission launches</title>
      <link>https://www.esa.int/Science_Exploration/Space_Science/Solar_Orbiter/mission_launches</link>
      <pubDate>{published}</pubDate></item>
      <item><title>Week in images</title>
      <link>https://www.esa.int/About_Us/Week_in_images/October_2026</link>
      <pubDate>{published}</pubDate></item>
    </channel></rss>"""


def test_esa_science_live_allowlist_is_exact_and_scan_filters_to_recent_science(
    tmp_path, monkeypatch
):
    path = _config(tmp_path, monkeypatch, source_override={"retention_days": 365})
    source = load_config(path)["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0]
    assert source["verification_status"] == "verified"
    assert is_supported_official_source(source)
    for change in (
        {"url": source["url"] + "?other=1"}, {"parser": "generic_rss"},
        {"verification_status": "official_page_seen"}, {"auth": {"token": "x"}},
        {"fixture_only": True},
    ):
        assert not is_supported_official_source({**source, **change})
    payload = _payload()
    def fake_fetch(*args, **kwargs):
        assert kwargs["max_bytes"] == 1_048_576
        return OfficialFetchResult(payload, 200, None, None, len(payload.encode()))

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    assert run_news_scan(path)["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute(
            "SELECT title, evidence_json FROM news_items WHERE scope='SYSTEM_SOLAR'"
        ).fetchone()
    assert row["title"] == "Solar Orbiter maps magnetic switchbacks"
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["ingest"]["fixture_only"] is False
    assert evidence["source"]["verification_status"] == "verified"
    assert evidence["science_rss"]["data_product_downloaded"] is False
    assert evidence["retention"]["retention_days"] == 7
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("COSMIC GET fetched ESA RSS"))
    ))
    request = Request({
        "type": "http", "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": "/COSMIC", "raw_path": b"/COSMIC", "query_string": b"", "headers": [],
        "client": ("127.0.0.1", 12345), "server": ("testserver", 80), "root_path": "",
    })
    endpoint = next(route.endpoint for route in build_router(str(path)).routes
                    if route.path == "/{scope}")
    html = endpoint(request, "COSMIC").body.decode()
    assert "Solar Orbiter maps magnetic switchbacks" in html
    assert "official live feed" in html
    assert "this ingest did not request a product download" in html
    assert "no product downloaded by this fixture" not in html


@pytest.mark.parametrize("override", [
    {"id": "nasa_jpl_science_feed"}, {"url": ESA_SPACE_SCIENCE_FEED + "?x=1"},
    {"official_url": "https://example.test/rss"}, {"fixture_only": True},
    {"verification_status": "candidate_needs_verification"},
    {"interval_minutes": 1},
])
def test_esa_science_live_config_rejects_nonexact_source(tmp_path, monkeypatch, override):
    with pytest.raises(ConfigError):
        load_config(_config(tmp_path, monkeypatch, source_override=override))


def test_esa_science_live_requires_http_opt_in_and_ignores_old_items(tmp_path, monkeypatch):
    path = _config(tmp_path, monkeypatch, allow_http=False)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("unapproved ESA HTTP fetch"))
    ))
    assert run_news_scan(path)["item_count"] == 0
    recent = _payload(age_days=10)
    path = _config(tmp_path / "recent", monkeypatch)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        OfficialFetchResult(recent, 200, None, None, len(recent.encode()))
    ))
    assert run_news_scan(path)["item_count"] == 1
    old = _payload(age_days=30)
    path = _config(tmp_path / "old", monkeypatch)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        OfficialFetchResult(old, 200, None, None, len(old.encode()))
    ))
    assert run_news_scan(path)["item_count"] == 0
