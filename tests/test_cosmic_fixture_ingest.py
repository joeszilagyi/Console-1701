from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml
from starlette.requests import Request

from console1701 import config as config_module
from console1701.api import build_router
from console1701.config import ConfigError, load_config
from console1701.db import connect_db, json_loads
from console1701.news.scanner import (
    _rebuild_science_clusters,
    purge_news_retention,
    run_news_scan,
)
from console1701.news.science_exoplanets import PS_COLUMNS
from console1701.news.science_mast import MAST_COLUMNS
from console1701.news.science_registry import list_science_source_registry
from console1701.news.science_sources import SCIENCE_FIXTURE_SOURCES
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
    assert all(json_loads(row["evidence_json"], {})["source"]["official_url"]
               for row in rows)
    assert all(json_loads(row["evidence_json"], {})["policy"]["auth_required"] is False
               for row in rows)
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


def _gcn_retraction_config(tmp_path, monkeypatch):
    path = _config(tmp_path, monkeypatch)
    payload = yaml.safe_load(path.read_text())
    circular = json.loads((FIXTURES / "gcn_circular.json").read_text())
    circular.update({
        "eventId": "FRB 20261015A",
        "subject": "Retraction: FRB 20261015A",
        "createdOn": int(datetime(2026, 10, 15, 18, 30, tzinfo=UTC).timestamp() * 1000),
    })
    circular_path = tmp_path / "gcn-retraction.json"
    circular_path.write_text(json.dumps(circular))
    payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"] = [
        {
            "id": source_id, "name": source_id, "kind": "api_json", "parser": parser,
            "enabled": True, "fixture_only": True, "official_url": official_url,
            "url": f"file://{fixture_path}",
        }
        for source_id, parser, official_url, fixture_path in (
            ("gcn_notices", "gcn_notice_fixture", "https://gcn.nasa.gov/docs/notices",
             FIXTURES / "gcn_notice.json"),
            ("gcn_circulars", "gcn_circular_fixture", "https://gcn.nasa.gov/circulars",
             circular_path),
        )
    ]
    path.write_text(yaml.safe_dump(payload))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("GCN fixture scan attempted HTTP"))
    ))
    return path, payload


def test_gcn_cross_source_retraction_survives_other_report_until_purge(tmp_path, monkeypatch):
    path, _ = _gcn_retraction_config(tmp_path, monkeypatch)
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute("SELECT id, evidence_json FROM news_items ORDER BY id").fetchall()
        event = conn.execute(
            "SELECT status, score, item_ids_json, ranking_explanation_json "
            "FROM science_events"
        ).fetchone()
        assert event["status"] == "retracted"
        assert event["score"] == 0
        assert len(json_loads(event["item_ids_json"], [])) == 2
        assert json_loads(event["ranking_explanation_json"], {})["retraction_override"]
        assert all(json_loads(row["evidence_json"], {})["science_event"]["status"]
                   == "retracted" for row in rows)
        notice_id = next(row["id"] for row in rows
                         if "gcn_notice" in json_loads(row["evidence_json"], {}))
        circular_id = next(row["id"] for row in rows if row["id"] != notice_id)

        conn.execute("UPDATE news_items SET expires_at = ? WHERE id = ?",
                     ("2026-01-01T00:00:00+00:00", notice_id))
        assert purge_news_retention(conn, config)["items"] == 1
        _rebuild_science_clusters(conn)
        retained = conn.execute("SELECT status, score FROM science_events").fetchone()
        assert tuple(retained) == ("retracted", 0)

        conn.execute("UPDATE news_items SET expires_at = ? WHERE id = ?",
                     ("2026-01-01T00:00:00+00:00", circular_id))
        assert purge_news_retention(conn, config)["items"] == 1
        _rebuild_science_clusters(conn)
        assert conn.execute("SELECT COUNT(*) FROM science_events").fetchone()[0] == 0


def test_gcn_circular_revision_withdraws_event_only_after_explicit_scope(
    tmp_path, monkeypatch
):
    path, payload = _gcn_retraction_config(tmp_path, monkeypatch)
    circular_path = Path(payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][1][
        "url"
    ].removeprefix("file://"))
    circular = json.loads(circular_path.read_text())
    circular["subject"] = "FRB 20261015A: Retraction of optical counterpart"
    circular_path.write_text(json.dumps(circular))
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        event = conn.execute("SELECT status, score FROM science_events").fetchone()
        assert (event["status"], event["score"] > 0) == ("active", True)
        assert conn.execute("SELECT COUNT(*) FROM science_withdrawals").fetchone()[0] == 0
        circular_item_id = conn.execute(
            "SELECT id FROM news_items WHERE title LIKE '%optical counterpart%'"
        ).fetchone()[0]

    circular["subject"] = "FRB 20261015A: Retraction of transient candidate"
    circular_path.write_text(json.dumps(circular))
    assert run_news_scan(path)["item_count"] == 2
    with connect_db(config["_db_path"]) as conn:
        event = conn.execute("SELECT status, score FROM science_events").fetchone()
        assert tuple(event) == ("retracted", 0)
        assert conn.execute("SELECT COUNT(*) FROM science_withdrawals").fetchone()[0] == 1
        item = conn.execute(
            "SELECT id, evidence_json FROM news_items WHERE title LIKE '%transient candidate%'"
        ).fetchone()
        assert item["id"] == circular_item_id
        assert json_loads(item["evidence_json"], {})["gcn_circular"]["withdraws_event"]


def test_gcn_withdrawal_survives_retraction_expiry_and_initial_reingest(tmp_path, monkeypatch):
    path, payload = _gcn_retraction_config(tmp_path, monkeypatch)
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert conn.execute("SELECT COUNT(*) FROM science_withdrawals").fetchone()[0] == 1
        row = conn.execute("SELECT id, evidence_json FROM news_items").fetchall()
        circular_id = next(item["id"] for item in row
                           if "gcn_circular" in json_loads(item["evidence_json"], {}))
        conn.execute("UPDATE news_items SET expires_at = ? WHERE id = ?",
                     ("2026-01-01T00:00:00+00:00", circular_id))
        assert purge_news_retention(conn, config)["items"] == 1
        _rebuild_science_clusters(conn)
        event = conn.execute("SELECT status, score, evidence_json FROM science_events").fetchone()
        assert (event["status"], event["score"]) == ("retracted", 0)
        assert json_loads(event["evidence_json"], {})[
            "withdrawal_basis"] == "retained_source_retraction"
        conn.commit()

    payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][1]["enabled"] = False
    path.write_text(yaml.safe_dump(payload))
    assert run_news_scan(path)["item_count"] == 1
    with connect_db(config["_db_path"]) as conn:
        event = conn.execute("SELECT status, score FROM science_events").fetchone()
        assert (event["status"], event["score"]) == ("retracted", 0)
        assert conn.execute("SELECT COUNT(*) FROM science_withdrawals").fetchone()[0] == 1

    other = json.loads((FIXTURES / "gcn_notice.json").read_text())
    other.update({"event_name": "FRB 20261015B", "id": "261015bbbb"})
    other_path = tmp_path / "other-gcn-notice.json"
    other_path.write_text(json.dumps(other))
    payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0]["url"] = (
        f"file://{other_path}"
    )
    path.write_text(yaml.safe_dump(payload))
    assert run_news_scan(path)["item_count"] == 1
    with connect_db(config["_db_path"]) as conn:
        events = conn.execute("SELECT status, score FROM science_events ORDER BY id").fetchall()
        assert sorted(event["status"] for event in events) == ["active", "retracted"]
        assert next(event["score"] for event in events if event["status"] == "active") > 0
        purge_news_retention(conn, config, now="2026-11-15T00:00:00+00:00")
        assert conn.execute("SELECT COUNT(*) FROM science_withdrawals").fetchone()[0] == 0


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
    assert "Official endpoint" in html
    assert "Fetch mode" in html and "local fixture" in html
    assert "Canonical URL" in html
    assert "this ingest did not request a product download" in html
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


@pytest.mark.parametrize((
    "source_id", "fixture_name", "kind", "contract", "evidence_key", "count"
), [
    ("esa_hubble_science_rss", "esa_telescope_science.rss", "rss", None, "science_rss", 1),
    ("esa_webb_science_rss", "esa_webb_science.rss", "rss", None, "science_rss", 1),
    ("nasa_exoplanet_ps_tap", "exoplanet_ps_tiny.json", "api_json", {
        "table": "ps", "format": "json", "columns": list(PS_COLUMNS),
        "default_only": True, "row_cap": 2, "since": "2026-10-14", "until": "2026-10-15",
    }, "exoplanet_archive", 2),
    ("mast_caom_tiny_metadata", "mast_caom_tiny.json", "api_json", {
        "service": "Mast.Caom.Filtered", "columns": list(MAST_COLUMNS),
        "format": "json", "page": 1, "row_cap": 2, "timeout_seconds": 10,
        "mission": "JWST", "target_name": "TRAPPIST-1",
        "t_min_start": 60245, "t_min_end": 60246,
    }, "mast_caom", 2),
    ("pds_collection_metadata", "pds_collection_metadata.json", "api_json", {
        "collection_lid": "urn:nasa:pds:msl_ice-dust:data_derived",
        "allowed_collection_lids": ["urn:nasa:pds:msl_ice-dust:data_derived"],
        "timeout_seconds": 10, "retention_days": 7,
    }, "pds_collection", 1),
    ("gcn_notices", "gcn_notice.json", "api_json", None, "gcn_notice", 1),
    ("nasa_science_news", "nasa_science_news_malformed.rss", "rss", None,
     "science_rss", 2),
    ("gcn_circulars", "gcn_circular.json", "api_json", None, "gcn_circular", 1),
    ("gracedb_public_alerts", "gracedb_public_alerts.json", "api_json", None,
     "gracedb_public_alert", 2),
])
def test_cosmic_fixture_adapters_run_offline_with_bounded_metadata(
    tmp_path, monkeypatch, source_id, fixture_name, kind, contract, evidence_key, count
):
    path = _config(tmp_path, monkeypatch)
    payload = yaml.safe_load(path.read_text())
    parser, official_url = SCIENCE_FIXTURE_SOURCES[source_id]
    source = {
        "id": source_id, "name": source_id, "kind": kind, "parser": parser,
        "enabled": True, "fixture_only": True, "official_url": official_url,
        "url": f"file://{FIXTURES / fixture_name}",
    }
    if contract is not None:
        source["query_contract"] = contract
    payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"] = [source]
    path.write_text(yaml.safe_dump(payload))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("COSMIC adapter attempted HTTP"))
    ))
    result = run_news_scan(path)
    assert result["status"] == "complete"
    assert result["item_count"] == count
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='SYSTEM_SOLAR'"
        ).fetchall()
        events = conn.execute("SELECT COUNT(*) FROM science_events").fetchone()[0]
    assert len(rows) == count
    assert events >= 1
    for row in rows:
        evidence = json_loads(row["evidence_json"], {})
        assert evidence["ingest"]["fixture_only"] is True
        assert evidence[evidence_key]
        if evidence_key == "gcn_circular":
            assert "fixture@example.test" not in row["evidence_json"]
            assert "map.fits" not in row["evidence_json"]
        if evidence_key in {"exoplanet_archive", "mast_caom", "pds_collection"}:
            assert evidence[evidence_key]["query_bounds"]
        for field in (
            "catalog_downloaded", "product_endpoint_called", "label_downloaded",
            "inventory_downloaded", "data_product_downloaded", "sky_map_downloaded",
            "image_downloaded",
        ):
            if field in evidence[evidence_key]:
                assert evidence[evidence_key][field] is False
        assert evidence["science_event"]["ranking"]["score"] >= 0


@pytest.mark.parametrize(("source_id", "parser", "kind", "official_url", "live_url"), [
    ("gcn_circulars", "gcn_circular_fixture", "api_json",
     "https://gcn.nasa.gov/circulars",
     "https://gcn.nasa.gov/circulars/33603.json"),
    ("nasa_science_news", "nasa_science_news_fixture", "rss",
     "https://science.nasa.gov/blogs/science-news/feed/",
     "https://science.nasa.gov/blogs/science-news/feed/"),
])
def test_cosmic_fixture_only_live_source_is_rejected_by_config(
    tmp_path, monkeypatch, source_id, parser, kind, official_url, live_url
):
    path = _config(tmp_path, monkeypatch)
    payload = yaml.safe_load(path.read_text())
    payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"] = [{
        "id": source_id, "name": source_id, "kind": kind,
        "parser": parser, "enabled": True, "fixture_only": False,
        "official_url": official_url, "url": live_url,
    }]
    path.write_text(yaml.safe_dump(payload))
    with pytest.raises(ConfigError):
        load_config(path)


def test_cosmic_heavy_archive_registry_cannot_be_configured_for_fixture_scan(
    tmp_path, monkeypatch
):
    heavy = [row for row in list_science_source_registry() if row["source_class"] in {
        "heavy_archive_candidate", "astronomy_catalog_candidate",
    }]
    assert len(heavy) >= 10
    for row in heavy:
        path = _config(tmp_path, monkeypatch)
        payload = yaml.safe_load(path.read_text())
        payload["solar_system_beyond"].update({
            "include_catalog_archives": True,
            "include_large_archive_queries": True,
            "allow_heavy_archive_sources": True,
        })
        payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"] = [{
            "id": row["source_key"], "name": row["source_name"],
            "kind": "api_json", "parser": "mast_caom_tiny_json", "enabled": True,
            "fixture_only": True, "official_url": row["raw_url"],
            "url": f"file://{FIXTURES / 'mast_caom_tiny.json'}",
        }]
        path.write_text(yaml.safe_dump(payload))
        with pytest.raises(ConfigError):
            load_config(path)


def test_cosmic_hype_only_fixture_reports_blocked_health_without_storing_claim(
    tmp_path, monkeypatch
):
    path = _config(tmp_path, monkeypatch)
    fixture = tmp_path / "hype-only.rss"
    fixture.write_text("""<rss version="2.0"><channel>
      <title>Jet Propulsion Laboratory – NASA</title>
      <item><title>NASA confirms aliens on Mars</title>
      <link>https://www.nasa.gov/missions/mars/alien-claim/</link>
      <pubDate>Thu, 15 Oct 2026 18:22:48 +0000</pubDate>
      <category>Astrophysics</category></item>
      </channel></rss>""")
    payload = yaml.safe_load(path.read_text())
    payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"] = [{
        "id": "nasa_jpl_science_feed", "name": "NASA JPL science fixture", "kind": "rss",
        "parser": "nasa_jpl_science_rss", "enabled": True, "fixture_only": True,
        "official_url": SCIENCE_FIXTURE_SOURCES["nasa_jpl_science_feed"][1],
        "url": f"file://{fixture}",
    }]
    path.write_text(yaml.safe_dump(payload))
    assert run_news_scan(path)["item_count"] == 0
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert conn.execute("SELECT COUNT(*) FROM news_items").fetchone()[0] == 0
        health = conn.execute(
            "SELECT state, evidence_json FROM news_source_health ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert health["state"] == "hype_blocked"
    assert json_loads(health["evidence_json"], {})["science_policy_dropped_count"] == 1


def test_cosmic_broad_archive_query_reports_firehose_block_before_storage(
    tmp_path, monkeypatch
):
    path = _config(tmp_path, monkeypatch)
    payload = yaml.safe_load(path.read_text())
    parser, official_url = SCIENCE_FIXTURE_SOURCES["nasa_exoplanet_ps_tap"]
    payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"] = [{
        "id": "nasa_exoplanet_ps_tap", "name": "Exoplanet metadata fixture",
        "kind": "api_json", "parser": parser, "enabled": True, "fixture_only": True,
        "official_url": official_url,
        "url": f"file://{FIXTURES / 'exoplanet_ps_tiny.json'}",
        "query_contract": {
            "table": "ps", "format": "json", "columns": list(PS_COLUMNS),
            "default_only": True, "row_cap": 100,
            "since": "2026-10-14", "until": "2026-10-15",
        },
    }]
    path.write_text(yaml.safe_dump(payload))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("broad archive attempted HTTP"))
    ))
    result = run_news_scan(path)
    assert result["status"] == "partial"
    assert result["item_count"] == 0
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert conn.execute("SELECT COUNT(*) FROM news_items").fetchone()[0] == 0
        health = conn.execute(
            "SELECT state FROM news_source_health ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert health["state"] == "archive_firehose_blocked"


def test_cosmic_auth_candidates_stay_unconfigurable_and_missing_auth_stops_ingest(
    tmp_path, monkeypatch
):
    auth_candidates = [row for row in list_science_source_registry()
                       if row["verification_status"] == "auth_required"]
    assert len(auth_candidates) >= 3
    assert {"tns_getting_started", "tns_api_manual"} <= {
        row["source_key"] for row in auth_candidates
    }
    for row in auth_candidates:
        assert row["source_health_behavior"] == "auth_required"
        path = _config(tmp_path, monkeypatch)
        payload = yaml.safe_load(path.read_text())
        payload["solar_system_beyond"].update({
            "allow_auth_required_sources": True, "include_tns": True,
            "include_literature_metadata": True, "allow_literature_metadata": True,
        })
        payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"] = [{
            "id": row["source_key"], "name": row["source_name"],
            "kind": "api_json", "parser": "gcn_notice_fixture", "enabled": True,
            "fixture_only": True, "official_url": row["raw_url"],
            "url": f"file://{FIXTURES / 'gcn_notice.json'}",
        }]
        path.write_text(yaml.safe_dump(payload))
        with pytest.raises(ConfigError):
            load_config(path)

    path = _config(tmp_path, monkeypatch, source_override={"auth": {"token": ""}})
    payload = yaml.safe_load(path.read_text())
    payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"] = [
        payload["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0]
    ]
    path.write_text(yaml.safe_dump(payload))
    monkeypatch.setattr("console1701.news.scanner.load_fixture_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("auth source read fixture"))
    ))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("auth source attempted HTTP"))
    ))
    result = run_news_scan(path)
    assert result["status"] == "partial" and result["item_count"] == 0
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        health = conn.execute(
            "SELECT state FROM news_source_health ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert health["state"] == "auth_required"
