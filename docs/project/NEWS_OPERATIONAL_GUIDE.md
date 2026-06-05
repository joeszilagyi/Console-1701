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

- `console-1701 news-scan` runs the fixture-backed ingest path and records source state, purge
  evidence, and item evidence in SQLite.
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

## Future Live Ingest

- Add live ingest only after fixture coverage, explicit source policy, and timeout/backoff rules
  exist for the source family.
- Keep operational notes close to the code and backlog so the next pass can verify the current
  enablement boundary without reopening the design docs.
