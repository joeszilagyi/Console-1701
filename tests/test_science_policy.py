from __future__ import annotations

from console1701.news.science_policy import classify_science_item


def _item(title, *, description="", scope="SYSTEM_SOLAR"):
    return {"scope": scope, "title": title, "description": description,
            "evidence": {"science_identity": {"mission": "SPHEREx"}}}


def test_explicit_alien_ufo_and_social_rumor_claims_are_dropped_before_storage():
    source = {"scope": "SYSTEM_SOLAR"}
    for title in (
        "NASA confirms aliens on Mars",
        "Alien life discovered near Jupiter",
        "Life found on Mars",
        "UFO sighting proves new space discovery",
        "Unverified claim about exoplanet signal",
    ):
        assert classify_science_item(source, _item(title)) is None


def test_explainer_and_sensational_language_get_background_evidence():
    source = {"scope": "SYSTEM_SOLAR"}
    original = _item("Shocking image: what is a brown dwarf?")
    output = classify_science_item(source, original)
    assert output is not None
    assert output["evidence"]["science_identity"]["public_value_class"] == "background"
    assert output["evidence"]["science_safety"]["attention_state"] == "background"
    assert len(output["evidence"]["science_safety"]["reasons"]) >= 2
    assert "public_value_class" not in original["evidence"]["science_identity"]


def test_science_policy_leaves_other_scope_and_legitimate_science_title_alone():
    source = {"scope": "SYSTEM_SOLAR"}
    legitimate = classify_science_item(source, _item("New exoplanet atmosphere spectrum"))
    assert legitimate is not None
    assert legitimate["evidence"]["science_safety"]["attention_state"] == "eligible"
    other = _item("UFO report", scope="GLOBAL")
    assert classify_science_item(source, other) is other


def test_archive_update_and_unreviewed_preprint_are_background_not_discoveries():
    source = {"scope": "SYSTEM_SOLAR"}
    archive = _item("Exoplanet Archive parameter update: TOI-4567 b")
    archive["tags"] = ["official", "archive_metadata"]
    archive["evidence"]["exoplanet_archive"] = {
        "date_semantics": "parameter_update_not_discovery_date"
    }
    labeled = classify_science_item(source, archive)
    assert labeled is not None
    assert labeled["evidence"]["science_safety"]["attention_state"] == "background"
    assert "archive metadata update" in " ".join(
        labeled["evidence"]["science_safety"]["reasons"]
    )
    assert archive["evidence"]["science_identity"] == {"mission": "SPHEREx"}
    preprint = classify_science_item(source, _item("Unreviewed preprint claims new cosmic signal"))
    assert preprint is not None
    assert preprint["evidence"]["science_safety"]["attention_state"] == "background"
