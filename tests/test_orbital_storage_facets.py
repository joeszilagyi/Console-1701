from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, init_db, json_dumps
from console1701.news.facets import orbital_item_facets, replace_orbital_item_facets
from console1701.news.scanner import purge_news_retention, run_news_scan
from console1701.news.storage import list_orbital_items_by_facet


def test_orbital_facets_require_explicit_bounded_evidence():
    facets = orbital_item_facets({
        "source": {"source_family": "swpc"},
        "orbital_identity": {
            "event_type": "geomagnetic_storm", "object_id": "2026-ABC",
            "mission_id": "ISS", "unverified_claim": "G5",
        },
        "orbital_safety": {"public_warning": True, "collision": False},
        "sensitivity": {"tracking": True, "rumor": False},
        "title": "Seattle impact, perhaps",
    }, ["local-impact", "general", {"untrusted": "tag"}])
    assert ("source_family", "swpc") in facets
    assert ("event_type", "geomagnetic_storm") in facets
    assert ("object_id", "2026-abc") in facets
    assert ("mission_id", "iss") in facets
    assert ("safety", "public_warning") in facets
    assert ("sensitivity", "tracking") in facets
    assert ("impact_tag", "local-impact") in facets
    assert ("safety", "collision") not in facets
    assert ("impact_tag", "general") not in facets


def test_orbital_scoped_storage_backfill_refresh_and_expiry(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    fixture = tmp_path / "orbital.json"
    fixture.write_text(json_dumps({"items": [{
        "title": "Test space weather bulletin", "url": "https://example.test/orbital/1",
        "description": "Short fixture summary",
    }]}))
    config_path = tmp_path / "config.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: true}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: test_orbital_fixture
                  name: Test ORBITAL fixture
                  kind: local_file_json
                  enabled: true
                  source_family: swpc
                  tags: [local-impact]
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        item = list_orbital_items_by_facet(conn, "source_family", "swpc")[0]
        item_id = item["id"]
        assert item["description"] == "Short fixture summary"
        assert "article_body" not in item["evidence"]
        assert len(list_orbital_items_by_facet(conn, "impact_tag", "local-impact")) == 1
        evidence = dict(item["evidence"])
        evidence["orbital_identity"] = {
            "event_type": "geomagnetic_storm", "object_id": "G4-2026",
            "mission_id": "ISS",
        }
        evidence["orbital_safety"] = {"public_warning": True}
        evidence["sensitivity"] = {"tracking": False}
        conn.execute("UPDATE news_items SET evidence_json = ? WHERE id = ?", (
            json_dumps(evidence), item_id,
        ))
        conn.execute("DELETE FROM news_item_facets WHERE item_id = ?", (item_id,))
        conn.commit()
        init_db(conn)
        assert len(list_orbital_items_by_facet(conn, "object_id", "g4-2026")) == 1
        assert len(list_orbital_items_by_facet(conn, "mission_id", "iss")) == 1
        assert len(list_orbital_items_by_facet(conn, "safety", "public_warning")) == 1
        assert list_orbital_items_by_facet(conn, "sensitivity", "tracking") == []
        with pytest.raises(ValueError):
            list_orbital_items_by_facet(conn, "unbounded_kind", "x")
        plan = conn.execute(
            "EXPLAIN QUERY PLAN SELECT item_id FROM news_item_facets "
            "WHERE scope='ORBITAL' AND facet_kind='mission_id' AND facet_value='iss'"
        ).fetchall()
        assert any("idx_news_item_facets_lookup" in row["detail"] for row in plan)
        evidence["orbital_identity"]["object_id"] = "G5-2026"
        replace_orbital_item_facets(conn, item_id, evidence, ["global-impact"])
        assert list_orbital_items_by_facet(conn, "object_id", "g4-2026") == []
        assert len(list_orbital_items_by_facet(conn, "object_id", "g5-2026")) == 1
        conn.execute("UPDATE news_items SET expires_at = ? WHERE id = ?", (
            (datetime.now(UTC) - timedelta(days=1)).isoformat(), item_id,
        ))
        assert list_orbital_items_by_facet(conn, "object_id", "g5-2026") == []
        purged = purge_news_retention(conn, config)
        assert purged["items"] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM news_item_facets WHERE item_id = ?", (item_id,)
        ).fetchone()[0] == 0
