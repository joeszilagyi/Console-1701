# Washington NWS Active Alerts Source Signoff

Verified 2026-10-08 for the first explicit official HTTP ingest slice.

- Owner and endpoint: U.S. National Weather Service, `https://api.weather.gov/alerts/active?area=WA`.
  The [NWS alerts service documentation](https://www.weather.gov/documentation/services-web-alerts)
  describes the public active-alert API and its state-area filter. The
  [NWS API guide](https://www.weather.gov/documentation/services-web-api) requires an identifying
  User-Agent and describes JSON/GeoJSON content. A HEAD request on 2026-10-08 returned HTTP 200,
  `application/geo+json`, and an ETag without a redirect. A bounded GET returned a GeoJSON
  `FeatureCollection` with two Washington alerts; the existing LOCAL parser accepted its shape and
  correctly matched zero Seattle-area items at that moment.
- Access and policy: public official API, no authentication, no homepage extraction, no social or
  scraped content. NWS recommends no more than one request every 30 seconds; the registry interval
  is ten minutes. HTTP 429 invokes the configured backoff. Conditional ETag/Last-Modified requests
  avoid re-downloading unchanged data when supported.
- Parser and geography: `nws_alerts_json` reads alert features and filters for Seattle-area text
  or configured zones. The `area=WA` query fetches Washington alerts, not a precise household
  location. The local policy layer must be explicitly enabled; no IP/GPS inference is performed.
- Storage and sensitivity: keep bounded title, description, event URL, alert severity/timing,
  affected-zone and matching evidence in local SQLite. Do not store raw responses or precise private
  locations. Normal news retention defaults to seven days for items, fourteen for fetch runs, and
  thirty for health rows.
- Failure behavior: a malformed payload records `parser_failed`, oversized or failed requests
  record failure, and HTTP 429 records `rate_limited`. Each source fails soft. GET routes never
  invoke this transport; the separate news timer remains disabled by default.
- Enablement: `news.enabled`, `local.enabled`, the LOCAL scope, the source, and
  `news.fetch_policy.allow_official_http` must all be true. The transport additionally accepts only
  the exact verified URL, parser, source id, scope, and kind. No production source is enabled by
  this signoff or by the committed example config.
