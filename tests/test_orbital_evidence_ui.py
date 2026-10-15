from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from starlette.requests import Request

from console1701.api import build_router
from console1701.config import load_config
from console1701.db import connect_db
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_item_detail

FIXTURE = Path(__file__).parent / "fixtures/orbital/swpc_alerts.json"


def _request() -> Request:
    return Request({
        "type": "http", "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": "/ORBITAL", "raw_path": b"/ORBITAL", "query_string": b"", "headers": [],
        "client": ("127.0.0.1", 12345), "server": ("testserver", 80), "root_path": "",
    })


def test_orbital_page_shows_stored_event_evidence_without_fetching(tmp_path, monkeypatch):
    fixture = FIXTURE
    path = tmp_path / "config.yml"
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: true}}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - id: swpc_alerts_json
                  enabled: true
                  url: "file://{fixture}"
    """).strip() + "\n")
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    assert run_news_scan(path)["item_count"] == 2
    monkeypatch.setattr(
        "console1701.news.scanner.load_fixture_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no fixture on GET")),
    )
    router = build_router(str(path))
    endpoint = next(route.endpoint for route in router.routes if route.path == "/{scope}")
    response = endpoint(_request(), "ORBITAL")
    html = response.body.decode()
    assert response.status_code == 200
    assert "Event confidence" in html
    assert "space_weather_alert" in html
    assert "Impact basis" in html
    assert "swpc_alert.potential_impacts.radio" in html
    assert "official severity score adds" in html
    assert "Source families" in html
    assert "Operational impact" in html
    assert "Public impact" in html
    assert "Geographic impact" in html
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute("SELECT id FROM news_items WHERE title LIKE 'WARNING%'").fetchone()
        item = get_news_item_detail(conn, int(row["id"]))
    contract = item["evidence"]["orbital"]
    assert contract["source_id"] == "swpc_alerts_json"
    assert contract["source_family"] == "swpc"
    assert contract["official_status"] == "official"
    assert contract["parser"] == "swpc_alerts_json"
    assert contract["event_type"] == "space_weather_alert"
    assert contract["event_confidence"] == "source_reported"
    assert contract["fetch_run_id"]
    assert contract["retention_expires_at"]
    assert contract["operational_impact_basis"] == [
        "Official SWPC alert", "SWPC source-reported potential impacts",
    ]
    assert contract["public_impact_basis"] == []
    assert contract["impact_basis"]["RADIO"] == [
        "swpc_alert.potential_impacts.radio",
    ]
    assert contract["source_diversity_basis"] == "not_correlated"
    assert contract["penalties"]["low_confidence_penalty"] > 0
    assert contract["sensitivity_decision"]["label"] == "ordinary"
