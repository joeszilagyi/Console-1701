from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_registry import get_global_source_registry_entry
from console1701.news.official_http import is_supported_official_source
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/global_pbs_world.rss"
FEED_URL = "https://www.pbs.org/newshour/feeds/rss/world"
SOURCE = {
    "id": "pbs_world_rss", "scope": "GLOBAL", "kind": "rss",
    "parser": "pbs_world_rss", "official_url": FEED_URL,
}


def test_pbs_world_rss_keeps_metadata_without_inferred_impact():
    registry = get_global_source_registry_entry("pbs_world_rss")
    assert registry is not None
    assert registry["parser"] == "pbs_world_rss"
    assert registry["enabled"] is False
    assert registry["verification_status"] == "candidate_needs_verification"
    assert is_supported_official_source({
        "id": "pbs_world_rss", "scope": "GLOBAL", "kind": "rss",
        "parser": "pbs_world_rss", "url": FEED_URL,
        "verification_status": "verified",
    }) is False
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 2
    assert items[0]["source_published_at"] == "2026-10-15T23:38:56+00:00"
    assert items[0]["description"] is None
    assert items[0]["evidence"]["pbs_world"]["creator"] == "Associated Press"
    assert items[0]["evidence"]["pbs_world"]["impact_verified"] is False
    assert items[0]["evidence"]["global_identity"]["international_impact"] is False
    assert "Fixture article excerpt" not in str(items)


def test_pbs_world_rss_rejects_wrong_identity_and_malformed_entries():
    raw = FIXTURE.read_text()
    with pytest.raises(NewsParserError, match="exact published feed"):
        parse_fixture_items({**SOURCE, "official_url": "https://example.org/rss"}, raw)
    with pytest.raises(NewsParserError, match="unverified channel"):
        parse_fixture_items(SOURCE, raw.replace("PBS News Hour - World", "Other"))
    with pytest.raises(NewsParserError, match="invalid publisher URL"):
        parse_fixture_items(SOURCE, raw.replace(
            "www.pbs.org/newshour/world/officials", "example.org/newshour/world/officials"
        ))
    with pytest.raises(NewsParserError, match="stable article metadata"):
        parse_fixture_items(SOURCE, raw.replace(
            "<guid isPermaLink=\"true\">https://www.pbs.org/newshour/world/officials",
            "<guid isPermaLink=\"true\">https://www.pbs.org/newshour/world/changed",
        ))
    with pytest.raises(NewsParserError, match="DTD"):
        parse_fixture_items(SOURCE, raw.replace("<rss", "<!DOCTYPE rss><rss", 1))
    with pytest.raises(PayloadTooLargeError, match="128 KiB"):
        parse_fixture_items(SOURCE, raw + " " * 131_072)


def test_pbs_world_rss_offline_scan_persists_background_only(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no publisher HTTP")),
    )
    path = tmp_path / "pbs.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: pbs_world_rss
                  enabled: true
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    result = run_news_scan(path)
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT description, evidence_json FROM news_items WHERE scope='GLOBAL'"
        ).fetchall()
    assert result["item_count"] == len(rows) == 2
    assert all(row["description"] is None for row in rows)
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert all(row["global_identity"]["international_impact"] is False for row in evidence)
    assert all(row["global_attention_policy"]["attention_state"] == "background"
               for row in evidence)
    assert "Fixture article excerpt" not in str([dict(row) for row in rows])
