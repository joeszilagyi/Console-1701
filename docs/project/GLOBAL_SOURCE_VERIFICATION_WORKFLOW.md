# GLOBAL Source Verification Workflow

Reference design:

- `docs/project/GLOBAL_WORLD_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

Use this checklist before any GLOBAL source is enabled beyond disabled metadata.

## Checklist

1. Confirm endpoint ownership.
1. Confirm the access method is lawful and machine-readable.
1. Confirm source terms, robots notes, and policy-sensitive constraints.
1. Confirm the parser shape and the exact fields that will be stored.
1. Confirm auth or key requirements, if any.
1. Confirm rate limits and refresh expectations.
1. Confirm retention sensitivity and how quickly stored rows should expire.
1. Confirm privacy risk and whether exact locations, article bodies, or other sensitive fields are
   prohibited.
1. Confirm geography and relevance filters for global, national, regional, media, nonprofit,
   platform, and manual-review-only sources.
1. Confirm the verification status that should be recorded in the registry.
1. Confirm the source-health behavior for the source before live ingest is enabled.

## Required Registry Fields

Record these fields before enabling any GLOBAL ingest:

- `source_key`
- `source_family`
- `source_class`
- `adapter`
- `scope`
- `official_status`
- `expected_access_kind`
- `verification_status`
- `policy_risk`
- `parser_risk`
- `privacy_risk`
- `retention_sensitivity`
- `future_phase`

## Source Health States

Keep the status honest:

- `disabled`
- `not_configured`
- `configured_never_run`
- `healthy`
- `stale`
- `failing`
- `parser_failed`
- `policy_blocked`
- `robots_blocked`
- `auth_required`
- `rate_limited`
- `unsupported`
- `manual_review_only`

## Notes

- Keep GLOBAL sources disabled by default until the checklist is complete.
- Prefer fixture-backed validation before any live ingest.
- Do not add page-load fetching while a source is still under verification.
