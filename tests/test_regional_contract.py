from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import parse_fixture_items
from console1701.news.regional_contract import build_regional_event_contract
from console1701.news.regional_registry import regional_registry_config_defaults
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_scope_view

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "news"


def _file_url(name: str) -> str:
    return f"file://{(FIXTURES / name).resolve()}"


def test_regional_contract_uses_official_ids_and_isolates_headlines():
    usgs = regional_registry_config_defaults("usgs_eq_geojson")
    nws = regional_registry_config_defaults("nws_active_alerts_wa")
    wsdot = regional_registry_config_defaults("wsdot_traveler_api")
    news = regional_registry_config_defaults("regional_news_rss")

    earthquake = parse_fixture_items(
        usgs, (FIXTURES / "regional_usgs_earthquakes.json").read_text()
    )[0]
    alert = parse_fixture_items(nws, (FIXTURES / "local_nws_alerts.json").read_text())[0]
    travel = parse_fixture_items(wsdot, (FIXTURES / "local_wsdot_alerts.json").read_text())[0]
    headlines = parse_fixture_items(news, (FIXTURES / "local_feed.rss").read_text())

    seismic = build_regional_event_contract(usgs, earthquake, hashed_url="a" * 64)
    weather = build_regional_event_contract(nws, alert, hashed_url="b" * 64)
    transport = build_regional_event_contract(wsdot, travel, hashed_url="c" * 64)
    isolated = [
        build_regional_event_contract(news, item, hashed_url=str(index) * 64)
        for index, item in enumerate(headlines, 1)
    ]

    assert seismic["event_type"] == "earthquake"
    assert seismic["matching_basis"] == "official_usgs_event_id"
    assert seismic["geography"]["basis"] == "official_point_with_configured_bounds"
    assert seismic["geography"]["matched"] is True
    assert weather["event_type"] == "weather_alert"
    assert "WAZ558" in weather["geography"]["zone_ids"]
    assert transport["event_type"] == "traveler_alert"
    assert transport["geography"]["routes"] == ["I-5"]
    assert all(event["confidence"] == "low" for event in isolated)
    assert isolated[0]["event_key"] != isolated[1]["event_key"]
    assert len({seismic["event_key"], weather["event_key"], transport["event_key"]}) == 3


def test_regional_nws_parser_excludes_alert_without_washington_zone_evidence():
    source = regional_registry_config_defaults("nws_active_alerts_wa")
    payload = json.loads((FIXTURES / "local_nws_alerts.json").read_text())
    outside = json.loads(json.dumps(payload["features"][1]))
    outside["id"] = "https://api.weather.gov/alerts/oregon-frost"
    outside["properties"]["@id"] = outside["id"]
    outside["properties"]["id"] = "oregon-frost"
    outside["properties"]["areaDesc"] = "Portland, Oregon"
    outside["properties"]["affectedZones"] = ["https://api.weather.gov/zones/forecast/ORZ006"]
    payload["features"].append(outside)

    items = parse_fixture_items(source, json.dumps(payload))

    assert len(items) == 2
    assert all("Oregon" not in item["title"] for item in items)


def test_regional_cluster_converges_same_official_event_without_family_inflation(tmp_path):
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        dedent(
            f"""
            paths: {{repo_roots: [], explicit_repos: []}}
            news:
              enabled: true
              scopes:
                REGIONAL:
                  enabled: true
                  sources:
                    - id: usgs_eq_geojson
                      enabled: true
                      url: "{_file_url('regional_usgs_earthquakes.json')}"
                    - id: secondary_usgs_fixture
                      name: Secondary USGS fixture path
                      kind: api_json
                      parser: usgs_earthquake_geojson
                      source_family: usgs
                      source_class: official_seismic_volcano
                      official_status: official
                      enabled: true
                      url: "{_file_url('regional_usgs_earthquakes.json')}"
            """
        ).strip() + "\n",
        encoding="utf-8",
    )
    first = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        scope = get_news_scope_view(conn, config, "REGIONAL", item_limit=10, cluster_limit=10)
        rows = conn.execute("SELECT evidence_json FROM news_items ORDER BY id").fetchall()
    item_evidence = [json_loads(row["evidence_json"], {}) for row in rows]

    assert first["status"] == "complete"
    assert first["item_count"] == 4
    assert len(scope["clusters"]) == 2
    assert all(cluster["item_count"] == 2 for cluster in scope["clusters"])
    assert all(cluster["evidence"]["family_count"] == 1 for cluster in scope["clusters"])
    assert all(cluster["evidence"]["corroborated"] is False for cluster in scope["clusters"])
    assert all(
        cluster["evidence"]["event"]["confidence"] == "high"
        for cluster in scope["clusters"]
    )
    assert all(evidence["ranking"]["score"] == sum(
        evidence["ranking"]["factors"].values()) for evidence in item_evidence)
    assert all(evidence["ranking"]["factors"]["regional_duplicate_family_penalty"] == -2
               for evidence in item_evidence)
    assert all(evidence["ranking"]["factors"]["regional_source_diversity_bonus"] == 0
               for evidence in item_evidence)
    assert all("local_public_impact_boost" not in evidence["ranking"]["factors"]
               for evidence in item_evidence)

    second = run_news_scan(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows_after = conn.execute("SELECT evidence_json FROM news_items ORDER BY id").fetchall()
    assert second["status"] == "complete"
    assert all(
        json_loads(row["evidence_json"], {})["ranking"]["factors"][
            "regional_duplicate_family_penalty"
        ] == -2 for row in rows_after
    )
