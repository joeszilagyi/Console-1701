# REGIONAL Source Verification Workflow

Reference design:

- `docs/project/REGIONAL_PNW_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

Use this checklist before any REGIONAL source is enabled beyond disabled metadata.

## Checklist

1. Confirm endpoint ownership.
1. Confirm the access method is lawful and machine-readable.
1. Confirm source terms, robots notes, and policy-sensitive constraints.
1. Confirm the parser shape and the exact fields that will be stored.
1. Confirm rate limits and refresh expectations.
1. Confirm retention sensitivity and how quickly stored rows should expire.
1. Confirm privacy risk and whether exact locations, article bodies, or other sensitive fields are
   prohibited.
1. Confirm geography and relevance filters for Washington, Puget Sound, Cascadia hazards, Oregon,
   BC, transport corridors, wildfire/smoke, seismic/volcano, public health, state government,
   regional news, and social sources.
1. Confirm the verification status that should be recorded in the registry.
1. Confirm the source-health behavior for the source before live ingest is enabled.

## Required Registry Fields

Record these fields before enabling any REGIONAL ingest:

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

- Keep REGIONAL sources disabled by default until the checklist is complete.
- Prefer fixture-backed validation before any live ingest.
- Do not add page-load fetching while a source is still under verification.

## Per-Source Record And Release Gate

Use the [shared per-source signoff record](NEWS_SOURCE_VERIFICATION_WORKFLOW.md#per-source-signoff-record)
for each exact REGIONAL feed or API. Add these regional decisions to its scope/ranking section:

- Name the official geography fields and state whether they identify a county, city, corridor,
  pass, ferry route, river basin, weather zone, point/radius, or only publisher jurisdiction.
- Define an out-of-region filter and a fallback for records with no reliable geography. A
  publisher's county is not automatically the impact area.
- Identify test/drill messages, inactive or ended alerts, duplicate official IDs, syndication,
  and zero-item responses before deriving public-impact or convergence scores.
- Record whether the endpoint is statewide, Washington-only, cross-border or genuinely regional;
  narrow it with documented query/filter fields when available.
- Retain only the fields required for metadata, evidence and the local UI. Explain how exact
  private locations and article bodies are excluded or redacted.

Worked decisions:

- [Washington NWS alerts](NWS_WASHINGTON_ALERTS_SOURCE_VERIFICATION.md) use official area/zone
  evidence and an exact allowlisted API URL; the registry default remains disabled.
- [WSDOT public Highway Alerts RSS](WSDOT_REGIONAL_HIGHWAY_ALERTS_RSS_VERIFICATION.md) is a
  statewide live-capable feed; its RSS location evidence is insufficient for LOCAL routing.
- [WSDOT Traveler JSON](REGIONAL_WSDOT_TRAVELER_JSON_VERIFICATION.md) has a documented schema
  and fixture parser but requires an assigned access code, so no JSON live path is enabled.
- [King County Emergency News RSS](REGIONAL_KING_COUNTY_EMERGENCY_RSS_VERIFICATION.md) has a
  verified fixture parser; test posts are classified separately and live ingest is held for its
  own exact-URL release gate.
- [Other county alert services](REGIONAL_COUNTY_EMERGENCY_SOURCE_REVIEW.md) remain disabled or
  manual-review-only until each public RSS candidate has an endpoint-specific signoff.

The shared [release gate](NEWS_SOURCE_VERIFICATION_WORKFLOW.md#release-gate) applies in full:
document the exact official URL, access policy, bounded response, fixture parser, interval,
retention, privacy and health behavior before adding a live allowlist tuple. Run only an explicit
opt-in `news-scan`; GET routes, host scans and tests must remain offline.
