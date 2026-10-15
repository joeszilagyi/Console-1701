from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from console1701 import config as config_module
from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.cisa_advisories import CISA_ADVISORIES_RSS_URL
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/national_cisa_advisories.rss"


def _source():
    return {
        "id": "cisa_advisories", "name": "CISA advisories", "scope": "NATIONAL",
        "kind": "rss", "parser": "cisa_advisories_rss", "source_family": "cisa",
        "official_status": "official", "official_url": CISA_ADVISORIES_RSS_URL,
        "url": f"file://{FIXTURE}",
    }


def test_cisa_advisory_fixture_keeps_metadata_without_body_or_kev_noise():
    items = parse_fixture_items(_source(), FIXTURE.read_text())
    assert len(items) == 6
    kinds = {item["evidence"]["cisa_advisory"]["kind"] for item in items}
    assert kinds == {
        "cybersecurity_advisory", "ics_medical_advisory",
        "cyber_alert", "emergency_directive", "ics_advisory", "cyber_bulletin",
    }
    ics = next(item for item in items if "Thermo Fisher" in item["title"])
    evidence = ics["evidence"]["cisa_advisory"]
    assert evidence["advisory_id"] == "icsma-26-288-01"
    assert evidence["cve_ids"] == ["CVE-2026-107777"]
    assert evidence["highest_cvss_score"] == 6.5
    assert evidence["highest_cvss_severity"] == "MEDIUM"
    assert evidence["infrastructure_sector"] == "Healthcare and Public Health"
    assert evidence["mitigation_url"] == ics["url"]
    assert evidence["body_stored"] is False
    assert ics["description"] is None
    directive = next(item for item in items if "Emergency Directive" in item["title"])
    assert directive["evidence"]["national_identity"]["cyber_emergency_directive"] is True
    assert not any("Known Exploited Vulnerability to Catalog" in item["title"] for item in items)


@pytest.mark.parametrize("change", [
    {"id": "cisa_private"}, {"scope": "GLOBAL"},
    {"official_url": "https://example.test/all.xml"},
])
def test_cisa_advisory_fixture_rejects_wrong_source(change):
    with pytest.raises(NewsParserError):
        parse_fixture_items({**_source(), **change}, FIXTURE.read_text())


def test_cisa_advisory_fixture_rejects_malformed_oversized_and_spoofed_xml():
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "<rss>")
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), "<!DOCTYPE rss><rss></rss>")
    with pytest.raises(PayloadTooLargeError):
        parse_fixture_items(_source(), " " * 2_097_153)
    spoof = FIXTURE.read_text().replace("www.cisa.gov", "example.test", 1)
    with pytest.raises(NewsParserError):
        parse_fixture_items(_source(), spoof)


def test_cisa_advisory_fixture_scans_offline_with_rank_and_identity(tmp_path, monkeypatch):
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "national": {"enabled": True},
        "news": {"enabled": True, "scopes": {"NATIONAL": {
            "enabled": True, "sources": [{**_source(), "enabled": True}],
        }}},
    }))
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("CISA fixture attempted HTTP"))
    ))
    result = run_news_scan(path)
    assert result["item_count"] == 6
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT title, evidence_json FROM news_items WHERE scope='NATIONAL'"
        ).fetchall()
    assert len(rows) == 6
    assert all(json_loads(row["evidence_json"], {})["ingest"]["fixture_only"] for row in rows)
    directive = next(row for row in rows if "Emergency Directive" in row["title"])
    stored = json_loads(directive["evidence_json"], {})
    assert stored["national"]["attention_state"] == "elevated"
    assert stored["national_event"]["ranking"]["factors"]["official_severity_score"] >= 30
    assert "Actions to Take" not in str(stored)
