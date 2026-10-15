from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
import yaml

from console1701 import config as config_module
from console1701.config import ConfigError, load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import OfficialFetchResult, is_supported_official_source
from console1701.news.scanner import run_news_scan
from console1701.news.science_exoplanets import (
    EXOPLANET_TAP_URL,
    live_exoplanet_request_url,
)

FIXTURE = Path(__file__).parent / "fixtures/science/exoplanet_ps_tiny.json"


def _config(tmp_path, monkeypatch, *, allow_http=True, source_override=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    source = {
        "id": "nasa_exoplanet_ps_tap", "name": "NASA Exoplanet Archive",
        "kind": "api_json", "parser": "exoplanet_ps_json", "enabled": True,
        "fixture_only": False, "official_url": EXOPLANET_TAP_URL,
        "url": EXOPLANET_TAP_URL,
    }
    source.update(source_override or {})
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "solar_system_beyond": {"enabled": True},
        "news": {"enabled": True, "fetch_policy": {"allow_official_http": allow_http},
                 "scopes": {"SYSTEM_SOLAR": {"enabled": True, "sources": [source]}}},
    }))
    return path


def test_exoplanet_live_tap_query_is_app_built_and_scan_is_bounded(tmp_path, monkeypatch):
    path = _config(tmp_path, monkeypatch)
    source = load_config(path)["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0]
    assert source["verification_status"] == "verified"
    assert source["interval_minutes"] == 1440
    assert is_supported_official_source(source)
    parsed = urlsplit(live_exoplanet_request_url(source))
    args = parse_qs(parsed.query)
    assert parsed.scheme == "https" and parsed.netloc == "exoplanetarchive.ipac.caltech.edu"
    assert args["format"] == ["json"]
    assert "select top 10" in args["query"][0]
    assert "default_flag=1" in args["query"][0]
    assert "select *" not in args["query"][0]
    assert source["query_contract"]["row_cap"] == 10
    rows = json.loads(FIXTURE.read_text())
    today = datetime.now(UTC).date().isoformat()
    for row in rows:
        row["rowupdate"] = today
    payload = json.dumps(rows)
    calls = []

    def fake_fetch(source, **kwargs):
        calls.append(kwargs)
        assert kwargs["max_bytes"] == 65_536
        return OfficialFetchResult(payload, 200, None, None, len(payload))

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    result = run_news_scan(path)
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        items = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='SYSTEM_SOLAR'"
        ).fetchall()
    assert result["status"] == "complete" and result["item_count"] == 2
    assert len(calls) == 1 and len(items) == 2
    for row in items:
        evidence = json_loads(row["evidence_json"], {})
        assert evidence["ingest"]["fixture_only"] is False
        assert evidence["exoplanet_archive"]["query_bounds"] == source["query_contract"]
        assert evidence["exoplanet_archive"]["catalog_downloaded"] is False


@pytest.mark.parametrize("override", [
    {"url": EXOPLANET_TAP_URL + "?query=select+*+from+ps"},
    {"parser": "generic_json_items"}, {"fixture_only": True},
    {"interval_minutes": 60}, {"query_contract": {"row_cap": 1000}},
    {"verification_status": "candidate_policy_sensitive"},
])
def test_exoplanet_live_config_rejects_nonexact_source(tmp_path, monkeypatch, override):
    with pytest.raises(ConfigError):
        load_config(_config(tmp_path, monkeypatch, source_override=override))


def test_exoplanet_live_http_disabled_blocks_fetch(tmp_path, monkeypatch):
    path = _config(tmp_path, monkeypatch, allow_http=False)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("unapproved TAP request"))
    ))
    assert run_news_scan(path)["item_count"] == 0


def test_exoplanet_live_allowlist_rejects_modified_query(tmp_path, monkeypatch):
    source = load_config(_config(tmp_path, monkeypatch))["news"]["scopes"]["SYSTEM_SOLAR"][
        "sources"
    ][0]
    source["query_contract"]["row_cap"] = 1000
    assert not is_supported_official_source(source)
