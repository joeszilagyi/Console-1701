from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.orbital_safety import classify_orbital_item
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_item_detail, get_news_scope_view


def _item(title, event_type):
    return {"title": title, "description": title, "url": "https://example.test/item",
            "evidence": {"orbital_identity": {"event_type": event_type}}}


def test_orbital_classifier_redacts_tactical_and_restricted_claims():
    classified = classify_orbital_item(
        {"source_class": "official_satellite_catalog"},
        _item("Classified satellite location over city", "satellite_update"),
    )
    assert classified["title"] == "Sensitive orbital tracking claim"
    assert classified["description"] is None
    assert classified["evidence"]["orbital_safety"]["tactical_tracking"] is True
    assert classified["evidence"]["orbital_safety"]["classified_inference"] is True
    assert classified["evidence"]["orbital_safety"]["redacted_before_storage"] is True
    restricted = classify_orbital_item(
        {"verification_status": "restricted_auth_required"},
        _item("Routine satellite item", "satellite_update"),
    )
    assert restricted["evidence"]["orbital_safety"]["restricted_source"] is True


def test_orbital_classifier_deemphasizes_rumor_panic_and_social_claims():
    launch = classify_orbital_item(
        {}, _item("Rumored launch tomorrow", "launch_update")
    )
    assert launch["evidence"]["orbital_identity"]["rumor"] is True
    assert launch["evidence"]["orbital_safety"]["launch_rumor"] is True
    assert launch["title"] == "Rumored launch tomorrow"
    neo = classify_orbital_item({}, _item("Doomsday asteroid will hit Earth", "neo_close_approach"))
    assert neo["evidence"]["orbital_safety"]["neo_panic_language"] is True
    reentry = classify_orbital_item({}, _item("Imminent impact from reentry", "reentry"))
    assert reentry["evidence"]["orbital_safety"]["sensitive_reentry"] is True
    debris = classify_orbital_item({}, _item("Doomsday debris collision", "orbital_debris"))
    assert debris["evidence"]["orbital_safety"]["debris_fear_framing"] is True
    social = classify_orbital_item(
        {"source_class": "social_candidate"}, _item("Launch eyewitness", "launch_update")
    )
    assert social["evidence"]["orbital_safety"]["social_only_claim"] is True


def test_orbital_classifier_leaves_official_warning_and_near_approach_facts_intact():
    warning = classify_orbital_item(
        {"source_class": "official_space_weather"},
        _item("SWPC G3 geomagnetic warning", "space_weather_alert"),
    )
    assert warning["title"] == "SWPC G3 geomagnetic warning"
    assert warning["evidence"]["orbital_safety"] == {}
    cad = classify_orbital_item(
        {"source_class": "official_neo"},
        _item("JPL close approach at 0.2 lunar distances", "neo_close_approach"),
    )
    assert cad["evidence"]["orbital_safety"] == {}


def test_hard_sensitive_fixture_is_redacted_and_hidden_with_short_retention(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures/orbital/swpc_alerts.json"

    def sensitive_first(source, payload):
        items = parse_fixture_items(source, payload)
        items[0]["title"] = "Classified satellite location over city"
        items[0]["description"] = items[0]["title"]
        return items

    monkeypatch.setattr("console1701.news.scanner.parse_fixture_items", sensitive_first)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    path = tmp_path / "config.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: true}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: swpc_alerts_json
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute(
            "SELECT * FROM news_items WHERE title='Sensitive orbital tracking claim'"
        ).fetchone()
        assert row is not None and row["description"] is None
        evidence = json_loads(row["evidence_json"], {})
        assert evidence["retention"]["retention_days"] == 1
        assert get_news_item_detail(conn, int(row["id"])) is None
        view = get_news_scope_view(conn, config, "ORBITAL")
    assert all("Classified satellite" not in item["title"] for item in view["items"])
    assert len(view["items"]) == 1
