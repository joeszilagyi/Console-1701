from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import ConfigError, load_config
from console1701.db import connect_db
from console1701.news.orbital_registry import get_orbital_source_registry_entry
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import list_orbital_items_by_facet

FIXTURE = Path(__file__).parent / "fixtures/orbital/jpl_fireball.json"
SOURCE = {
    "id": "jpl_fireball_api", "name": "JPL Fireballs", "scope": "ORBITAL",
    "kind": "api_json", "parser": "jpl_fireball_json",
    "source_family": "jpl_cneos", "url": f"file://{FIXTURE}",
}


def test_jpl_fireball_parser_preserves_source_units_location_and_velocity():
    assert get_orbital_source_registry_entry("jpl_fireball_api")["parser"] == (
        "jpl_fireball_json"
    )
    items = parse_fixture_items(dict(SOURCE, max_age_days=36500), FIXTURE.read_text())
    assert len(items) == 2
    located, unlocated = items
    evidence = located["evidence"]["jpl_fireball"]
    assert evidence["event_time_utc"] == "2026-10-15T12:00:00+00:00"
    assert evidence["latitude"] == 47.0
    assert evidence["longitude"] == -122.0
    assert evidence["altitude_km"] == 28.0
    assert evidence["radiated_energy_1e10_joules"] == 12.0
    assert evidence["estimated_impact_energy_kt"] == 0.4
    assert evidence["derived_speed_km_s"] == 10.247
    assert evidence["location_basis"] == "source_reported_peak_brightness"
    assert unlocated["evidence"]["jpl_fireball"]["location_basis"] == "not_reported"
    assert unlocated["evidence"]["jpl_fireball"]["derived_speed_km_s"] is None
    assert "No ground impact or damage is implied" in located["description"]


def test_jpl_fireball_parser_checks_signature_schema_and_freshness():
    with pytest.raises(NewsParserError, match="signature version"):
        parse_fixture_items(SOURCE, '{"signature":{"version":"9"},"count":0}')
    with pytest.raises(NewsParserError, match="Malformed"):
        parse_fixture_items(SOURCE, "{")
    assert parse_fixture_items(SOURCE, json.dumps({
        "signature": {"version": "1.2"}, "count": 0,
    })) == []
    with pytest.raises(NewsParserError, match="required field names"):
        parse_fixture_items(SOURCE, json.dumps({
            "signature": {"version": "1.2"}, "count": 1,
            "fields": ["date"], "data": [["2026-10-15 12:00:00"]],
        }))
    old_payload = FIXTURE.read_text().replace("2026-10-15", "2000-01-01")
    assert parse_fixture_items(dict(SOURCE, max_age_days=1), old_payload) == []

    ambiguous = json.loads(FIXTURE.read_text())
    second = list(ambiguous["data"][0])
    second[3:5] = ["80.0", "W"]  # Different location, identical API query fields.
    ambiguous["data"] = [ambiguous["data"][0], second]
    ambiguous["count"] = 2
    with pytest.raises(NewsParserError, match="share the available API query identity"):
        parse_fixture_items(dict(SOURCE, max_age_days=36500), json.dumps(ambiguous))


def test_jpl_fireball_fixture_scan_offline_and_config_thresholds(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    fixture = tmp_path / "recent-fireball.json"
    recent_date = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
    payload = json.loads(FIXTURE.read_text().replace("2026-10-15", recent_date))
    payload["data"][2][0] = payload["data"][0][0]
    fixture.write_text(json.dumps(payload))
    path = tmp_path / "config.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital:
          enabled: true
          fireball_min_impact_kt: 0.1
          fireball_max_age_days: 30
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: jpl_fireball_api
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    assert run_news_scan(path)["item_count"] == 2
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        assert len(list_orbital_items_by_facet(conn, "event_type", "fireball")) == 2
        assert conn.execute(
            "SELECT COUNT(*) FROM news_clusters WHERE scope='ORBITAL'"
        ).fetchone()[0] == 2
    path.write_text(path.read_text().replace(
        "fireball_max_age_days: 30", "fireball_max_age_days: 3000"
    ))
    with pytest.raises(ConfigError, match="fireball_max_age_days"):
        load_config(path)
