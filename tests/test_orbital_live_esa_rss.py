from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from pathlib import Path

import pytest
import yaml

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import OfficialFetchResult, is_supported_official_source
from console1701.news.orbital_rss import ESA_FEEDS
from console1701.news.scanner import run_news_scan


def _config(path: Path, key: str, *, verified=True, allow_http=True):
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "orbital": {"enabled": True},
        "news": {
            "enabled": True,
            "fetch_policy": {"allow_official_http": allow_http},
            "scopes": {"ORBITAL": {"enabled": True, "sources": [{
                "id": key, "enabled": True,
                "verification_status": "verified" if verified else "official_feed_seen",
                "url": ESA_FEEDS[key][0],
            }]}}
        },
    }))
    return path


def _payload(key: str, *, age_days=0) -> str:
    channel = ESA_FEEDS[key][1]
    stamp = format_datetime(datetime.now(UTC) - timedelta(days=age_days))
    return f"""<rss><channel><title>{channel}</title>
      <item><title>ESA astronaut returns from ISS</title>
      <link>https://www.esa.int/Science_Exploration/Human_and_Robotic_Exploration/ESA_astronaut_returns_from_ISS</link>
      <pubDate>{stamp}</pubDate></item>
      <item><title>Week in images</title>
      <link>https://www.esa.int/About_Us/Week_in_images/October_2026</link>
      <pubDate>{stamp}</pubDate></item>
      <item><title>Space debris reentry update</title>
      <link>https://www.esa.int/Space_Safety/Space_Debris/reentry_update</link>
      <pubDate>{stamp}</pubDate></item>
    </channel></rss>"""


@pytest.mark.parametrize("key", list(ESA_FEEDS))
def test_esa_live_feeds_are_exact_and_filter_to_orbital_items(tmp_path, monkeypatch, key):
    source = {
        "scope": "ORBITAL", "id": key, "kind": "rss", "parser": "esa_orbital_rss",
        "url": ESA_FEEDS[key][0], "verification_status": "verified",
    }
    assert is_supported_official_source(source)
    for changed in (
        {"url": source["url"] + "?other=1"}, {"parser": "generic_rss"},
        {"verification_status": "official_feed_seen"}, {"auth": {"token": "x"}},
    ):
        assert not is_supported_official_source({**source, **changed})
    payload = _payload(key)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda configured, **kwargs: OfficialFetchResult(
            payload, 200, None, None, len(payload)
        ),
    )
    config_path = _config(tmp_path / f"{key}.yml", key)
    assert run_news_scan(config_path)["item_count"] == 1
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute("SELECT title, evidence_json FROM news_items WHERE scope='ORBITAL'")
        row = row.fetchone()
    assert row["title"] == "ESA astronaut returns from ISS"
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["esa_rss"]["feed_url"] == source["url"]
    assert evidence["source"]["source_family"] == "esa"
    assert evidence["ingest"]["fixture_only"] is False


def test_esa_live_feed_gates_and_stale_items(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked HTTP")),
    )
    for index, settings in enumerate((
        {"verified": False}, {"allow_http": False},
    )):
        path = _config(tmp_path / f"blocked-{index}.yml", "esa_rss", **settings)
        assert run_news_scan(path)["item_count"] == 0
    payload = _payload("esa_iss", age_days=30)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda source, **kwargs: OfficialFetchResult(payload, 200, None, None, len(payload)),
    )
    assert run_news_scan(_config(tmp_path / "old.yml", "esa_iss"))["item_count"] == 0
