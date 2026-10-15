from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_events import correlate_global_items
from console1701.news.scanner import run_news_scan


def _item(
    item_id: int,
    *,
    family: str,
    title: str = "Tropical Cyclone Ana affects Example Island",
    country: str = "Example Island",
    event_type: str = "Tropical Cyclone",
    published_at: str = "2026-10-15T12:00:00+00:00",
    scope: str = "GLOBAL",
) -> dict:
    return {
        "id": item_id,
        "scope": scope,
        "title": title,
        "source_published_at": published_at,
        "first_seen_at": published_at,
        "evidence": {
            "source": {"source_family": family, "source_key": f"{family}_{item_id}"},
            "global": {
                "event_type": event_type,
                "affected_countries": [country],
                "geography_basis": "official_source_fields",
            },
        },
    }


def test_global_correlation_requires_independent_family_location_type_tokens_and_time():
    first = _item(1, family="gdacs")
    convergent = _item(2, family="reliefweb", published_at="2026-10-16T09:00:00+00:00")
    same_family = _item(3, family="gdacs")
    wrong_country = _item(4, family="who", country="Other Island")
    wrong_type = _item(5, family="wmo", event_type="Earthquake")
    old = _item(6, family="un", published_at="2026-10-01T12:00:00+00:00")
    local = _item(7, family="local", scope="LOCAL")
    groups = correlate_global_items([
        first, convergent, same_family, wrong_country, wrong_type, old, local
    ])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3], [4], [5], [6]]
    # A same-family title duplicate cannot bridge into an already formed event.
    assert [match["item_ids"] for match in groups[0]["matches"]] == [[1, 2]]
    assert groups[0]["corroborated"] is True
    assert groups[0]["families"] == ["gdacs", "reliefweb"]
    assert "independent_family" in groups[0]["matches"][0]["basis"]


def test_global_correlation_shared_official_id_and_unverified_location_rules():
    gdacs_rss = _item(1, family="gdacs", title="Orange alert for cyclone Ana")
    gdacs_rss["evidence"]["gdacs"] = {"event_type": "TC", "event_id": "12345"}
    gdacs_geojson = _item(2, family="gdacs", title="Cyclone Ana near island")
    gdacs_geojson["evidence"]["gdacs"] = {"event_type": "TC", "event_id": "12345"}
    unverified = _item(3, family="who")
    unverified["evidence"]["global"]["geography_basis"] = "title_suffix_unverified"
    groups = correlate_global_items([gdacs_rss, gdacs_geojson, unverified])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3]]
    assert groups[0]["matches"][0]["basis"] == ["shared_event_id"]
    assert groups[0]["corroborated"] is False

    changed_id = deepcopy(gdacs_geojson)
    changed_id["evidence"]["gdacs"]["event_id"] = "other"
    assert [group["item_ids"] for group in correlate_global_items([
        gdacs_rss, changed_id
    ])] == [[1], [2]]


def test_global_correlation_rejects_multi_country_bridge():
    island_a = _item(1, family="gdacs", country="Island A")
    broad_report = _item(2, family="reliefweb", country="Island A")
    broad_report["evidence"]["global"]["affected_countries"].append("Island C")
    island_c = _item(3, family="wmo", country="Island C")
    groups = correlate_global_items([island_a, broad_report, island_c])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3]]
    assert groups[0]["matches"][0]["basis"][1] == "country"


def test_global_correlation_uses_structured_ids_and_verified_region_context():
    storm_a = _item(1, family="nhc", country="")
    storm_b = _item(2, family="wmo", country="")
    for item in (storm_a, storm_b):
        item["evidence"]["global_identity"] = {
            "storm_id": "AL012026", "basin": "Atlantic",
            "institution": "WMO", "transport_sector": "aviation",
        }
        item["evidence"]["global"]["affected_regions"] = ["Caribbean"]
    groups = correlate_global_items([storm_a, storm_b])
    assert groups[0]["item_ids"] == [1, 2]
    assert groups[0]["matches"][0]["basis"] == ["shared_event_id"]
    assert groups[0]["identifiers"] == ["storm_id:al012026"]

    for item in (storm_a, storm_b):
        item["evidence"]["global_identity"].pop("storm_id")
    groups = correlate_global_items([storm_a, storm_b])
    basis = groups[0]["matches"][0]["basis"]
    assert "region" in basis and "basin" in basis
    assert "institution" in basis and "transport_sector" in basis


def test_global_correlation_uses_volcano_disease_and_cyber_context():
    volcano_a = _item(
        1, family="gvs", country="", event_type="Volcanic eruption",
        title="Mount Example volcanic eruption alert",
    )
    volcano_b = _item(
        2, family="wmo", country="", event_type="Volcanic eruption",
        title="Mount Example volcanic eruption advisory",
    )
    for item in (volcano_a, volcano_b):
        item["evidence"]["global_identity"] = {"volcano_name": "Mount Example"}
    assert "volcano_name" in correlate_global_items([
        volcano_a, volcano_b
    ])[0]["matches"][0]["basis"]

    disease_a = _item(
        3, family="who", event_type="outbreak", title="Measles outbreak on Example Island"
    )
    disease_b = _item(
        4, family="ecdc", event_type="outbreak", title="Measles outbreak on Example Island"
    )
    for item in (disease_a, disease_b):
        item["evidence"]["global_identity"] = {"disease": "measles"}
    assert "disease" in correlate_global_items([
        disease_a, disease_b
    ])[0]["matches"][0]["basis"]

    cyber_a = _item(5, family="cisa", title="Incident bulletin one")
    cyber_b = _item(6, family="enisa", title="Incident bulletin two")
    for item in (cyber_a, cyber_b):
        item["evidence"]["global_identity"] = {"cyber_incident_id": "INC-104"}
    assert correlate_global_items([cyber_a, cyber_b])[0]["matches"][0]["basis"] == [
        "shared_event_id"
    ]


def test_global_scan_stores_shared_id_event_without_duplicate_family_score(tmp_path, monkeypatch):
    def unexpected_fetch(*args, **kwargs):
        raise AssertionError("fixture correlation must not fetch HTTP")

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", unexpected_fetch)
    fixture = Path(__file__).parent / "fixtures/news/global_gdacs.geojson"
    config_path = tmp_path / "global.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - {{id: gdacs_a, name: GDACS A, kind: api_json, parser: gdacs_geojson,
                   source_family: gdacs, enabled: true, url: "file://{fixture}"}}
                - {{id: gdacs_b, name: GDACS B, kind: api_json, parser: gdacs_geojson,
                   source_family: gdacs, enabled: true, url: "file://{fixture}"}}
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT rank_score, evidence_json FROM news_items WHERE scope = 'GLOBAL'"
        ).fetchall()
        clusters = conn.execute(
            "SELECT item_count, score, evidence_json FROM news_clusters WHERE scope = 'GLOBAL'"
        ).fetchall()
    assert len(clusters) == 1
    assert clusters[0]["item_count"] == 2
    assert clusters[0]["score"] == max(row["rank_score"] for row in rows)
    event = json_loads(clusters[0]["evidence_json"], {})["global_event"]
    assert event["confidence"] == "source_reported"
    assert event["families"] == ["gdacs"]
    assert event["matches"][0]["basis"] == ["shared_event_id"]
    assert all(
        json_loads(row["evidence_json"], {})["global"]["event_confidence"]
        == "source_reported" for row in rows
    )
