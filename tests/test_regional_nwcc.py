from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.regional_nwcc import ATOM_URL
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/regional_nwcc_atom.xml"


def _source() -> dict:
    return {
        "id": "nwcc_blog", "scope": "REGIONAL", "kind": "rss",
        "parser": "nwcc_atom_fixture", "url": FIXTURE.as_uri(),
        "official_url": ATOM_URL,
    }


def test_nwcc_atom_preserves_fire_update_metadata_without_body_or_impact_claim():
    items = parse_fixture_items(_source(), FIXTURE.read_text(encoding="utf-8"))
    assert len(items) == 2
    first = items[0]["evidence"]["nwcc_fire_update"]
    assert first["post_id"] == "4802763443429890160"
    assert first["published_at"] == "2026-10-06T17:31:52+00:00"
    assert first["source_url"].endswith("little-giant-sisi-fires-update.html")
    assert first["body_stored"] is False
    assert first["ranking"]["public_impact_score"] == 0
    assert items[0]["description"] is None
    assert items[1]["evidence"]["nwcc_fire_update"]["final_update"] is True


def test_nwcc_atom_rejects_wrong_identity_and_live_source():
    fixture = FIXTURE.read_text(encoding="utf-8")
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items({**_source(), "url": ATOM_URL}, fixture)
    with pytest.raises(NewsParserError, match="invalid post identity"):
        parse_fixture_items(_source(), fixture.replace("blog-8946818807005393639", "blog-OTHER", 1))
    with pytest.raises(NewsParserError, match="unapproved article URL"):
        parse_fixture_items(_source(), fixture.replace(
            "https://nwccinfo.blogspot.com/2026/10/10062026-little-giant-sisi-fires-update.html",
            "https://example.invalid/article.html",
        ))


def test_nwcc_offline_scan_and_live_block(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("NWCC fixture/live-block tests must not fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    fixture_config = tmp_path / "fixture.yml"
    fixture_config.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - id: nwcc_blog
                  enabled: true
                  url: "{FIXTURE.as_uri()}"
                  official_url: "{ATOM_URL}"
    """).strip() + "\n", encoding="utf-8")
    result = run_news_scan(fixture_config)
    assert result["status"] == "complete" and result["item_count"] == 2
    config = load_config(fixture_config)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='REGIONAL'"
        ).fetchall()
    evidence = [json_loads(str(row["evidence_json"]), {}) for row in rows]
    assert all(row["nwcc_fire_update"]["body_stored"] is False for row in evidence)
    assert all(row["regional_event"]["confidence"] == "low" for row in evidence)

    live_config = tmp_path / "live.yml"
    live_config.write_text(dedent("""
        paths: {repo_roots: [], explicit_repos: []}
        news:
          enabled: true
          fetch_policy: {allow_official_http: true}
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - {id: nwcc_blog, enabled: true}
    """).strip() + "\n", encoding="utf-8")
    assert run_news_scan(live_config)["status"] == "partial"
    config = load_config(live_config)
    with connect_db(config["_db_path"]) as conn:
        run = conn.execute(
            "SELECT status FROM news_fetch_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert run["status"] == "policy_blocked"
