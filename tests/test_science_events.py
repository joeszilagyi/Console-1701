from __future__ import annotations

import json
from pathlib import Path

from console1701.news.parsers import parse_fixture_items
from console1701.news.science_events import correlate_science_items, science_item_signature


def _item(item_id, title, family, *, kind="science_release", when="2026-10-15T12:00:00Z",
          identity=None, extra=None):
    evidence = {"source": {"source_family": family, "source_key": f"{family}_source"},
                "science_identity": {"event_type": kind, **(identity or {})}}
    evidence.update(extra or {})
    return {"id": item_id, "scope": "SYSTEM_SOLAR", "title": title,
            "source_published_at": when, "evidence": evidence}


def test_shared_gcn_event_groups_preliminary_and_retraction_without_false_corroboration():
    first = _item(1, "GCN GRB 261015A initial", "nasa_gcn", extra={
        "gcn_notice": {"event_name": "GRB 261015A", "mission": "Swift"}})
    retract = _item(2, "GCN GRB 261015A retraction", "nasa_gcn", extra={
        "gcn_notice": {"event_name": "GRB 261015A", "mission": "Swift"}})
    groups = correlate_science_items([first, retract])
    assert len(groups) == 1
    assert groups[0]["item_ids"] == [1, 2]
    assert groups[0]["corroborated"] is False
    assert "gcn_event:grb 261015a" in groups[0]["identifiers"]


def test_gcn_circular_correlates_by_event_but_not_by_a_shared_source_family():
    notice = _item(1, "GCN GRB 261015A initial", "gcn", extra={
        "gcn_notice": {"event_name": "GRB 261015A"}})
    circular = _item(2, "GRB 261015A: optical follow-up", "gcn", extra={
        "gcn_circular": {"circular_id": 33603, "event_id": "GRB 261015A"}})
    unrelated = _item(3, "GRB 261015B: optical follow-up", "gcn", extra={
        "gcn_circular": {"circular_id": 33604, "event_id": "GRB 261015B"}})
    groups = correlate_science_items([notice, circular, unrelated])
    assert [group["item_ids"] for group in groups] == [[1, 2], [3]]
    assert groups[0]["corroborated"] is False


def test_gcn_circular_correction_cannot_bridge_conflicting_event_ids():
    fixture = Path(__file__).parent / "fixtures/science/gcn_circular.json"
    source = {
        "id": "gcn_circulars", "scope": "SYSTEM_SOLAR", "kind": "api_json",
        "parser": "gcn_circular_fixture", "fixture_only": True,
        "official_url": "https://gcn.nasa.gov/circulars",
        "url": fixture.resolve().as_uri(),
    }
    original_payload = json.loads(fixture.read_text())
    corrected_payload = dict(original_payload, eventId="GRB 230410B",
                             subject="GRB 230410B: Fermi GBM Final Real-time Localization")
    follow_up_payload = dict(original_payload, circularId=33604,
                             subject="GRB 230410A: Fermi GBM Follow-up Localization")
    items = [
        {**parse_fixture_items(source, json.dumps(payload))[0], "id": index}
        for index, payload in enumerate(
            (original_payload, corrected_payload, follow_up_payload), start=1
        )
    ]
    for item in items:
        item["evidence"]["source"] = {
            "source_family": "gcn", "source_key": "gcn_circulars",
        }
    groups = correlate_science_items(items)
    assert [group["item_ids"] for group in groups] == [[1, 3], [2]]
    assert groups[0]["matches"][0]["basis"] == [
        "event_kind", "shared_event_id", "time_window",
    ]
    assert groups[0]["corroborated"] is False


def test_science_parser_ids_require_matching_source_family():
    cases = (
        ("gcn_notice", "gcn", {"event_name": "GRB 261015A"}, "gcn_event:"),
        ("gcn_circular", "gcn", {"circular_id": 33603}, "gcn_circular:"),
        ("exoplanet_archive", "nasa_exoplanet_archive",
         {"planet_name": "Kepler-1 b"}, "planet:"),
        ("mast_caom", "mast", {"observation_id": "obs-123"}, "mast_observation:"),
        ("pds_collection", "nasa_pds", {"collection_lid": "urn:nasa:pds:test"},
         "pds_collection:"),
    )
    for field, family, value, prefix in cases:
        row = _item(1, "Same science item", "public_media", extra={field: value})
        signature = science_item_signature(row)
        assert not any(identifier.startswith(prefix) for identifier in signature[
            "identifiers"
        ])
        assert signature["kind"] == "science_release"
        row["evidence"]["source"]["source_family"] = family
        qualified = science_item_signature(row)
        assert any(identifier.startswith(prefix) for identifier in qualified[
            "identifiers"
        ])
        assert qualified["kind"] != "science_release"


def test_just_a_shared_mission_or_planet_does_not_merge_unrelated_releases():
    items = [
        _item(1, "Webb finds water on planet K2", "esa_webb", identity={"mission": "JWST"}),
        _item(2, "Webb maps dust around star Vela", "nasa_webb", identity={"mission": "JWST"}),
        _item(3, "Exoplanet Archive parameter update: K2", "nasa_exoplanet_archive",
              extra={"exoplanet_archive": {"planet_name": "K2"}}),
    ]
    assert [group["item_ids"] for group in correlate_science_items(items)] == [[1], [2], [3]]


def test_independent_matching_requires_context_tokens_and_complete_link():
    items = [
        _item(1, "Europa Clipper observes new ice plume", "nasa_jpl",
              identity={"mission": "Europa Clipper"}),
        _item(2, "Europa Clipper observes new ice plume", "esa_science",
              identity={"mission": "Europa Clipper"}),
        _item(3, "Europa Clipper observes new ice plume", "esa_science",
              identity={"mission": "Europa Clipper"}, when="2026-11-15T12:00:00Z"),
    ]
    groups = correlate_science_items(items)
    assert [group["item_ids"] for group in groups] == [[1, 2], [3]]
    assert groups[0]["corroborated"] is True
    assert "independent_family" in groups[0]["matches"][0]["basis"]


def test_different_event_kinds_and_scope_remain_separate():
    shared = {"dataset_id": "123"}
    items = [
        _item(1, "MAST data 123", "mast", extra={"mast_caom": shared}),
        _item(2, "PDS data 123", "nasa_pds", extra={"pds_collection": {
            "collection_lid": "123"}}),
        _item(3, "MAST data 123", "mast", extra={"mast_caom": shared}),
    ]
    items.append({**items[0], "id": 4, "scope": "ORBITAL"})
    assert [group["item_ids"] for group in correlate_science_items(items)] == [[1, 3], [2]]
