from __future__ import annotations

import json
from pathlib import Path

from console1701.news.parsers import parse_fixture_items

FIXTURE = Path(__file__).parent / "fixtures/science/gcn_circular.json"
SOURCE = {
    "id": "gcn_circulars", "scope": "SYSTEM_SOLAR", "kind": "api_json",
    "parser": "gcn_circular_fixture", "fixture_only": True,
    "official_url": "https://gcn.nasa.gov/circulars",
    "url": f"file://{FIXTURE}",
}


def _status(subject: str) -> tuple[str, bool, str | None]:
    payload = json.loads(FIXTURE.read_text())
    payload["eventId"] = "GRB 260705A"
    payload["subject"] = subject
    evidence = parse_fixture_items(SOURCE, json.dumps(payload))[0]["evidence"]
    circular = evidence["gcn_circular"]
    return (
        circular["status"], circular["withdraws_event"],
        (evidence.get("science_identity") or {}).get("public_value_class"),
    )


def test_gcn_circular_retraction_scope_uses_explicit_subject_evidence():
    assert _status("GRB 260705A: Retraction of optical counterpart") == (
        "component_retraction", False, "background"
    )
    assert _status("GRB 260822A: Retraction of GOTO optical counterpart detection") == (
        "component_retraction", False, "background"
    )
    assert _status("LIGO/Virgo S191120aj: Retraction of GW compact binary merger candidate") == (
        "retracted", True, None
    )
    assert _status("Retraction: GRB 260705A") == ("retracted", True, None)
    assert _status("Retraction of GCN 43965: GRB is actually solar flare") == (
        "retraction_review", False, "background"
    )
    assert _status("GRB 130505A: correction to GCN 14575") == (
        "correction", False, None
    )
