from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import dedent

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import (
    SWPC_BOULDER_K_URL,
    SWPC_PLANETARY_K_1M_URL,
    SWPC_PLANETARY_K_URL,
    OfficialFetchResult,
    is_supported_official_source,
)
from console1701.news.scanner import run_news_scan
from console1701.news.storage import get_news_scope_view

FIXTURES = Path(__file__).parent / "fixtures/orbital"
SOURCES = {
    "swpc_kp_summary_json": (SWPC_PLANETARY_K_URL, "swpc_kp_planetary.json"),
    "swpc_kp_1m_json": (SWPC_PLANETARY_K_1M_URL, "swpc_kp_1m.json"),
    "swpc_boulder_k_json": (SWPC_BOULDER_K_URL, "swpc_k_boulder.json"),
}


def _config(path: Path, *, minimum=5.0, allow_http=True):
    sources = "\n".join(
        f"                - id: {key}\n"
        "                  enabled: true\n"
        "                  verification_status: verified\n"
        f"                  url: {url}"
        for key, (url, _) in SOURCES.items()
    )
    path.write_text(dedent(f"""
        paths: {{repo_roots: [], explicit_repos: []}}
        orbital: {{enabled: true, kp_min_index: {minimum}}}
        news:
          enabled: true
          fetch_policy: {{allow_official_http: {str(allow_http).lower()}}}
          scopes:
            ORBITAL:
              enabled: true
              sources:
    """).strip() + "\n" + sources + "\n")
    return path


def _payloads(*, age_hours=0):
    result = {}
    for key, (_, name) in SOURCES.items():
        rows = json.loads((FIXTURES / name).read_text())
        current = datetime.now(UTC) - timedelta(hours=age_hours, minutes=15)
        for index, row in enumerate(rows):
            row["time_tag"] = (current + timedelta(minutes=index)).isoformat(timespec="seconds")
        result[key] = json.dumps(rows)
    return result


def test_k_index_live_allowlist_is_exact_and_enforces_high_signal_floor():
    for key, (url, _) in SOURCES.items():
        source = {
            "scope": "ORBITAL", "id": key, "kind": "api_json", "parser": "swpc_kp_json",
            "url": url, "verification_status": "verified", "min_k_index": 5.0,
        }
        assert is_supported_official_source(source)
        for changed in (
            {"url": url + "?x=1"}, {"parser": "generic_json_items"},
            {"verification_status": "candidate_needs_verification"},
            {"min_k_index": 4.9}, {"auth": {"token": "x"}},
        ):
            assert not is_supported_official_source({**source, **changed})


def test_k_index_live_scan_is_bounded_to_latest_records_and_offline_get(tmp_path, monkeypatch):
    path = _config(tmp_path / "live.yml")
    payloads = _payloads()
    calls = []

    def fake_fetch(source, **kwargs):
        calls.append(source["id"])
        data = payloads[source["id"]]
        return OfficialFetchResult(data, 200, None, None, len(data))

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    assert run_news_scan(path)["item_count"] == 3
    assert sorted(calls) == sorted(SOURCES)
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        rows = conn.execute(
            "SELECT evidence_json FROM news_items WHERE scope='ORBITAL'"
        ).fetchall()
    assert len(rows) == 3
    evidence = [json_loads(row["evidence_json"], {}) for row in rows]
    assert {row["source"]["source_key"] for row in evidence} == set(SOURCES)
    assert all(row["ingest"]["fixture_only"] is False for row in evidence)
    boulder = next(row for row in evidence if row["source"]["source_key"] == (
        "swpc_boulder_k_json"
    ))
    assert boulder["swpc_k_index"]["source_kind"] == "regional"
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("GET fetched HTTP")),
    )
    with connect_db(config["_db_path"]) as conn:
        assert len(get_news_scope_view(conn, config, "ORBITAL")["items"]) == 3


def test_k_index_live_gate_and_stale_measurement_do_not_fetch_or_store(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("HTTP blocked")),
    )
    for index, settings in enumerate((
        {"allow_http": False}, {"minimum": 4.0},
    )):
        blocked_path = _config(tmp_path / f"blocked-{index}.yml", **settings)
        assert run_news_scan(blocked_path)["item_count"] == 0
    path = _config(tmp_path / "stale.yml")
    payloads = _payloads(age_hours=24)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda source, **kwargs: OfficialFetchResult(
            payloads[source["id"]], 200, None, None, len(payloads[source["id"]])
        ),
    )
    assert run_news_scan(path)["item_count"] == 0
