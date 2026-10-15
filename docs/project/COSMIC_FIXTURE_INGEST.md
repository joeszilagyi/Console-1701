# COSMIC source ingest

COSMIC is the UI label for the internal `SYSTEM_SOLAR` recent-signal scope. It is disabled by
default. To exercise a verified parser without network access, set the science parent and scope
flags, then configure an exact fixture source. Run `news-scan` explicitly; opening `/COSMIC` only
reads stored SQLite rows.

```yaml
solar_system_beyond:
  enabled: true
news:
  enabled: true
  scopes:
    SYSTEM_SOLAR:
      enabled: true
      sources:
        - id: nasa_jpl_science_feed
          name: NASA JPL science fixture
          kind: rss
          parser: nasa_jpl_science_rss
          enabled: true
          fixture_only: true
          official_url: https://www.nasa.gov/centers-and-facilities/jpl/feed/
          url: file:///absolute/path/to/nasa_jpl_science.rss
```

The source ID, parser, and `official_url` must match the verified source identity. Fixture input
must be `file://`. The same exact-identity rule applies to the ESA Space Science, ESA Hubble/Webb,
NASA Science News, NASA Exoplanet Archive, MAST, PDS, and GCN fixture parsers. NASA Science News
uses the official blog feed URL, accepts only a known one-separator XML repair in local fixture
mode, and keeps live HTTP disabled while the source feed remains stale and malformed. Tiny
archive fixtures
also require their parser-specific `query_contract` with explicit columns, row and time bounds,
or collection ID; see the parser fixtures and tests for accepted shapes.

The scanner stores headline or record metadata, event correlation, rank reasons, query bounds,
source health, and retention evidence. The parser contracts reject oversized or broad archive
responses and do not call product, sky-map, image, article-body, or paper endpoints. Registry
candidates for heavy catalogs and archives cannot be configured as these fixture parsers, even
when the science heavy-archive flags are set.

ESA Space Science RSS and one bounded NASA Exoplanet Archive TAP metadata query are the opt-in
live COSMIC sources in this first pass. Set
`solar_system_beyond.enabled`, `news.enabled`, and `news.scopes.SYSTEM_SOLAR.enabled` to true,
configure this exact source, and invoke `news-scan`:

```yaml
news:
  fetch_policy:
    allow_official_http: true
  scopes:
    SYSTEM_SOLAR:
      enabled: true
      sources:
        - id: esa_space_science_feed
          name: ESA Space Science
          kind: rss
          parser: esa_science_rss
          enabled: true
          fixture_only: false
          official_url: https://www.esa.int/rssfeed/Our_Activities/Space_Science
          url: https://www.esa.int/rssfeed/Our_Activities/Space_Science
          interval_minutes: 60
```

The exact ESA URL/parser/verification status is checked again by the HTTP transport. Successful
live scans retain only source-dated science items from the last 14 days, cap response reads at
1 MiB, and retain item metadata for at most seven days. This opt-in never runs on page loads.
The [NASA Exoplanet Archive tiny TAP signoff](COSMIC_EXOPLANET_TAP_LIVE_SIGNOFF.md) gives the
separate exact API opt-in. Its URL is the official `/TAP/sync` base; the app supplies a fixed
seven-day, ten-row, seven-column query, rejects configured live query text, caps the response at
64 KiB, and waits at least 24 hours between reads. Other COSMIC HTTP URLs remain blocked;
broad archives and product downloads remain disabled.
