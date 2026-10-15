from __future__ import annotations

from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import pytest
import yaml

from console1701 import config as config_module
from console1701.config import ConfigError, load_config
from console1701.db import connect_db, json_loads
from console1701.news.official_http import OfficialFetchResult, is_supported_official_source
from console1701.news.scanner import run_news_scan
from console1701.news.science_rss import NASA_JPL_SCIENCE_FEED


def _config(tmp_path, monkeypatch, *, allow_http=True, override=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    state = tmp_path / "state"
    monkeypatch.setattr(config_module, "DEFAULT_STATE_DIR", state)
    monkeypatch.setattr(config_module, "DEFAULT_DB_PATH", state / "console.sqlite")
    monkeypatch.setattr(config_module, "DEFAULT_HANDOFF_DIR", state / "handoffs")
    source = {
        "id": "nasa_jpl_science_feed", "name": "NASA JPL science", "kind": "rss",
        "parser": "nasa_jpl_science_rss", "enabled": True, "fixture_only": False,
        "official_url": NASA_JPL_SCIENCE_FEED, "url": NASA_JPL_SCIENCE_FEED,
    }
    source.update(override or {})
    path = tmp_path / "config.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "solar_system_beyond": {"enabled": True},
        "news": {"enabled": True,
                 "fetch_policy": {"allow_official_http": allow_http},
                 "scopes": {"SYSTEM_SOLAR": {"enabled": True, "sources": [source]}}},
    }))
    return path


def _payload(*, age_days=0):
    published = format_datetime(datetime.now(UTC) - timedelta(days=age_days))
    return f"""<rss><channel><title>Jet Propulsion Laboratory – NASA</title>
      <item><title>NASA SPHEREx Telescope Sees Brown Dwarfs</title>
      <link>https://www.nasa.gov/missions/spherex/brown-dwarfs/</link>
      <pubDate>{published}</pubDate><category>Astrophysics</category></item>
      <item><title>NASA Roman Space Telescope Launches</title>
      <link>https://www.nasa.gov/missions/roman/roman-launches/</link>
      <pubDate>{published}</pubDate><category>Astrophysics</category></item>
      <item><title>NASA Satellites Observe El Niño</title>
      <link>https://science.nasa.gov/earth/el-nino/</link>
      <pubDate>{published}</pubDate><category>Earth</category></item>
    </channel></rss>"""


def test_jpl_science_live_exact_source_filters_operations_and_earth(tmp_path, monkeypatch):
    path = _config(tmp_path, monkeypatch)
    source = load_config(path)["news"]["scopes"]["SYSTEM_SOLAR"]["sources"][0]
    assert source["verification_status"] == "verified"
    assert source["interval_minutes"] >= 60
    assert is_supported_official_source(source)
    for changed in (
        {"url": NASA_JPL_SCIENCE_FEED + "?other=1"},
        {"official_url": "https://example.test/rss"},
        {"parser": "generic_rss"}, {"fixture_only": True},
        {"verification_status": "candidate_needs_verification"},
    ):
        assert not is_supported_official_source({**source, **changed})
    payload = _payload()

    def fake_fetch(*args, **kwargs):
        assert kwargs["max_bytes"] == 1_048_576
        return OfficialFetchResult(payload, 200, None, None, len(payload.encode()))

    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", fake_fetch)
    assert run_news_scan(path)["item_count"] == 1
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        row = conn.execute(
            "SELECT title, evidence_json FROM news_items WHERE scope='SYSTEM_SOLAR'"
        ).fetchone()
    assert "SPHEREx" in row["title"]
    evidence = json_loads(row["evidence_json"], {})
    assert evidence["ingest"]["fixture_only"] is False
    assert evidence["science_rss"]["data_product_downloaded"] is False


@pytest.mark.parametrize("override", [
    {"url": NASA_JPL_SCIENCE_FEED + "?x=1"},
    {"official_url": "https://example.test/rss"},
    {"parser": "generic_rss"}, {"fixture_only": True},
    {"verification_status": "candidate_needs_verification"},
    {"interval_minutes": 1},
])
def test_jpl_science_live_config_rejects_nonexact_source(tmp_path, monkeypatch, override):
    with pytest.raises(ConfigError):
        load_config(_config(tmp_path, monkeypatch, override=override))


def test_jpl_science_live_requires_http_opt_in_and_fresh_items(tmp_path, monkeypatch):
    path = _config(tmp_path / "blocked", monkeypatch, allow_http=False)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        (_ for _ in ()).throw(AssertionError("unapproved JPL HTTP fetch"))
    ))
    assert run_news_scan(path)["item_count"] == 0
    old = _payload(age_days=30)
    path = _config(tmp_path / "old", monkeypatch)
    monkeypatch.setattr("console1701.news.scanner.fetch_official_text", lambda *a, **kw: (
        OfficialFetchResult(old, 200, None, None, len(old.encode()))
    ))
    assert run_news_scan(path)["item_count"] == 0
