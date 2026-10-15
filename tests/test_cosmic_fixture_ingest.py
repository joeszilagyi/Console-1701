from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from starlette.requests import Request

from console1701 import config as config_module
from console1701.api import build_router
from console1701.config import ConfigError, load_config
from console1701.db import connect_db, json_loads
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_scope_view

FIXTURES = Path(__file__).parent / "fixtures/science"


def _config(tmp_path, monkeypatch, *, science_enabled=True, source_override=None):
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    sources = [
        {"id": "nasa_jpl_science_feed", "name": "NASA JPL science fixture", "kind": "rss",
         "parser": "nasa_jpl_science_rss", "enabled": True, "fixture_only": True,
         "official_url": "https://www.nasa.gov/centers-and-facilities/jpl/feed/",
         "url": f"file://{FIXTURES / 'nasa_jpl_science.rss'}"},
        {"id": "esa_space_science_feed", "name": "ESA science fixture", "kind": "rss",
         "parser": "esa_science_rss", "enabled": True, "fixture_only": True,
         "official_url": "https://www.esa.int/rssfeed/Our_Activities/Space_Science",
         "url": f"file://{FIXTURES / 'esa_space_science.rss'}"},
    ]
    if source_override:
        sources[0].update(source_override)
    config_path = tmp_path / "config.yml"
    config_path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "solar_system_beyond": {"enabled": science_enabled},
        "news": {"enabled": True, "scopes": {"SYSTEM_SOLAR": {
            "enabled": True, "sources": sources,
        }}},
    }))
    return config_path


def test_cosmic_fixture_scan_ingests_science_only_without_network(tmp_path, monkeypatch):
    path = _config(tmp_path, monkeypatch)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("COSMIC fixture scan attempted HTTP"))
    ))
    result = run_news_scan(path)
    assert result["status"] == "complete"
    assert result["scanned_sources"] == 2
    assert result["item_count"] >= 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT scope, title, evidence_json FROM news_items WHERE scope='SYSTEM_SOLAR'"
        ).fetchall()
        events = conn.execute(
            "SELECT event_type, score, item_ids_json, ranking_explanation_json, "
            "scope_label_status FROM science_events ORDER BY id"
        ).fetchall()
        view = get_news_scope_view(conn, config, "SYSTEM_SOLAR")
    assert len(rows) == result["item_count"]
    assert view["state"]["state"] == "healthy"
    assert all(row["scope"] == "SYSTEM_SOLAR" for row in rows)
    assert all(json_loads(row["evidence_json"], {})["ingest"]["fixture_only"] for row in rows)
    assert len(events) == len(view["clusters"])
    assert len(events) >= 2
    assert all(event["scope_label_status"] == "cosmic" for event in events)
    assert all(json_loads(event["ranking_explanation_json"], {})["score"] == event["score"]
               for event in events)
    assert all(json_loads(row["evidence_json"], {}).get("science_event") for row in rows)
    assert not any("Earth" in row["title"] and "weather" in row["title"].lower()
                   for row in rows)
    again = run_news_scan(path)
    assert again["status"] == "complete"
    with connect_db(config["_db_path"]) as conn:
        assert conn.execute("SELECT COUNT(*) FROM science_events").fetchone()[0] == len(events)


@pytest.mark.parametrize("override", [
    {"id": "science_journalism"},
    {"official_url": "https://example.test/fake"},
    {"parser": "generic_json_items"},
    {"fixture_only": False},
    {"source_family": "fake"},
])
def test_cosmic_fixture_config_rejects_impersonation(tmp_path, monkeypatch, override):
    with pytest.raises(ConfigError):
        load_config(_config(tmp_path, monkeypatch, source_override=override))


def test_cosmic_parent_gate_skips_configured_fixture(tmp_path, monkeypatch):
    path = _config(tmp_path, monkeypatch, science_enabled=False)
    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("disabled COSMIC read fixture"))
    ))
    assert run_news_scan(path)["scanned_sources"] == 0


def test_cosmic_page_shows_stored_evidence_without_fetch(tmp_path, monkeypatch):
    path = _config(tmp_path, monkeypatch)
    assert run_news_scan(path)["item_count"] >= 2
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("COSMIC GET fetched HTTP"))
    ))
    request = Request({
        "type": "http", "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": "/COSMIC", "raw_path": b"/COSMIC", "query_string": b"", "headers": [],
        "client": ("127.0.0.1", 12345), "server": ("testserver", 80), "root_path": "",
    })
    router = build_router(str(path))
    page = next(route.endpoint for route in router.routes if route.path == "/{scope}")
    html = page(request, "COSMIC").body.decode()
    assert "NASA’s SPHEREx Telescope Sees Brown Dwarfs" in html
    assert "Event confidence" in html
    assert "Query bounds" in html
    assert "Data products" in html
    assert "SYSTEM_SOLAR" not in html


def test_cosmic_scan_drops_hype_claims_before_sqlite_storage(tmp_path, monkeypatch):
    path = _config(tmp_path, monkeypatch)
    fixture = tmp_path / "science-policy.rss"
    extra = """
      <item><title>NASA confirms aliens on Mars</title>
      <link>https://www.nasa.gov/missions/mars/alien-claim/</link>
      <pubDate>Thu, 15 Oct 2026 18:22:48 +0000</pubDate>
      <category>Astrophysics</category></item>
      <item><title>UFO sighting proves new astronomy discovery</title>
      <link>https://www.nasa.gov/missions/spherex/ufo-claim/</link>
      <pubDate>Thu, 15 Oct 2026 18:22:48 +0000</pubDate>
      <category>Astrophysics</category></item>
      <item><title>Shocking image: what is a brown dwarf?</title>
      <link>https://www.nasa.gov/missions/spherex/brown-dwarf-explainer/</link>
      <pubDate>Thu, 15 Oct 2026 18:22:48 +0000</pubDate>
      <category>Astrophysics</category></item>
    """
    fixture.write_text(
        (FIXTURES / "nasa_jpl_science.rss").read_text().replace("</channel>",
                                                                f"{extra}</channel>")
    )
    payload = yaml.safe_load(path.read_text())
    payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0]["url"] = f"file://{fixture}"
    path.write_text(yaml.safe_dump(payload))
    result = run_news_scan(path)
    assert result["status"] == "complete"
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT title, description, evidence_json FROM news_items "
            "WHERE scope = 'SYSTEM_SOLAR'"
        ).fetchall()
    assert not any("alien" in row["title"].lower() or "ufo" in row["title"].lower()
                   for row in rows)
    explainer = next(row for row in rows if "Shocking image" in row["title"])
    safety = json_loads(explainer["evidence_json"], {})["science_safety"]
    assert safety["attention_state"] == "background"
    assert result["item_count"] == len(rows)
