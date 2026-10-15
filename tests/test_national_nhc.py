from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.national_events import correlate_national_items
from console1701.news.national_registry import national_registry_config_defaults
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_scope_view

FIXTURE = Path(__file__).parent / "fixtures/news/global_nhc_ep.rss"
NHC_KEYS = ("nhc_atlantic_rss", "nhc_eastern_pacific_rss", "nhc_central_pacific_rss")


def _source(key: str, path: Path) -> dict:
    source = national_registry_config_defaults(key)
    source.update({"enabled": True, "url": path.as_uri()})
    return source


def test_national_nhc_fixture_preserves_storm_identity_without_us_impact():
    source = _source("nhc_eastern_pacific_rss", FIXTURE)
    items = parse_fixture_items(source, FIXTURE.read_text())
    assert len(items) == 2
    advisory = items[0]
    identity = advisory["evidence"]["national_identity"]
    assert identity["official_event_ids"] == ["nhc:EP212026"]
    assert identity["storm_basins"] == ["eastern_pacific"]
    assert identity["event_type"] == "tropical_cyclone"
    assert identity["official_severity_score"] == 25
    assert identity["national_impact"] is False
    assert identity["multi_state_impact"] is False
    assert advisory["evidence"]["nhc_rss"]["watch_warning_geography_verified"] is False
    assert advisory["description"] is None
    assert advisory["evidence"]["nhc_rss"]["body_stored"] is False
    assert items[1]["evidence"]["national_identity"]["official_event_ids"] == [
        "nhc:EP202026"
    ]


def test_national_nhc_fixture_rejects_wrong_source_basin_and_live_url():
    source = _source("nhc_eastern_pacific_rss", FIXTURE)
    feed = FIXTURE.read_text()
    with pytest.raises(NewsParserError, match="basin does not match"):
        parse_fixture_items(_source("nhc_atlantic_rss", FIXTURE), feed)
    with pytest.raises(NewsParserError, match="exact fixture source identity"):
        parse_fixture_items({**source, "url": source["official_url"]}, feed)
    with pytest.raises(NewsParserError, match="exact fixture source identity"):
        parse_fixture_items({**source, "official_url": "https://example.test/feed"}, feed)
    with pytest.raises(PayloadTooLargeError, match="64 KiB"):
        parse_fixture_items(source, feed + " " * 65_536)
    with pytest.raises(NewsParserError, match="DTD or entities"):
        parse_fixture_items(source, "<!DOCTYPE rss>" + feed)
    with pytest.raises(NewsParserError, match="official HTTPS URL"):
        parse_fixture_items(source, feed.replace(
            "/text/refresh/MIATCPEP1+shtml/151739.shtml", "/news/151739.shtml"
        ))


def test_national_nhc_atcf_identity_survives_advisory_url_update():
    source = _source("nhc_eastern_pacific_rss", FIXTURE)
    original = parse_fixture_items(source, FIXTURE.read_text())
    revised_feed = FIXTURE.read_text().replace("Public Advisory Number 9a",
                                               "Public Advisory Number 10").replace(
        "151739.shtml", "152100.shtml"
    )
    revised = parse_fixture_items(source, revised_feed)[0]
    rows = []
    for item_id, item in enumerate((original[0], original[1], revised), 1):
        rows.append({
            **item, "id": item_id,
            "evidence": {**item["evidence"], "source": {
                "source_key": source["id"], "source_family": "noaa_nhc",
                "official_status": "official",
            }},
        })
    groups = correlate_national_items(rows)
    assert sorted(group["item_ids"] for group in groups) == [[1, 3], [2]]
    assert groups[0]["matches"][0]["basis"] == ["shared_official_event_id"]
    assert groups[0]["corroborated"] is False


def test_national_nhc_three_basin_scan_is_offline_and_empty_basins_are_healthy(
    tmp_path, monkeypatch
):
    empty_atlantic = tmp_path / "atlantic.rss"
    empty_central = tmp_path / "central.rss"
    for path, channel in ((empty_atlantic, "NHC Atlantic"),
                          (empty_central, "CPHC Central North Pacific")):
        path.write_text(
            f"<rss><channel><title>{channel}</title><item><title>"
            "There are no tropical cyclones at this time."
            "</title></item></channel></rss>"
        )
    config_path = tmp_path / "config.yml"
    config_path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {"enabled": True, "scopes": {"NATIONAL": {
            "enabled": True,
            "sources": [
                {"id": key, "enabled": True, "url": path.as_uri()}
                for key, path in zip(
                    NHC_KEYS, (empty_atlantic, FIXTURE, empty_central), strict=True
                )
            ],
        }}},
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("NHC fixture scan attempted HTTP"))
    ))
    result = run_news_scan(config_path)
    assert result["status"] == "complete"
    assert result["scanned_sources"] == 3
    assert result["item_count"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='NATIONAL' ORDER BY id"
        ).fetchall()
        cluster_count = conn.execute(
            "SELECT COUNT(*) FROM news_clusters WHERE scope='NATIONAL'"
        ).fetchone()[0]
        view = get_news_scope_view(conn, config, "NATIONAL")
        states = conn.execute(
            "SELECT state FROM news_source_health ORDER BY id"
        ).fetchall()
    assert [row["state"] for row in states] == ["healthy"] * 3
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert all(row["national_identity"]["multi_state_impact"] is False for row in evidence)
    assert all(row["national_identity"]["national_impact"] is False for row in evidence)
    assert all(row["national_policy"]["suppressed"] is True for row in evidence)
    assert all(any("verified U.S. watch geography" in reason
                   for reason in row["national_policy"]["reasons"])
               for row in evidence)
    assert cluster_count == 0
    assert view["items"] == [] and view["clusters"] == []
    assert {event_type for row in evidence
            for event_type in row["national_event"]["event_types"]} == {
        "tropical_cyclone"
    }
    assert all(row["national_event"]["ranking"]["factors"][
        "geographic_reach_score"] == 0 for row in evidence)


def test_national_nhc_live_url_stays_blocked_before_fetch(tmp_path, monkeypatch):
    config_path = tmp_path / "live.yml"
    config_path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {
            "enabled": True, "fetch_policy": {"allow_official_http": True},
            "scopes": {"NATIONAL": {"enabled": True, "sources": [{
                "id": "nhc_eastern_pacific_rss", "enabled": True,
            }]}},
        },
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("NHC live URL reached HTTP fetch"))
    ))
    result = run_news_scan(config_path)
    assert result["status"] == "partial"
    assert result["item_count"] == 0
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        health = conn.execute("SELECT state FROM news_source_health").fetchone()
    assert health["state"] in {"policy_blocked", "unsupported"}
