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

## Per-Source Signoff Record

Create `docs/project/<SCOPE>_<SOURCE>_SOURCE_VERIFICATION.md` before adding a live allowlist
entry. Keep the record even when the result is `blocked` or `reference_only`. Use these headings:

1. **Decision and date:** verified for fixture only, eligible for exact live allowlist, or blocked.
   State the unresolved question if blocked.
2. **Owner and exact endpoint:** publishing agency, HTTPS URL including query parameters, method,
   response format and content type, redirect behavior, authentication, and the official page that
   documents or links the endpoint. Distinguish an observed response from an API inferred from a
   website.
3. **Access policy:** source terms and robots notes, attribution, published rate limits or the
   conservative proposed cadence when none is published, and any commercial or redistribution
   constraint. Record the date of the policy read.
4. **Bounded sample and parser contract:** sample status/content type/size, root and item shape,
   stable IDs, time fields, URL fields, optional fields, pagination, errors, and a local fixture
   path. List stored fields and excluded fields; never commit a raw response that contains private
   material.
5. **Scope and ranking:** geographic filter, event relevance threshold, duplicate key, expiry,
   ranking signals, and how a zero-item response differs from a failed response.
6. **Privacy and retention:** exact-location policy, body or narrative storage rule, retention
   days for items/fetch runs/health, and any redaction evidence.
7. **Enablement and failure states:** exact scope/key/URL/parser/kind allowlist tuple, required
   config gates, interval and backoff, conditional requests if supported, `parser_failed`,
   `rate_limited`, `policy_blocked`, `stale`, and empty/success behavior. State that GET routes,
   host scans, and tests cannot fetch.
8. **Verification:** fixture tests, policy and no-fetch tests, bounded manual probe result if one
   was done, and limitations. Record whether a live smoke check actually ran; an offline test is
   not a live observation.

The [Washington NWS signoff](NWS_WASHINGTON_ALERTS_SOURCE_VERIFICATION.md) is a completed
first-source example. The [LOCAL FAA/NAS research](../../BACKLOG.md#faasea-airport-status-research)
illustrates a verified XML endpoint held reference-only until an XML parser and SEA filter exist.
The [REGIONAL workflow](REGIONAL_SOURCE_VERIFICATION_WORKFLOW.md) adds area-specific checks;
scope-specific workflows supplement this record rather than replacing it.

## Release Gate

Only promote a source from disabled metadata after the signoff identifies an exact official
machine-readable endpoint, a bounded fixture parser, scope/retention/privacy behavior, and policy
test coverage. Add the exact tuple to `official_http.py` only for an eligible official live source.
Keep the registry and example configuration disabled; operators must opt in and run `news-scan`.
If any required evidence is missing, record the blocker and leave the source reference-only or
manual-review-only. A successful direct research request alone is not permission to add live
ingestion.

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
