from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from console1701 import config as config_module
from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import OfficialFetchResult, is_supported_official_source
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.science_atel import ATEL_RSS_URL

FIXTURE = Path(__file__).parent / "fixtures/science/atel_telegrams.rss"


def _source():
    return {
        "id": "astronomers_telegram_rss", "name": "ATel fixture",
        "scope": "SYSTEM_SOLAR", "kind": "rss", "parser": "atel_rss",
        "enabled": True, "fixture_only": True, "official_url": ATEL_RSS_URL,
        "url": f"file://{FIXTURE}",
    }


def test_atel_rss_preserves_preliminary_metadata_without_body():
    items = parse_fixture_items(_source(), FIXTURE.read_text())
    assert len(items) == 2
    assert items[0]["source_published_at"] == "2026-10-15T17:38:14+00:00"
    assert items[0]["evidence"]["atel_telegram"]["atel_number"] == 18105
    assert items[0]["evidence"]["atel_telegram"]["full_body_stored"] is False
    assert items[1]["evidence"]["atel_telegram"]["object_tokens"] == ["EP260531A"]
    assert items[1]["evidence"]["science_identity"]["object_name"] == "EP260531A"
    assert items[1]["evidence"]["science_identity"]["public_value_class"] == "preliminary"


@pytest.mark.parametrize("change", [
    {"id": "other"}, {"scope": "ORBITAL"},
    {"kind": "api_json"},
    {"official_url": "https://example.test/?rss"},
])
def test_atel_rss_rejects_wrong_source(change):
    with pytest.raises(NewsParserError):
        parse_fixture_items({**_source(), **change}, FIXTURE.read_text())


def test_atel_rss_rejects_malformed_spoofed_and_oversized_xml():
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "<rss>")
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "<!DOCTYPE rss><rss></rss>")
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 65_537)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), FIXTURE.read_text().replace("read=18105", "read=18106"))


def test_atel_fixture_scans_offline_and_live_requires_opt_in(tmp_path, monkeypatch):
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    path = tmp_path / "config.yml"
    raw = {
        "paths": {"repo_roots": [], "explicit_repos": []},
        "solar_system_beyond": {"enabled": True},
        "news": {"enabled": True, "scopes": {"SYSTEM_SOLAR": {
            "enabled": True, "sources": [_source()],
        }}},
    }
    path.write_text(yaml.safe_dump(raw))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("ATel fixture attempted HTTP"))
    ))
    result = run_news_scan(path)
    assert result["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='SYSTEM_SOLAR'"
        ).fetchall()
    assert len(rows) == 2
    assert all(json_loads(row["evidence_json"], {})["ingest"]["fixture_only"] for row in rows)
    raw["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0].update({
        "url": ATEL_RSS_URL, "fixture_only": False,
    })
    path.write_text(yaml.safe_dump(raw))
    source = load_config(path)["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0]
    assert source["interval_minutes"] >= 30
    assert source["verification_status"] == "verified"
    assert is_supported_official_source(source)
    assert run_news_scan(path)["item_count"] == 0


def test_atel_live_exact_source_uses_64k_cap_and_rejects_wrong_identity(tmp_path, monkeypatch):
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    source = {**_source(), "url": ATEL_RSS_URL, "fixture_only": False}
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "solar_system_beyond": {"enabled": True},
        "news": {"enabled": True, "fetch_policy": {"allow_official_http": True},
                 "scopes": {"SYSTEM_SOLAR": {"enabled": True, "sources": [source]}}},
    }))
    configured = load_config(path)["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0]
    for change in (
        {"url": ATEL_RSS_URL + "= "}, {"parser": "generic_rss"},
        {"verification_status": "official_page_seen"}, {"fixture_only": True},
    ):
        assert not is_supported_official_source({**configured, **change})
    payload = FIXTURE.read_text()

    def fake_fetch(*args, **kwargs):
        assert kwargs["max_bytes"] == 65_536
        return OfficialFetchResult(payload, 200, None, None, len(payload.encode()))

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='SYSTEM_SOLAR'"
        ).fetchall()
    assert len(rows) == 2
    assert all(json_loads(row["evidence_json"], {})["ingest"]["fixture_only"] is False
               for row in rows)
