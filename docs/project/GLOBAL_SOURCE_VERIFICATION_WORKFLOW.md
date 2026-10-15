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

## Per-source signoff record

Keep a separate record for each exact URL and query. Write `unknown` where evidence is missing;
unknown access, policy, or parser fields block live admission.

| Field | Record |
| --- | --- |
| Source key and family | Registry identity, class, GLOBAL scope, independent publisher family |
| Owner and source type | Official, media, nonprofit, platform, open-data, restricted, or manual-review-only |
| Exact endpoint | HTTPS URL, method, format, query, redirect behavior and owning documentation |
| Observed response | Check date, status, content type, size, validators, schema/channel/version and fixture |
| Access and policy | Terms, robots, attribution, auth/key, rate guidance and any uncertainty |
| Parser contract | Item/row cap, stored fields, identifier, publication/update time, bounded summary, no body/product download |
| Geography and relevance | Country/region evidence, cross-border or global-impact basis, source-specific filters |
| Sensitivity and ranking | Humanitarian or conflict safeguards, preliminary status, severity fields, rumor and low-value treatment |
| Retention and health | Freshness, expiry, response cap, timeout, stale/failed/rate/auth/policy states |
| Decision | `reference_only`, `fixture_only`, or `live_opt_in`; reason, blockers, reviewer/date |

For `live_opt_in`, require an exact `OFFICIAL_SOURCES` tuple, source opt-in,
`verification_status: verified`, parent news and HTTP opt-ins, a bounded parser and transport,
offline 200/304/error/gate checks, and no GET or host-scan fetch. Registry defaults remain
disabled. A different query or endpoint needs a new signoff.

## Endpoint walkthroughs

| Source | Evidence and current decision |
| --- | --- |
| GDACS | [Official API/source shape and disaster/geography fixture](GLOBAL_GDACS_SOURCE_VERIFICATION.md). `fixture_only`; no exact live endpoint has passed the HTTP release gate. |
| WHO Disease Outbreak News | [Official OData shape and bounded health metadata](GLOBAL_WHO_DON_SOURCE_VERIFICATION.md). `fixture_only`; global jurisdiction and preliminary status must remain explicit. |
| ReliefWeb | [Disaster/report API and humanitarian contract](GLOBAL_RELIEFWEB_SOURCE_VERIFICATION.md). `fixture_only`; broad report searches need strict filters, row caps and public-impact evidence before live access. |
| USGS global earthquake feed | [Official GeoJSON shape and magnitude/geography rules](GLOBAL_USGS_GEOJSON_SOURCE_VERIFICATION.md). `fixture_only` for GLOBAL; the separately signed-off domestic USGS feed does not automatically authorize a GLOBAL query. |
| UN News and Press | [UN News](GLOBAL_UN_NEWS_RSS_SOURCE_VERIFICATION.md) and [UN Press](GLOBAL_UN_PRESS_RSS_SOURCE_VERIFICATION.md) exact RSS shapes. `fixture_only`; event type, source family, routine content and syndication must be checked per feed. |
| IAEA Top News | [Official RSS shape and nuclear-safety filter](GLOBAL_IAEA_RSS_SOURCE_VERIFICATION.md). `fixture_only`; routine agency stories do not imply incidents. |

Before promotion, update the linked source record with response and policy evidence for the exact
endpoint, then test the source-level and parent gates. Source-health should show the blocker
without attempting access.
