from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from pathlib import Path

import pytest
import yaml

from console1701.config import load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import OfficialFetchResult, is_supported_official_source
from console1701.news.orbital_registry import get_orbital_source_registry_entry
from console1701.news.orbital_rss import NASA_FEEDS
from console1701.news.scanner import run_news_scan

FEEDS = {
    "nasa_rss_feeds": ("NASA", "/missions/station/", "Station Crew Completes Spacewalk"),
    "nasa_iss_page": (
        "International Space Station (ISS) – NASA", "/missions/station/",
        "Station Crew Completes Spacewalk",
    ),
    "nasa_spacestation_blog": (
        "International Space Station - NASA", "/blogs/spacestation/",
        "SpaceX Dragon Docks at Station",
    ),
    "nasa_artemis": (
        "Artemis – NASA", "/missions/artemis/", "NASA Confirms Artemis Heat Shield Test",
    ),
    "nasa_artemis_blog": (
        "Artemis - NASA", "/blogs/artemis/", "NASA Completes Artemis Booster Stacking",
    ),
    "nasa_kennedy_blog": (
        "Kennedy Space Center - NASA", "/blogs/kennedy/", "Kennedy Teams Complete Launch Test",
    ),
}


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
                "url": NASA_FEEDS[key][0],
            }]}}
        },
    }))
    return path


def _payload(key: str, *, age_days=0) -> str:
    channel, path, title = FEEDS[key]
    stamp = format_datetime(datetime.now(UTC) - timedelta(days=age_days))
    return f"""<rss><channel><title>{channel}</title>
      <item><title>{title}</title>
      <link>https://www.nasa.gov{path}test-update/</link>
      <pubDate>{stamp}</pubDate></item>
      <item><title>Routine Student Feature</title>
      <link>https://www.nasa.gov{path}routine-feature/</link>
      <pubDate>{stamp}</pubDate></item>
    </channel></rss>"""


@pytest.mark.parametrize("key", list(FEEDS))
def test_nasa_live_feeds_are_exact_and_filter_to_orbital_items(tmp_path, monkeypatch, key):
    source = {
        "scope": "ORBITAL", "id": key, "kind": "rss", "parser": "nasa_orbital_rss",
        "url": NASA_FEEDS[key][0], "verification_status": "verified",
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
    assert row["title"] == FEEDS[key][2]
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["nasa_rss"]["feed_url"] == source["url"]
    assert evidence["source"]["source_family"] == (
        get_orbital_source_registry_entry(key)["source_family"]
    )
    assert evidence["ingest"]["fixture_only"] is False


def test_nasa_live_feed_gates_and_old_kennedy_items(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("blocked HTTP")),
    )
    for index, settings in enumerate((
        {"verified": False}, {"allow_http": False},
    )):
        path = _config(tmp_path / f"blocked-{index}.yml", "nasa_rss_feeds", **settings)
        assert run_news_scan(path)["item_count"] == 0
    key = "nasa_kennedy_blog"
    payload = _payload(key, age_days=30)
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda source, **kwargs: OfficialFetchResult(payload, 200, None, None, len(payload)),
    )
    assert run_news_scan(_config(tmp_path / "old.yml", key))["item_count"] == 0
