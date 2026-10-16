from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import is_supported_official_source
from console1701.news.parsers import NewsParserError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/global_wmo_bom.rss"
SOURCE = {"scope": "GLOBAL", "kind": "rss", "parser": "wmo_bom_rss"}


def test_wmo_bom_rss_is_not_live_allowlisted():
    assert not is_supported_official_source({
        **SOURCE,
        "id": "wmo_bom_cap_rss",
        "url": "https://severeweather.wmo.int/v2/cap-alerts/au-bom-en/rss.xml",
        "enabled": True,
        "verification_status": "verified",
        "official_status": "official",
    })


def test_wmo_bom_feed_metadata_is_bounded_and_does_not_claim_cap_status():
    items = parse_fixture_items(SOURCE, FIXTURE.read_text())
    assert len(items) == 3
    assert all(item["evidence"]["wmo_bom_rss"]["issuer"] == (
        "Australian Government Bureau of Meteorology"
    ) for item in items)
    assert all(item["evidence"]["global_identity"]["public_value_class"] == (
        "background"
    ) for item in items)
    assert items[0]["evidence"]["wmo_bom_rss"]["warning_state"] == (
        "cap_status_unverified"
    )
    assert items[0]["evidence"]["wmo_bom_rss"]["cap_severity"] is None
    assert items[0]["evidence"]["wmo_bom_rss"]["affected_area"] is None
    assert items[1]["evidence"]["wmo_bom_rss"]["warning_state"] == "cancelled"
    assert all(item["url"].startswith(
        "https://severeweather.wmo.int/v2/cap-alerts/au-bom-en/"
    ) for item in items)


@pytest.mark.parametrize("old,new,error", [
    ("Latest Official Public alerts in English for Bureau of Meteorology",
     "Unrelated alert feed", "channel identity"),
    ("https://severeweather.wmo.int/v2/cap-alerts/au-bom-en/rss.xml",
     "https://example.org/feed.xml", "official feed identity"),
    ("https://severeweather.wmo.int/v2/cap-alerts/au-bom-en/2026/10/15/23/20/53-6e7317681378adeb0300cf6cad39545b.xml",
     "https://example.org/alert.xml", "official CAP URL"),
])
def test_wmo_bom_rejects_changed_source_identity(old, new, error):
    with pytest.raises(NewsParserError, match=error):
        parse_fixture_items(SOURCE, FIXTURE.read_text().replace(old, new))


def test_wmo_bom_offline_scan_persists_background_warning_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("WMO fixture attempted HTTP"))
    ))
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "global": {"enabled": True},
        "news": {"enabled": True, "scopes": {"GLOBAL": {"enabled": True,
            "sources": [{
                "id": "wmo_bom_cap_rss", "name": "BoM via WMO RSS fixture",
                "kind": "rss", "parser": "wmo_bom_rss",
                "source_family": "wmo", "official_status": "official",
                "enabled": True, "url": f"file://{FIXTURE}",
            }],
        }}},
    }))
    result = run_news_scan(path)
    assert result["status"] == "complete" and result["item_count"] == 3
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='GLOBAL'"
        ).fetchall()
    assert len(rows) == 3
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert all(item["global"]["event_type"] == "weather_warning" for item in evidence)
    assert all(item["global"]["affected_countries"] == [] for item in evidence)
    assert all(item["global_attention_policy"]["attention_state"] == "background"
               for item in evidence)
