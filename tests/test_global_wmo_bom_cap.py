from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.global_events import correlate_global_items
from console1701.news.global_ranking import rank_global_event
from console1701.news.official_http import is_supported_official_source
from console1701.news.parsers import NewsParserError, PayloadTooLargeError, parse_fixture_items
from console1701.news.scanner import run_news_scan

FIXTURE = Path(__file__).parent / "fixtures/news/global_wmo_bom_cap.xml"
RSS = Path(__file__).parent / "fixtures/news/global_wmo_bom.rss"
CAP_URL = (
    "https://severeweather.wmo.int/v2/cap-alerts/au-bom-en/"
    "2026/10/15/23/20/53-6e7317681378adeb0300cf6cad39545b.xml"
)
SOURCE = {
    "id": "wmo_bom_cap_fixture", "scope": "GLOBAL", "kind": "rss",
    "parser": "wmo_bom_cap_xml", "official_url": CAP_URL,
}


def _severe_xml(raw: str, *, current: bool = False) -> str:
    text = raw.replace("<urgency>Unknown</urgency>", "<urgency>Expected</urgency>", 1)
    text = text.replace("<severity>Moderate</severity>", "<severity>Severe</severity>", 1)
    text = text.replace("<certainty>Unknown</certainty>", "<certainty>Likely</certainty>", 1)
    if current:
        now = datetime.now(UTC)
        text = text.replace(
            "2026-10-15T23:19:00+00:00",
            (now - timedelta(hours=1)).isoformat(timespec="seconds"),
        ).replace(
            "2026-10-17T13:00:00+00:00",
            (now + timedelta(hours=6)).isoformat(timespec="seconds"),
        ).replace(
            "2026-10-15T23:20:53+00:00",
            (now - timedelta(minutes=30)).isoformat(timespec="seconds"),
        )
    return text


def _rank(item: dict, now: str = "2026-10-16T01:00:00+00:00") -> dict:
    item["id"] = 1
    item["evidence"]["source"] = {
        "source_family": "wmo", "official_status": "official",
    }
    return rank_global_event({
        "families": ["wmo"], "countries": [], "identifiers": ["cap:sample"],
        "corroborated": False,
    }, [item], now=now)


def test_cap_info_blocks_keep_cancellation_separate_from_active_area():
    assert is_supported_official_source({
        **SOURCE, "url": CAP_URL, "verification_status": "verified",
    }) is False
    item, = parse_fixture_items(SOURCE, FIXTURE.read_text())
    cap = item["evidence"]["wmo_bom_cap"]
    assert cap["status"] == "Actual"
    assert cap["message_type"] == "Update"
    assert cap["cancelled_area_count"] == 1
    assert cap["infos"][0]["areas"] == [
        "New South Wales: Northern Tablelands forecast district"
    ]
    assert cap["infos"][1]["cancelled"] is True
    assert item["description"] is None
    assert item["evidence"]["global_identity"]["public_value_class"] == "background"
    assert "Warning narrative" not in str(item)
    rank = _rank(item)
    assert rank["factors"]["official_severity_score"] == 0
    assert rank["factors"]["active_alert_score"] == 0


def test_cap_scores_only_current_verified_high_severity_public_info():
    severe, = parse_fixture_items(SOURCE, _severe_xml(FIXTURE.read_text()))
    rank = _rank(severe)
    assert rank["factors"]["official_severity_score"] == 25
    assert rank["factors"]["active_alert_score"] == 20
    assert rank["factors"]["public_impact_score"] == 0
    assert rank["official_alert_basis"]
    assert _rank(severe, now="2026-10-18T00:00:00+00:00")["factors"][
        "official_severity_score"
    ] == 0

    cancelled, = parse_fixture_items(
        SOURCE, _severe_xml(FIXTURE.read_text()).replace("<msgType>Update</msgType>",
                                                   "<msgType>Cancel</msgType>")
    )
    test_notices = parse_fixture_items(
        SOURCE, _severe_xml(FIXTURE.read_text()).replace("<status>Actual</status>",
                                                   "<status>Test</status>")
    )
    assert _rank(cancelled)["factors"]["active_alert_score"] == 0
    assert test_notices == []


def test_cap_parser_rejects_wrong_authority_scope_and_unbounded_input():
    raw = FIXTURE.read_text()
    with pytest.raises(NewsParserError, match="exact WMO-hosted"):
        parse_fixture_items({**SOURCE, "official_url": "https://example.org/cap.xml"}, raw)
    with pytest.raises(NewsParserError, match="public issuing-authority"):
        parse_fixture_items(SOURCE, raw.replace("CAP.Message@bom.gov.au", "unknown@example.org"))
    with pytest.raises(NewsParserError, match="public issuing-authority"):
        parse_fixture_items(SOURCE, raw.replace(
            "<scope>Public</scope>", "<scope>Restricted</scope>"
        ))
    with pytest.raises(NewsParserError, match="CAP 1.2"):
        parse_fixture_items(SOURCE, raw.replace("urn:oasis:names:tc:emergency:cap:1.2", "bad"))
    with pytest.raises(NewsParserError, match="DTD"):
        parse_fixture_items(SOURCE, raw.replace("<alert", "<!DOCTYPE alert><alert", 1))
    with pytest.raises(PayloadTooLargeError, match="64 KiB"):
        parse_fixture_items(SOURCE, raw + " " * 65_536)


def test_wmo_rss_and_cap_fixture_join_without_independent_corroboration():
    rss_source = {
        "id": "wmo_bom_cap_rss", "scope": "GLOBAL", "kind": "rss",
        "parser": "wmo_bom_rss", "source_family": "wmo",
    }
    rss = parse_fixture_items(rss_source, RSS.read_text())[0]
    cap = parse_fixture_items(SOURCE, FIXTURE.read_text())[0]
    for item_id, item in ((1, rss), (2, cap)):
        item["id"] = item_id
        item["evidence"]["source"] = {"source_family": "wmo", "official_status": "official"}
    groups = correlate_global_items([rss, cap])
    assert groups[0]["item_ids"] == [1, 2]
    assert groups[0]["corroborated"] is False
    assert groups[0]["matches"][0]["basis"] == ["shared_event_id"]


def test_current_severe_cap_offline_scan_stores_source_backed_rank(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    fixture = tmp_path / "cap.xml"
    fixture.write_text(_severe_xml(FIXTURE.read_text(), current=True))
    path = tmp_path / "config.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        global: {{enabled: true}}
        news:
          enabled: true
          scopes:
            GLOBAL:
              enabled: true
              sources:
                - id: wmo_bom_cap_fixture
                  name: BoM CAP fixture
                  kind: rss
                  parser: wmo_bom_cap_xml
                  source_family: wmo
                  official_status: official
                  enabled: true
                  official_url: "{CAP_URL}"
                  url: "file://{fixture}"
    """).strip() + "\n")
    result = run_news_scan(path)
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute(
            "SELECT expires_at, evidence_json FROM news_items WHERE scope='GLOBAL'"
        ).fetchone()
        cluster = conn.execute(
            "SELECT evidence_json FROM news_clusters WHERE scope='GLOBAL'"
        ).fetchone()
    assert result["item_count"] == 1
    assert row is not None and cluster is not None
    item_evidence = json_loads(row["evidence_json"], {})
    cap_expiry = item_evidence["wmo_bom_cap"]["infos"][0]["expires_at"]
    assert row["expires_at"] == cap_expiry
    assert item_evidence["global"]["affected_regions"] == [
        "New South Wales: Northern Tablelands forecast district"
    ]
    ranking = json_loads(cluster["evidence_json"], {})["global_event"]["ranking"]
    assert ranking["factors"]["official_severity_score"] == 25
    assert ranking["factors"]["active_alert_score"] == 20
    assert ranking["factors"]["public_impact_score"] == 0
