from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.fsis_recalls import FSIS_API_URL
from console1701.news.national_events import correlate_national_items, national_item_signature
from console1701.news.national_policy import classify_national_item
from console1701.news.national_registry import get_national_source_registry_entry
from console1701.news.official_http import is_supported_official_source
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/national/fsis_recalls_observed.json"


def _source():
    return {
        "id": "fsis_recall_api", "scope": "NATIONAL", "kind": "api_json",
        "parser": "fsis_recalls_json", "fixture_only": True,
        "url": FSIS_API_URL, "source_family": "fsis", "official_status": "official",
    }


def test_fsis_fixture_preserves_current_notice_identity_and_distribution():
    registry = get_national_source_registry_entry("fsis_recall_api")
    assert registry is not None
    assert registry["parser"] == "fsis_recalls_json"
    assert registry["enabled"] is False
    assert is_supported_official_source({
        **_source(), "verification_status": "verified", "fixture_only": False,
    }) is False
    items = parse_fixture_items(_source(), FIXTURE.read_text())
    assert len(items) == 3
    first = items[0]["evidence"]["fsis_recall"]
    assert first["recall_number"] == "PHA-10062026-01"
    assert first["recall_classification"] == "Public Health Alert"
    assert first["risk_level"] == "Public Health Alert"
    assert first["distribution_state_labels"] == [
        "Alabama", "Florida", "Georgia", "Maryland", "Texas"
    ]
    assert first["active_notice"] is True
    assert first["public_instruction_url"] == items[0]["url"]
    assert first["detail_url_verified"] is True
    assert first["instruction_content_parsed"] is False
    assert first["summary_html_stored"] is False
    assert "Fixture narrative" not in str(items)
    assert "Private contact" not in str(items)
    assert items[0]["evidence"]["national_identity"]["official_event_ids"] == [
        "fsis:pha-10062026-01"
    ]
    assert items[0]["evidence"]["national_identity"]["multi_state_impact"] is False
    assert items[0]["evidence"]["national_identity"]["multi_state_distribution"] is True
    assert items[1]["evidence"]["fsis_recall"]["current_notice"] is True
    assert items[2]["evidence"]["fsis_recall"]["archive_recall"] is True
    assert items[2]["evidence"]["fsis_recall"]["establishment_names"] == [
        "Suzanna's Kitchen Inc"
    ]


def test_fsis_class_i_receives_source_classified_attention():
    source = _source()
    first, second, closed = parse_fixture_items(source, FIXTURE.read_text())
    assert classify_national_item(source, first)["attention_state"] == "elevated"
    assert classify_national_item(source, second)["attention_state"] == "elevated"
    assert classify_national_item(source, closed)["attention_state"] != "elevated"


@pytest.mark.parametrize(("field", "value"), [
    ("field_recall_number", ""),
    ("field_recall_number", "wrong-id"),
    ("field_recall_date", "wrong-date"),
    ("field_risk_level", "Critical"),
    ("field_recall_classification", "Class IV"),
    ("field_states", ["Florida", "<script>bad</script>"]),
    ("field_recall_url", "https://example.org/recalls-alerts/fake"),
    ("field_recall_number_export", "999-2026"),
])
def test_fsis_rejects_invalid_identity_and_classification(field, value):
    rows = json.loads(FIXTURE.read_text())
    rows[0][field] = value
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), json.dumps(rows))


def test_fsis_rejects_duplicate_conflicting_and_unbounded_rows():
    rows = json.loads(FIXTURE.read_text())
    with pytest.raises(NewsParserError, match="stable recall identity"):
        parse_fixture_items(_source(), json.dumps([rows[0], rows[0]]))
    rows[2]["field_active_notice"] = "True"
    conflicting = parse_fixture_items(_source(), json.dumps(rows))[2]
    assert conflicting["evidence"]["fsis_recall"]["lifecycle_conflict"] is True
    assert conflicting["evidence"]["national_identity"]["high_risk_recall"] is False
    with pytest.raises(NewsParserError, match="at most 50"):
        parse_fixture_items(_source(), json.dumps([rows[1]] * 51))
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 262_145)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "{")


def test_fsis_uses_recall_type_when_active_notice_banner_is_false():
    rows = json.loads(FIXTURE.read_text())
    rows[1]["field_active_notice"] = "False"
    item = parse_fixture_items(_source(), json.dumps([rows[1]]))[0]
    assert item["evidence"]["fsis_recall"]["current_notice"] is True
    assert item["evidence"]["national_identity"]["high_risk_recall"] is True


def test_fsis_combined_number_and_repeated_state_labels():
    rows = json.loads(FIXTURE.read_text())
    rows[1]["field_recall_number"] = "019-020-2026"
    rows[1]["field_recall_number_export"] = "019-020-2026"
    rows[1]["field_recall_url"] = (
        "http://www.fsis.usda.gov/recalls-alerts/prime-line-distributors-inc--and-ferrarini-"
        "usa-inc--recall-imported-ready-eat-pork"
    )
    rows[1]["field_states"] = ["Texas", "Florida", "Texas"]
    item = parse_fixture_items(_source(), json.dumps([rows[1]]))[0]
    assert item["evidence"]["national_identity"]["official_event_ids"] == [
        "fsis:019-020-2026"
    ]
    assert item["evidence"]["fsis_recall"]["distribution_state_labels"] == [
        "Texas", "Florida"
    ]


def test_fsis_expanded_recall_number_from_observed_2026_snapshot():
    rows = json.loads(FIXTURE.read_text())
    rows[1]["field_recall_number"] = "005-2026-EXP"
    rows[1]["field_recall_number_export"] = "005-2026-EXP"
    rows[1]["field_recall_url"] = (
        "http://www.fsis.usda.gov/recalls-alerts/ajinomoto-foods-north-america-inc--expands-"
        "recall-chicken-and-pork-fried-rice-ramen"
    )
    item = parse_fixture_items(_source(), json.dumps([rows[1]]))[0]
    assert item["evidence"]["national_identity"]["official_event_ids"] == [
        "fsis:005-2026-exp"
    ]


def _expansion_pair_rows():
    # Identity, titles and notice URLs follow the observed exact-number API
    # responses; unrelated metadata is borrowed from the existing test row.
    template = json.loads(FIXTURE.read_text())[2]
    original = deepcopy(template)
    original.update({
        "field_recall_number": "005-2026",
        "field_recall_number_export": "005-2026",
        "field_recall_date": "2026-02-19",
        "field_last_modified_date": "2026-02-19",
        "field_title": (
            "Ajinomoto Foods North America, Inc. Recalls Chicken Fried Rice Products "
            "Due to Possible Foreign Matter Contamination"
        ),
        "field_recall_url": (
            "http://www.fsis.usda.gov/recalls-alerts/ajinomoto-foods-north-america-"
            "inc--recalls-chicken-fried-rice-products-due-0"
        ),
    })
    expansion = deepcopy(template)
    expansion.update({
        "field_recall_number": "005-2026-EXP",
        "field_recall_number_export": "005-2026-EXP",
        "field_recall_date": "2026-03-03",
        "field_last_modified_date": "2026-04-15",
        "field_title": (
            "Ajinomoto Foods North America, Inc. Expands Recall for Chicken and Pork "
            "Fried Rice, Ramen, and Shu Mai Products Due to Possible Foreign Matter "
            "Contamination"
        ),
        "field_recall_url": (
            "http://www.fsis.usda.gov/recalls-alerts/ajinomoto-foods-north-america-"
            "inc--expands-recall-chicken-and-pork-fried-rice-ramen"
        ),
    })
    other = deepcopy(original)
    other["field_recall_number"] = other["field_recall_number_export"] = "006-2026"
    other["field_recall_url"] = "http://www.fsis.usda.gov/recalls-alerts/other-recall"
    return [original, expansion, other]


def test_fsis_expansion_joins_original_without_false_corroboration():
    parsed = parse_fixture_items(_source(), json.dumps(_expansion_pair_rows()))
    rows = [{**item, "id": index} for index, item in enumerate(parsed, 1)]
    for item in rows:
        item["evidence"]["source"] = {
            "source_family": "fsis", "source_key": "fsis_recall_api",
            "official_status": "official",
        }
    assert len({item["url"] for item in rows}) == 3
    groups = correlate_national_items(rows)
    assert [group["item_ids"] for group in groups] == [[1, 2], [3]]
    assert groups[0]["matches"][0]["basis"] == ["same_fsis_recall_series"]
    assert groups[0]["identifiers"] == ["fsis:005-2026", "fsis:005-2026-exp"]
    assert groups[0]["corroborated"] is False

    spoof = deepcopy(rows[1])
    spoof["evidence"]["source"]["source_family"] = "public_media"
    assert national_item_signature(spoof)["fsis_recall_number"] == ""
    assert [group["item_ids"] for group in correlate_national_items([rows[0], spoof])] == [
        [1], [2]
    ]
    extra_id = deepcopy(rows[1])
    extra_id["evidence"]["national_identity"]["official_event_ids"].append("fsis:006-2026")
    assert [group["item_ids"] for group in correlate_national_items([rows[0], extra_id])] == [
        [1], [2]
    ]


def test_fsis_expansion_scan_persists_one_event_and_two_notices(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected HTTP")),
    )
    fixture = tmp_path / "fsis-expansion.json"
    fixture.write_text(json.dumps(_expansion_pair_rows()[:2]))
    config_path = tmp_path / "fsis-expansion.yml"
    config_path.write_text(f"""
paths: {{repo_roots: [], explicit_repos: []}}
news:
  enabled: true
  scopes:
    NATIONAL:
      enabled: true
      sources:
        - id: fsis_recall_api
          enabled: true
          fixture_only: true
          retention_days: 365
          url: "{fixture.as_uri()}"
""".strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 2
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        notices = conn.execute(
            "SELECT canonical_url FROM news_items WHERE scope='NATIONAL'"
        ).fetchall()
        clusters = conn.execute(
            "SELECT item_count, evidence_json FROM news_clusters WHERE scope='NATIONAL'"
        ).fetchall()
    assert len({row["canonical_url"] for row in notices}) == 2
    assert len(clusters) == 1
    assert clusters[0]["item_count"] == 2
    event = json_loads(clusters[0]["evidence_json"], {})["national_event"]
    assert event["matches"][0]["basis"] == ["same_fsis_recall_series"]
    assert event["corroborated"] is False


def test_fsis_skips_spanish_translation_of_one_recall():
    rows = json.loads(FIXTURE.read_text())
    spanish = dict(rows[0], langcode="Spanish")
    assert len(parse_fixture_items(_source(), json.dumps([rows[0], spanish]))) == 1


def test_fsis_requires_exact_fixture_only_source():
    raw = FIXTURE.read_text()
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items({**_source(), "fixture_only": False}, raw)
    with pytest.raises(NewsParserError, match="fixture-only"):
        parse_fixture_items({**_source(), "url": "https://example.org/recalls"}, raw)
    with pytest.raises(NewsParserError, match="exact NATIONAL"):
        parse_fixture_items({**_source(), "id": "other"}, raw)


def test_fsis_fixture_scan_is_offline_and_keeps_separate_recalls(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("unexpected HTTP")),
    )
    config_path = tmp_path / "fsis.yml"
    config_path.write_text(f"""
paths: {{repo_roots: [], explicit_repos: []}}
news:
  enabled: true
  scopes:
    NATIONAL:
      enabled: true
      sources:
        - id: fsis_recall_api
          enabled: true
          fixture_only: true
          retention_days: 365
          url: "{FIXTURE.resolve().as_uri()}"
""".strip() + "\n")
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT canonical_url, evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchall()
    assert result["item_count"] == len(rows) == 3
    assert len({row["canonical_url"] for row in rows}) == 3
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert all(row["fsis_recall"]["public_instruction_url"] for row in evidence)
    assert all(row["ingest"]["fixture_only"] is True for row in evidence)
    assert all("public_impact_score" not in row["national_identity"] for row in evidence)
    class_i = next(row for row in evidence if row["fsis_recall"]["current_notice"]
                   and row["fsis_recall"]["recall_classification"] == "Class I")
    assert class_i["national_event"]["ranking"]["factors"][
        "official_severity_score"
    ] == 25
    assert class_i["national_event"]["ranking"]["factors"][
        "public_impact_score"
    ] == 25
    assert "Fixture narrative" not in str([dict(row) for row in rows])
