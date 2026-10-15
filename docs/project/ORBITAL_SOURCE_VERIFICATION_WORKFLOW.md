# ORBITAL Source Verification Workflow

Reference design:

- `docs/project/ORBITAL_SPACE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

Use this checklist before any ORBITAL source is enabled beyond disabled metadata.

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
1. Confirm orbital-domain filters and source family/class labeling.
1. Confirm tactical or sensitivity review for the source.
1. Confirm the verification status that should be recorded in the registry.
1. Confirm the source-health behavior for the source before live ingest is enabled.

## Required Registry Fields

Record these fields before enabling any ORBITAL ingest:

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

- Keep ORBITAL sources disabled by default until the checklist is complete.
- Prefer fixture-backed validation before any live ingest.
- Do not add page-load fetching while a source is still under verification.

## Per-source signoff record

Keep one record per exact endpoint. A verified parser shape does not by itself approve live
access. Write `unknown` for facts that have not been checked; an unknown policy or access field
blocks live allowlisting.

| Field | Record |
| --- | --- |
| Source key and scope | Registry key; `ORBITAL` |
| Owner and official status | Owning organization; official, provider, media, nonprofit, platform, restricted, open-data, or manual review |
| Exact URL and access method | HTTPS URL, format, request method; distinguish public feed from page or authenticated API |
| Verification evidence | Official directory or product page, date checked, observed response status, content type, shape and version |
| Terms and robots/policy | Direct source links and any applicable restrictions; record unknowns explicitly |
| Auth and rate | Key/account requirement, published rate guidance, conditional requests and local refresh interval |
| Parser and fields | Parser name, fixture, schema/channel checks, bounded stored fields, item cap, freshness limit |
| Scope and identity | ORBITAL domain filter, source family/class, event/object/mission IDs and duplicate-family rule |
| Safety | Tactical, privacy, reentry/debris, rumor and sensitivity treatment; excluded content |
| Health and retention | Disabled/blocked/failing/stale behavior, response cap, expiry and purge path |
| Decision | `reference_only`, `fixture_only`, or `live_opt_in`; reason, remaining blockers and reviewer/date |

For `live_opt_in`, require an exact `OFFICIAL_SOURCES` tuple, a source-level opt-in,
`verification_status: verified`, parent news and HTTP opt-ins, bounded response and timeout,
offline transport tests, and no GET/host-fetch path. Keep the registry default disabled. A
request to a different endpoint or with a different query is a new signoff.

## Endpoint walkthroughs

These records demonstrate the signoff boundary and link to the endpoint-specific evidence.

| Source | Evidence and parser | Decision and remaining constraint |
| --- | --- | --- |
| NOAA SWPC alerts JSON | [Official product and observed shape](ORBITAL_SWPC_ALERTS_SOURCE_VERIFICATION.md); `swpc_alerts_json` fixture parser, validity and cancellation evidence. | `live_opt_in` for the exact alerts URL with a 72-hour source-time window. Default stays disabled; application live scan has not been run. |
| ESA Top News and Human Spaceflight RSS | [ESA directory, two exact channels and fixtures](ORBITAL_ESA_RSS_SOURCE_VERIFICATION.md); `esa_orbital_rss` verifies channel, official article URL and publication time. | `live_opt_in` for the two exact URLs with seven-day freshness. Reentry and debris headlines remain excluded pending separate review. |
| NASA/JPL RSS candidate | [NASA feed checks and unresolved JPL response](ORBITAL_NASA_RSS_SOURCE_VERIFICATION.md). | Six NASA channels have `live_opt_in`; the JPL RSS candidate remains `reference_only` after a 403 response. It must not inherit NASA approval. |
| JPL CNEOS CAD and fireball APIs | [CAD](ORBITAL_JPL_CAD_SOURCE_VERIFICATION.md) and [fireball](ORBITAL_JPL_FIREBALL_SOURCE_VERIFICATION.md) field-array fixtures. | `fixture_only`. Exact bounded query, application-specific user agent/contact, fair-use rate behavior and live transport still need signoff. |

Before changing one of these decisions, record the new evidence in its source document and test
the exact transport/config combination. Source health should state the blocker instead of
attempting access.
