"""Exact source identities for COSMIC fixture and signed-off live ingestion."""

from __future__ import annotations

from typing import Any

SCIENCE_FIXTURE_SOURCES = {
    "astronomers_telegram_rss": (
        "atel_rss", "https://www.astronomerstelegram.org/?rss",
    ),
    "nasa_jpl_science_feed": (
        "nasa_jpl_science_rss", "https://www.nasa.gov/centers-and-facilities/jpl/feed/",
    ),
    "esa_space_science_feed": (
        "esa_science_rss", "https://www.esa.int/rssfeed/Our_Activities/Space_Science",
    ),
    "esa_hubble_science_rss": (
        "esa_telescope_science_rss", "https://feeds.feedburner.com/hubble_news/",
    ),
    "esa_webb_science_rss": (
        "esa_telescope_science_rss", "https://feeds.feedburner.com/esawebb/news/",
    ),
    "nasa_exoplanet_ps_tap": (
        "exoplanet_ps_json", "https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
    ),
    "mast_caom_tiny_metadata": (
        "mast_caom_tiny_json", "https://mast.stsci.edu/api/v0/invoke",
    ),
    "pds_collection_metadata": (
        "pds_collection_metadata", "https://pds.nasa.gov/api/search/1/products/",
    ),
    "gcn_notices": (
        "gcn_notice_fixture", "https://gcn.nasa.gov/docs/notices",
    ),
    "gracedb_public_alerts": (
        "gracedb_public_alert_fixture", "https://gracedb.ligo.org/api/v2/superevents/",
    ),
}


def exact_science_endpoint(source: dict[str, Any], endpoint: str) -> bool:
    """Accept an official URL, or a local fixture tied to that exact URL."""
    url = str(source.get("url") or "")
    if url == endpoint and source.get("official_url") in {None, endpoint}:
        return True
    return bool(url.startswith("file://") and source.get("fixture_only") is True
                and source.get("official_url") == endpoint)
