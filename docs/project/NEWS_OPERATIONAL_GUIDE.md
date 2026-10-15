# News Operational Guide

Use this guide when updating configuration, source policy, retention, or ingest behavior for the
news stack.

## Baseline Rules

- Keep news disabled by default unless a specific source and scope are explicitly configured.
- Treat page loads as SQLite/config reads only. Do not fetch external sources during GET requests.
- Prefer fixture-backed parsing and local test fixtures before any live network work.
- Keep homepage extraction disabled unless `news.fetch_policy.allow_homepage_extractors` is true.
- Keep social sources disabled unless their scope's explicit `allow_social_sources` flag is true.

## Operational Commands

- `console-1701 news-scan` runs fixture ingest and, only after explicit opt-in, allowlisted
  official HTTPS feeds. It records source state, purge evidence, and item evidence in
  SQLite. The web and host scanner never fetch this feed.
- `console-1701 news-sources` prints the current source registry, source policy, and source-health
  metadata.
- Start from `config.example.yml` or a minimal local YAML file. A live source needs
  `news.enabled`, its scope's `enabled`, the scope policy flag (`local`, `regional`, `national`,
  `global`, or `orbital`), the individual source's `enabled`, the exact source URL,
  `verification_status: verified`, and `news.fetch_policy.allow_official_http`. A configured
  source without every gate stays disabled/blocked and does not make a network request.
- Check a candidate with `console-1701 news-sources --config /path/to/config.yml` before an
  explicit `console-1701 news-scan --config /path/to/config.yml`. Review the scope's source-health
  panel or `news-sources` afterward for fetch status, last success, policy, parser, item count and
  errors. A successful scan can yield zero matching items.
- A one-off NWS smoke check can use a temporary config under the console config directory with
  only `nws_active_alerts_api` enabled. Check the source policy before the command, then inspect
  the fetch run, health, item count, and purge evidence afterward. Disable the source and all
  opt-ins before removing the temporary file; leave the news timer off unless recurring ingest
  has been explicitly requested. The 2026-10-08 first live check is recorded in the NWS signoff.

## Retention And Purge

- Retention is recent-signal oriented, not archival.
- News item, fetch-run and source-health defaults are 7, 14 and 30 days respectively under
  `news.retention`. ORBITAL item retention is capped at seven days; redacted sensitive ORBITAL
  records are capped at one day. Source-specific shorter retention can apply.
- Each ingest pass purges expired rows. Per-item `expires_at` and the last purge counts/time are
  stored in SQLite and exposed in item evidence and SYSTEM/source-health views. Run an explicit
  `news-scan`, then check those fields in the UI or source audit when changing retention. The
  ordinary host `scan` does not run news retention.
- When adjusting retention, keep the purge behavior deterministic and visible in the database state.

## Source Health

- Keep source-health states honest.
- Distinguish `disabled`, `not_configured`, `configured_never_run`, `healthy`, `stale`,
  `failing`, `parser_failed`, `policy_blocked`, `robots_blocked`, `auth_required`,
  `rate_limited`, `unsupported`, and `manual_review_only`.
- Surface source-health changes in the CLI and scope pages before enabling any live fetch path.

## Official HTTP Boundary

- `console1701/news/official_http.py` is the exact `(scope, source id, URL, kind, parser)`
  allowlist. Current opt-in entries are NWS Washington active alerts for LOCAL/REGIONAL, USGS
  M2.5+ day GeoJSON for REGIONAL/NATIONAL, WSDOT Highway Alerts RSS for REGIONAL, and ORBITAL
  NOAA SWPC alerts/scales/K-index/OVATION, six NASA news/Station/Artemis/Kennedy RSS feeds,
  and two ESA RSS feeds. All remain disabled in default config. GLOBAL has fixture parsers and
  signoff work but no allowlisted live endpoint; Solar System and Beyond has a disabled config
  foundation and no ingest scope yet. Do not enable the news timer by default.
- Source verification documents in `docs/project/` explain each exact endpoint, parser, response
  and policy boundary. A registry entry or working fixture is not live authorization. JPL CNEOS
  APIs, ESA reentry predictions, launch-provider pages, NASA/JPL direct RSS, and other unlisted
  candidates cannot be fetched by changing a config URL.
- Requests use HTTPS, a bounded timeout and response, an identifying User-Agent, no inherited
  proxy or cross-host redirect, conditional validators, per-source interval, and failure backoff.
- If both scopes use the NWS URL, one response is shared within the explicit scan while item and
  health evidence remains scope-specific. The URL-level interval/backoff gate prevents a newly
  enabled scope from immediately issuing another request. A new scope without a prior live success
  forces an unconditional response so a 304 cannot leave its initial item set empty.
- The USGS feed has a magnitude floor of 2.5. A live REGIONAL or NATIONAL USGS config below that
  threshold is blocked instead of silently omitting events. The parser also discards
  non-earthquake event types and out-of-region features. NATIONAL uses coarse U.S./territory
  coordinate relevance; it does not prove cross-border or multi-state impact. A successful
  zero-match response is healthy, not a failure.
- ORBITAL opt-ins keep source-specific freshness limits. Alerts, NOAA scales, K-index, OVATION,
  and NASA/ESA RSS have parser and mocked-transport tests; OVATION also requires configured
  LOCAL/REGIONAL coordinate windows and stores only a bounded modeled signal, not the grid.
  No application live ORBITAL scan is claimed by those tests.
- Live ingest must not hold an SQLite write transaction across the network request. Raw responses
  must not be persisted. Tests must mock transport; no live network test belongs in pytest.
- Add further live sources only after fixture coverage, explicit source signoff, allowlist review,
  and timeout/backoff rules exist for that source.
- Keep operational notes close to the code and backlog so the next pass can verify the current
  enablement boundary without reopening the design docs.
