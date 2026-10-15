# GLOBAL USGS GeoJSON first live source signoff

Verified 2026-10-15 for RS-084 against the [USGS GeoJSON summary feed
directory](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php).
The exact source is the [M4.5+ past-week GeoJSON
feed](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson).
A bounded direct read returned HTTP 200, `application/json; charset=utf-8`,
120,403 bytes, a `FeatureCollection`, and 172 features. It did not redirect.
This is a global seismic feed, not a country-impact or humanitarian-impact
source. It needs no credential, and only the public feed metadata is read.

The allowlist tuple is scope `GLOBAL`, key `usgs_eq_geojson_global`, this exact
URL, kind `api_json`, parser `usgs_earthquake_geojson`, and verification status
`verified`. Registry and standing config remain disabled. A live request needs
`news.enabled`, `global.enabled`, the GLOBAL scope and this source enabled,
`news.fetch_policy.allow_official_http: true`, and an explicit `news-scan`
command. The configured interval must be at least 30 minutes, and the parser
threshold must be at least the feed's M4.5 floor. The GLOBAL default is M6.0.
The transport enforces exact HTTPS identity, 1 MiB default response cap,
30-second maximum timeout, no redirects or inherited proxy, validators, and
backoff. No GET route, host scan, or pytest fetches the feed.

The parser keeps event ID, official event URL, event time, magnitude, depth,
felt/intensity, tsunami flag, source place string, and filter/ranking evidence.
The source place is not treated as verified country or public impact. Feed
payloads and linked event detail are not retained. Default item retention is
seven days; an optional `max_age_hours` can narrow the source window. A
successful response with zero M6+ matches is healthy.

The fixture backed parser, exact allowlist and config gates, offline 200/304
and interval handling, HTTP opt-in, and evidence tests are in
`tests/test_global_usgs.py` and `tests/test_global_live_usgs.py`. A later
per-source review is required before adding another GLOBAL live endpoint.

An isolated explicit `news-scan` with a temporary config and state on
2026-10-15 returned HTTP 200 and stored eight M6+ GLOBAL items with a
successful source run. Temporary opt-in and SQLite state were removed after
the scan. This observation does not assert verified country impact; the
source-place geography remains unverified in each item.
