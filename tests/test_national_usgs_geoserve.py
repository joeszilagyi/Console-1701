from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from console1701.config import ConfigError, load_config
from console1701.db import connect_db, json_loads
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/news"
ADMIN = json.loads((FIXTURES / "national_usgs_geoserve_admin.json").read_text())


def _earthquakes() -> str:
    template = json.loads((FIXTURES / "national_usgs_earthquakes.json").read_text())
    first = template["features"][0]
    features = []
    for event_id, longitude, latitude, place in (
        ("border-wa", -122.3, 48.5, "Near the border"),
        ("border-bc", -122.9, 49.25, "Near the border"),
        ("border-mx", -110.95, 31.2, "Near the border"),
        ("border-sea", -123.0, 49.0, "Near the border"),
        ("border-pr", -66.3, 18.2, "Near Puerto Rico"),
    ):
        feature = deepcopy(first)
        feature["id"] = event_id
        feature["properties"]["place"] = place
        feature["properties"]["url"] = (
            f"https://earthquake.usgs.gov/earthquakes/eventpage/{event_id}"
        )
        feature["geometry"]["coordinates"] = [longitude, latitude, 12.7]
        features.append(feature)
    template["features"] = features
    return json.dumps(template)


def _source(fixture: Path, admin: dict | None = None) -> dict:
    return {
        "id": "usgs_eq_geojson", "scope": "NATIONAL", "kind": "api_json",
        "parser": "usgs_earthquake_geojson", "url": fixture.resolve().as_uri(),
        "min_magnitude": 5.0, "geoserve_admin_fixture": ADMIN if admin is None else admin,
    }


def test_geoserve_sidecar_excludes_foreign_land_but_not_unknown_offshore(tmp_path):
    fixture = tmp_path / "earthquakes.json"
    fixture.write_text(_earthquakes())
    items = parse_fixture_items(_source(fixture), fixture.read_text())
    by_id = {item["evidence"]["usgs_earthquake"]["id"]: item for item in items}
    assert set(by_id) == {"border-wa", "border-sea", "border-pr"}
    assert by_id["border-wa"]["evidence"]["usgs_earthquake"]["filter"][
        "geography_basis"
    ] == "usgs_geoserve_admin_fixture"
    assert by_id["border-wa"]["evidence"]["usgs_earthquake"]["filter"][
        "geoserve_admin"
    ]["region"] == "Washington"
    assert by_id["border-pr"]["evidence"]["usgs_earthquake"]["filter"][
        "geoserve_admin"
    ]["iso"] == "PRI"
    assert by_id["border-sea"]["evidence"]["usgs_earthquake"]["filter"][
        "geoserve_admin"
    ]["status"] == "no_admin_polygon"
    assert all(item["evidence"]["national_identity"]["multi_state_impact"] is False
               for item in items)
    assert all(item["evidence"]["national_identity"].get("affected_states") is None
               for item in items)


def test_geoserve_sidecar_rejects_wrong_point_and_live_use(tmp_path):
    fixture = tmp_path / "earthquakes.json"
    fixture.write_text(_earthquakes())
    wrong = deepcopy(ADMIN)
    wrong["border-bc"]["metadata"]["request"] = wrong["border-wa"]["metadata"]["request"]
    with pytest.raises(NewsParserError, match="match the earthquake point"):
        parse_fixture_items(_source(fixture, wrong), fixture.read_text())
    live = _source(fixture) | {"url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"}
    with pytest.raises(NewsParserError, match="NATIONAL fixture-only"):
        parse_fixture_items(live, fixture.read_text())
    config_path = tmp_path / "live-sidecar.yml"
    config_path.write_text(yaml.safe_dump({
        "news": {"scopes": {"NATIONAL": {"sources": [{
            "id": "usgs_eq_geojson", "geoserve_admin_fixture": ADMIN,
        }]}}},
    }))
    with pytest.raises(ConfigError, match="requires a local USGS fixture"):
        load_config(config_path)


def test_geoserve_sidecar_offline_scan_persists_basis_without_http(tmp_path, monkeypatch):
    fixture = tmp_path / "earthquakes.json"
    fixture.write_text(_earthquakes())
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {"enabled": True, "scopes": {"NATIONAL": {"enabled": True,
                 "sources": [{"id": "usgs_eq_geojson", "enabled": True,
                              "url": fixture.resolve().as_uri(),
                              "geoserve_admin_fixture": ADMIN}]}}},
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("GeoServe fixture attempted HTTP"))
    ))
    result = run_news_scan(path)
    assert result["status"] == "complete" and result["item_count"] == 3
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchall()
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert len(evidence) == 3
    assert any(row["usgs_earthquake"]["filter"]["geography_basis"]
               == "usgs_geoserve_admin_fixture" for row in evidence)
    assert all(row["national_identity"]["multi_state_impact"] is False for row in evidence)
