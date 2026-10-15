from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, init_db
from console1701.news.facets import global_item_facets
from console1701.news.scanner import purge_news_retention, run_news_scan
from console1701.news.storage import list_global_items_by_facet

FIXTURES = Path(__file__).parent / "fixtures/news"


def test_global_sensitivity_and_impact_facets_require_explicit_evidence():
    facets = global_item_facets(
        {"source": {"source_family": "who"},
         "sensitivity": {"conflict": True, "rumor": False},
         "geography": {"verified_regions": ["Europe"]}},
        ["us-impact", "general"],
    )
    assert ("source_family", "who") in facets
    assert ("sensitivity", "conflict") in facets
    assert ("sensitivity", "rumor") not in facets
    assert ("region", "europe") in facets
    assert ("impact_tag", "us-impact") in facets


def _scan_global_fixtures(tmp_path: Path, monkeypatch) -> Path:
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("GLOBAL fixture scan must not fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    config_path = tmp_path / "config.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: gdacs_geojson_fixture
                  name: GDACS GeoJSON fixture
                  kind: api_json
                  parser: gdacs_geojson
                  source_family: gdacs
                  official_status: official
                  enabled: true
                  url: "file://{FIXTURES / 'global_gdacs.geojson'}"
                - id: reliefweb_disaster_fixture
                  name: ReliefWeb disaster fixture
                  kind: api_json
                  parser: reliefweb_disasters_json
                  source_family: reliefweb
                  official_status: official
                  enabled: true
                  url: "file://{FIXTURES / 'global_reliefweb_disasters.json'}"
    """).strip() + "\n")
    result = run_news_scan(config_path)
    assert result["status"] == "complete"
    assert result["item_count"] == 2
    return config_path


def test_global_facets_query_country_type_family_and_backfill(tmp_path, monkeypatch):
    config_path = _scan_global_fixtures(tmp_path, monkeypatch)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        assert [item["title"] for item in list_global_items_by_facet(
            conn, "country", "Costa Rica"
        )] == ["Earthquake in Costa Rica"]
        assert len(list_global_items_by_facet(conn, "event_type", "EQ")) == 1
        assert len(list_global_items_by_facet(conn, "event_type", "Tropical Cyclone")) == 1
        assert len(list_global_items_by_facet(conn, "source_family", "reliefweb")) == 1
        assert list_global_items_by_facet(conn, "country", "the Russian Federation") == []
        index_names = {
            row["name"] for row in conn.execute("PRAGMA index_list(news_item_facets)")
        }
        assert "idx_news_item_facets_lookup" in index_names
        conn.execute("DROP TABLE news_item_facets")
        conn.commit()
        init_db(conn)
        assert len(list_global_items_by_facet(conn, "country", "Costa Rica")) == 1


def test_global_facets_follow_item_refresh(tmp_path, monkeypatch):
    config_path = _scan_global_fixtures(tmp_path, monkeypatch)
    edited_fixture = tmp_path / "gdacs_changed.geojson"
    edited_fixture.write_text(
        (FIXTURES / "global_gdacs.geojson").read_text().replace("Costa Rica", "Panama")
    )
    original = f"file://{FIXTURES / 'global_gdacs.geojson'}"
    config_path.write_text(config_path.read_text().replace(original, f"file://{edited_fixture}"))
    assert run_news_scan(config_path)["status"] == "complete"
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        assert list_global_items_by_facet(conn, "country", "Costa Rica") == []
        assert len(list_global_items_by_facet(conn, "country", "Panama")) == 1


def test_global_facets_follow_retention_purge(tmp_path, monkeypatch):
    config_path = _scan_global_fixtures(tmp_path, monkeypatch)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        item = list_global_items_by_facet(conn, "country", "Costa Rica")[0]
        conn.execute("UPDATE news_items SET expires_at = ? WHERE id = ?", (
            "2020-01-01T00:00:00+00:00", item["id"]
        ))
        assert list_global_items_by_facet(conn, "country", "Costa Rica") == []
        purged = purge_news_retention(conn, config, now="2026-10-15T20:00:00+00:00")
        conn.commit()
        assert purged["items"] == 1
        assert list_global_items_by_facet(conn, "country", "Costa Rica") == []
        assert conn.execute(
            "SELECT COUNT(*) FROM news_item_facets WHERE item_id = ?", (item["id"],)
        ).fetchone()[0] == 0
