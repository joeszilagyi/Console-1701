# News Source Verification Workflow

This workflow is the checklist to run before any recent-signal source moves from disabled metadata
to a configured ingest path.

## Verification Questions

1. Confirm endpoint ownership.
1. Confirm the access method is lawful and machine-readable.
1. Confirm source terms, robots notes, and any policy-sensitive constraints.
1. Confirm parser shape and the exact fields that will be stored.
1. Confirm rate limits and freshness expectations.
1. Confirm retention sensitivity and how quickly stored rows should expire.
1. Confirm privacy risk and whether exact locations, article bodies, or other sensitive fields are
   prohibited.
1. Confirm the verification status that should be recorded in the registry.
1. Confirm the source-health behavior for the source before any live ingest is enabled.

## Required Registry Fields

Record these fields in the source registry or source policy payload before enabling ingest:

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

## Health Behavior

Use source-health rows to describe the current state honestly:

- `disabled` for disabled config entries.
- `configured_never_run` for enabled sources with no successful ingest yet.
- `healthy` for sources that completed ingest successfully.
- `stale` when the latest health row is too old.
- `failing` for repeated ingest failures.
- `parser_failed` when the parser rejects the payload.
- `policy_blocked` when the configuration is not allowed in the current phase.
- `auth_required` when auth is declared but not configured.
- `social_disabled` and `homepage_disabled` when those gates are off.
- `manual_review_only` for sources that remain in a manual-review phase.
- `unsupported` for sources that cannot be ingested in the current phase.

## Notes

- Keep the source disabled by default until the verification checklist is complete.
- Prefer fixture-backed validation before any live ingest.
- Do not add page-load fetching while a source is still under verification.
