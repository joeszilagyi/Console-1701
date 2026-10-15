from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import parse_fixture_items
from console1701.news.regional_contract import build_regional_event_contract
from console1701.news.regional_events import correlate_regional_items
from console1701.news.regional_registry import regional_registry_config_defaults
from console1701.news.scanner import purge_news_retention, run_news_scan
from console1701.news.storage import get_news_scope_view, list_regional_items_by_facet

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "news"


def _correlation_item(
    item_id: int, *, family: str, title: str, route: str = "I-5",
    event_type: str = "traveler_alert", published: str = "2026-10-15T10:00:00+00:00",
    official: bool = True,
) -> dict:
    return {
        "id": item_id, "scope": "REGIONAL", "title": title,
        "source_published_at": published,
        "evidence": {
            "source": {"source_key": f"source-{item_id}", "source_family": family,
                       "official_status": "official" if official else "unverified"},
            "regional_event": {
                "event_key": f"event-{item_id}", "event_type": event_type,
                "confidence": "high" if official else "low",
                "geography": {"matched": True, "routes": [route]},
            },
        },
    }


def test_regional_correlation_requires_independent_verified_context_and_time():
    title = "I-5 northbound closure near Tacoma after landslide"
    first = _correlation_item(1, family="wsdot", title=title)
    second = _correlation_item(2, family="county", title="Tacoma I-5 northbound landslide closure")
    groups = correlate_regional_items([first, second])
    assert len(groups) == 1
    assert groups[0]["corroborated"] is True
    assert "route" in groups[0]["matches"][0]["basis"]
    for change in (
        {"route": "SR-7"}, {"event_type": "weather_alert"},
        {"published": "2026-10-18T10:00:00+00:00"},
        {"official": False}, {"family": "wsdot"},
        {"title": "Unrelated traffic notice"},
    ):
        altered = _correlation_item(
            2, family=change.get("family", "county"), title=change.get("title", second["title"]),
            route=change.get("route", "I-5"),
            event_type=change.get("event_type", "traveler_alert"),
            published=change.get("published", "2026-10-15T10:00:00+00:00"),
            official=change.get("official", True),
        )
        assert len(correlate_regional_items([first, altered])) == 2


def test_regional_correlation_does_not_bridge_distinct_incidents():
    first = _correlation_item(1, family="wsdot", title="I-5 northbound Tacoma landslide closure")
    middle = _correlation_item(2, family="county", title="I-5 Tacoma landslide closure")
    last = _correlation_item(3, family="state", title="I-5 Tacoma landslide closure",
                             route="SR-7")
    groups = correlate_regional_items([first, middle, last])
    assert sorted(len(group["item_ids"]) for group in groups) == [1, 2]


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


def test_regional_scan_correlates_distinct_official_family_reports(tmp_path):
    payload = json.loads((FIXTURES / "local_wsdot_alerts.json").read_text())
    second = json.loads(json.dumps(payload))
    second["alerts"] = [second["alerts"][0]]
    second["alerts"][0]["AlertID"] = 2001
    second["alerts"][0]["Url"] = "https://wsdot.example.test/travel/alerts/2001"
    second_path = tmp_path / "second.json"
    second_path.write_text(json.dumps(second), encoding="utf-8")
    config_path = tmp_path / "regional.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - id: wsdot_traveler_api
                  enabled: true
                  url: "{_file_url('local_wsdot_alerts.json')}"
                - id: county_travel_fixture
                  name: County travel fixture
                  kind: api_json
                  parser: wsdot_travel_alerts_json
                  source_family: county_transport
                  source_class: official_transport
                  official_status: official
                  enabled: true
                  url: "{second_path.as_uri()}"
    """).strip() + "\n", encoding="utf-8")
    result = run_news_scan(config_path)
    assert result["item_count"] == 3, result
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        scope = get_news_scope_view(conn, config, "REGIONAL", cluster_limit=10)
    correlated = [cluster for cluster in scope["clusters"] if cluster["item_count"] == 2]
    assert len(correlated) == 1
    assert correlated[0]["evidence"]["corroborated"] is True
    assert "independent_family" in correlated[0]["evidence"]["correlation"]["matches"][0][
        "basis"
    ]


def test_regional_geography_facets_are_official_scoped_and_expire(tmp_path):
    config_path = tmp_path / "facets.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        regional: {{enabled: true}}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - id: wsdot_traveler_api
                  enabled: true
                  url: "{_file_url('local_wsdot_alerts.json')}"
                - id: usgs_eq_geojson
                  enabled: true
                  url: "{_file_url('regional_usgs_earthquakes.json')}"
    """).strip() + "\n", encoding="utf-8")
    assert run_news_scan(config_path)["item_count"] == 4
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        king = list_regional_items_by_facet(conn, "county", "KING COUNTY")
        route = list_regional_items_by_facet(conn, "route", "i-5")
        seismic = list_regional_items_by_facet(conn, "event_type", "earthquake")
        assert len(king) == 1
        assert len(route) == 1
        assert king[0]["id"] == route[0]["id"]
        assert len(seismic) == 2
        assert list_regional_items_by_facet(conn, "county", "Seattle") == []
        plan = conn.execute("""
            EXPLAIN QUERY PLAN
            SELECT item_id FROM news_item_facets
            WHERE scope = 'REGIONAL' AND facet_kind = 'route' AND facet_value = 'i-5'
        """).fetchall()
        assert any("idx_news_item_facets_lookup" in row["detail"] for row in plan)
        cluster_plan = conn.execute("""
            EXPLAIN QUERY PLAN
            SELECT id FROM news_clusters
            WHERE scope = 'REGIONAL'
            ORDER BY score DESC, last_seen_at DESC LIMIT 10
        """).fetchall()
        assert any("idx_news_clusters_scope_score" in row["detail"] for row in cluster_plan)
        with pytest.raises(ValueError, match="Unsupported REGIONAL facet"):
            list_regional_items_by_facet(conn, "headline", "Seattle")
        conn.execute(
            "UPDATE news_items SET expires_at = '2026-01-01T00:00:00+00:00' WHERE id = ?",
            (route[0]["id"],),
        )
        purged = purge_news_retention(conn, config, now="2026-10-15T12:00:00+00:00")
        assert purged["items"] == 1
        remaining_facets = conn.execute(
            "SELECT COUNT(*) FROM news_item_facets WHERE item_id = ?", (route[0]["id"],)
        ).fetchone()[0]
        assert remaining_facets == 0
