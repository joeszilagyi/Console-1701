from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from console1701.config import NEWS_SCOPES, ConfigError, iter_news_sources, load_config


def _write_config(path: Path, text: str) -> Path:
    path.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return path


def test_news_defaults_are_disabled_and_empty(tmp_path):
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            "paths: {repo_roots: [], explicit_repos: []}",
        )
    )

    assert config["news"]["enabled"] is False
    assert config["news"]["fetch_policy"]["page_load_external_fetches"] is False
    assert config["news"]["fetch_policy"]["allow_homepage_extractors"] is False
    assert config["local"]["enabled"] is False
    assert config["local"]["default_place_label"] == "Seattle"
    assert config["local"]["include_airport"] is True
    assert config["local"]["hazard_radius_miles"] == 75
    assert config["local"]["earthquake_min_magnitude"] == 3.0
    assert config["local"]["allow_neighborhood_blogs"] is False
    assert config["local"]["allow_social_sources"] is False
    assert list(config["news"]["scopes"]) == list(NEWS_SCOPES)
    assert iter_news_sources(config) == []
    assert all(not scope["enabled"] for scope in config["news"]["scopes"].values())


def test_config_example_contains_only_disabled_news_sources():
    config = load_config(Path(__file__).resolve().parents[1] / "config.example.yml")
    sources = iter_news_sources(config)

    assert config["news"]["enabled"] is False
    assert sources
    assert all(source["enabled"] is False for source in sources)
    assert all(source["kind"] != "homepage_headlines" for source in sources)


def test_news_source_defaults_to_disabled_and_parent_scope(tmp_path):
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            """
            paths: {repo_roots: [], explicit_repos: []}
            news:
              scopes:
                LOCAL:
                  sources:
                    - id: local_fixture
                      name: Local fixture
                      kind: local_file_json
                      url: file://./tests/fixtures/news/local_items.json
            """,
        )
    )

    source = iter_news_sources(config)[0]

    assert source["scope"] == "LOCAL"
    assert source["enabled"] is False
    assert source["priority"] == 50
    assert source["tags"] == []
    assert source["evidence_notes"] == []


def test_news_rejects_page_load_external_fetches(tmp_path):
    with pytest.raises(ConfigError, match="page_load_external_fetches must remain false"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  fetch_policy:
                    page_load_external_fetches: true
                """,
            )
        )


def test_news_rejects_unknown_scope(tmp_path):
    with pytest.raises(ConfigError, match="Unknown news scope"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  scopes:
                    GALACTIC:
                      enabled: false
                      sources: []
                """,
            )
        )


def test_news_rejects_unknown_source_kind(tmp_path):
    with pytest.raises(ConfigError, match="kind must be one of"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  scopes:
                    LOCAL:
                      sources:
                        - id: bad_kind
                          name: Bad kind
                          kind: scraper
                """,
            )
        )


def test_news_rejects_homepage_source_without_explicit_allowance(tmp_path):
    with pytest.raises(ConfigError, match="allow_homepage_extractors is false"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  scopes:
                    NATIONAL:
                      sources:
                        - id: homepage
                          name: Homepage
                          kind: homepage_headlines
                          selectors:
                            item: article
                """,
            )
        )


def test_news_accepts_homepage_source_with_explicit_allowance(tmp_path):
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            """
            news:
              fetch_policy:
                allow_homepage_extractors: true
              scopes:
                NATIONAL:
                  sources:
                    - id: homepage
                      name: Homepage
                      kind: homepage_headlines
                      selectors:
                        item: article
            """,
        )
    )

    assert iter_news_sources(config)[0]["kind"] == "homepage_headlines"


def test_local_rejects_unknown_source_class(tmp_path):
    with pytest.raises(ConfigError, match="source_class must be one of"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  scopes:
                    LOCAL:
                      sources:
                        - id: local_bad_class
                          name: Bad class
                          kind: local_file_json
                          source_class: mystery
                """,
            )
        )


def test_local_rejects_unknown_adapter(tmp_path):
    with pytest.raises(ConfigError, match="adapter must be one of"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  scopes:
                    LOCAL:
                      sources:
                        - id: local_bad_adapter
                          name: Bad adapter
                          kind: local_file_json
                          adapter: screen_scraper
                """,
            )
        )


def test_local_rejects_social_source_without_explicit_allowance(tmp_path):
    with pytest.raises(ConfigError, match="local.allow_social_sources true"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  scopes:
                    LOCAL:
                      sources:
                        - id: reddit_seattle
                          name: Reddit Seattle
                          kind: rss
                          source_family: reddit
                          source_class: social_candidate
                          adapter: manual_review_only
                """,
            )
        )


def test_local_accepts_social_source_with_explicit_allowance(tmp_path):
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            """
            local:
              allow_social_sources: true
            news:
              scopes:
                LOCAL:
                  sources:
                    - id: reddit_seattle
                      name: Reddit Seattle
                      kind: rss
                      source_family: reddit
                      source_class: social_candidate
                      adapter: manual_review_only
                      verification_status: candidate_policy_sensitive
            """,
        )
    )

    source = iter_news_sources(config)[0]

    assert source["source_family"] == "reddit"
    assert source["source_class"] == "social_candidate"
    assert source["adapter"] == "manual_review_only"
    assert source["verification_status"] == "candidate_policy_sensitive"


def test_regional_defaults_can_seed_nws_source(tmp_path):
    config = load_config(
        _write_config(
            tmp_path / "config.yml",
            """
            news:
              scopes:
                REGIONAL:
                  sources:
                    - id: nws_active_alerts_wa
            """,
        )
    )

    source = iter_news_sources(config)[0]

    assert config["regional"]["enabled"] is False
    assert config["regional"]["allow_social_sources"] is False
    assert config["regional"]["allow_homepage_extractors"] is False
    assert source["name"] == "NWS active alerts for Washington"
    assert source["source_family"] == "nws"
    assert source["source_class"] == "official_weather_hazard"
    assert source["adapter"] == "official_api_json"
    assert source["verification_status"] == "official_page_seen"


def test_local_rejects_neighborhood_blog_without_explicit_allowance(tmp_path):
    with pytest.raises(ConfigError, match="local.allow_neighborhood_blogs true"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  scopes:
                    LOCAL:
                      sources:
                        - id: west_seattle_blog
                          name: West Seattle Blog
                          kind: rss
                          source_family: west_seattle_blog
                          source_class: neighborhood_blog
                          adapter: rss_atom
                """,
            )
        )


def test_news_rejects_duplicate_source_ids(tmp_path):
    with pytest.raises(ConfigError, match="Duplicate news source id"):
        load_config(
            _write_config(
                tmp_path / "config.yml",
                """
                news:
                  scopes:
                    LOCAL:
                      sources:
                        - id: repeated
                          name: First
                          kind: local_file_json
                    REGIONAL:
                      sources:
                        - id: repeated
                          name: Second
                          kind: local_file_json
                """,
            )
        )
