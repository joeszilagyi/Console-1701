from __future__ import annotations

from console1701.news.science_events import correlate_science_items


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


def test_just_a_shared_mission_or_planet_does_not_merge_unrelated_releases():
    items = [
        _item(1, "Webb finds water on planet K2", "esa_webb", identity={"mission": "JWST"}),
        _item(2, "Webb maps dust around star Vela", "nasa_webb", identity={"mission": "JWST"}),
        _item(3, "Exoplanet Archive parameter update: K2", "nasa_exoplanet",
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
        _item(1, "MAST data 123", "nasa_mast", extra={"mast_caom": shared}),
        _item(2, "PDS data 123", "nasa_pds", extra={"pds_collection": {
            "collection_lid": "123"}}),
        _item(3, "MAST data 123", "nasa_mast", extra={"mast_caom": shared}),
    ]
    items.append({**items[0], "id": 4, "scope": "ORBITAL"})
    assert [group["item_ids"] for group in correlate_science_items(items)] == [[1, 3], [2]]
