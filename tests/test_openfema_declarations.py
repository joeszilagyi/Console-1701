from __future__ import annotations

import json
from pathlib import Path

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.national_policy import classify_national_item
from console1701.news.official_http import is_supported_official_source
from console1701.news.openfema_declarations import API_URL
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/national/openfema_declarations_2026_10_15.json"


def _source():
    return {
        "id": "openfema_disaster_declarations", "scope": "NATIONAL",
        "kind": "api_json", "parser": "openfema_declarations_fixture",
        "source_family": "fema", "official_status": "official",
        "url": FIXTURE.resolve().as_uri(), "official_url": API_URL,
    }


def test_openfema_observed_fixture_uses_declaration_date_and_tribal_scope():
    items = parse_fixture_items(_source(), FIXTURE.read_text())
    assert len(items) == 2
    older = items[0]
    assert older["source_published_at"] == "2026-09-01T00:00:00+00:00"
    assert older["evidence"]["openfema_declaration"]["last_refresh"] == (
        "2026-10-14T11:04:54+00:00"
    )
    assert older["evidence"]["openfema_declaration"]["recent_declaration_at_refresh"] is False
    assert classify_national_item(_source(), older)["attention_state"] == "background"
    assert older["evidence"]["national_identity"]["affected_states"] == ["KS"]
    tribal = items[1]
    assert tribal["evidence"]["openfema_declaration"]["places"][0]["tribal_request"]
    assert tribal["evidence"]["national_identity"]["affected_states"] == []
    assert tribal["evidence"]["national_identity"]["jurisdictions"] == [
        "tribal declaration"
    ]
    assert tribal["evidence"]["openfema_declaration"]["active_hazard_claimed"] is False


def test_openfema_place_revisions_coalesce_without_cluster_size_inflation():
    payload = json.loads(FIXTURE.read_text())
    first = payload["DisasterDeclarationsSummaries"][0]
    extra = dict(first, placeCode="99103", designatedArea="Fixture County")
    older_revision = dict(first, lastRefresh="2026-10-13T00:00:00.000Z")
    payload["DisasterDeclarationsSummaries"] += [extra, older_revision]
    items = parse_fixture_items(_source(), json.dumps(payload))
    assert len(items) == 2
    assert [entry["place_code"] for entry in items[0]["evidence"][
        "openfema_declaration"
    ]["places"]] == ["99101", "99103"]
    assert items[0]["evidence"]["national_identity"]["official_event_ids"] == [
        "fema:dr-4943-ks"
    ]


def test_openfema_empty_and_other_documented_declaration_types():
    payload = json.loads(FIXTURE.read_text())
    payload["DisasterDeclarationsSummaries"] = []
    assert parse_fixture_items(_source(), json.dumps(payload)) == []
    base = json.loads(FIXTURE.read_text())["DisasterDeclarationsSummaries"][0]
    for kind, number in (("EM", 3506), ("FM", 5201)):
        row = dict(base, disasterNumber=number, declarationType=kind,
                   femaDeclarationString=f"{kind}-{number}-KS")
        payload["DisasterDeclarationsSummaries"] = [row]
        item, = parse_fixture_items(_source(), json.dumps(payload))
        assert item["evidence"]["openfema_declaration"]["declaration_type"] == kind


def test_openfema_rejects_wrong_source_and_unbounded_or_inconsistent_rows():
    source = _source() | {"official_url": "https://example.test/data"}
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())
    source = _source() | {"url": API_URL}
    with pytest.raises(NewsParserError):
        parse_fixture_items(source, FIXTURE.read_text())
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 65_537)
    payload = json.loads(FIXTURE.read_text())
    payload["DisasterDeclarationsSummaries"][0]["femaDeclarationString"] = "DR-4943-NM"
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(payload))
    payload = json.loads(FIXTURE.read_text())
    payload["DisasterDeclarationsSummaries"] *= 11
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(payload))


def test_openfema_registry_fixture_scans_without_http(tmp_path, monkeypatch):
    assert is_supported_official_source(_source() | {"url": API_URL}) is False
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected HTTP")),
    )
    config_path = tmp_path / "fema.yml"
    config_path.write_text(f"""
paths: {{repo_roots: [], explicit_repos: []}}
national: {{enabled: true}}
news:
  enabled: true
  scopes:
    NATIONAL:
      enabled: true
      sources:
        - id: openfema_disaster_declarations
          enabled: true
          url: "{FIXTURE.resolve().as_uri()}"
""".strip() + "\n")
    result = run_news_scan(config_path)
    assert result["status"] == "complete", result
    assert result["item_count"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        items = conn.execute(
            "SELECT evidence_json, source_published_at FROM news_items "
            "WHERE scope='NATIONAL' ORDER BY source_published_at"
        ).fetchall()
        assert len(items) == 2
        first = json_loads(items[0]["evidence_json"], {})
        assert first["ingest"]["fixture_only"] is True
        assert first["openfema_declaration"]["last_refresh"].startswith("2026-10-14")
        assert items[0]["source_published_at"].startswith("2026-09-01")
        clusters = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='NATIONAL'"
        ).fetchall()
        assert len(clusters) == 2
