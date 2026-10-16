from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.cdc_han import QUERY as CDC_QUERY
from console1701.news.cdc_han import SEARCH_URL as CDC_SEARCH_URL
from console1701.news.national_events import correlate_national_items, national_item_signature
from console1701.news.parsers import parse_fixture_items
from console1701.news.scanner import run_news_scan


def _item(item_id: int, family: str, *, state: str = "WA",
          published: str = "2026-10-15T12:00:00+00:00") -> dict:
    return {
        "id": item_id, "scope": "NATIONAL",
        "title": "Major regional airport ground stop disruption",
        "source_published_at": published, "first_seen_at": published,
        "evidence": {
            "source": {
                "source_family": family, "source_key": f"{family}_{item_id}",
                "official_status": "official" if family in {
                    "nws", "usgs", "nhtsa", "cpsc", "fema", "cisa", "faa",
                    "cdc", "bls", "noaa_nhc",
                } else "publisher",
            },
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


def test_national_source_ids_require_matching_source_family():
    cases = (
        ("usgs_earthquake", "usgs", {"id": "us1001"}, "usgs:us1001"),
        ("nws_alert", "nws", {"id": "urn:alert:one"}, "nws:urn:alert:one"),
        ("nhtsa_recall", "nhtsa", {"campaign_number": "26V123"},
         "nhtsa_campaign:26v123"),
        ("cpsc_recall", "cpsc", {"recall_id": "1234"}, "cpsc:1234"),
        ("openfema_declaration", "fema", {"declaration": "DR-4943-KS"},
         "fema:dr-4943-ks"),
        ("cisa_kev", "cisa", {"cve_id": "CVE-2026-1234"}, "cve:cve-2026-1234"),
        ("federal_register", "federal_register", {"document_number": "2026-00001"},
         "fr_document:2026-00001"),
        ("govinfo_publication", "govinfo", {"document_id": "BILLS-119hr1enr"},
         "govinfo_document:bills-119hr1enr"),
        ("cdc_han", "cdc", {"notice_id": "CDCHAN-00533"},
         "cdc_han:cdchan-00533"),
        ("bls_release", "bls", {"entry_id": "https://www.bls.gov/id/2026"},
         "bls:https://www.bls.gov/id/2026"),
        ("nhc_rss", "noaa_nhc", {"storm_id": "EP212026"}, "nhc:ep212026"),
    )
    for field, family, value, identifier in cases:
        first = _item(1, "public_media")
        second = _item(2, "public_media")
        for item in (first, second):
            item["evidence"][field] = value
        assert identifier not in national_item_signature(first)["identifiers"]
        assert [group["item_ids"] for group in correlate_national_items([
            first, second
        ])] == [[1], [2]]
        first["evidence"]["source"]["source_family"] = family
        assert identifier in national_item_signature(first)["identifiers"]


def test_national_nws_and_faa_geography_require_matching_source_family():
    row = _item(1, "public_media")
    row["evidence"]["national_identity"].update({
        "event_type": "", "affected_states": [], "affected_airports": [],
    })
    row["evidence"]["nws_alert"] = {"geocode": {"UGC": ["WAC033"]}}
    row["evidence"]["faa_nas_status"] = {"airport_code": "SEA"}
    signature = national_item_signature(row)
    assert signature["event_type"] == ""
    assert signature["affected_states"] == set()
    assert signature["affected_airports"] == set()

    row["evidence"]["source"]["source_family"] = "nws"
    signature = national_item_signature(row)
    assert signature["affected_states"] == {"wa"}
    assert signature["affected_airports"] == set()
    row["evidence"]["source"]["source_family"] = "faa"
    signature = national_item_signature(row)
    assert signature["affected_states"] == set()
    assert signature["affected_airports"] == {"sea"}


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
    first["evidence"]["source"] = {
        "source_family": "cpsc", "source_key": "cpsc_a", "official_status": "official"
    }
    revision = deepcopy(first)
    revision["id"] = 2
    revision["url"] = revision["canonical_url"] = (
        "https://www.cpsc.gov/Recalls/2026/updated-recall-page"
    )
    revision["evidence"]["source"] = {
        "source_family": "cpsc", "source_key": "cpsc_b", "official_status": "official"
    }
    revision["evidence"].pop("national_identity")  # Earlier stored rows lack this contract.
    other = {**parsed[1], "id": 3}
    other["evidence"]["source"] = {
        "source_family": "cpsc", "source_key": "cpsc_c", "official_status": "official"
    }
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
    first["evidence"]["source"] = {
        "source_family": "fema", "source_key": "fema_a", "official_status": "official"
    }
    revision = deepcopy(first)
    revision["id"] = 2
    revision["url"] = revision["canonical_url"] = "https://www.fema.gov/disaster/4943/revision"
    revision["evidence"]["source"] = {
        "source_family": "fema", "source_key": "fema_b", "official_status": "official"
    }
    revision["evidence"].pop("national_identity")
    other = {**parsed[1], "id": 3}
    other["evidence"]["source"] = {
        "source_family": "fema", "source_key": "fema_c", "official_status": "official"
    }
    groups = correlate_national_items([first, revision, other])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3]]
    assert groups[0]["matches"][0]["basis"] == ["shared_official_event_id"]
    assert groups[0]["identifiers"] == ["fema:dr-4943-ks"]
    assert groups[0]["corroborated"] is False


def test_cdc_han_notice_identity_requires_its_parser_family_and_official_source():
    fixture = Path(__file__).parent / "fixtures/national/cdc_han_search_2026_10_15.json"
    source = {
        "id": "cdc_han_notices", "scope": "NATIONAL", "kind": "api_json",
        "parser": "cdc_han_search_fixture", "source_family": "cdc",
        "official_status": "official", "official_url": CDC_SEARCH_URL,
        "url": fixture.resolve().as_uri(), "query_contract": CDC_QUERY,
    }
    parsed = parse_fixture_items(source, fixture.read_text())
    first = {**parsed[0], "id": 1}
    first["evidence"]["source"] = {
        "source_family": "cdc", "source_key": "cdc_han_notices",
        "official_status": "official",
    }
    revision = deepcopy(first)
    revision["id"] = 2
    revision["title"] = "Updated notice title from the same CDC identifier"
    other = {**parsed[1], "id": 3}
    other["evidence"]["source"] = first["evidence"]["source"]
    other["canonical_url"] = first["canonical_url"]
    other["title"] = first["title"]
    groups = correlate_national_items([first, revision, other])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3]]
    assert groups[0]["matches"][0]["basis"] == ["shared_official_event_id"]
    assert groups[0]["corroborated"] is False

    foreign = deepcopy(revision)
    foreign["evidence"]["source"] = {
        "source_family": "public_media", "source_key": "publisher",
        "official_status": "publisher",
    }
    foreign["canonical_url"] = "https://publisher.example/notice-coverage"
    assert national_item_signature(foreign)["identifiers"] == set()
    assert [group["item_ids"] for group in correlate_national_items([first, foreign])] == [
        [1], [2]
    ]


def test_national_syndicated_article_does_not_count_as_independent_confirmation():
    first = _item(1, "publisher_one")
    second = _item(2, "publisher_two")
    first["canonical_url"] = "https://wire.example/story/123"
    second["canonical_url"] = "https://wire.example/story/123"
    group = correlate_national_items([first, second])[0]
    assert group["item_ids"] == [1, 2]
    assert group["matches"][0]["basis"] == ["same_article_url"]
    assert group["corroborated"] is False


def test_national_shared_url_and_syndication_require_nearby_publication():
    first = _item(1, "faa")
    later = _item(2, "faa", published="2026-10-01T12:00:00+00:00")
    for item in (first, later):
        item["canonical_url"] = "https://www.faa.gov/airport-status/SEA"
        item["evidence"]["faa_nas_status"] = {"airport_code": "SEA"}
    assert [group["item_ids"] for group in correlate_national_items([
        first, later
    ])] == [[1], [2]]

    near = deepcopy(later)
    near["source_published_at"] = "2026-10-14T12:00:00+00:00"
    assert [group["item_ids"] for group in correlate_national_items([
        first, near
    ])] == [[1], [2]]

    article = _item(5, "publisher_one")
    article_copy = _item(6, "publisher_two", published="2026-10-14T12:00:00+00:00")
    for item in (article, article_copy):
        item["canonical_url"] = "https://wire.example/story/nearby"
    assert correlate_national_items([article, article_copy])[0]["matches"][0][
        "basis"
    ] == ["same_article_url"]

    old_article_copy = deepcopy(article_copy)
    old_article_copy["source_published_at"] = "2026-10-01T12:00:00+00:00"
    assert [group["item_ids"] for group in correlate_national_items([
        article, old_article_copy
    ])] == [[5], [6]]
    for item in (article, article_copy, old_article_copy):
        item["canonical_url"] = f"https://publisher.example/story/{item['id']}"
        item["evidence"]["national_identity"]["syndication_id"] = "wire-123"
    assert [group["item_ids"] for group in correlate_national_items([
        article, old_article_copy
    ])] == [[5], [6]]
    assert correlate_national_items([article, article_copy])[0]["matches"][0]["basis"] == [
        "same_syndication_id"
    ]

    official = _item(3, "nws")
    old_revision = _item(4, "nws", published="2026-10-01T12:00:00+00:00")
    for item in (official, old_revision):
        item["evidence"]["nws_alert"] = {"id": "urn:alert:long-lived"}
    assert correlate_national_items([official, old_revision])[0]["matches"][0][
        "basis"
    ] == ["shared_official_event_id"]


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
                   source_family: nhtsa, official_status: official,
                   enabled: true, url: "file://{fixture}"}}
                - {{id: nhtsa_b, name: NHTSA B, kind: api_json, parser: nhtsa_recalls_json,
                   source_family: nhtsa, official_status: official,
                   enabled: true, url: "file://{fixture}"}}
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
