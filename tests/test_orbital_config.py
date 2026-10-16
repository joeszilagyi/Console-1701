from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
import yaml

from console1701.config import ConfigError, load_config
from console1701.db import connect_db
from console1701.news.orbital_registry import list_orbital_source_registry
from console1701.news.scanner import run_news_scan
from console1701.news.source_policy import evaluate_source_policy
from console1701.news.storage import get_news_scope_states


def _write(path: Path, body: str) -> Path:
    path.write_text(dedent(body).strip() + "\n")
    return path


def test_orbital_config_defaults_and_validates_policy_flags(tmp_path):
    path = _write(tmp_path / "baseline.yml", """
        paths: {repo_roots: [], explicit_repos: []}
    """)
    config = load_config(path)
    orbital = config["orbital"]
    assert orbital["enabled"] is False
    assert orbital["include_space_weather"] is True
    assert orbital["include_debris"] is False
    assert orbital["include_satellite_catalog"] is False
    assert orbital["include_social_sources"] is False
    assert orbital["allow_auth_required_sources"] is False
    assert orbital["allow_restricted_sources"] is False
    assert orbital["allow_tactical_sources"] is False
    assert orbital["allow_homepage_extractors"] is False
    bad = _write(tmp_path / "bad.yml", """
        paths: {repo_roots: [], explicit_repos: []}
        orbital: {allow_tactical_sources: perhaps}
    """)
    with pytest.raises(ConfigError, match="orbital.allow_tactical_sources"):
        load_config(bad)


def test_orbital_parent_and_sensitive_sources_block_before_read(tmp_path, monkeypatch):
    config_path = _write(tmp_path / "gates.yml", """
        paths: {repo_roots: [], explicit_repos: []}
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - {id: swpc_alerts_json, enabled: true, url: file:///missing-swpc.json,
                   parser: generic_json_items}
                - {id: reddit_space, enabled: true, url: file:///missing-reddit.json}
                - {id: space_track_home, enabled: true, url: file:///missing-space-track.json}
                - {id: celestrak_elements, enabled: true,
                   url: file:///missing-celestrak.json, parser: generic_json_items}
    """)
    monkeypatch.setattr(
        "console1701.news.scanner.load_fixture_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no fixture read")),
    )
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    result = run_news_scan(config_path)
    config = load_config(config_path)
    with connect_db(config["_db_path"]) as conn:
        states = {row["source_key"]: row["state"] for row in conn.execute(
            "SELECT s.source_key, h.state FROM news_source_health h "
            "JOIN news_sources s ON s.id = h.source_id"
        )}
        scope = get_news_scope_states(conn, config)["ORBITAL"]
    assert result["item_count"] == 0
    assert scope["state"] == "disabled"
    assert states["swpc_alerts_json"] == "policy_blocked"
    assert states["reddit_space"] == "policy_blocked"
    assert states["space_track_home"] == "auth_required"
    assert states["celestrak_elements"] == "policy_blocked"


def test_orbital_topic_social_restricted_and_parser_gates(tmp_path, monkeypatch):
    path = _write(tmp_path / "enabled.yml", """
        paths: {repo_roots: [], explicit_repos: []}
        orbital:
          enabled: true
          include_space_weather: false
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - {id: swpc_alerts_json, enabled: true, url: file:///missing-swpc.json,
                   parser: generic_json_items}
                - {id: reddit_space, enabled: true, url: file:///missing-reddit.json}
                - {id: celestrak_elements, enabled: true,
                   url: file:///missing-celestrak.json, parser: generic_json_items}
                - {id: nasa_news, enabled: true, url: file:///missing-nasa.rss}
    """)
    monkeypatch.setattr(
        "console1701.news.scanner.load_fixture_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no fixture read")),
    )
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    assert run_news_scan(path)["item_count"] == 0
    config = load_config(path)
    with connect_db(config["_db_path"]) as conn:
        states = {row["source_key"]: row["state"] for row in conn.execute(
            "SELECT s.source_key, h.state FROM news_source_health h "
            "JOIN news_sources s ON s.id = h.source_id"
        )}
    assert states == {
        "swpc_alerts_json": "policy_blocked",
        "reddit_space": "social_disabled",
        "celestrak_elements": "sensitivity_blocked",
        "nasa_news": "manual_review_only",
    }


def test_orbital_restricted_flags_do_not_admit_generic_tracking_parser(tmp_path):
    path = _write(tmp_path / "restricted.yml", """
        paths: {repo_roots: [], explicit_repos: []}
        orbital:
          enabled: true
          include_satellite_catalog: true
          allow_restricted_sources: true
          allow_tactical_sources: true
        news:
          enabled: true
          scopes:
            ORBITAL:
              enabled: true
              sources:
                - {id: celestrak_elements, enabled: true,
                   url: file:///missing-celestrak.json, parser: generic_json_items}
                - {id: space_track_home, enabled: true,
                   url: file:///missing-space-track.json, parser: generic_json_items,
                   auth: {api_key: configured-test-key}}
    """)
    config = load_config(path)
    sources = ((config["news"]["scopes"])["ORBITAL"])["sources"]
    by_id = {source["id"]: evaluate_source_policy(config, source) for source in sources}
    assert by_id["celestrak_elements"]["gate_state"] == "needs_scope_filter"
    assert by_id["space_track_home"]["gate_state"] == "policy_blocked"


def test_all_orbital_candidates_stay_closed_with_parent_off(tmp_path, monkeypatch):
    sources = [
        {"id": entry["source_key"], "enabled": True, "url": "file:///missing-orbital"}
        for entry in list_orbital_source_registry()
    ]
    path = tmp_path / "all-candidates.yml"
    path.write_text(yaml.safe_dump({
        "paths": {"repo_roots": [], "explicit_repos": []},
        "news": {"enabled": True, "scopes": {
            "ORBITAL": {"enabled": True, "sources": sources}
        }},
    }))
    monkeypatch.setattr(
        "console1701.news.scanner.load_fixture_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no fixture read")),
    )
    monkeypatch.setattr(
        "console1701.news.scanner.fetch_official_text",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no HTTP")),
    )
    result = run_news_scan(path)
    assert result["scanned_sources"] == len(sources) == 137
    assert result["item_count"] == 0
