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
- Enablement: `news.enabled`, `news.fetch_policy.allow_official_http`, and the selected scope and
  source must all be true. LOCAL also requires `local.enabled` and source id
  `nws_active_alerts_api`; REGIONAL requires `regional.enabled` and source id
  `nws_active_alerts_wa`. The transport accepts only this exact verified URL, parser, kind, and
  scope/id pair. If both scopes are selected, one upstream response is shared per scan. No
  production source is enabled by this signoff or by the committed example config.
- Operational smoke check, 2026-10-08 11:00 PDT: a one-time config in the console config directory
  enabled only this source for an explicit `news-scan`. The request returned HTTP 200, GeoJSON
  metadata of 8,185 bytes, and an ETag. The source recorded `success`/`healthy`, zero Seattle-area
  matching items, and a retention purge with zero deletions. An immediate second command skipped
  the source under its ten-minute interval and created no second fetch run. The temporary opt-in
  was then disabled and removed; the stored source is disabled, the standing config was unchanged,
  and the separate news timer remains disabled. This does not validate HTTP 304 or live alert-item
  persistence, which require a later eligible unchanged response or a Seattle-relevant alert.
- REGIONAL smoke check, 2026-10-08 11:11 PDT: a one-time REGIONAL-only config under the console
  config directory enabled this same exact URL for one explicit command. It returned HTTP 200,
  8,185 bytes, and an ETag; SQLite recorded two Washington alert items in two separate official-ID
  event clusters, `success`/`healthy` state, and non-fixture evidence. An immediate repeat made no
  request under the ten-minute interval. The temporary opt-in was disabled and removed, the stored
  REGIONAL source is disabled, the standing config was unchanged, and the news timer is disabled.
  Two equal alert headlines carried distinct official IDs, so they were not falsely merged.
  A live HTTP 304 remains unobserved.
