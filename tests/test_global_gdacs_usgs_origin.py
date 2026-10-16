from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_events import correlate_global_items
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURES = Path(__file__).parent / "fixtures/news"
GDACS = FIXTURES / "global_gdacs.geojson"
USGS = FIXTURES / "global_usgs_gdacs_costa_rica.json"


def _pair() -> tuple[dict, dict]:
    gdacs, = parse_fixture_items(
        {"scope": "GLOBAL", "kind": "api_json", "parser": "gdacs_geojson"},
        GDACS.read_text(),
    )
    usgs, = parse_fixture_items(
        {"scope": "GLOBAL", "kind": "api_json", "parser": "usgs_earthquake_geojson",
         "min_magnitude": 4.5}, USGS.read_text(),
    )
    for item_id, item, family in ((1, gdacs, "gdacs"), (2, usgs, "usgs")):
        item["id"] = item_id
        item["evidence"]["source"] = {
            "source_family": family, "source_key": f"{family}_fixture",
            "official_status": "official",
        }
    return gdacs, usgs


def test_observed_gdacs_usgs_origin_joins_without_independent_credit():
    gdacs, usgs = _pair()
    assert gdacs["evidence"]["gdacs"]["coordinates"] == [
        usgs["evidence"]["usgs_earthquake"]["longitude"],
        usgs["evidence"]["usgs_earthquake"]["latitude"],
    ]
    group, = correlate_global_items([gdacs, usgs])
    assert group["item_ids"] == [1, 2]
    assert group["matches"][0]["basis"] == ["shared_upstream_earthquake_origin"]
    assert group["families"] == ["gdacs", "usgs"]
    assert group["credited_families"] == ["usgs"]
    assert group["dependent_duplicate_count"] == 1
    assert group["corroborated"] is False


def test_origin_match_rejects_changed_time_location_magnitude_or_authority():
    gdacs, usgs = _pair()
    for changed in (
        {"time": "2026-10-15T15:40:45+00:00"},
        {"longitude": -86.02},
        {"magnitude": 4.7},
    ):
        other = deepcopy(usgs)
        other["evidence"]["usgs_earthquake"].update(changed)
        assert [group["item_ids"] for group in correlate_global_items([
            gdacs, other
        ])] == [[1], [2]]
    candidate = deepcopy(usgs)
    candidate["evidence"]["source"]["official_status"] = "official_candidate"
    assert [group["item_ids"] for group in correlate_global_items([
        gdacs, candidate
    ])] == [[1], [2]]
    wrong_family = deepcopy(usgs)
    wrong_family["evidence"]["source"]["source_family"] = "un_press"
    assert [group["item_ids"] for group in correlate_global_items([
        gdacs, wrong_family
    ])] == [[1], [2]]


def test_one_gdacs_origin_cannot_bridge_two_distinct_usgs_events():
    gdacs, usgs = _pair()
    second = deepcopy(usgs)
    second["id"] = 3
    second["evidence"]["usgs_earthquake"]["id"] = "us6000different"
    second["evidence"]["usgs_earthquake"]["time"] = "2026-10-15T15:40:39+00:00"
    second["evidence"]["usgs_earthquake"]["latitude"] = 10.308
    second["url"] = second["canonical_url"] = (
        "https://earthquake.usgs.gov/earthquakes/eventpage/us6000different"
    )
    assert [group["item_ids"] for group in correlate_global_items([
        gdacs, usgs, second
    ])] == [[1, 2], [3]]


def test_observed_origin_offline_scan_has_one_noncorroborated_event(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected HTTP")),
    )
    config_path = tmp_path / "global-origin.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true, earthquake_min_magnitude: 4.5}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: gdacs_origin_fixture
                  name: GDACS origin fixture
                  kind: api_json
                  parser: gdacs_geojson
                  source_family: gdacs
                  official_status: official
                  enabled: true
                  url: "file://{GDACS}"
                - id: usgs_origin_fixture
                  name: USGS origin fixture
                  kind: api_json
                  parser: usgs_earthquake_geojson
                  source_family: usgs
                  official_status: official
                  enabled: true
                  url: "file://{USGS}"
    """).strip() + "\n")
    result = run_news_scan(config_path)
    assert result["status"] == "complete"
    assert result["item_count"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT item_count,evidence_json FROM news_clusters WHERE scope='GLOBAL'"
        ).fetchall()
    assert len(rows) == 1 and rows[0]["item_count"] == 2
    event = json_loads(rows[0]["evidence_json"], {})["global_event"]
    assert event["corroborated"] is False
    assert event["credited_families"] == ["usgs"]
    assert event["ranking"]["factors"]["source_diversity_score"] == 11
    assert event["ranking"]["factors"]["cluster_size_score"] == 1
