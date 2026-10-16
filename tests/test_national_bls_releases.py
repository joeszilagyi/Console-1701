from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from console1701 import config as config_module
from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.national_registry import national_registry_config_defaults
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/news"


def _source(series: str) -> dict:
    key = "bls_employment_situation_atom" if series == "empsit" else "bls_cpi_atom"
    source = national_registry_config_defaults(key)
    assert source is not None
    source["url"] = f"file://{FIXTURES / f'national_bls_{series}.atom'}"
    return source


@pytest.mark.parametrize("series", ["empsit", "cpi"])
def test_bls_release_fixture_preserves_source_identity_without_body(series):
    source = _source(series)
    items = parse_fixture_items(source, (FIXTURES / f"national_bls_{series}.atom").read_text())
    assert len(items) == 1
    item = items[0]
    evidence = item["evidence"]["bls_release"]
    assert evidence["series"] == series
    assert evidence["entry_id"].startswith(series + "-")
    assert evidence["body_stored"] is False
    assert item["description"] is None
    assert item["evidence"]["national_identity"]["official_event_ids"] == [
        f"bls:{evidence['entry_id']}"
    ]
    assert "Fixture body" not in str(item)


@pytest.mark.parametrize("change", [
    {"id": "bls_home"}, {"scope": "GLOBAL"},
    {"official_url": "https://example.test/empsit.rss"},
])
def test_bls_release_rejects_wrong_source(change):
    fixture = (FIXTURES / "national_bls_empsit.atom").read_text()
    with pytest.raises(NewsParserError):
        parse_fixture_items({**_source("empsit"), **change}, fixture)


def test_bls_release_rejects_spoofed_and_unbounded_entries():
    source = _source("empsit")
    fixture = (FIXTURES / "national_bls_empsit.atom").read_text()
    for bad in (
        fixture.replace("www.bls.gov/news.release", "example.test/news.release"),
        fixture.replace("bls.gov:feed:empsit", "bls.gov:feed:cpi"),
        fixture.replace("<category>News Release</category>", "<category>Blog</category>"),
        "<!DOCTYPE feed>" + fixture,
        fixture.replace("<entry>", "<entry><link href=\"https://example.test\" />"),
    ):
        with pytest.raises(NewsParserError):
            parse_fixture_items(source, bad)
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(source, fixture + " " * 262_145)


def test_bls_release_fixture_scans_offline_with_configured_title_terms(tmp_path, monkeypatch):
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    path = tmp_path / "config.yml"
    sources = [{**_source(series), "enabled": True} for series in ("empsit", "cpi")]
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {"enabled": True, "scopes": {"NATIONAL": {
            "enabled": True, "sources": sources,
        }}},
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("BLS fixture attempted HTTP"))
    ))
    result = run_news_scan(path)
    assert result["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT title, description, evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchall()
    assert len(rows) == 2
    assert all(row["description"] is None for row in rows)
    assert all(json_loads(row["evidence_json"], {})["national"]["attention_state"] ==
               "background" for row in rows)
    assert all(json_loads(row["evidence_json"], {})["ingest"]["fixture_only"]
               for row in rows)


def test_bls_release_live_url_stays_blocked_before_fetch(tmp_path, monkeypatch):
    path = tmp_path / "live.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {"enabled": True, "fetch_policy": {"allow_official_http": True},
                 "scopes": {"NATIONAL": {"enabled": True, "sources": [
                     {"id": "bls_employment_situation_atom", "enabled": True},
                 ]}}},
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("BLS live URL reached HTTP fetch"))
    ))
    result = run_news_scan(path)
    assert result["status"] == "partial"
    assert result["item_count"] == 0
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        health = conn.execute("SELECT state FROM news_source_health").fetchone()
    assert health["state"] in {"policy_blocked", "unsupported"}
