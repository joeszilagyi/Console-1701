from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.national_events import correlate_national_items
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan


def _item(item_id: int, family: str, *, state: str = "WA",
          published: str = "2026-10-15T12:00:00+00:00") -> dict:
    return {
        "id": item_id, "scope": "NATIONAL",
        "title": "Major regional airport ground stop disruption",
        "source_published_at": published, "first_seen_at": published,
        "evidence": {
            "source": {"source_family": family, "source_key": f"{family}_{item_id}"},
            "national_identity": {
                "event_type": "aviation_disruption",
                "affected_states": [state],
                "affected_airports": ["SEA"],
                "infrastructure_sectors": ["aviation"],
                "agency": "FAA",
            },
        },
    }


def test_national_correlation_uses_structured_context_and_complete_link():
    faa = _item(1, "faa")
    news = _item(2, "ap")
    same_family = _item(3, "faa")
    wrong_type = _item(4, "reuters")
    wrong_type["evidence"]["national_identity"]["event_type"] = "weather_alert"
    old = _item(5, "public_media", published="2026-10-01T12:00:00+00:00")
    local = _item(6, "local")
    local["scope"] = "LOCAL"
    groups = correlate_national_items([faa, news, same_family, wrong_type, old, local])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3], [4], [5]]
    assert groups[0]["corroborated"] is True
    assert "affected_airports" in groups[0]["matches"][0]["basis"]
    assert groups[0]["families"] == ["ap", "faa"]

    mismatch = deepcopy(news)
    mismatch["evidence"]["national_identity"]["affected_states"] = ["CA"]
    mismatch["evidence"]["national_identity"]["affected_airports"] = ["LAX"]
    mismatch["evidence"]["national_identity"]["infrastructure_sectors"] = []
    assert [group["item_ids"] for group in correlate_national_items([faa, mismatch])] == [
        [1], [2]
    ]


def test_national_correlation_shared_official_id_does_not_fake_diversity():
    first = _item(1, "nhtsa")
    second = _item(2, "nhtsa")
    first["evidence"]["nhtsa_recall"] = {"campaign_number": "26V123"}
    second["evidence"]["nhtsa_recall"] = {"campaign_number": "26V123"}
    groups = correlate_national_items([first, second])
    assert [group["item_ids"] for group in groups] == [[1, 2]]
    assert groups[0]["matches"][0]["basis"] == ["shared_official_event_id"]
    assert groups[0]["corroborated"] is False


def test_cpsc_official_recall_id_correlates_url_revision_without_impact_inference():
    fixture = Path(__file__).parent / "fixtures/national/cpsc_recalls_2026_10_01.json"
    source = {
        "id": "cpsc_recalls_api", "scope": "NATIONAL", "kind": "api_json",
        "parser": "cpsc_recalls_json", "fixture_only": True,
        "url": "https://www.saferproducts.gov/RestWebServices/Recall",
        "query_contract": {"recall_date_start": "2026-10-01", "recall_date_end": "2026-10-02",
                           "format": "json", "timeout_seconds": 10},
    }
    parsed = parse_fixture_items(source, fixture.read_text())
    first = {**parsed[0], "id": 1}
    first["evidence"]["source"] = {"source_family": "cpsc", "source_key": "cpsc_a"}
    revision = deepcopy(first)
    revision["id"] = 2
    revision["url"] = revision["canonical_url"] = (
        "https://www.cpsc.gov/Recalls/2026/updated-recall-page"
    )
    revision["evidence"]["source"] = {"source_family": "cpsc", "source_key": "cpsc_b"}
    revision["evidence"].pop("national_identity")  # Earlier stored rows lack this contract.
    other = {**parsed[1], "id": 3}
    other["evidence"]["source"] = {"source_family": "cpsc", "source_key": "cpsc_c"}
    groups = correlate_national_items([first, revision, other])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3]]
    assert groups[0]["matches"][0]["basis"] == ["shared_official_event_id"]
    assert groups[0]["corroborated"] is False
    assert groups[0]["affected_states"] == []
    assert groups[0]["multi_state_impact"] is False


def test_openfema_declaration_id_survives_missing_identity_and_url_revision():
    fixture = Path(__file__).parent / "fixtures/national/openfema_declarations_2026_10_15.json"
    source = {
        "id": "openfema_disaster_declarations", "scope": "NATIONAL",
        "kind": "api_json", "parser": "openfema_declarations_fixture",
        "source_family": "fema", "official_status": "official",
        "url": fixture.resolve().as_uri(),
        "official_url": "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries",
    }
    parsed = parse_fixture_items(source, fixture.read_text())
    first = {**parsed[0], "id": 1}
    first["evidence"]["source"] = {"source_family": "fema", "source_key": "fema_a"}
    revision = deepcopy(first)
    revision["id"] = 2
    revision["url"] = revision["canonical_url"] = "https://www.fema.gov/disaster/4943/revision"
    revision["evidence"]["source"] = {"source_family": "fema", "source_key": "fema_b"}
    revision["evidence"].pop("national_identity")
    other = {**parsed[1], "id": 3}
    other["evidence"]["source"] = {"source_family": "fema", "source_key": "fema_c"}
    groups = correlate_national_items([first, revision, other])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3]]
    assert groups[0]["matches"][0]["basis"] == ["shared_official_event_id"]
    assert groups[0]["identifiers"] == ["fema:dr-4943-ks"]
    assert groups[0]["corroborated"] is False


def test_national_syndicated_article_does_not_count_as_independent_confirmation():
    first = _item(1, "publisher_one")
    second = _item(2, "publisher_two")
    first["canonical_url"] = "https://wire.example/story/123"
    second["canonical_url"] = "https://wire.example/story/123"
    group = correlate_national_items([first, second])[0]
    assert group["item_ids"] == [1, 2]
    assert group["matches"][0]["basis"] == ["same_article_url"]
    assert group["corroborated"] is False


def test_national_shared_url_cannot_bridge_unrelated_official_events():
    first = _item(1, "nws")
    second = _item(2, "nws")
    for item in (first, second):
        item["canonical_url"] = "https://weather.gov/alerts"
    first["evidence"]["nws_alert"] = {"id": "urn:alert:one"}
    second["evidence"]["nws_alert"] = {"id": "urn:alert:two"}
    assert [group["item_ids"] for group in correlate_national_items([
        first, second
    ])] == [[1], [2]]

    second["evidence"]["nws_alert"]["id"] = "urn:alert:one"
    assert correlate_national_items([first, second])[0]["item_ids"] == [1, 2]

    unrelated = _item(3, "public_media")
    unrelated["canonical_url"] = first["canonical_url"]
    unrelated["title"] = "Routine airport terminal renovation announcement"
    assert [group["item_ids"] for group in correlate_national_items([
        first, unrelated
    ])] == [[1], [3]]

    unrelated["title"] = first["title"]
    unrelated["evidence"]["national_identity"]["event_type"] = "weather_alert"
    assert [group["item_ids"] for group in correlate_national_items([
        first, unrelated
    ])] == [[1], [3]]


def test_national_scan_persists_correlation_without_http(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    fixture = Path(__file__).parent / "fixtures/news/national_nhtsa_recalls.json"
    config_path = tmp_path / "national.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        national: {{enabled: true}}
        news:
          enabled: true
          scopes:
            NATIONAL:
              enabled: true
              sources:
                - {{id: nhtsa_a, name: NHTSA A, kind: api_json, parser: nhtsa_recalls_json,
                   source_family: nhtsa, enabled: true, url: "file://{fixture}"}}
                - {{id: nhtsa_b, name: NHTSA B, kind: api_json, parser: nhtsa_recalls_json,
                   source_family: nhtsa, enabled: true, url: "file://{fixture}"}}
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] >= 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        clusters = conn.execute(
            "SELECT item_count, score, evidence_json FROM news_clusters WHERE scope = 'NATIONAL'"
        ).fetchall()
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope = 'NATIONAL'"
        ).fetchall()
    assert any(row["item_count"] == 2 for row in clusters)
    events = [json_loads(row["evidence_json"], {})["national_event"] for row in clusters]
    assert all(row["score"] == event["ranking"]["score"]
               for row, event in zip(clusters, events, strict=True))
    assert any(event["matches"][0]["basis"] == ["shared_official_event_id"]
               for event in events if event["matches"])
    assert all("national_event" in json_loads(row["evidence_json"], {}) for row in rows)
