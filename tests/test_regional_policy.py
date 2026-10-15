from __future__ import annotations

from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.regional_policy import apply_regional_privacy_policy
from console1701.news.scanner import run_news_scan


def _item(title, description=""):
    return {"scope": "REGIONAL", "title": title, "description": description,
            "tags": [], "evidence": {"headline_location": title}}


def test_regional_private_address_redacted_from_text_and_evidence():
    source = {"scope": "REGIONAL", "source_family": "regional_news"}
    original = _item("Routine call at 123 Main Street", "Near 456 N Pine Ave Apt 2")
    result = apply_regional_privacy_policy(source, original)
    assert "123 Main" not in result["title"]
    assert "456 N Pine" not in result["description"]
    assert "123 Main" not in str(result["evidence"])
    assert result["evidence"]["privacy"]["redaction_applied"] is True
    assert result["evidence"]["privacy"]["low_acuity_private"] is True
    assert "123 Main Street" in original["title"]  # Input was not mutated.


def test_low_value_outage_and_social_report_stay_background_without_verified_impact():
    outage = apply_regional_privacy_policy(
        {"scope": "REGIONAL", "source_family": "utility"},
        _item("Isolated residential outage in one neighborhood"),
    )
    assert outage["evidence"]["privacy"]["residential_outage_below_threshold"] is True
    assert outage["evidence"]["privacy"]["attention_state"] == "background"
    social = apply_regional_privacy_policy(
        {"scope": "REGIONAL", "source_family": "reddit"},
        _item("People discuss a reported outage"),
    )
    assert social["evidence"]["privacy"]["low_acuity_private"] is True


def test_official_impact_metadata_overrides_low_value_headline_penalty():
    item = _item("Residential outage in several blocks")
    item["evidence"]["nws_alert"] = {"ranking": {"total_alert_weight": 30}}
    result = apply_regional_privacy_policy(
        {"scope": "REGIONAL", "source_family": "nws"}, item,
    )
    assert result["evidence"]["privacy"]["low_acuity_private"] is False
    assert result["evidence"]["privacy"]["public_impact_basis"] == "official_alert_metadata"


def test_scan_redacts_regional_address_before_sqlite_storage(tmp_path):
    feed = tmp_path / "regional.rss"
    feed.write_text(dedent("""
        <rss version="2.0"><channel><title>Regional News</title>
        <item><title>Routine report at 123 Main Street</title>
        <link>https://example.org/regional/report-1</link>
        <description>Minor incident near 456 Pine Avenue.</description>
        <pubDate>Thu, 15 Oct 2026 12:00:00 GMT</pubDate></item>
        </channel></rss>
    """).strip())
    config_path = tmp_path / "config.yml"
    config_path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        news:
          enabled: true
          scopes:
            REGIONAL:
              enabled: true
              sources:
                - id: regional_news_rss
                  enabled: true
                  url: "file://{feed}"
    """).strip() + "\n")
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute("SELECT title, description, evidence_json FROM news_items").fetchone()
    evidence = json_loads(row["evidence_json"], {})
    assert "123 Main" not in row["title"]
    assert "456 Pine" not in row["description"]
    assert "123 Main" not in row["evidence_json"]
    assert evidence["privacy"]["low_acuity_private"] is True
    assert evidence["ranking"]["factors"]["regional_privacy_penalty"] == -20
