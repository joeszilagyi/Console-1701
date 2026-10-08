from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.ranking import build_rank_result


def test_wsdot_official_rss_preserves_ids_and_strips_embedded_markup() -> None:
    source = {
        "id": "wsdot_highway_alerts_rss",
        "scope": "REGIONAL",
        "kind": "rss",
        "parser": "wsdot_highway_alerts_rss",
        "url": "https://www.wsdot.wa.gov/traffic/api/HighwayAlerts/rss.aspx",
    }
    fixture = (
        Path(__file__).resolve().parent / "fixtures/news/regional_wsdot_highway_alerts.rss"
    ).read_text()
    items = parse_fixture_items(source, fixture)

    assert len(items) == 2
    assert [item["evidence"]["wsdot_alert"]["alert_id"] for item in items] == [
        "718142", "718143"
    ]
    assert items[0]["source_published_at"] == "2026-10-08T14:17:47+00:00"
    assert items[0]["url"].startswith("https://www.wsdot.wa.gov/")
    assert "<" not in items[0]["title"] + (items[0]["description"] or "")
    assert items[0]["evidence"]["wsdot_alert"]["priority"] == "High"
    assert "I-5" in items[0]["evidence"]["wsdot_alert"]["route_tokens"]

    with pytest.raises(NewsParserError, match="invalid identity"):
        parse_fixture_items(source, fixture.replace("refnum=718142", "refnum=999999"))
    with pytest.raises(NewsParserError, match="no alert rows"):
        parse_fixture_items(
            source, '<rss><channel><title>WA State Highway Alerts</title></channel></rss>'
        )


def test_parse_usgs_regional_geojson_filters_and_preserves_seismic_evidence() -> None:
    source = {
        "id": "usgs_eq_geojson",
        "scope": "REGIONAL",
        "kind": "api_json",
        "parser": "usgs_earthquake_geojson",
        "priority": 90,
    }
    fixture = (
        Path(__file__).resolve().parent / "fixtures/news/regional_usgs_earthquakes.json"
    ).read_text()
    items = parse_fixture_items(source, fixture)

    assert len(items) == 2
    puget = next(item for item in items if "Seattle" in item["title"])
    usgs = puget["evidence"]["usgs_earthquake"]
    assert puget["source_published_at"] == "2026-05-05T17:00:00+00:00"
    assert usgs["id"] == "wa-puget-001"
    assert usgs["magnitude"] == 4.6
    assert usgs["depth_km"] == 11.3
    assert usgs["felt"] == 83
    assert usgs["filter"]["min_magnitude"] == 3.0
    assert usgs["ranking"]["regional_seismic_weight"] > 0
    assert "public-impact" in puget["tags"]

    ranking = build_rank_result(
        source,
        puget,
        seen_at="2026-05-05T18:00:00+00:00",
        combined_tags=puget["tags"],
        latest_health_state="healthy",
        repeat_count=0,
    )
    assert ranking["factors"]["regional_seismic_boost"] == usgs["ranking"][
        "regional_seismic_weight"
    ]
    assert ranking["score"] == sum(ranking["factors"].values())

    stricter = parse_fixture_items({**source, "min_magnitude": 4.0}, fixture)
    assert len(stricter) == 1

    non_earthquake = json.loads(fixture)
    blast = json.loads(json.dumps(non_earthquake["features"][0]))
    blast["id"] = "wa-quarry-blast"
    blast["properties"]["type"] = "quarry blast"
    non_earthquake["features"].append(blast)
    assert len(parse_fixture_items(source, json.dumps(non_earthquake))) == 2


def test_usgs_regional_geojson_rejects_invalid_bounds_and_malformed_feed() -> None:
    source = {
        "id": "usgs_eq_geojson",
        "scope": "REGIONAL",
        "kind": "api_json",
        "parser": "usgs_earthquake_geojson",
        "min_latitude": 52,
        "max_latitude": 45,
    }
    with pytest.raises(NewsParserError, match="bounds or magnitude"):
        parse_fixture_items(source, '{"type":"FeatureCollection","features":[]}')
    with pytest.raises(NewsParserError, match="FeatureCollection"):
        parse_fixture_items({**source, "min_latitude": 45, "max_latitude": 50}, "[]")


def test_parse_spd_blotter_rss_feed_adds_preliminary_incident_evidence() -> None:
    source = {
        "id": "spd_blotter_feed",
        "name": "SPD Blotter Feed",
        "scope": "LOCAL",
        "kind": "local_file_rss",
        "parser": "spd_blotter_rss",
        "source_family": "spd",
        "source_class": "official_incident",
    }
    payload = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <rss>
      <channel>
        <item>
          <title>Preliminary Incident Report: Collision on 3rd Ave and Pine</title>
          <link>https://spdblotter.seattle.gov/reports/collision-001</link>
          <description>Police responding to a possible collision and major
          traffic backup.</description>
          <pubDate>2026-06-01T12:00:00Z</pubDate>
          <category>SPD Blotter</category>
        </item>
      </channel>
    </rss>
    """

    items = parse_fixture_items(source, payload)
    assert len(items) == 1
    evidence = items[0]["evidence"]
    assert "spd_blotter" in evidence
    spd = evidence["spd_blotter"]
    assert isinstance(spd, dict)
    assert spd["incident_type"] == "traffic_incident"
    assert spd["preliminary_report"] is True
    assert int(spd["ranking"]["incident_score"]) > 0
    assert items[0]["tags"]
    ranking = build_rank_result(
        source,
        items[0],
        seen_at=datetime.now(UTC).isoformat(),
        combined_tags=items[0]["tags"],
        latest_health_state="healthy",
        repeat_count=0,
    )
    assert int(ranking["factors"]["local_public_impact_boost"]) > 0


def test_parse_spd_blotter_rss_feed_marks_private_medical_calls_as_low_acuity() -> None:
    source = {
        "id": "spd_blotter_feed",
        "name": "SPD Blotter Feed",
        "scope": "LOCAL",
        "kind": "local_file_rss",
        "parser": "spd_blotter_rss",
        "source_family": "spd",
        "source_class": "official_incident",
    }
    payload = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <rss>
      <channel>
        <item>
          <title>Preliminary Incident Report: Medical aid call in Ballard</title>
          <link>https://spdblotter.seattle.gov/reports/medical-011</link>
          <description>Overdose response requested by 1825 4th Ave.</description>
          <pubDate>2026-06-01T12:00:00Z</pubDate>
          <category>SPD Blotter</category>
        </item>
      </channel>
    </rss>
    """

    items = parse_fixture_items(source, payload)
    assert len(items) == 1
    evidence = items[0]["evidence"]
    assert evidence["privacy"]["low_acuity_private"] is True
    assert evidence["privacy"]["exact_location_suppressed"] is True
    assert evidence["privacy"]["public_impact_justified"] is False
    assert evidence["privacy"]["overdose_related"] is True
    assert evidence["privacy"]["privacy_category"] == "overdose"
    assert "privacy-redacted" in items[0]["tags"]
    spd = evidence["spd_blotter"]
    assert isinstance(spd, dict)
    assert spd["privacy"]["public_impact_justified"] is False
    assert spd["privacy"]["overdose_related"] is True
    assert spd["privacy"]["privacy_category"] == "overdose"
    assert int(spd["ranking"]["incident_score"]) <= 10
    ranking = build_rank_result(
        source,
        items[0],
        seen_at=datetime.now(UTC).isoformat(),
        combined_tags=items[0]["tags"],
        latest_health_state="healthy",
        repeat_count=0,
    )
    assert ranking["factors"]["local_privacy_penalty"] == -40


def test_parse_sdot_blog_rss_feed_prioritizes_transport_disruption() -> None:
    source = {
        "id": "sdot_blog_feed",
        "name": "SDOT Blog Feed",
        "scope": "LOCAL",
        "kind": "local_file_rss",
        "parser": "sdot_blog_feed",
        "source_family": "sdot",
        "source_class": "official_transport",
    }
    payload = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <rss>
      <channel>
        <item>
          <title>Bridge closure announcement: I-5 lanes reduced</title>
          <link>https://sdot.blog/local/bridge-closure</link>
          <description>Traffic delays and detours while crews investigate water
          main issues.</description>
          <pubDate>2026-06-01T12:10:00Z</pubDate>
          <category>Seattle</category>
        </item>
      </channel>
    </rss>
    """

    items = parse_fixture_items(source, payload)
    assert len(items) == 1
    evidence = items[0]["evidence"]
    assert "sdot_blog" in evidence
    sdot = evidence["sdot_blog"]
    assert isinstance(sdot, dict)
    assert sdot["incident_type"] in {
        "traffic_disruption",
        "transit_disruption",
        "traffic_collision",
    }
    assert int(sdot["ranking"]["traffic_impact_score"]) >= 24
    ranking = build_rank_result(
        source,
        items[0],
        seen_at=datetime.now(UTC).isoformat(),
        combined_tags=items[0]["tags"],
        latest_health_state="healthy",
        repeat_count=0,
    )
    assert int(ranking["factors"]["local_transit_impact_boost"]) > 0


def test_parse_local_news_rss_feed_includes_generic_local_news_signal() -> None:
    source = {
        "id": "local_news_feed",
        "name": "Local News Feed",
        "scope": "LOCAL",
        "kind": "local_file_rss",
        "parser": "local_news_rss",
        "source_family": "local_news",
        "source_class": "local_news",
    }
    payload = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <rss>
      <channel>
        <item>
          <title>Neighborhood meeting announced near downtown</title>
          <link>https://citynews.local/story/42</link>
          <description>Community meeting discussing park improvements.</description>
          <pubDate>2026-06-01T12:20:00Z</pubDate>
          <category>Community</category>
        </item>
      </channel>
    </rss>
    """

    items = parse_fixture_items(source, payload)
    assert len(items) == 1
    evidence = items[0]["evidence"]
    assert "local_news" in evidence
    local_news = evidence["local_news"]
    assert isinstance(local_news, dict)
    assert local_news["news_type"] == "local_news"


def test_parse_local_news_rss_feed_tracks_routes_and_service_areas() -> None:
    source = {
        "id": "local_news_feed",
        "name": "Local News Feed",
        "scope": "LOCAL",
        "kind": "local_file_rss",
        "parser": "local_news_rss",
        "source_family": "local_news",
        "source_class": "local_news",
        "service_area_keywords": ["Downtown", "West Seattle", "Capitol Hill"],
    }
    payload = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <rss>
      <channel>
        <item>
          <title>Downtown road lane closure on I-5 near West Seattle bridge</title>
          <link>https://citynews.local/story/bridge-closure</link>
          <description>Emergency response and traffic detours are in effect.</description>
          <pubDate>2026-06-01T13:00:00Z</pubDate>
          <category>Traffic</category>
        </item>
      </channel>
    </rss>
    """

    items = parse_fixture_items(source, payload)
    assert len(items) == 1
    evidence = items[0]["evidence"]
    assert "local_news" in evidence
    local_news = evidence["local_news"]
    assert isinstance(local_news, dict)
    assert local_news["traffic_related"] is True
    route_tokens = local_news["route_tokens"]
    assert "I-5" in route_tokens
    assert any(area in local_news["service_areas"] for area in {"Downtown", "West Seattle"})
    assert int(local_news["ranking"]["local_news_score"]) > 12


def test_parse_sdot_blog_rankings_are_route_and_area_aware() -> None:
    source = {
        "id": "sdot_blog_feed",
        "name": "SDOT Blog Feed",
        "scope": "LOCAL",
        "kind": "local_file_rss",
        "parser": "sdot_blog_feed",
        "source_family": "sdot",
        "source_class": "official_transport",
    }
    payload = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <rss>
      <channel>
        <item>
          <title>Transit updates: Route 7 detour around I-5 closure</title>
          <link>https://sdot.blog/local/route7-detour</link>
          <description>Transit disruption reported near downtown with alternate
          route guidance.</description>
          <pubDate>2026-06-01T13:20:00Z</pubDate>
          <category>Transit</category>
        </item>
      </channel>
    </rss>
    """

    items = parse_fixture_items(source, payload)
    assert len(items) == 1
    evidence = items[0]["evidence"]
    sdot = evidence["sdot_blog"]
    assert int(sdot["route_count"]) >= 1
    assert int(sdot["ranking"]["traffic_impact_score"]) >= 30
    ranking = build_rank_result(
        source,
        items[0],
        seen_at=datetime.now(UTC).isoformat(),
        combined_tags=items[0]["tags"],
        latest_health_state="healthy",
        repeat_count=0,
    )
    assert int(ranking["factors"]["local_transit_impact_boost"]) > 0
