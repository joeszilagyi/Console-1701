# NATIONAL Source Verification Workflow

Reference design:

- `docs/project/NATIONAL_US_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`
- [Shared per-source signoff record and release gate](NEWS_SOURCE_VERIFICATION_WORKFLOW.md)

Use this checklist before any NATIONAL source is enabled beyond disabled metadata.

The registry is a candidate inventory. `official_page_seen`, a parseable fixture, or a successful
research GET does not by itself admit a live source. A NATIONAL live source needs a signed exact
scope/key/URL/kind/parser tuple in `official_http.py`, a disabled registry default, an explicit
`news-scan` opt-in, and a worked per-source record linked below.

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
1. Confirm agency, sector, and state filters for the source.
1. Confirm the verification status that should be recorded in the registry.
1. Confirm the source-health behavior for the source before live ingest is enabled.

## NATIONAL Scope Decisions

For each source record, resolve these fields rather than filling them from a headline:

| Decision | Evidence to record | Conservative default |
| --- | --- | --- |
| Agency and sector | Issuer, source family, official class, allowed agency/sector IDs, and whether a linked page is merely a document host | Do not treat hosted press material as a structured alert |
| U.S. geography | Source-provided state/territory/zone/airport/distribution/jurisdiction fields and whether the event is truly national or multi-state | Keep place text and coarse coordinates labeled as unverified impact |
| Public action | Source severity/classification, instructions, effective/expiry dates, affected units or systems, and any legal action window | Do not infer severity or action from the title |
| Filtering | Agency, release, product, economic series, document type, and impact allowlists needed to avoid routine volume | Suppress or leave disabled when filters are missing |
| Authentication | Public endpoint or local key; key storage, key absence state, quota/rate terms, and whether one request is useful | `auth_required` and no request when credentials are absent |
| Sensitivity | Individual/private locations, health details, article bodies, legal/market implications, retention and attribution | Store bounded metadata only; no investment advice or private detail |
| Health | Published cadence or conservative interval, 200/304/empty behavior, 429/backoff, schema failure and stale threshold | A successful zero-filter-match fetch is healthy, not an invented event |

The first-pass NATIONAL source-specific admission boundary is one verified USGS feed. Other
candidate URLs remain disabled while endpoint behavior or filters are unresolved. Source status
must describe the actual evidence: `verified` only after the exact feed, parser, policy gates,
fixture and live-path checks are recorded; `official_page_seen` remains a research status.

## Worked Decisions

- [USGS M2.5+ day live signoff](NATIONAL_USGS_LIVE_SOURCE_SIGNOFF.md): exact official feed,
  M5.0 NATIONAL default, coarse U.S./territory coordinate filter, isolated HTTP 200 smoke check,
  and disabled-by-default opt-in.
- [NHTSA recall lookup verification](NATIONAL_NHTSA_RECALL_API_VERIFICATION.md): official
  campaign lookup and high-risk fields are fixture-tested; lookup is not a recent recall discovery
  feed, so live admission is still closed.
- [CISA KEV research](NATIONAL_CISA_KEV_ENDPOINT_RESEARCH.md): official JSON and due-date
  semantics are known; the full snapshot and rollout/cadence policy need a separate live decision.
- [CISA advisory feed verification](NATIONAL_CISA_ADVISORY_ENDPOINT_BLOCKER.md): an exact
  CISA-hosted RSS feed and fixture parser are verified, while its 1.24 MB snapshot exceeds the
  default live fetch cap; live admission remains closed.
- [CDC HAN blocker](NATIONAL_CDC_HAN_ENDPOINT_BLOCKER.md): no verified current
  machine-readable item shape from the tested paths; no invented fixture or live request.
- [FDA recall source review](NATIONAL_FDA_RECALL_SOURCE_VERIFICATION.md): RSS metadata lacks
  classification, severity and distribution, so title metadata must not become a high-risk claim.
- [FAA NAS XML fixture](NATIONAL_FAA_NAS_XML_FIXTURE_VERIFICATION.md),
  [Federal Register filtered API](NATIONAL_FEDERAL_REGISTER_API_FIXTURE_VERIFICATION.md), and
  [GovInfo RSS collections](NATIONAL_GOVINFO_RSS_FIXTURE_VERIFICATION.md): official shapes have
  offline adapters; source-specific live admission and filters remain separate.
- FSIS and CPSC direct endpoint probes were blocked (HTTP 403 and timeout, respectively) in the
  RS-041/RS-042 work. Their parser shape and live access remain unresolved in `BACKLOG.md`.

Before changing a candidate to live, link its record from this list and verify the exact tuple,
registry status, disabled config, policy gate, no-fetch GET/host-scan tests, source health, bounded
storage, and an isolated explicit smoke result when a live request is appropriate. Record a
blocked decision with the exact failed endpoint/status and next evidence needed; continue other
sources without relaxing the gate.

## Required Registry Fields

Record these fields before enabling any NATIONAL ingest:

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

- Keep NATIONAL sources disabled by default until the checklist is complete.
- Prefer fixture-backed validation before any live ingest.
- Do not add page-load fetching while a source is still under verification.
