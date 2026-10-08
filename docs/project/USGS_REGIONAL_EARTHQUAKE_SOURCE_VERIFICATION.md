# REGIONAL USGS Earthquake GeoJSON Source Signoff

Verified 2026-10-08 for a second exact-URL official HTTP ingest slice.

- Owner and endpoint: U.S. Geological Survey,
  `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson`.
  The [USGS GeoJSON summary documentation](https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php)
  links this magnitude-2.5+ past-day feed, describes its `FeatureCollection` shape and event fields,
  and states that the feed updates every minute. A bounded GET on 2026-10-08 returned a valid
  `FeatureCollection` with 27 features. HEAD returned HTTP 200, `application/json`, and a
  `Last-Modified` header without a redirect.
- Access and policy: public official feed, no authentication, no article/page scraping, no detail
  requests. The selected registry interval is five minutes, slower than the documented one-minute
  feed update. The exact URL is allowlisted only for REGIONAL `usgs_eq_geojson` with the verified
  `usgs_earthquake_geojson` parser. HTTP 429 and transport failures use existing backoff; the
  scanner sends conditional `Last-Modified` requests when available.
- Geography and relevance: the parser keeps only earthquake-type features within its configured
  Washington/PNW coordinate bounds and at or above the magnitude threshold. The feed itself
  contains only M2.5+ events, so live source admission rejects thresholds below 2.5 rather than
  silently promising unavailable smaller events. The default REGIONAL threshold is 3.0. Radius
  matching is still pending.
- Storage and sensitivity: preserve bounded title, official event URL, event ID, time, magnitude,
  depth, felt/intensity, alert level, public-impact and geography evidence in local SQLite. Do not
  store the raw feed response. Keep the normal seven-day item, fourteen-day fetch, and thirty-day
  source-health retention rules. A response with zero in-region matches is a healthy source fetch,
  not a parser failure.
- Failure and enablement: malformed GeoJSON records `parser_failed`; HTTP 429 records
  `rate_limited`; oversized or failed requests fail soft. `news.enabled`, `regional.enabled`, the
  REGIONAL scope, `usgs_eq_geojson`, and `news.fetch_policy.allow_official_http` must all be true.
  The separate news timer and committed example config remain disabled. Tests mock transport and
  do not call USGS live.
- Operational smoke check, 2026-10-08 11:20 PDT: a one-time explicit scan returned HTTP 200,
  19,438 bytes, and `Last-Modified`; SQLite recorded one successful run, healthy state, and zero
  events meeting the current REGIONAL filter. An immediate repeat was interval-skipped with no
  second request. The temporary opt-in was disabled and removed, its source row persisted disabled,
  and the standing config/news timer were unchanged. A live HTTP 304 and a live in-region item
  remain unobserved; mocked/fixture tests cover both contracts.
