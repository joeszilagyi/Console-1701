from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.ranking import build_rank_result


def test_national_nhtsa_recall_fixture_groups_campaign_and_preserves_safety_evidence() -> None:
    source = {
        "id": "nhtsa_recalls", "scope": "NATIONAL", "kind": "api_json",
        "parser": "nhtsa_recalls_json", "source_family": "nhtsa",
    }
    fixture = (
        Path(__file__).resolve().parent / "fixtures/news/national_nhtsa_recalls.json"
    ).read_text()
    items = parse_fixture_items(source, fixture)
    assert len(items) == 2
    first = items[0]
    evidence = first["evidence"]["nhtsa_recall"]
    assert evidence["campaign_number"] == "26V123000"
    assert evidence["vehicles"] == [
        {"model_year": "2025", "make": "EXAMPLE", "model": "SEDAN"},
        {"model_year": "2026", "make": "EXAMPLE", "model": "WAGON"},
    ]
    assert first["url"] == "https://api.nhtsa.gov/recalls/campaignNumber?campaignNumber=26V123000"
    assert first["source_published_at"] == "2026-10-14T00:00:00+00:00"
    assert evidence["date_precision"] == "day"
    assert evidence["potential_units_affected"] == 120000
    assert evidence["park_it"] is True and evidence["park_outside"] is True
    assert evidence["ranking"]["vehicle_safety_score"] == 35
    assert evidence["body_stored"] is False
    assert items[1]["evidence"]["nhtsa_recall"]["potential_units_affected"] is None
    assert items[1]["evidence"]["nhtsa_recall"]["ranking"]["vehicle_safety_score"] == 0

    high_rank = build_rank_result(source, first, seen_at="2026-10-15T00:00:00+00:00",
                                  combined_tags=first["tags"], latest_health_state="healthy",
                                  repeat_count=0)
    low_rank = build_rank_result(source, items[1], seen_at="2026-10-15T00:00:00+00:00",
                                 combined_tags=items[1]["tags"], latest_health_state="healthy",
                                 repeat_count=0)
    assert high_rank["factors"]["national_vehicle_safety_bonus"] == 35
    assert low_rank["factors"]["national_vehicle_safety_bonus"] == 0

    malformed = json.loads(fixture)
    malformed["Count"] = 2
    with pytest.raises(NewsParserError, match="matching Count"):
        parse_fixture_items(source, json.dumps(malformed))
    malformed["Count"] = 3
    malformed["results"][1]["Component"] = "BRAKES"
    with pytest.raises(NewsParserError, match="conflicting rows"):
        parse_fixture_items(source, json.dumps(malformed))
    assert parse_fixture_items(source, '{"Count": 0, "results": []}') == []
    with pytest.raises(NewsParserError, match="NATIONAL scope"):
        parse_fixture_items({**source, "scope": "LOCAL"}, fixture)


def test_regional_nws_fixture_preserves_official_county_zone_and_alert_evidence() -> None:
    source = {
        "id": "nws_active_alerts_wa", "scope": "REGIONAL", "kind": "api_json",
        "parser": "nws_alerts_json",
    }
    fixture = (
        Path(__file__).resolve().parent / "fixtures/news/regional_nws_alerts.json"
    ).read_text()
    items = parse_fixture_items(source, fixture)

    assert [item["evidence"]["nws_alert"]["id"] for item in items] == [
        "regional-king-flood", "regional-spokane-wind"
    ]
    king = items[0]["evidence"]["nws_alert"]
    assert king["county_codes"] == ["053033"]
    assert king["county_area_labels"] == ["King County"]
    assert king["affected_states"] == ["WA"]
    assert king["affected_zones"] == ["https://api.weather.gov/zones/forecast/WAZ558"]
    assert king["effective"] == "2026-10-15T11:00:00+00:00"
    assert king["expires"] == "2026-10-16T11:00:00+00:00"
    assert king["instruction_url"] == "https://www.weather.gov/sew/"
    assert king["ranking"]["total_alert_weight"] > 0

    county_items = parse_fixture_items({**source, "county_codes": ["053033"]}, fixture)
    assert [item["title"] for item in county_items] == ["Flood Warning for King County"]
    zone_items = parse_fixture_items({**source, "zone_ids": ["WAZ036"]}, fixture)
    assert [item["title"] for item in zone_items] == ["Wind Advisory for Spokane County"]
    out_of_region = parse_fixture_items({**source, "county_keywords": ["Oregon"]}, fixture)
    assert out_of_region == []

    same_only = json.loads(fixture)
    same_only["features"] = [dict(same_only["features"][0])]
    same_only["features"][0]["properties"] = dict(same_only["features"][0]["properties"])
    same_only["features"][0]["properties"]["affectedZones"] = []
    same_only["features"][0]["properties"]["geocode"] = {"SAME": ["053033"]}
    county_item = parse_fixture_items(source, json.dumps(same_only))[0]["evidence"]["nws_alert"]
    assert county_item["affected_states"] == ["WA"]
    assert county_item["geography_basis"] == "official_same_county_codes"


def test_national_nws_fixture_preserves_territory_and_official_instructions() -> None:
    source = {
        "id": "nws_active_alerts_api",
        "scope": "NATIONAL",
        "kind": "api_json",
        "parser": "nws_alerts_json",
    }
    fixture = (
        Path(__file__).resolve().parent / "fixtures/news/national_nws_alerts.json"
    ).read_text()
    items = parse_fixture_items(source, fixture)

    assert len(items) == 2
    flood = items[0]["evidence"]["nws_alert"]
    wind = items[1]["evidence"]["nws_alert"]
    assert flood["id"] == "national-wa-flood"
    assert flood["affected_states"] == ["WA"]
    assert flood["geography_basis"] == "official_ugc_zone_ids"
    assert flood["effective"] == "2026-10-15T13:00:00+00:00"
    assert flood["expires"] == "2026-10-16T13:00:00+00:00"
    assert flood["severity"] == "Severe"
    assert flood["urgency"] == "Immediate"
    assert flood["certainty"] == "Observed"
    assert flood["instruction"] == "Move to higher ground."
    assert flood["instruction_url"] == "https://www.weather.gov/sew/"
    assert flood["source_url"] == items[0]["url"]
    assert flood["ranking"]["total_alert_weight"] > wind["ranking"][
        "total_alert_weight"
    ]
    assert wind["affected_states"] == ["PR"]
    assert wind["instruction_url"] is None


def test_national_usgs_fixture_filters_geography_and_magnitude() -> None:
    source = {
        "id": "usgs_national_fixture",
        "scope": "NATIONAL",
        "kind": "api_json",
        "parser": "usgs_earthquake_geojson",
    }
    fixture = (
        Path(__file__).resolve().parent / "fixtures/news/national_usgs_earthquakes.json"
    ).read_text()
    items = parse_fixture_items(source, fixture)

    assert [item["evidence"]["usgs_earthquake"]["id"] for item in items] == [
        "national-ca-001", "national-ak-002", "national-pr-003"
    ]
    assert [item["evidence"]["usgs_earthquake"]["filter"]["region"] for item in items] == [
        "contiguous_us", "alaska", "puerto_rico_usvi"
    ]
    assert all(item["evidence"]["usgs_earthquake"]["filter"]["min_magnitude"] == 5.0
               for item in items)
    assert all(item["evidence"]["usgs_earthquake"]["filter"]["geography_basis"]
               == "coarse_us_region_coordinates" for item in items)
    assert items[0]["evidence"]["usgs_earthquake"]["felt"] == 247
    assert items[0]["evidence"]["usgs_earthquake"]["depth_km"] == 12.7
    assert all("national" in item["tags"] for item in items)

    stricter = parse_fixture_items({**source, "min_magnitude": 5.5}, fixture)
    assert len(stricter) == 1
    with pytest.raises(NewsParserError, match="finite nonnegative"):
        parse_fixture_items({**source, "min_magnitude": float("nan")}, fixture)


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


def test_wsdot_documented_json_shape_preserves_corridor_and_status_evidence() -> None:
    source = {
        "id": "wsdot_traveler_api", "scope": "REGIONAL", "kind": "api_json",
        "parser": "wsdot_travel_alerts_json",
        "url": "https://wsdot.wa.gov/traffic/api/",
    }
    fixture = (
        Path(__file__).resolve().parent / "fixtures/news/regional_wsdot_traveler_alerts.json"
    ).read_text()
    items = parse_fixture_items(source, fixture)

    assert len(items) == 3
    pass_alert = items[0]["evidence"]["wsdot_alert"]
    assert pass_alert["alert_id"] == "81001"
    assert pass_alert["route_tokens"] == ["I-90"]
    assert pass_alert["impact"] == "closure"
    assert pass_alert["event_category"] == "Closure"
    assert pass_alert["event_status"] == "Open"
    assert pass_alert["start_roadway_location"]["direction"] == "Eastbound"
    assert pass_alert["start_roadway_location"]["milepost"] == 52.0
    assert pass_alert["end_roadway_location"]["milepost"] == 60.0
    assert pass_alert["start_time"] == "2026-10-15T10:00:00+00:00"
    assert pass_alert["end_time"] == "2026-10-16T00:00:00+00:00"
    assert items[0]["source_published_at"] == "2026-10-15T11:00:00+00:00"
    assert items[0]["url"].endswith("refnum=81001")
    assert pass_alert["source_url_basis"] == "official_rss_refnum_link"
    assert pass_alert["ranking"]["public_impact_score"] > 30

    border = items[1]["evidence"]["wsdot_alert"]
    assert border["start_roadway_location"]["direction"] == "Northbound"
    assert border["county"] == "Whatcom"
    closed = items[2]["evidence"]["wsdot_alert"]
    assert closed["event_status"] == "Closed"
    assert closed["impact"] == "resolved"
    assert closed["ranking"]["public_impact_score"] == 0

    duplicate = json.loads(fixture)
    duplicate[1]["AlertID"] = duplicate[0]["AlertID"]
    with pytest.raises(NewsParserError, match="duplicates alert ID"):
        parse_fixture_items(source, json.dumps(duplicate))
    malformed_time = json.loads(fixture)
    malformed_time[0]["LastUpdatedTime"] = "/Date(invalid)/"
    with pytest.raises(NewsParserError, match="timestamp"):
        parse_fixture_items(source, json.dumps(malformed_time))
    markup = json.loads(fixture)
    markup[0]["HeadlineDescription"] = "<b>I-90</b> eastbound closed"
    assert parse_fixture_items(source, json.dumps(markup))[0]["title"] == "I-90 eastbound closed"
    assert parse_fixture_items(source, '{"alerts": []}') == []


def test_king_county_emergency_rss_separates_alerts_recovery_and_tests() -> None:
    source = {
        "id": "king_county_emergency_news", "scope": "REGIONAL", "kind": "rss",
        "parser": "king_county_emergency_rss", "source_family": "county_emergency",
    }
    fixture = (
        Path(__file__).resolve().parent / "fixtures/news/regional_king_county_emergency.rss"
    ).read_text()
    items = parse_fixture_items(source, fixture)

    assert len(items) == 3
    assert [item["evidence"]["king_county_emergency"]["classification"] for item in items] == [
        "emergency_alert", "recovery", "test"
    ]
    alert = items[0]
    assert alert["source_published_at"] == "2026-10-15T10:00:00+00:00"
    assert alert["description"] == (
        "Residents in the posted zone should follow official evacuation directions."
    )
    assert "<p>" not in alert["description"]
    assert alert["evidence"]["king_county_emergency"]["county"] == "King County"
    assert alert["evidence"]["king_county_emergency"]["geography_basis"] == (
        "publisher_jurisdiction_only"
    )
    assert alert["evidence"]["king_county_emergency"]["body_stored"] is False
    assert "public-impact" in alert["tags"]
    assert items[2]["evidence"]["king_county_emergency"]["ranking"]["public_impact_score"] == 0
    assert "public-impact" not in items[2]["tags"]

    ranking = build_rank_result(
        source, alert, seen_at="2026-10-15T11:00:00+00:00",
        combined_tags=alert["tags"], latest_health_state="healthy", repeat_count=0,
    )
    assert ranking["factors"]["regional_public_impact_bonus"] == 25
    with pytest.raises(NewsParserError, match="unexpected channel"):
        parse_fixture_items(source, fixture.replace("King County Emergency News", "Other News"))
    with pytest.raises(NewsParserError, match="official URL"):
        parse_fixture_items(
            source,
            fixture.replace("kcemergency.com/2026/10/15", "example.com/2026/10/15"),
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

    nearby = parse_fixture_items({
        **source, "center_latitude": 47.6, "center_longitude": -122.4,
        "radius_km": 100,
    }, fixture)
    assert [item["evidence"]["usgs_earthquake"]["id"] for item in nearby] == [
        "wa-puget-001"
    ]
    radius_filter = nearby[0]["evidence"]["usgs_earthquake"]["filter"]
    assert radius_filter["geography_basis"] == "configured_radius_and_bounds"
    assert 0 < radius_filter["distance_km"] < 100
    with pytest.raises(NewsParserError, match="requires center"):
        parse_fixture_items({**source, "radius_km": 100}, fixture)
    with pytest.raises(NewsParserError, match="radius center"):
        parse_fixture_items({
            **source, "center_latitude": 47.6, "center_longitude": -122.4,
            "radius_km": -1,
        }, fixture)

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
          <title>Preliminary Incident Report: Medical aid call at 1825 4th Ave in Ballard</title>
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
    assert "1825" not in json.dumps(items[0], sort_keys=True)
    assert items[0]["title"] == "SPD incident report near Ballard"
    assert "narrative are withheld" in items[0]["description"]
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


def test_parse_spd_minor_report_redacts_private_address_without_medical_terms() -> None:
    source = {
        "id": "spd_blotter_feed", "name": "SPD Blotter Feed", "scope": "LOCAL",
        "kind": "local_file_rss", "parser": "spd_blotter_rss", "source_family": "spd",
    }
    payload = """<rss><channel><item>
      <title>Incident update at 712 Example St in Ballard</title>
      <link>https://spdblotter.seattle.gov/reports/minor-012</link>
      <description>Officers responded to a private residence at 712 Example St.</description>
      <pubDate>2026-06-01T12:00:00Z</pubDate>
    </item></channel></rss>"""

    item = parse_fixture_items(source, payload)[0]
    privacy = item["evidence"]["privacy"]
    assert privacy["privacy_category"] == "minor_police"
    assert privacy["low_public_value_private"] is True
    assert privacy["exact_location_suppressed"] is True
    assert "712" not in json.dumps(item, sort_keys=True)
    ranking = build_rank_result(
        source, item, seen_at="2026-06-01T12:00:00+00:00",
        combined_tags=item["tags"], latest_health_state="healthy", repeat_count=0,
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
