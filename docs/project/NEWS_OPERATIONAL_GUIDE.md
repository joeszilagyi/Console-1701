# News Operational Guide

Use this guide when updating configuration, source policy, retention, or ingest behavior for the
news stack.

## Baseline Rules

- Keep news disabled by default unless a specific source and scope are explicitly configured.
- Treat page loads as SQLite/config reads only. Do not fetch external sources during GET requests.
- Prefer fixture-backed parsing and local test fixtures before any live network work.
- Keep homepage extraction disabled unless `news.fetch_policy.allow_homepage_extractors` is true.
- Keep social sources disabled unless `local.allow_social_sources` is true.

## Operational Commands

- `console-1701 news-scan` runs fixture ingest and, only after explicit opt-in, the allowlisted
  Washington NWS official HTTPS feed. It records source state, purge evidence, and item evidence in
  SQLite. The web and host scanner never fetch this feed.
- `console-1701 news-sources` prints the current source registry, source policy, and source-health
  metadata.
- A one-off NWS smoke check can use a temporary config under the console config directory with
  only `nws_active_alerts_api` enabled. Check the source policy before the command, then inspect
  the fetch run, health, item count, and purge evidence afterward. Disable the source and all
  opt-ins before removing the temporary file; leave the news timer off unless recurring ingest
  has been explicitly requested. The 2026-10-08 first live check is recorded in the NWS signoff.

## Retention And Purge

- Retention is recent-signal oriented, not archival.
- Purge evidence is stored in SQLite and exposed through the system health views.
- When adjusting retention, keep the purge behavior deterministic and visible in the database state.

## Source Health

- Keep source-health states honest.
- Distinguish `disabled`, `not_configured`, `configured_never_run`, `healthy`, `stale`,
  `failing`, `parser_failed`, `policy_blocked`, `robots_blocked`, `auth_required`,
  `rate_limited`, `unsupported`, and `manual_review_only`.
- Surface source-health changes in the CLI and scope pages before enabling any live fetch path.

## Official HTTP Boundary

- The only supported live URLs are documented in the NWS and USGS source signoffs. NWS is available
  to LOCAL and REGIONAL; USGS M2.5+ past-day GeoJSON is REGIONAL only. LOCAL requires
  `local.enabled`; REGIONAL requires `regional.enabled`. Each also requires news, its scope, source,
  and `allow_official_http` flags. Do not enable the news timer by default.
- Requests use HTTPS, a bounded timeout and response, an identifying User-Agent, no inherited
  proxy or cross-host redirect, conditional validators, per-source interval, and failure backoff.
- If both scopes use the NWS URL, one response is shared within the explicit scan while item and
  health evidence remains scope-specific. The URL-level interval/backoff gate prevents a newly
  enabled scope from immediately issuing another request. A new scope without a prior live success
  forces an unconditional response so a 304 cannot leave its initial item set empty.
- The USGS feed has a magnitude floor of 2.5. A live REGIONAL USGS config below that threshold is
  blocked instead of silently omitting events. The parser also discards non-earthquake event types
  and out-of-region features. A successful zero-match response is healthy, not a failure.
- Live ingest must not hold an SQLite write transaction across the network request. Raw responses
  must not be persisted. Tests must mock transport; no live network test belongs in pytest.
- Add further live sources only after fixture coverage, explicit source signoff, allowlist review,
  and timeout/backoff rules exist for that source.
- Keep operational notes close to the code and backlog so the next pass can verify the current
  enablement boundary without reopening the design docs.
