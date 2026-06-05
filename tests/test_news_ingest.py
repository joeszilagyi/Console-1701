from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

import console1701.config as config_module
from console1701.cli import main
from console1701.config import load_config
from console1701.db import connect_db, init_db, json_loads
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import purge_news_retention, run_news_scan
from console1701.news.storage import get_news_sources_status

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "news"


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


def _file_url(path: Path) -> str:
    return f"file://{path.resolve()}"


@pytest.fixture(autouse=True)
def _isolated_console_state(monkeypatch, tmp_path):
    state_dir = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state_dir)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state_dir / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state_dir / "handoffs")


def test_parse_fixture_items_support_json_rss_atom_and_homepage():
    json_source = {
        "id": "json",
        "scope": "LOCAL",
        "kind": "local_file_json",
        "parser": "generic_json_items",
    }
    rss_source = {"id": "rss", "scope": "LOCAL", "kind": "local_file_rss"}
    atom_source = {"id": "atom", "scope": "ORBITAL", "kind": "atom"}
    homepage_source = {
        "id": "homepage",
        "scope": "NATIONAL",
        "kind": "homepage_headlines",
        "parser": "homepage_selectors",
        "homepage_url": "https://news.example.test/",
        "selectors": {
            "item": "article",
            "title": "h2",
            "url": "a",
            "description": "p",
        },
    }

    json_items = parse_fixture_items(json_source, (FIXTURE_DIR / "local_items.json").read_text())
    rss_items = parse_fixture_items(rss_source, (FIXTURE_DIR / "local_feed.rss").read_text())
    atom_items = parse_fixture_items(atom_source, (FIXTURE_DIR / "local_feed.atom").read_text())
    homepage_items = parse_fixture_items(
        homepage_source,
        (FIXTURE_DIR / "homepage.html").read_text(),
    )

    assert len(json_items) == 2
    assert json_items[0]["source_published_at"] == "2026-05-05T17:30:00+00:00"
    assert json_items[1]["url"] == "https://alerts.example.test/power-outage?a=1&b=2"
    assert len(rss_items) == 2
    assert rss_items[0]["tags"] == ["transit", "official"]
    assert len(atom_items) == 2
    assert atom_items[0]["tags"] == ["orbital", "forecast"]
    assert len(homepage_items) == 2
    assert homepage_items[0]["url"] == "https://news.example.test/port/cruise-terminal-plan"


def test_parse_nws_alert_fixture_filters_local_alerts_and_preserves_evidence():
    source = {
        "id": "nws_active_alerts_api",
        "scope": "LOCAL",
        "kind": "api_json",
        "parser": "nws_alerts_json",
        "zone_ids": ["WAZ558"],
    }

    items = parse_fixture_items(source, (FIXTURE_DIR / "local_nws_alerts.json").read_text())

    assert len(items) == 1
    assert items[0]["title"] == "High Wind Warning issued May 5 for Seattle"
    assert items[0]["source_published_at"] == "2026-05-05T17:00:00+00:00"
    assert {"official", "weather", "alert", "nws", "severe"}.issubset(items[0]["tags"])
    evidence = items[0]["evidence"]["nws_alert"]
    assert evidence["event"] == "High Wind Warning"
    assert evidence["severity"] == "Severe"
    assert evidence["urgency"] == "Expected"
    assert evidence["certainty"] == "Likely"
    assert evidence["affected_zones"] == ["https://api.weather.gov/zones/forecast/WAZ558"]
    assert evidence["effective"] == "2026-05-05T17:00:00+00:00"
    assert evidence["expires"] == "2026-05-06T06:00:00+00:00"
    assert evidence["ranking"]["active_alert"] is True
    assert evidence["ranking"]["total_alert_weight"] == 58
    assert evidence["filter"]["matched_keywords"] == ["Seattle"]
    assert evidence["filter"]["matched_zone_ids"] == ["WAZ558"]


def test_parse_alertseattle_rss_fixture_preserves_official_alert_evidence():
    source = {
        "id": "alertseattle_feed",
        "scope": "LOCAL",
        "kind": "rss",
        "parser": "alertseattle_rss",
    }

    items = parse_fixture_items(source, (FIXTURE_DIR / "local_alertseattle.rss").read_text())

    assert len(items) == 2
    utility = items[0]["evidence"]["alertseattle"]
    emergency = items[1]["evidence"]["alertseattle"]
    assert items[0]["title"] == "Power outage affecting parts of Capitol Hill"
    assert items[0]["source_published_at"] == "2026-05-05T22:15:00+00:00"
    assert {"official", "alertseattle", "city-alert", "utility", "moderate"}.issubset(
        items[0]["tags"]
    )
    assert utility["event_type"] == "utility"
    assert utility["severity"] == "moderate"
    assert utility["ranking"]["city_alert_score"] == 42
    assert emergency["event_type"] == "emergency"
    assert emergency["severity"] == "severe"
    assert emergency["ranking"]["city_alert_score"] == 54


def test_parse_metro_rss_fixture_preserves_route_and_impact_evidence():
    source = {
        "id": "metro_service_advisories_rss",
        "scope": "LOCAL",
        "kind": "rss",
        "parser": "metro_rss",
        "service_area_keywords": ["Downtown Seattle", "Ballard"],
    }

    items = parse_fixture_items(
        source,
        (FIXTURE_DIR / "local_metro_service_advisories.rss").read_text(),
    )

    assert len(items) == 2
    first = items[0]["evidence"]["metro_advisory"]
    second = items[1]["evidence"]["metro_advisory"]
    assert items[0]["title"] == "Routes 7, 49 and 60 rerouted in Downtown Seattle"
    assert items[0]["source_published_at"] == "2026-05-05T19:15:00+00:00"
    assert first["route_ids"] == ["7", "49", "60"]
    assert first["affected_service_areas"] == ["Downtown Seattle"]
    assert first["impact"] == "reroute"
    assert first["ranking"]["transit_impact_score"] == 37
    assert {"official", "transit", "metro", "route-7", "route-49", "route-60"}.issubset(
        items[0]["tags"]
    )
    assert second["route_ids"] == ["40"]
    assert second["affected_service_areas"] == ["Ballard"]
    assert second["impact"] == "delay"


def test_parse_local_blog_rss_fixture_preserves_neighborhood_metadata_only_evidence():
    source = {
        "id": "west_seattle_blog_feed",
        "scope": "LOCAL",
        "kind": "rss",
        "parser": "local_blog_rss",
        "source_family": "west_seattle_blog",
        "neighborhood_keywords": ["West Seattle", "Capitol Hill"],
    }

    items = parse_fixture_items(source, (FIXTURE_DIR / "local_blog_feed.rss").read_text())

    assert len(items) == 2
    bridge = items[0]["evidence"]["local_blog"]
    civic = items[1]["evidence"]["local_blog"]
    assert items[0]["title"] == "West Seattle Bridge lane blocked after collision"
    assert items[0]["source_published_at"] == "2026-05-05T23:05:00+00:00"
    assert {"local-news", "neighborhood-blog", "disruption", "west-seattle"}.issubset(
        items[0]["tags"]
    )
    assert bridge["publisher_family"] == "west_seattle_blog"
    assert bridge["neighborhoods"] == ["West Seattle"]
    assert bridge["signal_type"] == "disruption"
    assert bridge["ranking"]["local_blog_score"] == 22
    assert bridge["storage"]["headline_metadata_only"] is True
    assert bridge["storage"]["article_body_stored"] is False
    assert civic["neighborhoods"] == ["Capitol Hill"]
    assert civic["signal_type"] == "civic"


def test_parse_sfd_fire_911_fixture_redacts_low_acuity_private_locations():
    source = {
        "id": "sfd_fire_911_dataset",
        "scope": "LOCAL",
        "kind": "open_data_json",
        "parser": "sfd_fire_911_socrata",
        "dataset_id": "kzjm-xkqj",
        "homepage_url": "https://dev.socrata.com/foundry/data.seattle.gov/kzjm-xkqj",
    }

    items = parse_fixture_items(source, (FIXTURE_DIR / "local_sfd_fire_911.json").read_text())

    assert len(items) == 2
    major = items[0]
    aid = items[1]
    assert major["title"] == "SFD Structure Fire near E Pine St"
    assert major["source_published_at"] == "2026-05-05T20:05:00+00:00"
    major_evidence = major["evidence"]["sfd_fire_911"]
    assert major_evidence["dataset_id"] == "kzjm-xkqj"
    assert major_evidence["row_id"] == "row-major-fire"
    assert major_evidence["incident_number"] == "F260050001"
    assert major_evidence["unit_count"] == 7
    assert major_evidence["location_tokens"] == ["Capitol Hill", "E Pine St"]
    assert major_evidence["public_impact"]["elevated"] is True
    assert major["evidence"]["privacy"]["exact_location_suppressed"] is False

    assert aid["title"] == "SFD Aid Response near Ballard"
    assert aid["description"] == (
        "SFD reported Aid Response with 1 reported unit(s). Exact location suppressed by "
        "LOCAL privacy rules."
    )
    aid_evidence = aid["evidence"]["sfd_fire_911"]
    aid_privacy = aid["evidence"]["privacy"]
    assert aid_evidence["row_id"] == "row-aid-response"
    assert aid_evidence["public_impact"]["elevated"] is False
    assert aid_privacy["exact_location_suppressed"] is True
    assert aid_privacy["low_acuity_private"] is True
    assert aid_privacy["display_location"] == "Ballard"
    assert aid_privacy["raw_address_stored"] is False
    assert "9876" not in json.dumps(aid, sort_keys=True)


def test_parse_wsdot_alert_fixture_filters_seattle_corridors_and_scores_impact():
    source = {
        "id": "wsdot_traffic_api",
        "scope": "LOCAL",
        "kind": "api_json",
        "parser": "wsdot_travel_alerts_json",
        "route_keywords": ["I-5", "SR 99"],
        "area_keywords": ["Seattle", "Downtown"],
    }

    items = parse_fixture_items(source, (FIXTURE_DIR / "local_wsdot_alerts.json").read_text())

    assert len(items) == 1
    assert items[0]["title"] == "I-5 northbound lane blocked near Downtown Seattle"
    assert items[0]["source_published_at"] == "2026-05-05T21:05:00+00:00"
    assert {"official", "transport", "wsdot", "lane_blocked", "i-5"}.issubset(items[0]["tags"])
    evidence = items[0]["evidence"]["wsdot_alert"]
    assert evidence["alert_id"] == "1001"
    assert evidence["route_tokens"] == ["I-5"]
    assert evidence["impact"] == "lane_blocked"
    assert evidence["impact_weight"] == 22
    assert evidence["ranking"]["public_impact_score"] == 28
    assert evidence["filter"]["matched_route_tokens"] == ["I-5"]
    assert evidence["filter"]["matched_area_keywords"] == ["Seattle", "Downtown"]


def test_parse_city_light_outage_fixture_filters_local_area_and_scores_utility_impact():
    source = {
        "id": "city_light_outage_fixture",
        "scope": "LOCAL",
        "kind": "api_json",
        "parser": "city_light_outages_json",
        "area_keywords": ["Capitol Hill"],
    }

    items = parse_fixture_items(
        source,
        (FIXTURE_DIR / "local_city_light_outages.json").read_text(),
    )

    assert len(items) == 1
    assert items[0]["title"] == "City Light outage affecting Capitol Hill"
    assert items[0]["source_published_at"] == "2026-05-06T05:20:00+00:00"
    assert {"official", "utility", "city-light", "power-outage", "major_outage"}.issubset(
        items[0]["tags"]
    )
    evidence = items[0]["evidence"]["city_light_outage"]
    assert evidence["outage_id"] == "scl-capitol-hill-001"
    assert evidence["area"] == "Capitol Hill"
    assert evidence["customers_affected"] == 2400
    assert evidence["estimated_restoration_at"] == "2026-05-06T08:30:00+00:00"
    assert evidence["filter"]["matched_area_keywords"] == ["Capitol Hill"]
    assert evidence["ranking"]["customer_impact_weight"] == 24
    assert evidence["ranking"]["status_weight"] == 12
    assert evidence["ranking"]["utility_impact_score"] == 39


def test_parse_faa_airport_status_fixture_filters_sea_and_scores_airport_impact():
    source = {
        "id": "faa_airport_status_fixture",
        "scope": "LOCAL",
        "kind": "api_json",
        "parser": "faa_airport_status_json",
        "airport_codes": ["SEA"],
    }

    items = parse_fixture_items(
        source,
        (FIXTURE_DIR / "local_faa_airport_status_sea.json").read_text(),
    )

    assert len(items) == 1
    assert items[0]["title"] == "FAA SEA airport status: Ground Delay"
    assert items[0]["source_published_at"] == "2026-05-05T23:10:00+00:00"
    assert {"official", "airport", "faa", "sea", "ground_delay"}.issubset(items[0]["tags"])
    evidence = items[0]["evidence"]["faa_airport_status"]
    assert evidence["airport_code"] == "SEA"
    assert evidence["airport_name"] == "Seattle-Tacoma Intl"
    assert evidence["status"] == "Ground Delay"
    assert evidence["reason"] == "Low ceilings"
    assert evidence["ranking"]["event_weight"] == 34
    assert evidence["ranking"]["delay_minutes"] == 45
    assert evidence["ranking"]["delay_weight"] == 9
    assert evidence["ranking"]["airport_impact_score"] == 43
    assert evidence["filter"]["matched_airport_codes"] == ["SEA"]


def test_run_news_scan_ingests_local_fixtures_and_dedupes(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: local_json
                  name: Local JSON
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_items.json")}"
                  parser: generic_json_items
                  tags: [fixture, local]
                  priority: 60
                - id: local_rss
                  name: Local RSS
                  kind: local_file_rss
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_feed.rss")}"
                  priority: 55
        """,
    )

    first = run_news_scan(config_path)
    second = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        items = conn.execute(
            """
            SELECT title, trend_score, tags_json, evidence_json
            FROM news_items
            ORDER BY title
            """
        ).fetchall()
        fetch_runs = conn.execute("SELECT status FROM news_fetch_runs ORDER BY id").fetchall()
        clusters = conn.execute("SELECT cluster_key, item_count FROM news_clusters").fetchall()

    assert first["status"] == "complete"
    assert first["item_count"] == 4
    assert first["healthy_sources"] == 2
    assert second["status"] == "complete"
    assert len(items) == 4
    assert any(int(row["trend_score"]) == 2 for row in items)
    tag_values = {tag for row in items for tag in json_loads(str(row["tags_json"]), [])}
    evidence_rows = [json_loads(str(row["evidence_json"]), {}) for row in items]
    assert {"fixture", "local"}.issubset(tag_values)
    assert any(str(row.get("fixture_path", "")).endswith(".json") for row in evidence_rows)
    ranked_local_row = next(
        row
        for row in evidence_rows
        if str(row.get("fixture_path", "")).endswith("local_items.json")
        and row["ranking"]["factors"]["official_source_boost"] == 12
    )
    ranking = ranked_local_row["ranking"]
    assert ranking["factors"]["source_priority"] == 60
    assert ranking["factors"]["scope_priority_boost"] == 18
    assert ranking["factors"]["official_source_boost"] == 12
    assert ranking["factors"]["recency_bonus"] >= 0
    assert ranking["reasons"]
    assert [row["status"] for row in fetch_runs] == ["success", "success", "success", "success"]
    assert len(clusters) == 4


def test_run_news_scan_ingests_registry_backed_nws_alert_fixture(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: nws_active_alerts_api
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_nws_alerts.json")}"
                  zone_ids: [WAZ558]
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        row = conn.execute(
            """
            SELECT title, tags_json, evidence_json
            FROM news_items
            WHERE source_kind = 'api_json'
            """
        ).fetchone()
        source = conn.execute(
            """
            SELECT source_key, name, policy_json
            FROM news_sources
            WHERE source_key = 'nws_active_alerts_api'
            """
        ).fetchone()

    evidence = json_loads(str(row["evidence_json"]), {})
    policy = json_loads(str(source["policy_json"]), {})

    assert result["status"] == "complete"
    assert result["item_count"] == 1
    assert row["title"] == "High Wind Warning issued May 5 for Seattle"
    assert "official" in json_loads(str(row["tags_json"]), [])
    assert evidence["nws_alert"]["severity"] == "Severe"
    assert evidence["nws_alert"]["ranking"]["total_alert_weight"] == 58
    assert evidence["ranking"]["factors"]["official_source_boost"] == 12
    assert evidence["ranking"]["factors"]["local_official_alert_boost"] == 28
    assert evidence["ranking"]["factors"]["local_source_severity_boost"] == 30
    assert source["name"] == "NWS active alerts API"
    assert policy["source_class"] == "official_weather_hazard"
    assert policy["adapter"] == "official_api_json"
    assert policy["parser"] == "nws_alerts_json"


def test_run_news_scan_ingests_registry_backed_alertseattle_fixture(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: alertseattle_feed
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_alertseattle.rss")}"
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        rows = conn.execute(
            """
            SELECT title, evidence_json
            FROM news_items
            ORDER BY title
            """
        ).fetchall()
        source = conn.execute(
            """
            SELECT name, policy_json
            FROM news_sources
            WHERE source_key = 'alertseattle_feed'
            """
        ).fetchone()

    evidence_rows = [json_loads(str(row["evidence_json"]), {}) for row in rows]
    policy = json_loads(str(source["policy_json"]), {})

    assert result["status"] == "complete"
    assert result["item_count"] == 2
    assert source["name"] == "AlertSeattle RSS feed candidate"
    assert policy["adapter"] == "rss_atom"
    assert policy["parser"] == "alertseattle_rss"
    assert any(evidence["alertseattle"]["severity"] == "severe" for evidence in evidence_rows)
    assert {
        evidence["ranking"]["factors"]["local_source_severity_boost"]
        for evidence in evidence_rows
    } == {18, 30}
    assert any(
        evidence["ranking"]["factors"]["official_source_boost"] == 12 for evidence in evidence_rows
    )
    assert any(
        evidence["ranking"]["factors"]["local_official_alert_boost"] == 24
        for evidence in evidence_rows
    )


def test_run_news_scan_ingests_registry_backed_metro_rss_fixture(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: metro_service_advisories_rss
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_metro_service_advisories.rss")}"
                  service_area_keywords: ["Downtown Seattle", "Ballard"]
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        rows = conn.execute(
            """
            SELECT title, evidence_json
            FROM news_items
            ORDER BY title
            """
        ).fetchall()
        source = conn.execute(
            """
            SELECT name, policy_json
            FROM news_sources
            WHERE source_key = 'metro_service_advisories_rss'
            """
        ).fetchone()

    evidence_rows = [json_loads(str(row["evidence_json"]), {}) for row in rows]
    policy = json_loads(str(source["policy_json"]), {})

    assert result["status"] == "complete"
    assert result["item_count"] == 2
    assert source["name"] == "King County Metro service advisories RSS"
    assert policy["adapter"] == "rss_atom"
    assert policy["parser"] == "metro_rss"
    assert any(
        evidence["metro_advisory"]["route_ids"] == ["7", "49", "60"] for evidence in evidence_rows
    )
    assert any(
        evidence["ranking"]["factors"]["official_source_boost"] == 12 for evidence in evidence_rows
    )
    assert any(
        evidence["ranking"]["factors"]["local_transit_impact_boost"] == 37
        for evidence in evidence_rows
    )


def test_run_news_scan_ingests_registry_backed_regional_news_rss_fixture(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - id: regional_news_rss
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_feed.rss")}"
                  service_area_keywords: ["Seattle", "Capitol Hill"]
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        rows = conn.execute(
            """
            SELECT title, evidence_json
            FROM news_items
            ORDER BY title
            """
        ).fetchall()
        source = conn.execute(
            """
            SELECT name, policy_json
            FROM news_sources
            WHERE source_key = 'regional_news_rss'
            """
        ).fetchone()

    evidence_rows = [json_loads(str(row["evidence_json"]), {}) for row in rows]
    policy = json_loads(str(source["policy_json"]), {})

    assert result["status"] == "complete"
    assert result["item_count"] == 2
    assert source["name"] == "Regional news RSS"
    assert policy["parser"] == "regional_news_rss"
    assert any(
        evidence["local_news"]["service_areas"] == ["Seattle"] for evidence in evidence_rows
    )
    assert any(
        evidence["ranking"]["factors"]["scope_priority_boost"] == 14
        for evidence in evidence_rows
    )


def test_run_news_scan_ingests_gated_registry_backed_local_blog_fixture(tmp_path):
    blocked_config = _write_config(
        tmp_path / "blocked.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: west_seattle_blog_feed
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_blog_feed.rss")}"
        """,
    )
    with pytest.raises(config_module.ConfigError, match="local.allow_neighborhood_blogs true"):
        load_config(blocked_config)

    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        local:
          allow_neighborhood_blogs: true
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: west_seattle_blog_feed
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_blog_feed.rss")}"
                  neighborhood_keywords: ["West Seattle", "Capitol Hill"]
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        rows = conn.execute(
            """
            SELECT title, evidence_json
            FROM news_items
            ORDER BY title
            """
        ).fetchall()
        source = conn.execute(
            """
            SELECT name, policy_json
            FROM news_sources
            WHERE source_key = 'west_seattle_blog_feed'
            """
        ).fetchone()

    evidence_rows = [json_loads(str(row["evidence_json"]), {}) for row in rows]
    policy = json_loads(str(source["policy_json"]), {})

    assert result["status"] == "complete"
    assert result["item_count"] == 2
    assert source["name"] == "West Seattle Blog feed"
    assert policy["source_class"] == "neighborhood_blog"
    assert policy["parser"] == "local_blog_rss"
    assert policy["local"]["allow_neighborhood_blogs"] is True
    assert any(
        evidence["local_blog"]["storage"]["article_body_stored"] is False
        for evidence in evidence_rows
    )
    assert any(evidence["local_blog"]["signal_type"] == "disruption" for evidence in evidence_rows)
    assert any(
        evidence["ranking"]["factors"]["local_blog_signal_boost"] == 20
        for evidence in evidence_rows
    )


def test_run_news_scan_ingests_registry_backed_sfd_fire_911_fixture(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: sfd_fire_911_dataset
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_sfd_fire_911.json")}"
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        rows = conn.execute(
            """
            SELECT title, description, evidence_json
            FROM news_items
            ORDER BY title
            """
        ).fetchall()
        source = conn.execute(
            """
            SELECT name, policy_json
            FROM news_sources
            WHERE source_key = 'sfd_fire_911_dataset'
            """
        ).fetchone()

    evidence_by_title = {
        str(row["title"]): json_loads(str(row["evidence_json"]), {}) for row in rows
    }
    descriptions = {str(row["title"]): str(row["description"]) for row in rows}
    policy = json_loads(str(source["policy_json"]), {})

    assert result["status"] == "complete"
    assert result["item_count"] == 2
    assert source["name"] == "Seattle Real-Time Fire 911 Calls dataset"
    assert policy["adapter"] == "socrata_json"
    assert policy["parser"] == "sfd_fire_911_socrata"
    major = evidence_by_title["SFD Structure Fire near E Pine St"]
    aid = evidence_by_title["SFD Aid Response near Ballard"]
    assert major["sfd_fire_911"]["public_impact"]["elevated"] is True
    assert major["ranking"]["factors"]["local_public_impact_boost"] == 34
    assert major["privacy"]["article_body_stored"] is False
    assert aid["privacy"]["exact_location_suppressed"] is True
    assert aid["privacy"]["redaction_applied"] is True
    assert aid["privacy"]["article_body_stored"] is False
    assert aid["privacy"]["overdose_related"] is False
    assert aid["privacy"]["privacy_category"] == "low_acuity"
    assert aid["ranking"]["factors"]["local_public_impact_boost"] == 0
    assert aid["ranking"]["factors"]["local_privacy_penalty"] == -40
    assert "9876" not in descriptions["SFD Aid Response near Ballard"]
    assert "9876" not in json.dumps(aid, sort_keys=True)


def test_run_news_scan_ingests_registry_backed_wsdot_alert_fixture(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: wsdot_traffic_api
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_wsdot_alerts.json")}"
                  route_keywords: ["I-5", "SR 99"]
                  area_keywords: ["Seattle", "Downtown"]
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        row = conn.execute(
            """
            SELECT title, evidence_json
            FROM news_items
            WHERE source_kind = 'api_json'
            """
        ).fetchone()
        source = conn.execute(
            """
            SELECT name, policy_json
            FROM news_sources
            WHERE source_key = 'wsdot_traffic_api'
            """
        ).fetchone()

    evidence = json_loads(str(row["evidence_json"]), {})
    policy = json_loads(str(source["policy_json"]), {})

    assert result["status"] == "complete"
    assert result["item_count"] == 1
    assert row["title"] == "I-5 northbound lane blocked near Downtown Seattle"
    assert source["name"] == "WSDOT traffic API page"
    assert policy["adapter"] == "official_api_json"
    assert policy["parser"] == "wsdot_travel_alerts_json"
    assert evidence["wsdot_alert"]["route_tokens"] == ["I-5"]
    assert evidence["wsdot_alert"]["ranking"]["public_impact_score"] == 28
    assert evidence["ranking"]["factors"]["local_public_impact_boost"] == 28
    assert evidence["ranking"]["factors"]["official_source_boost"] == 12


def test_run_news_scan_ingests_city_light_outage_fixture(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: city_light_outage_fixture
                  name: City Light outage fixture
                  kind: api_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_city_light_outages.json")}"
                  parser: city_light_outages_json
                  source_family: city_light
                  source_class: official_utility
                  adapter: source_health_probe_only
                  verification_status: candidate_needs_verification
                  area_keywords: ["Capitol Hill"]
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        row = conn.execute(
            """
            SELECT title, evidence_json
            FROM news_items
            WHERE source_id = (
              SELECT id FROM news_sources WHERE source_key = 'city_light_outage_fixture'
            )
            """
        ).fetchone()
        source = conn.execute(
            """
            SELECT name, policy_json
            FROM news_sources
            WHERE source_key = 'city_light_outage_fixture'
            """
        ).fetchone()

    evidence = json_loads(str(row["evidence_json"]), {})
    policy = json_loads(str(source["policy_json"]), {})

    assert result["status"] == "complete"
    assert result["item_count"] == 1
    assert row["title"] == "City Light outage affecting Capitol Hill"
    assert source["name"] == "City Light outage fixture"
    assert policy["source_class"] == "official_utility"
    assert policy["adapter"] == "source_health_probe_only"
    assert evidence["city_light_outage"]["ranking"]["utility_impact_score"] == 39
    assert evidence["ranking"]["factors"]["local_utility_impact_boost"] == 39
    assert evidence["ranking"]["factors"]["official_source_boost"] == 12


def test_run_news_scan_ingests_faa_airport_status_fixture(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: faa_airport_status_fixture
                  name: FAA SEA airport status fixture
                  kind: api_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_faa_airport_status_sea.json")}"
                  parser: faa_airport_status_json
                  source_family: faa
                  source_class: official_airport_port
                  adapter: airport_status_json_or_xml
                  verification_status: candidate_needs_verification
                  airport_codes: ["SEA"]
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        row = conn.execute(
            """
            SELECT title, evidence_json
            FROM news_items
            WHERE source_id = (
              SELECT id FROM news_sources WHERE source_key = 'faa_airport_status_fixture'
            )
            """
        ).fetchone()
        source = conn.execute(
            """
            SELECT name, policy_json
            FROM news_sources
            WHERE source_key = 'faa_airport_status_fixture'
            """
        ).fetchone()

    evidence = json_loads(str(row["evidence_json"]), {})
    policy = json_loads(str(source["policy_json"]), {})

    assert result["status"] == "complete"
    assert result["item_count"] == 1
    assert row["title"] == "FAA SEA airport status: Ground Delay"
    assert source["name"] == "FAA SEA airport status fixture"
    assert policy["source_class"] == "official_airport_port"
    assert policy["adapter"] == "airport_status_json_or_xml"
    assert evidence["faa_airport_status"]["ranking"]["airport_impact_score"] == 43
    assert evidence["ranking"]["factors"]["local_airport_port_boost"] == 43
    assert evidence["ranking"]["factors"]["official_source_boost"] == 12


def test_run_news_scan_links_similar_local_items_to_same_event(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: city_light_outage_fixture_a
                  name: City Light outage fixture A
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_city_light_outages.json")}"
                  parser: city_light_outages_json
                  source_family: city_light
                  source_class: official_utility
                  adapter: source_health_probe_only
                - id: city_light_outage_fixture_b
                  name: City Light outage fixture B
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_city_light_outages.json")}"
                  parser: city_light_outages_json
                  source_family: city_light
                  source_class: official_utility
                  adapter: source_health_probe_only
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)

    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        items = conn.execute(
            """
            SELECT id, local_event_id, evidence_json
            FROM news_items
            ORDER BY id
            """
        ).fetchall()
        local_events = conn.execute(
            """
            SELECT
              id, item_ids_json, source_ids_json, source_diversity_score,
              ranking_explanation_json
            FROM local_events
            """
        ).fetchall()

    assert result["status"] == "complete"
    assert len(items) == 2
    assert len(local_events) == 1
    event_ids = {int(row["local_event_id"]) for row in items}
    event_id = int(local_events[0]["id"])
    assert event_ids == {event_id}
    event_row = local_events[0]
    item_ids = json_loads(str(event_row["item_ids_json"]), [])
    source_ids = json_loads(str(event_row["source_ids_json"]), [])
    event_ranking = json_loads(str(event_row["ranking_explanation_json"]), {})
    assert len(item_ids) == 2
    assert len(source_ids) == 2
    assert int(event_row["source_diversity_score"]) == 1
    assert int(event_ranking.get("topic_repetition_score", 0)) > 0
    assert event_ranking.get("topic_repetition_tokens")
    item_evidences = [
        json_loads(str(row["evidence_json"]), {}).get("local_event", {}) for row in items
    ]
    assert any(entry.get("matched") is False for entry in item_evidences)
    assert any(entry.get("matched") is True for entry in item_evidences)
    ranking_factors = [
        json_loads(str(row["evidence_json"]), {}).get("ranking", {}).get("factors", {})
        for row in items
    ]
    assert any(
        int(factors.get("local_source_diversity_score", 0)) == 1 for factors in ranking_factors
    )
    assert any(
        int(factors.get("local_duplicate_family_penalty", 0)) == 0 for factors in ranking_factors
    )
    assert any(
        int(factors.get("local_duplicate_family_penalty", 0)) < 0 for factors in ranking_factors
    )
    assert any(int(factors.get("local_cluster_size_bonus", 0)) > 0 for factors in ranking_factors)


def test_run_news_scan_fails_soft_for_bad_fixture_and_non_file_source(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: good_json
                  name: Good JSON
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_items.json")}"
                - id: bad_rss
                  name: Bad RSS
                  kind: local_file_rss
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "malformed.rss")}"
                - id: blocked_remote
                  name: Blocked remote
                  kind: rss
                  enabled: true
                  url: "https://example.invalid/feed.xml"
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        statuses = conn.execute(
            "SELECT status, error_class FROM news_fetch_runs ORDER BY id"
        ).fetchall()
        health_rows = conn.execute(
            "SELECT state, message FROM news_source_health ORDER BY id"
        ).fetchall()
        item_count = conn.execute("SELECT COUNT(*) AS count FROM news_items").fetchone()["count"]

    assert result["status"] == "partial"
    assert result["healthy_sources"] == 1
    assert len(result["errors"]) == 2
    assert [row["status"] for row in statuses] == ["success", "parser_failed", "policy_blocked"]
    assert [row["state"] for row in health_rows] == ["healthy", "parser_failed", "policy_blocked"]
    assert int(item_count) == 2


def test_run_news_scan_respects_payload_cap_and_retention_purge(tmp_path):
    huge_fixture = tmp_path / "huge.json"
    huge_payload = {
        "items": [
            {
                "title": "x" * 500,
                "url": "https://example.test/a",
                "description": "y" * 2000,
            }
        ]
    }
    huge_fixture.write_text(json.dumps(huge_payload), encoding="utf-8")
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          retention:
            items_days: 7
            fetch_runs_days: 14
            source_health_days: 30
          fetch_policy:
            max_response_bytes: 120
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: huge_json
                  name: Huge JSON
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(huge_fixture)}"
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        source_id = conn.execute(
            "SELECT id FROM news_sources WHERE source_key = 'huge_json'"
        ).fetchone()["id"]
        conn.execute(
            """
            INSERT INTO news_items (
              source_id, scope, canonical_url, url, url_hash, title, description,
              source_published_at, first_seen_at, last_seen_at, expires_at, source_kind,
              tags_json, rank_score, trend_score, evidence_json, content_hash, status
            )
            VALUES (
              ?, 'LOCAL', 'https://expired.example/a', 'https://expired.example/a', 'deadbeef',
              'Expired item', NULL, NULL, '2026-04-01T00:00:00+00:00',
              '2026-04-01T00:00:00+00:00', '2026-04-02T00:00:00+00:00',
              'local_file_json', '[]', 0, 0, '{{}}', 'hash', 'active'
            )
            """,
            (source_id,),
        )
        conn.execute(
            """
            INSERT INTO news_fetch_runs (
              source_id, started_at, finished_at, status, item_count, evidence_json
            )
            VALUES (
              ?, '2026-04-01T00:00:00+00:00', '2026-04-01T00:00:01+00:00',
              'success', 0, '{{}}'
            )
            """,
            (source_id,),
        )
        conn.execute(
            """
            INSERT INTO news_source_health (
              source_id, observed_at, state, last_success_at, last_failure_at,
              consecutive_failures, stale_after, message, evidence_json
            )
            VALUES (?, '2026-04-01T00:00:00+00:00', 'healthy', '2026-04-01T00:00:00+00:00',
                    NULL, 0, NULL, 'old', '{{}}')
            """,
            (source_id,),
        )
        purged = purge_news_retention(conn, config, now="2026-05-11T10:00:00+00:00")
        remaining = conn.execute("SELECT COUNT(*) AS count FROM news_items").fetchone()["count"]

    assert result["status"] == "partial"
    assert result["errors"]
    assert purged == {
        "items": 1,
        "fetch_runs": 1,
        "source_health": 1,
        "local_events": 0,
    }
    assert int(remaining) == 0


def test_parse_fixture_items_bounds_text_lengths():
    source = {"id": "json", "scope": "LOCAL", "kind": "local_file_json"}
    payload = {
        "items": [
            {
                "title": "T" * 600,
                "url": "https://example.test/bounded",
                "description": "D" * 3000,
                "published_at": "Tue, 05 May 2026 18:05:00 GMT",
            }
        ]
    }

    items = parse_fixture_items(source, json.dumps(payload))

    assert len(items[0]["title"]) == 280
    assert len(items[0]["description"]) == 1200
    assert items[0]["source_published_at"] == "2026-05-05T18:05:00+00:00"


def test_cli_news_scan_command_prints_summary(tmp_path, capsys):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: orbital_atom
                  name: Orbital Atom
                  kind: atom
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_feed.atom")}"
        """,
    )

    exit_code = main(["news-scan", "--config", str(config_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "News scan complete" in captured.out
    assert captured.err == ""


def test_cli_news_sources_command_reports_policy_and_health(tmp_path, capsys):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: orbital_atom
                  name: Orbital Atom
                  kind: atom
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_feed.atom")}"
        """,
    )

    assert main(["news-scan", "--config", str(config_path)]) == 0
    exit_code = main(["news-sources", "--config", str(config_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert (
        "ORBITAL orbital_atom enabled=yes kind=atom family=unknown class=unknown "
        "verification=unknown access=unknown"
    ) in captured.out
    assert "policy=allowed_fixture_only" in captured.out
    assert "health=healthy" in captured.out
    assert "items=2" in captured.out
    assert "note=Fixture ingest succeeded" in captured.out
    assert "last_success=" in captured.out
    assert "next_eligible=" in captured.out


def test_news_sources_status_includes_recent_fetch_and_health_history(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: good_json
                  name: Good JSON
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_items.json")}"
                - id: bad_rss
                  name: Bad RSS
                  kind: local_file_rss
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "malformed.rss")}"
        """,
    )

    run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        statuses = {row["source_key"]: row for row in get_news_sources_status(conn, config)}

    assert statuses["good_json"]["recent_fetch_runs"][0]["status"] == "success"
    assert statuses["good_json"]["recent_health_rows"][0]["state"] == "healthy"
    assert statuses["bad_rss"]["recent_fetch_runs"][0]["status"] == "parser_failed"
    assert statuses["bad_rss"]["recent_health_rows"][0]["state"] == "parser_failed"


def test_run_news_scan_records_last_purge_and_last_result(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: local_json
                  name: Local JSON
                  kind: local_file_json
                  enabled: true
                  url: "{_file_url(FIXTURE_DIR / "local_items.json")}"
        """,
    )

    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        rows = conn.execute(
            """
            SELECT key, value
            FROM settings
            WHERE key IN ('news.last_purge', 'news.last_scan_result')
            """
        ).fetchall()
    settings = {str(row["key"]): json_loads(str(row["value"])) for row in rows}

    assert result["status"] == "complete"
    assert settings["news.last_purge"]["summary"] == {
        "items": 0,
        "fetch_runs": 0,
        "source_health": 0,
        "local_events": 0,
    }
    assert settings["news.last_purge"]["before_counts"]["news_items"] == 2
    assert settings["news.last_purge"]["after_counts"]["news_items"] == 2
    assert settings["news.last_purge"]["cutoffs"]["items_before"]
    assert settings["news.last_scan_result"]["status"] == "complete"
    assert settings["news.last_scan_result"]["item_count"] == 2


def test_news_sources_status_derives_policy_and_never_run_states(tmp_path):
    config_path = _write_config(
        tmp_path / "config.yml",
        """
        paths: {repo_roots: [], explicit_repos: []}
        news:
          enabled: true
          scopes:
            LOCAL:
              enabled: true
              sources:
                - id: auth_fixture
                  name: Auth fixture
                  kind: local_file_json
                  enabled: true
                  url: "file:///tmp/auth.json"
                  auth: {token: ""}
                - id: disabled_fixture
                  name: Disabled fixture
                  kind: local_file_json
                  enabled: false
                  url: "file:///tmp/disabled.json"
                  source_family: nws
                  source_class: official_weather_hazard
                  adapter: rss_atom
                  verification_status: candidate_needs_verification
                  official_status: official
                  future_phase: L6
                  expected_access_kind: documented official JSON API
                  policy_risk: low
                  parser_risk: low
                  retention_sensitivity: medium
            REGIONAL:
              enabled: false
              sources:
                - id: disabled_scope_remote
                  name: Disabled scope remote
                  kind: rss
                  enabled: true
                  url: "https://example.invalid/feed.xml"
            ORBITAL:
              enabled: true
              sources:
                - id: waiting_fixture
                  name: Waiting fixture
                  kind: atom
                  enabled: true
                  url: "file:///tmp/waiting.atom"
        """,
    )

    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        init_db(conn)
        statuses = {row["source_key"]: row for row in get_news_sources_status(conn, config)}

    assert statuses["auth_fixture"]["health_state"] == "auth_required"
    assert statuses["disabled_fixture"]["health_state"] == "disabled"
    assert statuses["disabled_scope_remote"]["health_state"] == "policy_blocked"
    assert statuses["waiting_fixture"]["health_state"] == "configured_never_run"
    assert statuses["disabled_fixture"]["source_family"] == "nws"
    assert statuses["disabled_fixture"]["source_class"] == "official_weather_hazard"
    assert statuses["disabled_fixture"]["adapter"] == "rss_atom"
    assert statuses["disabled_fixture"]["verification_status"] == "candidate_needs_verification"
    assert statuses["disabled_fixture"]["official_status"] == "official"
    assert statuses["disabled_fixture"]["future_phase"] == "L6"
    assert statuses["disabled_fixture"]["expected_access_kind"] == "documented official JSON API"
    assert statuses["disabled_fixture"]["policy_risk"] == "low"
    assert statuses["disabled_fixture"]["parser_risk"] == "low"
    assert statuses["disabled_fixture"]["retention_sensitivity"] == "medium"
    assert statuses["disabled_fixture"]["policy"]["local"]["official_status"] == "official"
    assert statuses["disabled_fixture"]["policy"]["local"]["future_phase"] == "L6"
    assert (
        statuses["disabled_fixture"]["policy"]["local"]["expected_access_kind"]
        == "documented official JSON API"
    )
    assert (
        statuses["disabled_fixture"]["policy"]["local"]["verification_status"]
        == "candidate_needs_verification"
    )
