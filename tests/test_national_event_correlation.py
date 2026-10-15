from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.national_events import correlate_national_items
from console1701.news.scanner import run_news_scan


def _item(item_id: int, family: str, *, state: str = "WA",
          published: str = "2026-10-15T12:00:00+00:00") -> dict:
    return {
        "id": item_id, "scope": "NATIONAL",
        "title": "Major regional airport ground stop disruption",
        "source_published_at": published, "first_seen_at": published,
        "evidence": {
            "source": {"source_family": family, "source_key": f"{family}_{item_id}"},
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
                   source_family: nhtsa, enabled: true, url: "file://{fixture}"}}
                - {{id: nhtsa_b, name: NHTSA B, kind: api_json, parser: nhtsa_recalls_json,
                   source_family: nhtsa, enabled: true, url: "file://{fixture}"}}
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
