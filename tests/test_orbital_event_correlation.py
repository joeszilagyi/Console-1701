from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.orbital_events import correlate_orbital_items
from console1701.news.parsers import parse_fixture_items
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


def test_nasa_channel_variants_and_jpl_do_not_count_as_independent_sources():
    title = "Crew Dragon docks with International Space Station"
    release = _item(1, "nasa", title)
    station = _item(2, "nasa_space_station", title)
    blog = _item(3, "nasa_blogs", title)
    jpl = _item(4, "jpl_cneos", title)
    groups = correlate_orbital_items([release, station, blog, jpl])
    assert [group["item_ids"] for group in groups] == [[1], [2], [3], [4]]
    assert all(group["families"] == ["nasa"] for group in groups)


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


def test_linked_launch_article_uses_source_launch_window_without_corroboration(
    tmp_path, monkeypatch
):
    orbital_fixtures = Path(__file__).parent / "fixtures/orbital"
    launch = json.loads((orbital_fixtures / "launch_library_upcoming.json").read_text())
    launch["results"][0]["id"] = "bf2c3027-a314-403e-a416-2bfd5d165ad1"
    launch_path = tmp_path / "linked-launch.json"
    launch_path.write_text(json.dumps(launch))
    article_path = orbital_fixtures / "spaceflight_news_articles.json"
    launch_source = {
        "id": "launch_library_upcoming", "scope": "ORBITAL",
        "parser": "launch_library_json", "source_family": "launch_library",
    }
    article_source = {
        "id": "spaceflight_news_articles", "scope": "ORBITAL",
        "parser": "spaceflight_news_json", "source_family": "spaceflight_news_api",
    }
    launch_item, = parse_fixture_items(launch_source, launch_path.read_text())
    article_item, = parse_fixture_items(article_source, article_path.read_text())
    assert launch_item["evidence"]["orbital_identity"]["provider"] == "SpaceX"
    for item_id, item, family in (
        (1, launch_item, "launch_library"),
        (2, article_item, "spaceflight_news_api"),
    ):
        item["id"] = item_id
        item["evidence"]["source"] = {"source_family": family}
    groups = correlate_orbital_items([launch_item, article_item])
    assert len(groups) == 1
    assert groups[0]["item_ids"] == [1, 2]
    assert groups[0]["matches"][0]["basis"] == [
        "event_type", "shared_event_id", "launch_window",
    ]
    assert groups[0]["corroborated"] is False
    article_item["source_published_at"] = "2026-09-01T12:00:00Z"
    assert len(correlate_orbital_items([launch_item, article_item])) == 2

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
                - id: launch_library_upcoming
                  enabled: true
                  url: "file://{launch_path}"
                - id: spaceflight_news_articles
                  enabled: true
                  url: "file://{article_path}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='ORBITAL'"
        ).fetchall()
        assert len(rows) == 1
        event = json_loads(rows[0]["evidence_json"], {})["orbital_event"]
        assert event["corroborated"] is False
        assert event["families"] == ["launch_library"]
        assert event["matches"][0]["basis"][-1] == "launch_window"


def test_linked_docking_article_joins_exact_event_near_source_time(tmp_path, monkeypatch):
    orbital_fixtures = Path(__file__).parent / "fixtures/orbital"
    event_path = orbital_fixtures / "launch_library_events.json"
    article = {
        "results": [{
            "id": 40800, "title": "CRS-35 Dragon docking at ISS",
            "url": "https://example.org/crs-35-docking", "news_site": "Space News",
            "published_at": "2026-10-15T12:00:00Z", "summary": "Docking coverage.",
            "launches": [], "events": [{"event_id": 1525}],
        }],
    }
    article_path = tmp_path / "linked-event.json"
    article_path.write_text(json.dumps(article))
    event_source = {
        "id": "launch_library_events", "scope": "ORBITAL",
        "parser": "launch_library_json", "source_family": "launch_library",
    }
    article_source = {
        "id": "spaceflight_news_articles", "scope": "ORBITAL",
        "parser": "spaceflight_news_json", "source_family": "spaceflight_news_api",
    }
    event_item, = parse_fixture_items(event_source, event_path.read_text())
    article_item, = parse_fixture_items(article_source, article_path.read_text())
    assert event_item["evidence"]["orbital_identity"]["launch_library_event_id"] == "1525"
    assert article_item["evidence"]["orbital_identity"]["launch_library_event_id"] == "1525"
    for item_id, item, key, family in (
        (1, event_item, "launch_library_events", "launch_library"),
        (2, article_item, "spaceflight_news_articles", "spaceflight_news_api"),
    ):
        item["id"] = item_id
        item["evidence"]["source"] = {"source_key": key, "source_family": family}
    groups = correlate_orbital_items([event_item, article_item])
    assert len(groups) == 1
    assert groups[0]["matches"][0]["basis"] == [
        "linked_launch_library_event_id", "event_window",
    ]
    assert groups[0]["corroborated"] is False

    article_item["source_published_at"] = "2026-11-01T12:00:00Z"
    assert len(correlate_orbital_items([event_item, article_item])) == 2
    article_item["source_published_at"] = "2026-10-15T12:00:00Z"
    article_item["evidence"]["orbital_identity"]["launch_library_event_id"] = "1526"
    assert len(correlate_orbital_items([event_item, article_item])) == 2

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
                - id: launch_library_events
                  enabled: true
                  url: "file://{event_path}"
                - id: spaceflight_news_articles
                  enabled: true
                  url: "file://{article_path}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='ORBITAL'"
        ).fetchall()
        assert len(rows) == 1
        event = json_loads(rows[0]["evidence_json"], {})["orbital_event"]
        assert event["corroborated"] is False
        assert event["matches"][0]["basis"] == [
            "linked_launch_library_event_id", "event_window",
        ]
