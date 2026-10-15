from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.orbital_events import correlate_orbital_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/orbital/swpc_alerts.json"


def _item(item_id, family, title, *, event_type="iss_update", object_id=None,
          stamp="2026-10-15T12:00:00+00:00", context=None):
    return {
        "id": item_id, "scope": "ORBITAL", "title": title,
        "source_published_at": stamp,
        "evidence": {
            "source": {"source_family": family, "source_key": f"{family}_{item_id}"},
            "orbital_identity": {
                "event_type": event_type, "object_id": object_id, **(context or {}),
            },
        },
    }


def test_orbital_correlation_requires_identity_or_independent_convergence():
    nasa = _item(1, "nasa", "Crew Dragon docks with International Space Station")
    esa = _item(2, "esa", "Crew Dragon docks with International Space Station")
    nasa_duplicate = _item(3, "nasa", nasa["title"])
    old = _item(4, "esa", esa["title"], stamp="2026-09-01T12:00:00+00:00")
    wrong_type = _item(5, "esa", esa["title"], event_type="launch_update")
    groups = correlate_orbital_items([nasa, esa, nasa_duplicate, old, wrong_type])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3], [4], [5]]
    assert groups[0]["corroborated"] is True
    assert "independent_family" in groups[0]["matches"][0]["basis"]


def test_orbital_identity_is_type_scoped_time_bounded_and_not_corroboration():
    alert = _item(1, "swpc", "SWPC geomagnetic warning", event_type="space_weather_alert",
                  object_id="K07W:2026-10-15T12:00:00+00:00")
    mirror = _item(2, "swpc", "NOAA warning duplicate", event_type="space_weather_alert",
                   object_id="K07W:2026-10-15T12:00:00+00:00")
    scale = _item(3, "swpc", "NOAA G3 warning", event_type="space_weather_scale",
                  object_id="K07W:2026-10-15T12:00:00+00:00")
    much_later = _item(4, "swpc", alert["title"], event_type="space_weather_alert",
                       object_id="K07W:2026-10-15T12:00:00+00:00",
                       stamp="2026-11-15T12:00:00+00:00")
    groups = correlate_orbital_items([alert, mirror, scale, much_later])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3], [4]]
    assert groups[0]["matches"][0]["basis"] == [
        "event_type", "shared_event_id", "time_window",
    ]
    assert groups[0]["corroborated"] is False


def test_orbital_mission_context_needs_title_and_complete_link():
    nasa = _item(1, "nasa", "Artemis II crew launches mission",
                 context={"mission_name": "Artemis II"})
    esa = _item(2, "esa", "Artemis II crew aboard mission",
                context={"mission_name": "Artemis II"})
    broad = _item(3, "agency", "Artemis II launches update",
                  context={"mission_name": "Artemis II"})
    groups = correlate_orbital_items([nasa, esa, broad])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3]]
    assert "mission_name" in groups[0]["matches"][0]["basis"]


def test_orbital_fixture_scan_persists_event_evidence_without_network(tmp_path, monkeypatch):
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
                  url: "file://{FIXTURE}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='ORBITAL' ORDER BY id"
        ).fetchall()
        assert len(rows) == 2
        event = json_loads(rows[0]["evidence_json"], {})["orbital_event"]
        assert event["item_ids"] and event["families"] == ["swpc"]
        assert event["corroborated"] is False
