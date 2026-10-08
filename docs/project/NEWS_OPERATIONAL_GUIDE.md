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

- The only supported live URL is documented in
  `docs/project/NWS_WASHINGTON_ALERTS_SOURCE_VERIFICATION.md`. It remains disabled unless all news,
  local, scope, source, and `allow_official_http` flags are true. Do not enable the news timer by
  default.
- Requests use HTTPS, a bounded timeout and response, an identifying User-Agent, no inherited
  proxy or cross-host redirect, conditional validators, per-source interval, and failure backoff.
- Live ingest must not hold an SQLite write transaction across the network request. Raw responses
  must not be persisted. Tests must mock transport; no live network test belongs in pytest.
- Add further live sources only after fixture coverage, explicit source signoff, allowlist review,
  and timeout/backoff rules exist for that source.
- Keep operational notes close to the code and backlog so the next pass can verify the current
  enablement boundary without reopening the design docs.
