# COSMIC local fixture ingest

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

The source ID, parser, and `official_url` must match the verified source identity. The actual
input URL must be `file://`. An HTTP URL is rejected for this scope even when the global official
HTTP flag is enabled. The same exact-identity rule applies to the ESA Space Science, ESA
Hubble/Webb, NASA Exoplanet Archive, MAST, PDS, and GCN fixture parsers. Tiny archive fixtures
also require their parser-specific `query_contract` with explicit columns, row and time bounds,
or collection ID; see the parser fixtures and tests for accepted shapes.

The scanner stores headline or record metadata, event correlation, rank reasons, query bounds,
source health, and retention evidence. The parser contracts reject oversized or broad archive
responses and do not call product, sky-map, image, article-body, or paper endpoints. Registry
candidates for heavy catalogs and archives cannot be configured as these fixture parsers, even
when the science heavy-archive flags are set. Live science ingest is a separate later phase.
