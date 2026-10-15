from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db
from console1701.news.orbital_ranking import rank_orbital_event
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_item_detail, get_news_scope_view

NOW = "2026-10-15T18:00:00+00:00"


def _item(item_id, family, *, stamp="2026-10-15T17:00:00+00:00", source=None,
          safety=None, identity=None, **facts):
    return {
        "id": item_id, "source_published_at": stamp,
        "evidence": {
            "source": {"source_family": family, "official_status": "official",
                       "priority": 80, **(source or {})},
            "orbital_identity": identity or {}, "orbital_safety": safety or {},
            **facts,
        },
    }


def _group(*families, corroborated=False, identifiers=None):
    return {"families": list(families), "corroborated": corroborated,
            "identifiers": identifiers or []}


def test_orbital_rank_uses_official_scale_and_explicit_impact_without_panic():
    alert = _item(
        1, "swpc", safety={"official_alert": True},
        swpc_alert={"noaa_scale": "G3", "issued_at": "2026-10-15T17:00:00+00:00",
                    "valid_until": "2026-10-15T19:00:00+00:00", "potential_impacts": [
            {"system": "radio"}, {"system": "aurora"},
        ]},
        identity={"impact_tags": ["REGIONAL_IMPACT"]},
    )
    ranked = rank_orbital_event(_group("swpc", identifiers=["swpc:one"]), [alert], now=NOW)
    assert ranked["score"] > 0
    assert ranked["factors"]["official_severity_score"] == 24
    assert ranked["factors"]["operational_impact_score"] == 10
    assert ranked["factors"]["active_alert_or_launch_window_score"] == 15
    assert ranked["impact_tags"] == ["regional_impact"]
    assert "impact prediction" not in " ".join(ranked["reasons"])


def test_orbital_rank_favors_independent_sources_and_penalizes_duplicates():
    first = _item(1, "nasa", identity={"event_type": "iss_update"})
    second = _item(2, "esa", identity={"event_type": "iss_update"})
    duplicate = _item(3, "nasa", identity={"event_type": "iss_update"})
    corroborated = rank_orbital_event(
        _group("nasa", "esa", corroborated=True), [first, second], now=NOW
    )
    repeated = rank_orbital_event(
        _group("nasa"), [first, duplicate], now=NOW
    )
    assert corroborated["score"] > repeated["score"]
    assert repeated["factors"]["duplicate_family_penalty"] == 3
    assert repeated["factors"]["low_confidence_penalty"] == 24


def test_orbital_rank_deemphasizes_stale_low_value_and_suppresses_tactical():
    routine = _item(
        1, "nasa", stamp="2026-10-10T17:00:00+00:00",
        identity={"public_value_class": "routine"},
        ingest={"source_health_state_at_ingest": "stale"},
    )
    ranked = rank_orbital_event(_group("nasa"), [routine], now=NOW)
    assert ranked["factors"]["recency_score"] == 0
    assert ranked["factors"]["stale_source_penalty"] == 8
    assert ranked["factors"]["low_public_value_penalty"] == 30
    tactical = _item(2, "catalog", safety={"tactical_tracking": True})
    blocked = rank_orbital_event(_group("catalog"), [tactical], now=NOW)
    assert blocked["score"] == 0
    assert blocked["sensitivity"]["hard_suppression_flags"] == ["tactical_tracking"]


def test_orbital_close_approach_does_not_infer_threat_from_distance():
    cad = _item(1, "jpl", identity={"event_type": "neo_close_approach"},
                jpl_close_approach={"distance_lunar": 0.2})
    ranked = rank_orbital_event(_group("jpl", identifiers=["cad:one"]), [cad], now=NOW)
    assert ranked["factors"]["official_severity_score"] == 0
    assert ranked["factors"]["public_impact_score"] == 0


def test_expired_swpc_warning_is_not_an_active_window():
    expired = _item(
        1, "swpc", safety={"official_alert": True},
        swpc_alert={"issued_at": "2026-10-10T12:00:00+00:00",
                    "valid_until": "2026-10-10T20:00:00+00:00", "noaa_scale": "G3"},
    )
    ranked = rank_orbital_event(_group("swpc"), [expired], now=NOW)
    assert ranked["factors"]["active_alert_or_launch_window_score"] == 0


def test_orbital_ui_hides_tactical_item_even_if_stored(tmp_path, monkeypatch):
    fixture = Path(__file__).parent / "fixtures/orbital/swpc_alerts.json"

    def sensitive_first(source, payload):
        items = parse_fixture_items(source, payload)
        items[0]["evidence"]["orbital_safety"]["tactical_tracking"] = True
        items[0]["title"] = "Tactical object 12345 movement"
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
        view = get_news_scope_view(conn, config, "ORBITAL")
        tactical_id = conn.execute(
            "SELECT id FROM news_items WHERE title='Sensitive orbital tracking claim'"
        ).fetchone()[0]
        assert get_news_item_detail(conn, tactical_id) is None
    assert len(view["items"]) == len(view["clusters"]) == 1
    assert all("Tactical object" not in row["title"] for row in view["items"])
