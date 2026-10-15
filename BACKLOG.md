# BACKLOG

This file tracks requested or discovered work that has not been implemented yet. Keep it current
whenever new ideas come up and are not completed immediately.

## Current Baseline

- The homepage is host-first: Debian install, machine identity, hardware, storage, network,
  services, processes, logs, power/thermal, developer tools, raw evidence, and local work below.
- Host snapshots are persisted in SQLite via `host_snapshots`.
- Normal scans run the safe system probe and preserve existing repo scan behavior.
- `/api/host` and `/api/host/history` expose persisted host state.
- `/api/live` exposes local live sensor state for the top lane without external network calls.
- The top sensor lane currently covers System, Network, CPU/RAM, and Filesystem with live bars,
  five-minute page-session trend traces, local health colors, adaptive polling, and inline
  explanations.
- Alert rows can launch a user-clicked local terminal with an interactive Codex scenario.
- The local delta image is displayed from `console1701/static/codex-alert-delta.png`.
- Recent-signal/news support remains disabled by default: `news:` config validation rejects unsafe
  shapes, SQLite metadata tables exist, storage helpers expose disabled/not-configured states, and
  explicit fixture ingest exists, and three exact official HTTPS feed URLs are available behind opt-in
  gates.
- `console-1701 news-scan` provides explicit local-fixture ingest for enabled `file://`
  JSON/RSS/Atom/homepage sources, updates source health/fetch runs/items/clusters in SQLite, and
  performs retention purge even when news is disabled.
- A first official HTTP path exists for the exact verified Washington NWS alerts endpoint in LOCAL
  and REGIONAL. It remains disabled by default and requires explicit news, scope-policy, source,
  and HTTP opt-ins. The two scopes share one upstream request per scan.
- REGIONAL USGS earthquake GeoJSON now has an exact-URL opt-in live path with M2.5+ past-day feed
  signoff, regional/magnitude filtering, and the same disabled-by-default policy.
- REGIONAL WSDOT Highway Alerts RSS has an exact-URL opt-in live path using the public official
  feed, numeric alert IDs, bounded sanitized headlines, and source-specific snapshot retirement.
  WSDOT's separate JSON API still requires an access code and remains disabled.
- A disabled-by-default `local:` policy config now exists for Seattle-specific inclusion flags,
  hazard thresholds, and explicit social/neighborhood-blog allowances.
- A static LOCAL source registry now seeds disabled metadata for core official, blog, and
  policy-sensitive social candidates without fetching.
- LOCAL fixture parsing now includes an NWS active-alert JSON parser with Seattle/King/Puget Sound
  filtering and alert severity evidence.
- LOCAL fixture parsing now includes a King County Metro RSS parser with route, service-area, and
  transit-impact evidence.
- LOCAL fixture parsing now includes an SFD Fire 911 Socrata parser with privacy-safe location
  tokens and low-acuity redaction evidence.
- LOCAL fixture parsing now includes a WSDOT traveler-alert JSON parser with Seattle corridor
  filtering and public-impact evidence.
- LOCAL fixture parsing now includes an AlertSeattle RSS parser with official city-alert event and
  severity evidence.
- LOCAL fixture parsing now includes a neighborhood-blog RSS parser with explicit config gating,
  neighborhood matching, and headline-metadata-only evidence.
- LOCAL fixture parsing now includes City Light outage JSON and FAA/SEA airport status JSON fixture
  parsers with LOCAL utility and airport-impact evidence.
- LOCAL deterministic ranking now consumes parser evidence for official alerts, public impact,
  transit impact, utility impact, airport impact, neighborhood-blog signal, and privacy penalties.
- `/api/news/summary`, `/api/news/scopes/{scope}`, `/api/news/sources`, and `/api/news/items/{id}`
  now expose SQLite-backed recent-signal state without triggering fetches.
- OVERVIEW, LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, and SYSTEM now render real
  disabled/not-configured/source-backed recent-signal panels instead of placeholder bays.
- `console-1701 news-sources` lists configured source policy and health state without fetching.
- General scan history now has 90-day bounded retention, a preview/apply maintenance command, and
  an automatic small prune on each scan. The latest host and per-repo evidence is preserved.
- Pytest now uses temporary console state, and scans release the SQLite write transaction before
  running configured tests.

## Host Operations Follow-Up

### Failed x11vnc System Service

Status: needs owner review; outside console-1701 service recovery.

The 2026-10-08 live host snapshot remains `CAUTION` (score 85) because the unrelated system unit
`x11vnc.service` is failed. Its recorded May 11 log says `-auth guess: failed for display=':0'`.
Confirm whether this VNC service is still wanted before changing its configuration or state. If
wanted, inspect its systemd unit and display/auth setup, then verify it starts cleanly; if retired,
have the host owner disable it so the console reports host health accurately. Do not treat this as
a console web-service or scanner failure.

## GitHub Merge Gate

Status: implemented.

A read-only GitHub Actions `tests-and-lint` job now runs pytest and Ruff for PRs and `main`. Its
first PR run exposed and resolved a timezone-dependent test, and the rerun plus merged `main` push
passed. The existing `main-protection` ruleset now targets the default branch, requires that check
from the GitHub Actions app, requires PRs, and blocks deletion/force-push. Its dormant
linear-history rule was removed to retain the project's merge-commit practice. GitHub's effective
branch-rules endpoint returns the expected four rules for `main`.

## Scoped Recent Signal / News Ingestion

Architecture reference:

- `docs/project/NEWS_SCOPE_INGESTION_ARCHITECTURE_DESIGN.md`

### Disabled-By-Default News Config

Status: implemented.

Add a `news:` config tree that defaults to fully disabled. Include retention, fetch policy, scope,
and source definitions. Reject page-load external fetching, unknown scopes, unknown source kinds,
and homepage extraction unless explicitly allowed. Update `config.example.yml` with disabled example
sources only and no live source enabled by default.

### News SQLite Schema

Status: implemented.

Add JSON-heavy SQLite tables for recent signal state:

- `news_sources`
- `news_fetch_runs`
- `news_items`
- `news_clusters`
- `news_source_health`

Include indexes for latest-by-scope, latest-by-source, source health, retention purge by
`expires_at`, and dedupe by normalized URL hash. Do not store full article bodies by default.

### Local Fixture Ingest Harness

Status: implemented.

Create a news ingest path that reads local RSS/Atom/JSON/homepage fixtures only. This phase must not
make network calls. It should normalize fixture items into SQLite, update source health, run
retention purge, and provide deterministic evidence for each item.

### Parser Tests

Status: implemented.

Add tests for RSS fixtures, Atom fixtures, JSON API fixtures, homepage fixture selectors,
malformed feeds, huge payload rejection/truncation, bounded title/description lengths, timestamp
normalization, and fail-soft parser errors.

### Source Policy And Robots Evidence Layer

Status: implemented.

Add a policy module that records source basis, source kind, enablement, auth requirement state,
homepage-extractor allowance, robots decisions when applicable, and policy notes. Homepage extraction
must be blocked unless explicitly enabled and must record robots evidence when used. Robots handling
is an operational courtesy, not a legal shield.

Current state: source policy is recorded in `news_sources.policy_json`, surfaced in API/UI/CLI, and
includes fixture, allowlisted official HTTP, and blocked-live bases; source kind, enablement, auth
state, homepage-extractor allowance, and a robots placeholder state. The NWS official API does not
require robots checking; live homepage robots fetch/decision evidence is still pending.

### Retention Purge

Status: implemented.

Add deterministic purge logic for expired news items, old fetch runs, old source health rows, and any
future raw-payload debug rows. Default intent: recent awareness, not archive. Expose retention policy
and last purge evidence in SYSTEM.

Current state: SQLite purge runs during `console-1701 news-scan` for items, fetch runs, and source
health. SYSTEM now shows last purge evidence, retention state basics, before/after row counts, and
cutoff timing. Any future raw-payload debug retention and deeper historical purge audit views are
still pending.

### Deterministic Ranking

Status: implemented for first pass.

Add explainable ranking with no LLM calls. Candidate factors: recency, source priority, official
source boost, scope priority, user-pinned tags, repeated topic/cluster count, source-provided alert
severity, item freshness, and source health confidence. Store ranking factors in evidence.

Current state: fixture ingest now stores explicit ranking factors and reasons in item evidence for
source priority, recency, freshness, official-tag boost, scope priority, repeat observations, tag
density, prior source-health confidence, source-provided severity, and topic repetition. Event
merging now records the topic-repetition contract alongside the existing cluster-size and
cross-source signals. LOCAL event-correlation now also applies a capped, explainable
`local_source_family_boost` for trusted official and local-news families. The
candidate factor set and stored reasons are present; finer scope-specific
severity normalization is a later ranking refinement.

### Scope Page UI

Status: implemented.

Replace non-INTERNAL placeholder bays with real disabled/not-configured/source-backed panels when
news support exists. LOCAL, REGIONAL, NATIONAL, GLOBAL, and ORBITAL should share a compact template
partial where possible. Do not show fake headlines or demo data.

### OVERVIEW Synthesis Bays

Status: implemented.

Turn OVERVIEW into a cross-scope synthesis surface with four initial bays: Attention now, Local and
regional pulse, National and global pulse, and Orbital and source health. Local, INTERNAL, and SYSTEM
urgent items should not be buried under broad distant headlines.

### SYSTEM Source Health Bay

Status: implemented.

Add SYSTEM panels for source ingest status, stale sources, failed parsers, disabled sources, last
successful fetch by source/scope, retention state, DB size, source table counts, config validation
warnings, and evidence that page loads do not perform external fetches.

Current state: SYSTEM now shows source ingest status, derived source-state counts, scope readiness,
source policy/health rows, short fetch/health transition history, table counts, last
finished/successful ingest timestamps, purge evidence, page-load safety evidence, DB size, and
derived config warnings.

### Official API/RSS First Live Ingest

Status: implemented for first pass.

After fixture ingest and tests exist, add explicit enabled HTTP fetch for safe official APIs/RSS only.
Use timeouts, response size caps, per-source intervals, backoff, ETag/Last-Modified support, honest
user agent, and fail-soft per-source behavior. Tests must use mocked HTTP or a local test server, not
live network.

Current state: an allowlisted, explicit HTTPS client supports exact verified official URLs across
LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, and COSMIC. It has bounded
timeout/response size, a User-Agent, no redirects or inherited proxy, conditional ETag/Last-Modified
requests, URL-level interval/backoff, local SQLite evidence, and mocked transport tests. LOCAL and
REGIONAL share the NWS response in one scan. Isolated explicit NWS, USGS, ESA, and SWPC scans
returned HTTP 200 and healthy state, with source-backed items in multiple scopes. Temporary
opt-ins were removed; default config and news timer remain disabled. Live HTTP 304 remains
unobserved, while mocked 304 handling is covered. Each additional URL requires a separate
source-specific signoff.

### Homepage Extractor Later And Disabled

Status: partially implemented.

Add homepage headline extraction only after API/RSS support is stable. Keep it disabled unless
`allow_homepage_extractors` is true. Require per-source selectors, no recursive crawling, bounded
payloads, robots/policy evidence, and no article body archive.

Current state: fixture parsing for `homepage_selectors` already exists, and
`news.fetch_policy.allow_homepage_extractors` blocks live homepage sources by default. The remaining
work is the live crawler/fetch path, robots checks for configured homepages, and the per-source
selector inventory for real production domains.

### Social Adapters Later And Terms-Sensitive

Status: partially implemented.

Treat social sources as terms-sensitive. Bluesky/AT Protocol is the preferred first candidate if
social signals are needed. Reddit and X require explicit compliant access methods. Do not scrape HTML
to bypass platform APIs, auth, paywalls, rate limits, or bot controls. Keep retention short.

Current state: local config already requires `allow_social_sources` before social candidates can be
enabled, the built-in registry keeps social entries disabled by default, and `manual_review_only`
paths exist for policy-sensitive candidates. The remaining work is a compliant live social adapter
and retention policy for any future enabled social source.

### Documentation Update

Status: completed 2026-10-15 for first-pass operations.

When news scaffolding exists, update README, config documentation, safety notes, and command help to
explain disabled-by-default behavior, page-load SQLite-only reads, explicit ingest commands,
retention, source policy, and how to audit source health.

Current state: README, config example, CLI help and `docs/project/NEWS_OPERATIONAL_GUIDE.md`
describe disabled defaults, exact source/scope/HTTP gates, fixture versus live status, explicit
`news-scan` and no-fetch `news-sources`, SQLite-only page loads, timer posture, source-health
audit, retention windows and purge evidence. The guide lists the current LOCAL/REGIONAL/NATIONAL
and ORBITAL allowlist families and records that GLOBAL and Solar System and Beyond have no live
endpoint. Endpoint-specific signoffs remain in their source documents.

### Separate Disabled Systemd News Timer

Status: implemented.

If scheduled news ingest is added, create a separate user-level `console-1701-news-scan.timer`.
Existing `console-1701-scan.timer` must not silently start external fetching. The news timer should
be disabled unless news ingest is explicitly configured and enabled.

## LOCAL Seattle Recent Signal Layer

Architecture reference:

- `docs/project/LOCAL_SEATTLE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### LOCAL Source Registry Design Implementation

Status: completed 2026-10-15 for the first-pass disabled inventory.

Implement the LOCAL source registry from the design document with explicit `source_key`,
`source_family`, `source_class`, adapter, scope, priority, policy risk, parser risk, privacy risk,
retention sensitivity, verification status, and future phase fields. Validate enum values and keep
all sources disabled until explicitly configured.

The registry now contains all 119 LOCAL design-table entries, with existing reviewed core entries
retained as explicit overrides. Enum, HTTPS URL, priority, interval, future-phase, unique-key, and
disabled-default validation runs at import. Config entries inherit metadata unless the user
overrides it; SQLite sync persists the full inventory during `news-scan`. Reference-only entries
such as the City Light outage page and FAA SEA status page are blocked before fixture or HTTP
access even if enabled in config. Tests compare design keys, check representative metadata and
the persisted count, and exercise the no-ingest gate. Inventory presence is not endpoint signoff
or live-ingest authorization; those remain separate backlog rows.

### Disabled-By-Default LOCAL Config

Status: implemented.

Add a LOCAL config shape that defaults to disabled, with `include_airport`, `include_port`,
`include_king_county_transit`, `include_wsdot_seattle_corridors`, `include_ferries`,
`hazard_radius_miles`, `earthquake_min_magnitude`, `allow_neighborhood_blogs`, and
`allow_social_sources`. Reject social sources unless explicitly allowed. Reject homepage extraction
unless a future `allow_homepage_extractors` flag is explicitly true.

### LOCAL SQLite Schema Or Extension

Status: completed 2026-10-15 for the first-pass LOCAL storage contract.

Add SQLite storage for LOCAL source registry state, fetch runs, normalized items, event clusters or
`local_events`, source health, ranking explanations, and retention purge evidence. Use JSON-heavy
columns and indexes for latest-by-scope, source health, event ranking, source family, and
`expires_at` purge. Do not store full article bodies by default.

The schema persists the 119-row LOCAL source registry, configured sources, fetch runs, normalized
items, source health, local events, score components, ranking explanations, and retention evidence.
`local_events` has a dedicated `ranking_explanation_json` field, item links, geography and family
JSON, and expiry. Indexes cover latest items by scope/source, source health, scoped source family,
LOCAL event time and impact ranking, and expiry purge. A schema/query-plan test verifies the new
scoped impact index; a retention regression verifies expired LOCAL event deletion and purge counts.
The item schema has no full article-body or raw-payload column. Existing databases receive the
idempotent indexes on `init_db`, and the scoped source-key migration preserves dependent rows.

### LOCAL Fixture Pack

Status: implemented.

Create local-only fixtures for SFD Socrata JSON, AlertSeattle RSS, King County Metro RSS, NWS alert
JSON, WSDOT alert JSON, local blog RSS, City Light outage data, and FAA/SEA airport status. Fixture
ingest must not perform network calls and must be safe for pytest.

Current state: `tests/fixtures/news/local_sfd_fire_911.json` covers SFD Socrata rows for a major
public-impact fire incident and a low-acuity aid response with exact-address redaction.
`tests/fixtures/news/local_nws_alerts.json` covers a LOCAL NWS active-alert fixture with one
Seattle-relevant alert and one filtered non-local alert.
`tests/fixtures/news/local_metro_service_advisories.rss` covers Metro advisory RSS route and
service-area extraction. `tests/fixtures/news/local_wsdot_alerts.json` covers Seattle corridor
filtering and lane-blocked public-impact scoring. `tests/fixtures/news/local_alertseattle.rss`
covers AlertSeattle city-alert severity extraction. `tests/fixtures/news/local_blog_feed.rss`
covers gated neighborhood-blog metadata-only parsing. `tests/fixtures/news/local_city_light_outages.json`
covers Seattle-area outage filtering and utility-impact evidence.
`tests/fixtures/news/local_faa_airport_status_sea.json` covers SEA airport-status filtering and
airport-impact evidence. These are explicit local fixtures only and do not mark City Light or
FAA/SEA live endpoints as verified.

### Socrata Parser For SFD Fire 911

Status: implemented.

Build a `socrata_json` fixture parser for Seattle Real-Time Fire 911 metadata. Preserve dataset ID,
row ID, incident type, observed timestamp, unit count if present, location tokens, source URL, and
privacy redaction evidence. Low-acuity medical/private calls must not automatically elevate.

### RSS/Atom Parser For Official And Local Feeds

Status: implemented.

Build an RSS/Atom parser for fixture feeds first, covering AlertSeattle, SPD Blotter, SDOT Blog,
Metro, local news, and neighborhood blogs where feeds verify later. Parse title, URL, published
timestamp, bounded description, categories, source id, and evidence. Never fetch article bodies.

Current state: generic RSS/Atom parsing exists for fixture feeds, Metro RSS has route/service-impact
evidence, AlertSeattle RSS has official city-alert severity evidence, and neighborhood-blog RSS has
metadata-only local signal evidence behind the explicit neighborhood-blog config gate. `spd_blotter_rss`
and `sdot_blog_rss` emit structured local-impact evidence (`spd_blotter`, `sdot_blog`) and ranking
inputs. Local-news feeds now emit route and service-area-matched `local_news` evidence with deterministic
scoring and deterministic `local_news` token propagation into LOCAL event signatures for better correlation
across routing and neighborhood context.

### NWS Alert Fixture Parser

Status: implemented.

Build a fixture parser for NWS active alert JSON filtered to Seattle, King County, Puget Sound, and
configured nearby hazard zones. Preserve severity, urgency, certainty, event type, affected zones,
effective/expiration times, and active-alert ranking evidence.

### WSDOT Official API Fixture Parser

Status: implemented.

Build a fixture parser for WSDOT traveler information affecting Seattle corridors, ferries, bridges,
passes, routes, or regional access. Preserve route/facility tokens, closure/delay severity, published
time, source URL, and public-impact scoring evidence.

### Metro RSS Parser

Status: implemented.

Build a fixture parser for King County Metro service advisories RSS. Preserve route IDs, affected
service area, advisory title, published time, source URL, and transit-impact ranking evidence.

### FAA/SEA Airport Status Research

Status: implemented (research complete; live ingest remains in the separate LOCAL and NATIONAL tasks).

Verified 2026-10-15: the FAA's NAS Status user guide explicitly publishes machine-readable XML
for active airport and en-route events, and the NAS Status footer exposes its XML link. A bounded
read of `https://nasstatus.faa.gov/api/airport-status-information` returned HTTP 200,
`application/xml`, root `AIRPORT_STATUS_INFORMATION`, a source `Update_Time`, and active
`Delay_type` groups. Airport events carry `ARPT` and, by type, `Reason`, `Avg`, `Max`,
arrival/departure direction, or closure `Start`/`Reopen`. The sample had no SEA event, which is
normal for an active-event feed and does not prove SEA is on time. The public `robots.txt` had no
disallow rule; no rate limit was identified in the reviewed FAA guide. A conservative ten-minute
cadence is a proposed limit, not a published FAA allowance. The XML's `Dtd_File` points at a legacy URL that currently
returns HTML, so parsing must not depend on fetching an external DTD.

The Port's SEA flight-status and checkpoint-wait pages returned public HTML; this review did not
establish a published machine-readable API for either. Treat those pages and the FAA SEA status
page as human reference surfaces. The existing FAA JSON fixture is synthetic and is **not** the
verified XML shape. The LOCAL NAS XML registry entry is now reference-only and disabled until an
XML fixture parser, SEA-only filtering, event expiry, and exact-URL live-ingest controls are tested
under RS-011/RS-044. No live fetch path was enabled by this research.

Evidence: [FAA NAS Status user guide](https://nasstatus.faa.gov/static/media/NASStatusUserGuide.cccc6d48.pdf),
[NAS Status](https://nasstatus.faa.gov/),
[NAS XML endpoint](https://nasstatus.faa.gov/api/airport-status-information),
[Port SEA flight status](https://www.portseattle.org/sea/flight-status),
[Port checkpoint times](https://www.portseattle.org/page/live-estimated-checkpoint-wait-times).

### City Light Outage Endpoint Research

Status: not implemented.

Identify whether Seattle City Light outage data has a stable official endpoint behind the public
outage pages or maps. Prefer official APIs or feature services. Do not scrape ArcGIS/Experience map
HTML. If no suitable endpoint exists, keep the source `manual_review_only` or
`source_health_probe_only`.

Current state: the public outage page and map web app are the verified public surface, and the LOCAL
registry now points `city_light_outages_home` at that surface with `source_health_probe_only`.
Seattle City Light still needs a verified machine-readable endpoint before any live ingest can be
enabled.

### SPD Call Data Privacy Review

Status: implemented.

Review SPD Call Data and Significant Incident Report sources for privacy, preliminary-report caveats,
address handling, retention, and display rules. Ordinary minor calls and exact private locations must
not be elevated without public-impact justification.

Current state: SPD blotter parsing now emits explicit low-acuity privacy evidence in both
`evidence["privacy"]` and `evidence["spd_blotter"]["privacy"]`, caps private non-public
`incident_score` values, adds privacy-redacted tagging, and routes low-acuity evidence into
existing LOCAL privacy penalty ranking.

### ArcGIS Dashboard Underlying Endpoint Research

Status: not implemented.

Research underlying official feature services for SPD dashboards, City Light outage maps, and SDOT
traffic/camera maps. Do not screen scrape dashboards. Mark sources `manual_review_only` or
`source_health_probe_only` when no stable official endpoint is available.

Current state: SDOT traffic cameras have a verified public ArcGIS/open-data surface, the SPD crime
and calls-for-service dashboards have official public pages but no exposed GIS service in the
inspected `gisdata.seattle.gov/server/rest/services/SPD` folder, and the City Light outage map is
still only verified as a public outage surface. The remaining work is to map any stable underlying
feature services and keep the unresolved dashboard sources in probe-only or manual-review states.

### LOCAL Deterministic Event Correlation

Status: implemented.

Implement deterministic LOCAL event matching by time window, source family, normalized title tokens,
route/facility tokens, neighborhood, intersection, weather zone, airport/port facility, utility
area, and privacy-safe location tokens. Do not use LLMs, embeddings, or hidden cloud calls.

Current state: Added `local_events` persistence, deterministic event signature building,
time-window matching, source-fallback family scoring, and automatic `news_items.local_event_id`
linking during LOCAL fixture ingest. Purge now removes expired local events and clears orphaned item
links. Evidence records include deterministic match score, matching flags, and ranking component
summaries for observability.

### LOCAL Deterministic Ranking

Status: implemented (first pass).

Implement explainable LOCAL ranking with recency, official severity, source diversity, public
impact, source priority, active alert state, cluster size, privacy penalty, duplicate-family
penalty, stale-source penalty, and low-confidence penalty. Store score features and ranking reasons
in JSON evidence.

Current state: item ranking now adds explicit LOCAL factors from parser evidence:
`local_official_alert_boost`, `local_public_impact_boost`, `local_transit_impact_boost`,
`local_utility_impact_boost`, `local_airport_port_boost`, `local_blog_signal_boost`, and
`local_privacy_penalty`. These cover AlertSeattle, NWS, SFD, WSDOT, Metro, City Light, FAA/SEA, and
local-blog fixtures with stored factor values and human-readable reasons.
`apply_local_event_ranking_adjustments` now injects deterministic LOCAL event-correlation terms:
`local_source_diversity_score`, `local_source_diversity_bonus`,
`local_cluster_size_bonus`, `local_duplicate_family_penalty`,
`local_stale_source_penalty` (when applicable), and
`local_low_confidence_penalty` into ranking evidence. Duplicate-family penalty behavior is now
observable, and local-event merging updates item rank evidence after merge.
LOCAL NWS alert ranking now records `local_recency_state` and
`local_active_alert_bonus`. An actual alert only receives the active bonus while its official
effective/expiry window is current; an older active alert receives a larger bounded bonus so its
importance does not disappear merely because publication time ages. Expired alerts receive no
active bonus. The state survives local-event ranking adjustments, alongside factor totals and
human-readable reasons. Tests cover active versus expired scoring and the existing source
diversity, cluster, privacy, stale health, and low-confidence terms.

### LOCAL Privacy Redaction Rules

Status: implemented (first pass for supported public-safety parsers).

Add deterministic redaction rules for public safety data. Suppress exact addresses for low-acuity
medical calls, overdose calls, private residential aid, single-source minor police calls, and
low-public-value private distress. Prefer neighborhood or intersection-level display unless an
official source frames the incident as public-impact.

Current state: the SFD Fire 911 and SPD blotter fixture parsers now suppress exact private-location
storage/display for low-acuity medical/private incidents, keep privacy-safe location tokens, and
store explicit redaction evidence including low-acuity versus overdose privacy categories. LOCAL
ranking now further suppresses private/sensitive items when they remain single-family or social-only
and only partially relaxes that suppression when independent cross-source confirmation exists.
The SFD parser now discards nested `report_location`/`location` address strings from correlation
tokens and excludes exact cross-street input for low-acuity calls. The SPD parser replaces the
title and description of low-acuity or otherwise low-public-value minor reports with a bounded
location-safe summary before storage, omits route tokens for those reports, and records a distinct
`minor_police` privacy category. Both parsers retain source links and safe geography while
privacy ranking suppresses isolated private incidents. Regression fixtures include addresses in
SFD nested location data and SPD title, description, and numeric route-token text; no exact address
appears in the normalized item. Future adapters must apply the same rule before ingest.

### LOCAL UI Disabled States

Status: implemented.

Replace LOCAL placeholders only after storage/config support exists. Show honest states for disabled,
not configured, configured but disabled, never scanned, stale, policy blocked, parser failed, social
disabled, and homepage extraction disabled. Do not show fake headlines.

Current state: App rendering tests now verify LOCAL scope cards for disabled, not configured,
configured-but-disabled, never-run, stale, and parser-failed/failing scenarios, and assert that no
fixture headline text is rendered in those non-live states. Source-policy block states for social and
homepage extraction are now surfaced as dedicated health states and included in scope-card readouts.

### LOCAL Source Health States

Status: implemented (first-pass state contract and presentation).

Implement source health states for LOCAL: `disabled`, `not_configured`, `configured_never_run`,
`healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`, `robots_blocked`,
`auth_required`, `rate_limited`, `unsupported`, and `manual_review_only`. Surface these states in
SYSTEM later and summarize them on LOCAL.

Current state: API/UI/CLI source summaries now derive `disabled`, `configured_never_run`,
`healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`, `social_disabled`,
`homepage_disabled`, `auth_required`, `manual_review_only`, `rate_limited`, `robots_blocked`,
and `unsupported` from config, policy, fetch runs, and latest health rows. Remaining live-fetch-
specific robots and rate-limit evidence will only be populated when a verified live source is
enabled; the states themselves are wired and tested. `not_configured` is a scope state when no
sources exist, rather than a state for a nonexistent source. A shared LOCAL/REGIONAL/NATIONAL
offline state-matrix test now verifies LOCAL source counts and labels in the scope API, scope page,
and SYSTEM summary for stale, parser failure, policy block, never run, disabled, manual review,
robots block, rate limit, unsupported, and auth required. No external fetch is performed.

### LOCAL Evidence Drawer Contract

Status: implemented (first pass).

Define and test evidence payloads for LOCAL items and events. Include source ids, source names,
families, classes, item URLs, canonical URLs, official flags, source published times, first/last
seen, fetch run ids, parser names, source health, ranking features, privacy redaction decision,
retention expiration, matching tokens, geographic basis, event confidence, and policy notes.

Current state: `/api/news/items/{id}` now returns source metadata, latest fetch/health state,
policy notes, ranking evidence, fetch run id, retention expiration, canonical URL/storage fields,
and explicit privacy/body-storage flags for stored item rows, and scope/source/cluster panels now
surface click-open evidence drawers plus short source fetch/health histories for that audit data in
the website. Local event rows are now readable via `/api/news/local-events/{event_id}`, and
item detail includes a resolved local-event envelope with associated item summary. Event
correlation explanation, explicit geography basis normalization, and scope-specific matching
contract details now land in local-event payloads via `matching_contract` and
`geography_basis`, with local-item evidence carrying the resolved event envelope.
The LOCAL item drawer now shows source key/name, family/class, official status, parser, item and
canonical URLs, published/first/last seen times, fetch run and source health at ingest, explicit
recency state, ranking factors/reasons, privacy category/reason, retention expiry, policy notes,
and matching tokens. Event detail now supplies a bounded item provenance summary for every member:
source identity and class, official status/confirmation, canonical and item URLs, times/expiry,
parser, fetch run, health at ingest, ranking factors, privacy decision, and policy notes. The
event payload also labels correlation confidence as `single_source`, `low`, `medium`, or `high`
from the deterministic match score, separate from source official status. The existing geography
and matching contract remains available, and item detail resolves its linked event. Fixture/API/UI
tests verify the contract without an external fetch.

### LOCAL Official-Source Live Ingest Phase

Status: implemented (first safe official source).

After fixture parsing, correlation, ranking, retention, and tests exist, add opt-in live ingest for
one safe official source at a time. First candidates are SFD Fire 911 Socrata, NWS alerts, King
County Metro RSS, and WSDOT API. Keep every source disabled by default and require an explicit
command. No page-load fetches.

Current state: the explicit `news-scan` path can fetch only the verified Washington NWS alerts URL
when every opt-in gate is true. One controlled command successfully fetched that source and a
second immediate command was skipped by the interval gate. On this machine the standing config now
opts in to this source at a 30-minute interval and the separate news timer runs every 30 minutes;
new installs remain off by default. SFD Fire 911, King County Metro, WSDOT, and other sources still
require endpoint signoff and allowlist additions before live ingest. The first-pass acceptance is
the single verified Washington NWS feed: exact scope/key/URL/parser/content-type allowlist,
explicit `news-scan`, disabled new-install defaults, opt-in policy, bounded response/time,
conditional requests, interval skip, source health, and no page-load fetch are covered by offline
tests. Other named candidates remain separate source-verification and adapter work, not live
capabilities claimed by this row.

### LOCAL News/Blog RSS Ingest Phase

Status: partially implemented.

Add opt-in RSS/Atom ingest for local news and neighborhood blogs only after source verification.
Store headline metadata only, bound descriptions, avoid article bodies, avoid paywall bypass, and
prevent duplicate syndicated articles from inflating independent convergence.

Current state: fixture parsers for `local_blog_rss` and `local_news_rss` already exist, and local
config can gate neighborhood blogs behind `allow_neighborhood_blogs`. The remaining work is the
opt-in live RSS/Atom ingest command and source-specific duplicate-syndication handling for enabled
local news and neighborhood-blog sources.

### LOCAL Social Source Policy Review

Status: partially implemented.

Review Bluesky AT Protocol, Reddit official API or permitted feed access, and X official API rules
before implementing any community/social adapter. Keep social disabled by default, require explicit
configuration, use short retention, and never scrape HTML to bypass platform restrictions.

Current state: local config already requires `allow_social_sources` before social sources can be
enabled, the built-in registry keeps social candidates disabled by default, and
`manual_review_only` entries stay gated for explicit review rather than live ingest. The remaining
work is a compliant live social adapter and a short-retention policy for any enabled social source.

### Documentation For Source Verification

Status: implemented (first-pass workflow and signoff template).

Document the later source verification workflow: confirm endpoint ownership, access method, source
terms, robots/policy notes, parser shape, rate limits, retention sensitivity, privacy risk,
verification status, and source-health behavior before enabling any source.

Current state: `docs/project/NEWS_SOURCE_VERIFICATION_WORKFLOW.md` now captures the shared
verification checklist, required registry fields, source-health states, a reusable per-source
signoff record, and an explicit release gate. It links the completed Washington NWS signoff, the
FAA/NAS XML hold decision, and scope-specific verification workflows. The template separates
officially documented access, bounded manual observations, offline fixture tests, and actual live
smoke checks; missing evidence leaves a source disabled or reference-only.

### Tests For No Page-Load External Fetches

Status: implemented.

Add tests proving GET routes and page renders read SQLite/config only and never call network fetchers.
Include disabled/not configured/stale/failing state tests for LOCAL and SYSTEM source health.

Current state: GET route regression coverage now exercises OVERVIEW, LOCAL, SYSTEM, and
`/api/news/*` reads with enabled recent-signal config and a missing fixture path, proving page/API
loads do not trigger ingest or fixture reads. Schema-level coverage now includes LOCAL stale and
failing (parser-failed) state derivation, including scope-level `failing` and `stale` outcomes.
SYSTEM scope-state matrix coverage is now complete for stale and failing aggregates and is exercised
in summary-level tests.

## REGIONAL Pacific Northwest Recent Signal Layer

Architecture reference:

- `docs/project/REGIONAL_PNW_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### REGIONAL Source Registry Design Implementation

Status: completed 2026-10-15 for the first-pass disabled inventory.

Implement the REGIONAL source registry from the design document with explicit `source_key`,
`source_family`, `source_class`, adapter, scope, priority, official status, policy risk, parser
risk, privacy risk, retention sensitivity, verification status, and future phase fields. Validate
enum values and keep all REGIONAL sources disabled until explicitly configured.

The REGIONAL registry now contains all 224 design-table entries plus six pre-existing reviewed
operational candidates. All 230 rows are disabled by default. At load time it validates unique
keys, classes/adapters/kinds, official and verification status, risks, HTTPS URLs, priority,
interval, and future phase. The config layer inherits metadata, and SQLite sync persists the full
inventory. Reference-only pages and documentation cannot trigger fixture or HTTP ingest when
configured; focused tests compare every design row, confirm the persisted count, and exercise that
gate. Inventory presence is not endpoint verification or live-ingest approval; those remain
separate backlog work.

### Disabled-By-Default REGIONAL Config

Status: implemented.

Add a `regional_sources:` or equivalent REGIONAL config tree that defaults to disabled. Include
geography flags for Washington, Puget Sound, Cascadia hazards, Oregon relevance, BC relevance,
transport corridors, wildfire/smoke, seismic/volcano, public health, state government, regional
news, and social sources. Reject social sources unless explicitly allowed and reject homepage
extraction unless a future `allow_homepage_extractors` flag is true.

Current state: the top-level `regional` config tree defaults to disabled and carries validated
Washington, Puget Sound/Cascadia, Oregon/BC relevance, transport, wildfire/smoke, seismic,
public-health, state-government, regional-news, social, and homepage-extraction settings. Source
normalization rejects REGIONAL social sources unless `regional.allow_social_sources` is true and
rejects homepage extraction unless both the regional and shared fetch-policy gates are true. A
config matrix verifies defaults, type validation, and the two explicit gates. All registry sources
remain disabled unless individually configured.

### REGIONAL SQLite Schema Or Extension

Status: completed 2026-10-15 for the first-pass REGIONAL storage contract.

Add or extend SQLite storage for REGIONAL source registry state, fetch runs, normalized items,
`regional_events` or scoped clusters, source health, ranking explanations, geographic labels, and
retention purge evidence. Use JSON-heavy columns and indexes for latest-by-scope, event ranking,
source health, source family, geographic filters, and `expires_at` purge. Do not store full article
bodies by default.

The shared schema persists all 230 REGIONAL registry rows, configured sources, fetch runs, items,
source health, and scoped `news_clusters` with member, family, geography, confidence, and ranking
evidence. `news_item_facets` now indexes source-provided REGIONAL zone, route, facility, county, and
region labels, plus event type and source family. It excludes free-text USGS place labels from
county/region facets. Tests verify indexed facet and cluster queries, no inferred county, and
expiry-purge cascade for facets. Existing item, health, family, score, and expiry indexes cover the
other first-pass queries. No full article body is stored. A separate `regional_events` table is
unnecessary for this first-pass contract; richer event/geography behavior remains in the
correlation and ranking rows.

### REGIONAL Fixture Pack

Status: partially implemented.

Create local-only fixtures for NWS active alert JSON, WSDOT travel alert JSON, WSF bulletin/API
shape, WA DNR wildfire data after endpoint verification, NWCC feed shape after verification, USGS
earthquake GeoJSON, USGS water/hydrology data, King County emergency feed, Ecology/AirNow AQI,
regional news RSS, and verified outage data if an official endpoint is found. Fixture ingest must
not perform network calls and must be safe for pytest.

Current state: the registry-backed RSS parser now accepts `regional_news_rss`, and a regional scan
regression reuses the existing RSS fixture corpus to prove the REGIONAL ingest path. The shared
local fixture corpus also now exercises REGIONAL NWS and WSDOT ingest paths. Dedicated regional
USGS earthquake GeoJSON fixture and parser now cover Washington-area coordinate and magnitude
filtering, event evidence, and a capped seismic ranking factor. A dedicated REGIONAL NWS fixture
now covers King/Spokane WA alerts and an out-of-region Oregon alert, including official county/zone
codes and configured filter behavior. A synthetic WSDOT JSON fixture now follows the official
documented `Alert`/`RoadwayLocation` REST schema, including corridor, pass, border, WCF timestamp,
and closed-alert cases; it is not an observed authenticated response. A synthetic King County
Emergency News RSS fixture now covers warning, recovery, and test posts with source-specific
classification and an offline scan. Dedicated WSF, wildfire, hydrology, other county emergency, AQI,
outage, and other regional fixture shapes remain pending endpoint verification; do not invent
live API shapes to close this pack.

### NWS Alert Parser For Washington

Status: implemented (first pass).

Build a fixture-first NWS alert parser filtered to Washington, Puget Sound, configured counties,
weather zones, and regional hazard rules. Preserve alert id, event type, severity, urgency,
certainty, affected zones, counties, effective time, expiration time, source URL, instruction URL,
and official-alert ranking evidence.

Current state: the existing NWS fixture parser now runs in REGIONAL scope through the registry-
backed ingest path. It rejects alerts without Washington zone, SAME county, or explicit state-label
evidence; the disabled registry seed uses the documented `area=WA` endpoint. The
REGIONAL regression covers in- and out-of-region fixture cases. Dedicated Washington-only fixture
coverage now preserves official UGC zone ids, SAME county codes, explicit county area labels,
alert timing, instruction URLs, severity/urgency/certainty, and ranking evidence. Optional
`county_codes`, `county_keywords`, `zone_ids`, and `area_keywords` narrow REGIONAL ingest after a
Washington geography gate. A Washington SAME county code alone is sufficient when zone ids are
absent, with `official_same_county_codes` recorded as the geography basis. A dedicated fixture and
end-to-end scan test cover filtering and retained evidence; out-of-region Oregon alerts stay out.

### WSDOT Traveler API Fixture Parser

Status: implemented (documented JSON fixture parser; live JSON remains disabled).

Build a fixture parser for WSDOT traveler information affecting regional corridors, mountain
passes, bridges, border crossings, and major Washington routes. Preserve route, direction, milepost
or facility tokens, closure/delay severity, source update time, source URL, and transport-impact
ranking evidence.

Current state: the existing WSDOT travel-alert parser now runs in REGIONAL scope through the
registry-backed ingest path. A dedicated synthetic REGIONAL fixture now follows WSDOT's official
REST `Alert`/`RoadwayLocation` JSON example: numeric ID, `HeadlineDescription`,
`ExtendedDescription`, category/status/priority, county/region, start/end roadway direction and
milepost, and `/Date(milliseconds-offset)/` timestamps. The parser preserves these fields as
bounded evidence, strips embedded markup, rejects duplicate IDs or invalid times, and records
official route/facility/transport ranking. A closed alert receives zero public-impact score. When
the documented JSON has no item URL, the parser uses WSDOT's RSS `refnum` link as an auditable
identity and notes its basis; that legacy link may redirect to the general alerts page.
`docs/project/REGIONAL_WSDOT_TRAVELER_JSON_VERIFICATION.md` records the access-code requirement,
unverified HTTPS/live behavior, retention, and release gate. The separate public Highway Alerts
RSS source remains the only live-capable WSDOT adapter, behind exact-url opt-ins. No JSON access
code or authenticated live path was added.

### WSF Bulletin/API Fixture Parser

Status: not implemented.

Build a fixture parser for Washington State Ferries bulletins and API records after access-code and
endpoint behavior are designed. Preserve ferry route, terminal, vessel when public, delay or
cancellation status, start/end times, source URL, and ferry-impact ranking evidence.

### WA DNR Wildfire Endpoint Research

Status: not implemented.

Research WA DNR wildfire source options and identify official machine-readable endpoints or feature
services for current wildfire incident information. Do not screen scrape ArcGIS dashboard HTML. If
no suitable endpoint exists, keep dashboard sources `source_health_probe_only` or
`manual_review_only`.

### NWCC Feed Verification

Status: not implemented.

Verify whether NWCC provides an RSS/Atom or stable public feed suitable for metadata ingestion.
Record source ownership, feed URL, terms/policy notes, parser shape, refresh interval, and fallback
behavior. Keep the source disabled until verification is complete.

### USGS Earthquake GeoJSON Parser

Status: implemented (first pass).

Build a fixture-first parser for USGS earthquake GeoJSON filtered to Washington, Puget Sound,
Cascadia, and configured radius/magnitude rules. Preserve event id, magnitude, depth, place, time,
felt/intensity fields where present, source URL, bounding basis, and seismic ranking evidence.

Current state: the REGIONAL registry now selects a dedicated `usgs_earthquake_geojson` parser. A
synthetic fixture covers Washington-area events, out-of-region exclusion, and magnitude threshold
exclusion. The parser preserves USGS ids, magnitude/depth/place/time, felt and intensity measures,
official event URL, filter bounds, and a capped seismic score. It now excludes non-earthquake
feature types before assigning earthquake identity. Configurable geographic bounds and minimum
magnitude are supported; an optional center/radius filter now further narrows the REGIONAL result
using great-circle distance, and the distance and basis are retained in item evidence. Filter
inputs are finite and bounded, and a configured radius requires both coordinates. Live admission
still requires at least 2.5 because the signed-off feed has that floor. Exact-source verification
and opt-in live ingest are complete. No in-region earthquake occurred during the prior live smoke
check, so live item observation remains an operational evidence gap, not a parser blocker.

### USGS Water/Hydrology Fixture Parser

Status: not implemented.

Build a fixture parser for USGS water/hydrology data using gauge allowlists and river-basin filters.
Preserve gauge id, river name, location, timestamp, stage/flow values, stage category if available,
staleness evidence, source URL, and flood/hydrology ranking evidence.

### NWRFC Endpoint Research

Status: not implemented.

Research NWRFC river, forecast, and weather source candidates for stable machine-readable endpoints.
Document parser shape, gauge or basin filters, policy notes, refresh interval, and whether sources
should stay `source_health_probe_only` if no suitable endpoint exists.

### Ecology/AirNow AQI Endpoint Research

Status: not implemented.

Research Washington Ecology, Puget Sound Clean Air, AirNow, and related AQI/smoke endpoint options.
Prefer official APIs or feeds, document access requirements and terms, and avoid dashboard scraping.
Design station filters, AQI thresholds, retention, and source-health behavior before implementation.

### PSE/SnoPUD/Tacoma Outage Endpoint Research

Status: not implemented.

Research official outage data options for PSE, SnoPUD, Tacoma Power, Seattle City Light, and related
regional utility sources. Do not scrape public outage map HTML or ArcGIS Experience pages. If stable
official endpoints cannot be found, keep those sources manual-review-only or source-health-only.

### King County Emergency Feed Parser

Status: implemented (fixture-first; live ingest disabled).

Build a fixture-first parser for King County Emergency News if a feed endpoint is verified.
Preserve title, URL, published timestamp, bounded description, categories/tags, emergency/alert
classification, county geography, source URL, and county-emergency ranking evidence.

Current state: King County Emergency Management's official Emergency News blog exposes an RSS feed
at `https://kcemergency.com/feed/`. The REGIONAL registry points to that feed, with its source still
disabled. A source-specific parser validates the channel, official HTTPS item URL and publication
time, retains a bounded plain-text description and categories, and records publisher jurisdiction
without assuming countywide impact. Deterministic classification distinguishes emergency alerts,
recovery posts, routine notices and tests; tests receive no emergency public-impact score. A
synthetic three-item fixture, parser tests and a configured offline scan cover the shape and
ranking. `docs/project/REGIONAL_KING_COUNTY_EMERGENCY_RSS_VERIFICATION.md` records ownership,
bounded endpoint observation, retention and the separate live-ingest release gate.

### County Emergency Alert Source Verification

Status: implemented (source review; no live county feed enabled).

Verify Snohomish, Pierce, Thurston, Whatcom, Skagit, Kitsap, Clallam, Jefferson, and other regional
county emergency sources before implementation. Record source ownership, feed/API availability,
access method, parser risk, policy notes, privacy risk, source-health behavior, and fallback state.

Current state: `docs/project/REGIONAL_COUNTY_EMERGENCY_SOURCE_REVIEW.md` records official source
pages and access paths for Snohomish, Pierce, Thurston, Whatcom, Skagit, Kitsap, Clallam and
Jefferson. It distinguishes advertised public RSS categories from signup-only alert services,
records parser/policy/privacy risk, source-health and fallback behavior, and requires per-feed
bounded signoff before any exact-URL live opt-in. No feed or API was enabled by the review.

### Regional News RSS Parser

Status: partially implemented.

Build a fixture-first RSS/Atom parser for verified regional news, public media, local TV/radio, and
nonprofit feeds. Store headline metadata only, bound descriptions, preserve publisher/source
family, detect duplicate or syndicated stories, and prevent duplicated articles from inflating
independent convergence.

Current state: `console1701/news/parsers.py` now dispatches `regional_news_rss` through the shared
RSS parser path, and the REGIONAL ingest tests cover that alias with the existing local RSS fixture.
Scope-specific regional feed curation and duplication handling are still pending.

### REGIONAL Deterministic Event Correlation

Status: partially implemented.

Implement deterministic REGIONAL event matching by source family, time window, normalized title
tokens, event type, county, city, route, mountain pass, ferry route, airport, port, river basin,
weather zone, fire incident name, volcano, seismic region, AQI station, and public-health
jurisdiction. Do not use LLMs, embeddings, or hidden cloud calls.

Current state: USGS, NWS, and WSDOT fixtures match updates by their official event IDs into scoped
clusters. The cluster rebuild also supports conservative cross-family matching by equal official
event type, shared parser-backed geography, at least three title tokens, and a 48-hour publication
window. It requires every pair to match and keeps unverified headlines isolated by URL. The
item/cluster contract stores pairwise matching basis and tokens, confidence, member IDs, and
source families. The remaining regional token families await source parsers; see
`docs/project/REGIONAL_EVENT_CONTRACT.md`.

### REGIONAL Deterministic Ranking

Status: implemented for first pass.

Implement explainable REGIONAL ranking with recency, official severity, source diversity, temporal
proximity, public impact, geographic relevance, active alert state, source priority, cluster size,
privacy penalty, duplicate-family penalty, stale-source penalty, low-confidence penalty, and
out-of-region penalty. Store score features and ranking reasons in JSON evidence.

Current state: shared deterministic ranking stores recency, source priority/health, official
severity (including a capped USGS seismic boost), geography, public impact, and confidence/privacy
terms. REGIONAL adds a bounded active NWS alert boost only before its official expiry, an explicit
stale-source penalty, and an out-of-region seismic guard for rejected filter evidence. Cluster
rebuilds recalculate event size, genuinely independent family diversity, same-family duplication,
and temporal proximity from source publication times without accumulating bonuses on repeat scans.
Every factor and reason is persisted in the item evidence contract and shown in the drawer. The
out-of-region term normally stays zero because REGIONAL parsers exclude rejected events before
storage; it is a deterministic guard for malformed or historical stored evidence. New source
families still need source-specific severity and sensitivity reviews when admitted.

### REGIONAL Privacy And Public-Impact Rules

Status: implemented 2026-10-15 for first-pass REGIONAL ingest.

Add deterministic REGIONAL privacy and public-impact rules. Suppress exact private addresses for
low-value incidents, avoid amplifying residential outages below threshold, keep routine
public-safety and social-only reports low priority, and prefer county, corridor, zone, basin,
facility, or regional labels unless official public-impact evidence requires more detail.

Current state: `regional_policy.py` runs before REGIONAL SQLite storage and replaces exact street
address patterns in titles, descriptions, tags, and parser evidence with a withheld marker.
Official URL attribution is preserved. Residential/isolated outages, routine public-safety
headlines, and social-only reports remain background unless an official NWS, WSDOT, USGS, or county
impact score crosses its explicit threshold. The stored privacy contract states redaction and
impact basis, and the existing REGIONAL rank applies a 20-point low-acuity penalty. Direct and
offline scan tests verify address redaction before persistence, background treatment, and an
official-impact exception. Broader source-specific address and geography handling can be
refined as new parsers are added.

### REGIONAL UI Disabled States

Status: implemented.

Replace REGIONAL placeholders only after storage/config support exists. Show honest states for
disabled, not configured, configured but disabled, never scanned, stale, policy blocked, parser
failed, social disabled, homepage extraction disabled, and manual-review-only sources. Do not show
fake headlines.

Current state: the shared REGIONAL page and SQLite-backed API render source state, items, clusters,
and evidence drawers without fetching. Page regressions cover disabled, not configured, configured
but disabled, never run, stale, parser failure, policy blocking, social disabled, homepage disabled,
and manual-review states. REGIONAL social sources receive a scope-specific blocked message. Empty
states show no fabricated headline.

### REGIONAL Source Health States

Status: implemented.

Implement source health states for REGIONAL: `disabled`, `not_configured`,
`configured_never_run`, `healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`,
`robots_blocked`, `auth_required`, `rate_limited`, `unsupported`, and `manual_review_only`. Surface
these states in SYSTEM later and summarize them on REGIONAL.

Current state: the shared source-health derivation and REGIONAL page/API surface the listed states.
The REGIONAL matrix regression covers disabled, never-run, stale, parser-failed, policy-blocked,
manual-review, robots-blocked, auth-required, rate-limited, and unsupported states without fetching.
Healthy and failing behavior is covered by the shared source and scope tests. Scope-specific visual
presentation remains tracked under REGIONAL UI Disabled States.

### REGIONAL Evidence Drawer Contract

Status: implemented for first pass.

Define and test evidence payloads for REGIONAL items and events. Include source ids, names,
families, classes, item URLs, canonical URLs, official flags, published times, first/last seen,
fetch run ids, parser names, source health, ranking features, geographic match basis, public impact
basis, source diversity basis, privacy redaction decision, retention expiration, matching tokens,
event type, event confidence, and policy notes.

Current state: each stored REGIONAL item now carries a versioned evidence contract with source ID,
name, family, class, official status, URLs, publication and observation times, fetch run, parser,
source health, geographic basis/match, event type/confidence, matching basis/tokens, source
diversity, public-impact basis, privacy-redaction decision, ranking features, retention expiry,
and policy notes. Cluster evidence stores pairwise match reasons and a contract snapshot for every
member alongside source-family counts, corroboration, and score. REGIONAL item and cluster drawers
render those fields. An offline scan/page/API regression verifies persistence and presentation;
future source parsers must supply their own evidence fields when admitted.

### REGIONAL Official-Source Live Ingest Phase

Status: implemented for first pass.

After fixtures, correlation, ranking, retention, source health, and tests exist, add opt-in live
ingest for one safe official source at a time. First candidates are NWS alerts for Washington,
WSDOT Traveler API, USGS earthquake GeoJSON, and King County Emergency News feed if valid. Keep
every source disabled by default and require an explicit command. No page-load fetches.

Current state: the exact verified NWS Washington alert endpoint is available behind news,
REGIONAL policy, scope, source, and HTTP opt-ins. A controlled explicit scan returned HTTP 200 and
persisted two Washington alert items with official-ID event evidence; an immediate repeat was
interval-skipped. On this machine the standing config now opts in to LOCAL/REGIONAL NWS,
REGIONAL USGS, and REGIONAL WSDOT RSS at 30-minute intervals, with the separate news timer enabled. LOCAL and REGIONAL
share one NWS request per scan. Successful HTTP 200 snapshots now retire absent active items;
304 and failed scans preserve the prior snapshot. The LOCAL page shows labeled REGIONAL context,
feed health, and a 60-second SQLite-only refresh. The verified USGS M2.5+ past-day feed returned
HTTP 200 and healthy state but no in-region events at activation. The official public WSDOT
Highway Alerts RSS returned HTTP 200 with 189 statewide current items and a healthy source state;
it is REGIONAL only because the RSS lacks reliable Seattle-specific location fields. Repository
defaults and new installs remain off. The WSDOT access-code JSON API and county feeds still
require separate authorization or endpoint-specific signoff before live ingest.

WSDOT follow-up: its legacy per-alert RSS links currently redirect to a general alert page.
Investigate an official stable alert-specific link without arbitrary crawling; preserve the numeric
WSDOT ID for identity in the meantime. Do not enable LOCAL WSDOT until a defensible Seattle-area
geography filter is tested against real source fields or clearly documented text evidence.

The first-pass admission criterion is met by exact NWS, USGS, and WSDOT opt-ins with isolated
live checks and offline gate tests. WSDOT JSON and county feed promotion are separate source
expansions.

### REGIONAL News RSS Ingest Phase

Status: not implemented.

Add opt-in RSS/Atom ingest for verified regional news and public-media feeds only after source
verification. Store headline metadata only, bound descriptions, avoid article bodies, avoid paywall
bypass, and prevent duplicate syndicated articles from inflating independent convergence.

### REGIONAL Social Source Policy Review

Status: not implemented.

Review Bluesky AT Protocol, Reddit official API or permitted feed access, and X official API rules
before implementing any community/social adapter. Keep social disabled by default, require explicit
configuration, use short retention, and never scrape HTML to bypass platform restrictions.

### Documentation For Source Verification

Status: implemented (first-pass workflow and regional signoff examples).

Document the later REGIONAL source verification workflow: confirm endpoint ownership, access method,
source terms, robots/policy notes, parser shape, rate limits, retention sensitivity, privacy risk,
verification status, geography/relevance filters, and source-health behavior before enabling any
source.

Current state: `docs/project/REGIONAL_SOURCE_VERIFICATION_WORKFLOW.md` now captures the shared
verification checklist, required registry fields, and scope-specific geography/relevance filters.
It points to the shared per-source signoff record and release gate, adds regional geography,
test/inactive, syndication, privacy and fallback checks, and links worked NWS, WSDOT and King
County decisions plus the cross-county review. Each new live source still needs its own signoff.

### Tests For No Page-Load External Fetches

Status: implemented.

Add tests proving GET routes and page renders read SQLite/config only and never call REGIONAL
network fetchers. Include disabled/not configured/stale/failing/policy-blocked/parser-failed state
tests for REGIONAL and SYSTEM source health.

Current state: the shared GET-route regression now renders REGIONAL and reads its scope API with
an enabled source pointing at a missing fixture. It proves page/API reads stay SQLite/config only
and do not invoke ingest. The REGIONAL/SYSTEM source-state matrix covers disabled, not configured,
never run, stale, failing, policy-blocked, parser-failed, manual-review, robots-blocked,
rate-limited, unsupported and auth-required states. A separate GET regression exercises LOCAL,
REGIONAL and SYSTEM with explicit official HTTP opt-in and a fetcher that raises if called.

## NATIONAL United States Recent Signal Layer

Architecture reference:

- `docs/project/NATIONAL_US_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### NATIONAL Source Registry Design Implementation

Status: implemented.

Implement the NATIONAL source registry from the design document with explicit `source_key`,
`source_family`, `source_class`, adapter, scope, priority, official status, policy risk, parser
risk, privacy risk, retention sensitivity, verification status, and future phase fields. Validate
enum values and keep all NATIONAL sources disabled until explicitly configured.

Current state: the checked-in NATIONAL registry contains all 227 source targets from the design
inventory, with their original provenance, risk, verification, priority, phase, and access fields.
The loader validates required enum values and scope/URL shape. Config defaults for known source IDs
remain disabled and reject invalid metadata. The registry is persisted by explicit `news-scan`
and summarized from SQLite. Candidate adapter/kind assignments are inert planning metadata;
they do not authorize live requests.

### Disabled-By-Default NATIONAL Config

Status: implemented.

Add a `national_sources:` or equivalent NATIONAL config tree that defaults to disabled. Include
flags for federal alerts, weather hazards, disasters, public health, recalls, transportation,
aviation, cybersecurity, energy/grid, economic releases, Federal Register, Congress, courts,
national news, social sources, and state events with national impact. Reject social sources unless
explicitly allowed and reject homepage extraction unless a future `allow_homepage_extractors` flag
is true.

Current state: `national:` now has disabled defaults, type and threshold validation, explicit
social-source gating, and a separate scope switch. Source policy and the live-source gate require
the national policy switch before any future exact-allowlisted official HTTP source can run. The
repository example config documents the defaults. No NATIONAL live source is allowlisted or
enabled by this config work; homepage extraction remains blocked by the shared fetch policy.

### NATIONAL SQLite Schema Or Extension

Status: implemented (first-pass scoped storage and indexed facets).

Add or extend SQLite storage for NATIONAL source registry state, fetch runs, normalized items,
`national_events` or scoped clusters, source health, ranking explanations, agency/sector/state
labels, and retention purge evidence. Use JSON-heavy columns and indexes for latest-by-scope, event
ranking, source health, source family, agency/sector/state filters, and `expires_at` purge. Do not
store full article bodies by default.

Current state: the shared `news_source_registry` now supports `(scope, source_key)` uniqueness so
LOCAL and NATIONAL can retain their documented overlapping IDs. Existing SQLite databases migrate
in place while preserving registry rows. NATIONAL registry rows and summaries are stored by
`news-scan`. Scoped items, fetch runs, source health, and cluster tables already support NATIONAL.
Configured `news_sources` now has the same scoped uniqueness; its migration preserves source IDs
and dependent fetch/item rows. A fixture scan verifies independent LOCAL and NATIONAL ingest with
the same documented source key. The shared scoped item-facet table and its
`(scope, facet_kind, facet_value, item_id)` index now hold NATIONAL agency, sector, state and
source-family labels. NWS state labels come only from official `affected_states`; USGS point
coordinates are not guessed into state labels. A bounded query helper returns active NATIONAL
items by facet. Tests cover NWS/USGS fixture ingest, lookup, old-row backfill, the index, expiry
purge and cascading facet deletion. Shared scope/score and source-health indexes remain available
to NATIONAL. No article body column was added.

### NATIONAL Fixture Pack

Status: partially implemented.

Create local-only fixtures for NWS active alert JSON, NHC advisory/RSS data, USGS earthquake
GeoJSON, CDC HAN, FDA recalls, FSIS Recall API, CPSC Recalls API, NHTSA recalls, CISA advisories,
CISA KEV, FAA NAS status, Federal Register API, BLS releases, and national news RSS. Fixture ingest
must not perform network calls and must be safe for pytest.

Current state: `tests/fixtures/news/national_nws_alerts.json` covers two official active-alert
features, including a U.S. territory and an untrusted instruction-link candidate.
`national_usgs_earthquakes.json` covers California, Alaska, Puerto Rico, an out-of-region event,
and a below-threshold event. `national_nhtsa_recalls.json` covers campaign grouping, model rows,
park instructions and missing optional population data. `national_cisa_kev.json` covers full
catalog envelope, CVE identity, due dates, ransomware/triage evidence, and offline scan.
`national_faa_nas_status.xml` covers FAA delay, ground stop, closure notice, airport filtering,
and offline scan. `national_federal_register_documents.json` covers document filters, action
windows, low-value suppression, and offline scan. `national_govinfo_enrolled_bills.rss` covers
allowlisted collection, title filtering, identity and offline scan. `national_fda_recalls.rss`
covers bounded FDA-hosted notice metadata, translated-notice uncertainty and offline scan. The
other NATIONAL source-family fixtures listed above remain pending.

### NWS Active Alert Parser

Status: implemented for fixture ingest.

Build a fixture-first NWS active alert parser for NATIONAL scope. Preserve alert id, event type,
severity, urgency, certainty, affected states/zones, effective time, expiration time, source URL,
instruction URL, and official-alert ranking evidence.

Current state: the shared `nws_alerts_json` parser handles NATIONAL fixtures and stores alert ID,
event, severity, urgency, certainty, affected UGC-derived states or territories and zone URLs,
effective/expiration timestamps, source URL, bounded instruction text, an official HTTPS
weather.gov instruction link when present, and deterministic alert ranking evidence. Invalid or
nonofficial instruction links remain absent. This does not enable NATIONAL live HTTP ingestion.

### NHC Advisory/Feed Verification

Status: implemented (source verification; parser and live ingest remain disabled).

Verify National Hurricane Center advisory/feed endpoints before implementation. Record feed/API
ownership, advisory cycle fields, storm name/id handling, watch/warning fields, parser shape,
policy notes, refresh interval, and source-health behavior. Keep sources disabled until verified.

Current state: `docs/project/NATIONAL_NHC_SOURCE_VERIFICATION.md` records NHC/CPHC ownership,
official basin RSS URLs, the regular/intermediate advisory cycles, storm/wallet identity limits,
watch/warning product distinctions, a proposed disabled polling policy, and source-health behavior.
Bounded Atlantic, Eastern Pacific and Central Pacific XML reads confirmed RSS 2.0 item fields,
cyclone-summary namespace fields, advisory product differences, conditional-request headers and
empty-basin sentinel behavior. The future NATIONAL fixture parser and exact-URL live signoff remain
separate tasks; no NHC endpoint is allowlisted or enabled.

### USGS Earthquake GeoJSON Parser

Status: partially implemented.

Build a fixture-first parser for USGS earthquake GeoJSON filtered to U.S. national relevance,
configured magnitude thresholds, territories, and felt/multi-state impact rules. Preserve event id,
magnitude, depth, place, time, felt/intensity fields where present, source URL, bounding basis, and
seismic ranking evidence.

Current state: NATIONAL fixture parsing reuses the strict official-event URL and USGS GeoJSON
contract, with a configurable magnitude threshold defaulting to `national.earthquake_min_magnitude`
and coarse coordinate regions for the contiguous U.S., Alaska, Hawaii, Puerto Rico/U.S. Virgin
Islands, Guam/Northern Mariana Islands, and American Samoa. It stores the region/bounding basis,
event ID, magnitude, depth, place, time, felt/intensity, official URL, and seismic ranking terms.
The coarse regions are a first-pass relevance filter, not a U.S. boundary determination; nuanced
cross-border and multi-state felt-impact routing remains pending.

### FEMA/OpenFEMA Disaster Declarations Research

Status: implemented (research; no parser or live ingest enabled).

Research OpenFEMA disaster declarations and related FEMA data sources for stable API shapes,
declaration update behavior, incident type fields, state/FEMA region filters, retention,
source-health evidence, and ranking impact. Do not implement live fetch until endpoint behavior is
verified.

Current state: `docs/project/NATIONAL_OPENFEMA_DECLARATIONS_RESEARCH.md` records FEMA ownership,
the documented v2 JSON API, bounded response shape, query controls, twenty-minute dataset update
frequency, FEMA's `disasterNumber` plus `placeCode` primary key, nonpersistent generated IDs,
`lastRefresh` semantics, declaration and state/region fields, policy/attribution requirements,
privacy, retention, source-health behavior, ranking limits and a later exact-source release gate.
The separate NATIONAL fixture parser and live adapter remain unimplemented and disabled.

### CDC HAN Parser

Status: not implemented.

Build a fixture-first parser for CDC Health Alert Network notices after feed/page shape is verified.
Preserve alert id or URL, title, published/update time, alert type, affected population or
jurisdiction if provided, public instruction URL, preliminary status, bounded description, and
public-health ranking evidence.

Blocker reviewed 2026-10-15: official HAN pages expose notice IDs and alert types, but no
current machine-readable HAN feed/API was verified. Former RSS addresses redirect to CDC's
general emergency page, and candidate new XML paths return 404. See
`docs/project/NATIONAL_CDC_HAN_ENDPOINT_BLOCKER.md`. Keep the sources disabled as manual references;
do not scrape the notice list or invent a parser input shape. Continue when CDC documents a
current public endpoint.

### FDA Recall Endpoint/Feed Verification

Status: implemented (source verification; live ingest disabled).

Verify FDA recall endpoint/feed options before implementation. Identify whether RSS, enforcement
report data, or another official endpoint provides stable recall metadata. Preserve endpoint
ownership, parser shape, recall class/hazard/product fields, distribution geography, policy notes,
refresh interval, and source-health behavior.

Current state: `docs/project/NATIONAL_FDA_RECALL_SOURCE_VERIFICATION.md` records the official
Recalls, Food Safety and MedWatch RSS URLs, bounded item/XML and conditional-header observations,
cross-feed duplicates, absent structured severity/geography fields, policy/robots notes,
proposed interval, source-health behavior, and a future exact-URL release gate. The separate
openFDA enforcement API has useful classification and distribution fields but explicitly warns
against using its reports to issue public alerts or track recall lifecycle; it is held as
research/reference data for this feature. No FDA live source is enabled.

### FSIS Recall API Parser

Status: not implemented.

2026-10-15 source check: FSIS confirms a public API, but its linked documentation and candidate
API path returned HTTP 403 in bounded checks. Response shape and access remain unverified; see
`docs/project/NATIONAL_NHTSA_RECALL_API_VERIFICATION.md`. Keep disabled.

Build a fixture-first parser for the FSIS Recall API. Preserve recall id, product, firm, recall
class, hazard, distribution geography, public instruction URL, recall date, active/update status,
source URL, and food-safety ranking evidence.

### CPSC Recalls API Parser

Status: completed 2026-10-15 for bounded fixture ingest; live scanning remains disabled.

2026-10-15 follow-up: CPSC's official API page and programmer guide document a REST/JSON
service. A one-day HTTPS date query returned HTTP 200 JSON, 12 recall rows, and validated the
response shape. `cpsc_recalls_json` now validates an exact fixture source, seven-day query window,
15-second timeout ceiling, 1 MiB payload, 100-row cap, CPSC recall permalink, recall identity and
date. It stores bounded product, firm, hazard, injury-report and remedy text; labels death/injury
**risk** without claiming a reported death, and marks distribution geography unavailable when the
API does not structure it. Source-stated risk contributes capped NATIONAL attention and ranking;
the official response subset fixture and parser tests pass. No live
adapter or allowlisted network fetch is enabled. See
`docs/project/NATIONAL_NHTSA_RECALL_API_VERIFICATION.md`.

Build a fixture-first parser for the CPSC Recalls API. Preserve recall id, product, firm, hazard,
injury/death risk indicators when source-provided, recall date, URL, distribution scope, public
instruction URL, and consumer-safety ranking evidence.

### NHTSA Recalls API Parser

Status: implemented for fixture ingest; live integration remains disabled.

`nhtsa_recalls_json` validates the official lookup response envelope, groups model rows by
campaign, preserves bounded recall/safety fields, campaign source URL, day-precision report date,
consumer instruction URL, and capped vehicle-safety ranking evidence. A synthetic fixture,
parser tests and offline scan test pass. NATIONAL agency/sector facets include NHTSA and
transportation. The official API is a lookup and has no verified recent-recall discovery stream;
live polling requires separate signoff. See
`docs/project/NATIONAL_NHTSA_RECALL_API_VERIFICATION.md`.

Build a fixture-first parser for NHTSA recall APIs. Preserve recall campaign id, make/model/year or
equipment fields, component, safety risk, remedy, recall date, source URL, affected population
metadata where available, and vehicle-safety ranking evidence.

### FAA NAS Status Fixture Parser

Status: implemented for NATIONAL offline XML fixture ingest; live remains disabled.

The exact FAA NAS XML endpoint and active-event groups were checked on 2026-10-15. The
`faa_nas_status_xml` parser validates root/update time, rejects DTD/entity declarations and
unsupported active lists, groups events by airport, requires a verified airport-code allowlist,
preserves delay and closure source text, and supplies capped aviation ranking and NATIONAL
FAA/aviation facets. A synthetic fixture and offline scan test pass. Yearless closure times,
partial-airport closures, and country ambiguity remain explicit in the evidence. See
`docs/project/NATIONAL_FAA_NAS_XML_FIXTURE_VERIFICATION.md`.

Build a fixture-first parser for FAA NAS status and airport status candidates after endpoint
behavior is verified. Preserve airport, system, event type, delay estimate, ground stop or ground
delay status, closure status, start/end times, source update time, source URL, and aviation-impact
ranking evidence.

### CISA Advisory Parser

Status: not implemented.

2026-10-15 endpoint check: CISA's advisory page documents categories, but a candidate RSS query
returned HTTP 403 and a guessed XML path returned HTTP 404. No verified machine-readable schema
exists for this parser yet; see `docs/project/NATIONAL_CISA_ADVISORY_ENDPOINT_BLOCKER.md`. Keep
disabled while other source work proceeds.

Build a fixture-first parser for CISA cybersecurity advisories, alerts, ICS advisories, bulletins,
and emergency directives after feed/API shapes are verified. Preserve advisory id, title, CVE ids,
vendor/product, severity where source-provided, mitigation URL, published/update time, directive
flag, source URL, and cyber ranking evidence.

### CISA KEV Endpoint Research

Status: implemented as endpoint research; fixture parser and live ingest remain separate work.

The official JSON catalog and JSON Schema returned HTTP 200 in bounded reads on 2026-10-15.
Documented envelope, CVE identity, required/optional fields, date semantics, full-snapshot update
behavior, due-date interpretation, conditional headers, proposed cadence, policy gate, and
source-health states. The website advertises CSV but the guessed sibling CSV URL returned 404;
its exact current path is not signed off. See `docs/project/NATIONAL_CISA_KEV_ENDPOINT_RESEARCH.md`.
An offline fixture parser now validates the catalog envelope and CVE rows, preserves bounded
source evidence, and supplies cyber ranking and NATIONAL facets. No live KEV source was enabled.

Research CISA Known Exploited Vulnerabilities machine-readable endpoint options, including JSON/CSV
availability, schema fields, due date handling, update behavior, source policy, refresh interval,
and source-health behavior. Keep KEV disabled until endpoint verification and fixture tests exist.

### Federal Register API Parser With Filters

Status: implemented for offline filtered fixture ingest; live remains disabled.

The published-documents JSON envelope and default row metadata were verified in a bounded
official API read on 2026-10-15. `federal_register_documents_json` requires explicit agency,
document-type and title-impact allowlists, suppresses routine administrative notices, validates
document identity/URL, preserves optional comment/effective dates and bounded action evidence,
and supplies capped ranking and agency/sector facets. A synthetic fixture and offline scan test
pass. Optional action-window fields were not present in the default sampled list response, so
live field selection remains unsigned. See
`docs/project/NATIONAL_FEDERAL_REGISTER_API_FIXTURE_VERIFICATION.md`.

Build a fixture-first Federal Register API parser with agency allowlists, document type allowlists,
high-impact filters, public-comment/action window fields, and low-public-value suppression. Prevent
routine notices from flooding NATIONAL attention.

### GovInfo RSS Parser

Status: implemented for filtered offline fixture ingest; live remains disabled.

Three exact official GovInfo collection feeds returned RSS with GUID, title, date, details link,
category, and HTML content-file descriptions in bounded 2026-10-15 reads. The parser accepts
only verified collection channels with explicit title impact terms, validates official identity
and URL, strips/bounds description metadata, and preserves publication-stage and timestamp
caveats. A synthetic enrolled-bills fixture and offline scan test pass. See
`docs/project/NATIONAL_GOVINFO_RSS_FIXTURE_VERIFICATION.md`.

Build a fixture-first parser for allowlisted GovInfo RSS feeds. Preserve collection, title, URL,
published timestamp, bounded description, document identifiers, and official publication evidence.
Keep feeds filtered and disabled by default.

### Congress.gov API Design, Disabled And Auth-Required

Status: not implemented.

Design Congress.gov API access as disabled by default and `auth_required` unless a local key source
is explicitly configured. Define bill/action filters, public-impact thresholds, storage limits,
source-health states, and tests proving no API-key source runs without configuration.

### BLS/BEA/FRED/Treasury Economic Source Allowlist Design

Status: not implemented.

Design official economic source handling around configured release/series allowlists. Cover BLS,
BEA, FRED/Federal Reserve, Treasury Fiscal Data, Census, and Treasury sanctions where relevant.
Prevent investment advice, stock-picking, market speculation, and unbounded economic data ingestion.

### National News RSS Parser

Status: not implemented.

Build a fixture-first RSS/Atom parser for verified national news, public media, wire, broadcaster,
and nonprofit feeds. Store headline metadata only, bound descriptions, preserve publisher/source
family, detect duplicate or syndicated stories, and prevent duplicated articles from inflating
independent convergence.

### NATIONAL Deterministic Event Correlation

Status: partially implemented.

NATIONAL clusters now use official USGS, NWS, NHTSA, CISA KEV, Federal Register, and GovInfo IDs
where present, plus cautious cross-family matching on event type, explicit state/territory,
FEMA/NWS region, storm basin, airport, distribution area, infrastructure sector, population group,
or jurisdiction context, title tokens, and a 72-hour window. Match evidence, families, confidence,
and identity are persisted in item and cluster JSON. Same-family repeats are not marked
corroborated; complete-link grouping prevents a broad bridge from merging two incompatible events.
The currently verified fixture parsers supply only some of these fields, so coverage of all
specified dimensions and source-specific event mappings remains open. An offline duplicate-campaign
scan and synthetic context tests pass.

Implement deterministic NATIONAL event matching by source family, time window, normalized title
tokens, event type, agency, affected states, affected territories, FEMA region, NWS region, storm
basin, affected airports, product distribution area, infrastructure sector, affected population
group, court/federal jurisdiction, and national/multi-state labels. Do not use LLMs, embeddings, or
hidden cloud calls.

### NATIONAL Deterministic Ranking

Status: implemented for first-pass NATIONAL event clusters.

`national_ranking.py` scores stored clusters using bounded recency, official severity, independent
family diversity, temporal proximity, source-evidenced public impact, verified state/territory
reach, active alert state, source priority, cluster size, and explicit local/regional impact. It
subtracts duplicate-family, stale-source, low-confidence, low-public-value, and out-of-scope
penalties. Every nonzero factor has a stored reason and cluster/item JSON evidence; source-reported
NWS, USGS, NHTSA, CISA KEV, FAA NAS, and Federal Register metadata feed cautious signals. Headlines
alone cannot establish severity, impact, or reach. The cluster score no longer sums duplicate item
scores. Focused factor tests and an offline duplicate-campaign scan pass. Source-specific policy
classification and suppression remain in RS-051.

Implement explainable NATIONAL ranking with recency, official severity, source diversity, temporal
proximity, public impact, geographic reach, active alert state, source priority, cluster size,
local/regional impact, duplicate-family penalty, stale-source penalty, low-confidence penalty,
low-public-value penalty, and out-of-scope penalty. Store score features and ranking reasons in JSON
evidence.

### NATIONAL Low-Public-Value And Public-Impact Rules

Status: implemented for first-pass NATIONAL attention classification.

`national_policy.py` classifies source/item metadata before storage and records a reasoned
`national_policy` evidence block. It suppresses routine agency press families and personnel
announcements, opinion/punditry, generic campaign politics, procedural court filings, local-only
reports without explicit national impact, vague social-only claims, and economic releases outside a
configured title allowlist. Suppressed metadata stays auditable but is excluded from NATIONAL item
and cluster attention views. Same-article URLs and explicit syndication IDs merge without counting
as independent confirmation or adding duplicate article score. Official severe NWS alerts,
high-risk NHTSA recalls, CISA KEV, active FAA NAS disruptions, filtered Federal Register actions,
and explicit official disaster, cyber directive, high-risk recall, and public-health guidance
evidence receive cautious elevation. Headline-only severity is never inferred. Source-specific
parsers for later candidates will need to supply the explicit identity/action fields; the rules
already have offline unit and scan coverage.

Add deterministic NATIONAL rules that suppress routine agency press releases, generic political
messaging, minor personnel announcements, punditry, duplicate syndicated stories, local stories with
no national impact, vague social-only reports, routine court filings, and unconfigured economic
releases. Elevate official alerts, high-risk recalls, cyber directives, aviation disruption,
federal disaster declarations, and public-health warnings with action guidance.

### NATIONAL UI Disabled States

Status: implemented.

Replace NATIONAL placeholders only after storage/config support exists. Show honest states for
disabled, not configured, configured but disabled, never scanned, stale, policy blocked, parser
failed, auth required, rate limited, social disabled, homepage extraction disabled, and
manual-review-only sources. Do not show fake headlines.

Current state: NATIONAL uses the shared scope page and source-health readout. Page regressions now
cover disabled, not configured, configured but disabled, never scanned, stale, policy blocked,
parser failed, auth required, rate limited, social disabled, homepage extraction disabled, and
manual-review-only states without ingest or fabricated items. NATIONAL social sources receive a
scope-specific disabled message when the national social allowance is off.

### NATIONAL Source Health States

Status: implemented.

Implement source health states for NATIONAL: `disabled`, `not_configured`,
`configured_never_run`, `healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`,
`robots_blocked`, `auth_required`, `rate_limited`, `unsupported`, and `manual_review_only`. Surface
these states in SYSTEM later and summarize them on NATIONAL.

Current state: the shared source-health calculation covers NATIONAL and the NATIONAL page/API
expose its scope summary without fetching. The REGIONAL/NATIONAL matrix regression verifies stale,
parser-failed, policy-blocked, configured-never-run, disabled, manual-review-only, robots-blocked,
rate-limited, unsupported, and auth-required source states on both scopes. Shared scope-state tests
also cover disabled, not-configured, and healthy outcomes.

### NATIONAL Evidence Drawer Contract

Status: implemented for first-pass NATIONAL items and events.

NATIONAL items persist a versioned `evidence.national` contract with source identity, class,
family, official status, item/canonical URLs, publication and observation times, fetch run,
parser, health at ingest, event type/confidence, state/territory/airport fields and geography
basis, match tokens, public impact and source-diversity basis, ranking features, retention,
policy notes, and low-value/out-of-scope penalties. Cluster evidence includes event identity,
matching reasons/tokens, affected geography, score factors/reasons, and bounded member provenance.
The NATIONAL item and cluster drawers render these fields. A fixture scan and read-only HTML/API
contract test verifies persistence and display without HTTP access.

Define and test evidence payloads for NATIONAL items and events. Include source ids, names,
families, classes, item URLs, canonical URLs, official flags, published times, first/last seen,
fetch run ids, parser names, source health, ranking features, geographic reach basis, public impact
basis, source diversity basis, retention expiration, matching tokens, event type, event confidence,
policy notes, low-public-value penalty, and out-of-scope penalty.

### NATIONAL Official-Source Live Ingest Phase

Status: implemented at the first-source boundary; other candidates remain disabled.

The exact official USGS M2.5+ past-day GeoJSON feed is now allowlisted for NATIONAL
`usgs_eq_geojson` only after every parent, source, verification, magnitude, and HTTP opt-in gate.
The NATIONAL parser retains only earthquake-type features within coarse U.S./territory coordinate
regions and at/above its configured threshold; it does not infer cross-border or multi-state
impact. A bounded isolated explicit live scan returned HTTP 200, healthy source state, and one
stored NATIONAL item at the default 5.0 threshold. Mocked tests cover default blocking, gate
rejection, conditional refresh, and no test HTTP. The standing config remains disabled. See
`docs/project/NATIONAL_USGS_LIVE_SOURCE_SIGNOFF.md`. NWS, CISA, FSIS, FAA and other live candidates
require their own source-specific verification and admission.

After fixtures, correlation, ranking, retention, source health, and tests exist, add opt-in live
ingest for one safe official source at a time. First candidates are NWS active alerts, USGS
earthquake GeoJSON, CISA advisories or KEV if endpoint is verified, FSIS Recall API, and FAA NAS
status if endpoint behavior is verified. Keep every source disabled by default and require an
explicit command. No page-load fetches.

### NATIONAL News RSS Ingest Phase

Status: not implemented.

Add opt-in RSS/Atom ingest for verified national news, public-media, wire, broadcaster, and
nonprofit feeds only after source verification. Store headline metadata only, bound descriptions,
avoid article bodies, avoid paywall bypass, and prevent duplicate syndicated articles from
inflating independent convergence.

### NATIONAL Social Source Policy Review

Status: not implemented.

Review Bluesky AT Protocol, Reddit official API or permitted feed access, and X official API rules
before implementing any national community/social adapter. Keep social disabled by default, require
explicit configuration, use short retention, and never scrape HTML to bypass platform restrictions.

### Documentation For Source Verification

Status: implemented for the first-pass NATIONAL source workflow.

`docs/project/NATIONAL_SOURCE_VERIFICATION_WORKFLOW.md` now applies the shared per-source signoff
and release gate to agency/sector, U.S. geography, public action, filtering, authentication,
sensitivity, and source-health decisions. It links the completed exact USGS live signoff, fixture
and research decisions for NHTSA, CISA KEV, FDA, FAA, Federal Register and GovInfo, and explicit
CDC HAN/CISA advisory and FSIS/CPSC blockers. It distinguishes research and fixture evidence from
live admission, requires a disabled registry default and exact transport tuple, and records the
first isolated live smoke outcome. New sources need their own worked record before admission.

Document the later NATIONAL source verification workflow: confirm endpoint ownership, access
method, source terms, robots/policy notes, parser shape, auth/key requirements, rate limits,
retention sensitivity, privacy risk, verification status, agency/sector/state filters, and
source-health behavior before enabling any source.

Current state: `docs/project/NATIONAL_SOURCE_VERIFICATION_WORKFLOW.md` now captures the shared
verification checklist, required registry fields, and scope-specific agency/sector/state filters.
Per-source signoff templates and endpoint-specific walkthroughs still need a dedicated follow-up.

### Tests For No Page-Load External Fetches

Status: implemented.

Add tests proving GET routes and page renders read SQLite/config only and never call NATIONAL
network fetchers. Include disabled/not configured/stale/failing/auth-required/policy-blocked/parser
failed state tests for NATIONAL and SYSTEM source health.

Current state: the GET-route regression now includes NATIONAL page and API paths with a deliberately
missing fixture, and fails if scan or official HTTP fetch is attempted. It also checks SYSTEM page
and summary state. NATIONAL/SYSTEM baseline and source-state matrix regressions cover disabled,
not configured, never run, stale, parser failure, policy blocking, auth required, and failing
aggregation without a network call.

### Tests For No API-Key Source Running Without Config

Status: implemented.

Add tests proving Congress.gov, BEA, FRED, and any other API-key or auth-required source cannot run
without explicit local configuration. The tests should assert clear `auth_required` source-health
state and no network calls.

Current state: the NATIONAL registry marks Congress.gov API, BEA developer/API reference, FRED API
docs, and AirNow API docs as key-required candidates; these remain disabled and are not live
endpoints. The scanner rejects every enabled source with declared but unconfigured auth before
fixture access or HTTP. A regression covers those four candidates plus a custom auth-required
source, asserting `auth_required` fetch/health states, zero stored items, and no fixture or network
access. No credential is stored in SQLite policy evidence.

## GLOBAL World Recent Signal Layer

Architecture reference:

- `docs/project/GLOBAL_WORLD_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### GLOBAL Source Registry Design Implementation

Status: implemented.

Implement the GLOBAL source registry from the design document with explicit `source_key`,
`source_name`, `source_family`, `source_class`, `scope`, `raw_url`, access kind, adapter type,
refresh interval, priority, official status, privacy risk, policy risk, parser risk, retention
sensitivity, verification status, source-health behavior, and future phase fields. Validate enum
values and keep every GLOBAL source disabled until explicitly configured.

Current state: `console1701/news/global_registry.json` contains all 172 original GLOBAL source
targets plus one verified IAEA Top News RSS entry, preserving provenance, access, risk, verification, priority, and
future-phase fields. The loader validates scope, URL shape, enum values, and duplicate keys, and
adds source-health planning behavior. Config defaults remain disabled, known metadata fields reject
unknown values, and explicit `news-scan` persists the inventory in `news_source_registry`. This is
planning metadata; it does not enable or allowlist any GLOBAL live request.

### Disabled-By-Default GLOBAL Config

Status: implemented.

Add a `global:` or equivalent GLOBAL config tree that defaults to disabled. Include flags for
disasters, humanitarian, public health, weather hazards, tropical cyclones, earthquakes, tsunamis,
volcanoes, wildfire/smoke, air quality, conflict-humanitarian, diplomacy/institutions,
transport/supply chain, cybersecurity, global economy, global news, social sources, U.S. impact
tags, and local impact tags. Reject social, auth-required, heavy open-data, and homepage extraction
sources unless explicit local flags are set.

Current state: `global:` defaults to disabled and validates the specified inclusion flags,
impact tags, thresholds, and attention settings. Source normalization validates registry metadata.
Enabled auth-required and high-policy-risk conflict sources still require explicit configuration
before config loads; social, heavy open-data, homepage, and manual-review candidates load into
visible source health but are blocked before file or network access until their gates are met.
The example config documents disabled settings. No GLOBAL source is live allowlisted.

### GLOBAL SQLite Schema Or Extension

Status: completed 2026-10-15 for first-pass storage contract.

Add or extend SQLite storage for GLOBAL source registry state, fetch runs, normalized items,
`global_events` or scoped clusters, source health, ranking explanations, crisis sensitivity flags,
impact tags, retention purge evidence, and source verification metadata. Use JSON-heavy columns and
indexes for latest-by-scope, event ranking, source health, source family, event type, affected
country/region, and `expires_at` purge. Do not store full article bodies by default.

Current state: the shared scoped source registry stores all 173 GLOBAL inventory rows and exposes a
GLOBAL registry summary. Shared source, fetch, item, health, cluster, and retention tables persist
GLOBAL records without full article bodies. `news_item_facets` indexes country, verified region,
event type, source family, impact tag, and explicit sensitivity flags; it backfills existing GLOBAL
items, refreshes when item evidence changes, and cascades on retention purge. Query and purge tests
verify those paths. Broader event correlation and sensitivity classification remain separate rows.

### GLOBAL Fixture Pack

Status: partially implemented.

Create local-only fixtures for GDACS feeds/API responses, ReliefWeb disasters and reports, WHO
Disease Outbreak News, ECDC RSS, USGS earthquake GeoJSON, NHC RSS, Smithsonian GVP weekly report,
UN News RSS, UN Press RSS, IAEA RSS, global news RSS, source-health states, disabled sources, stale
sources, auth-required sources, and parser failures. Fixture ingest must not perform network calls
and must be safe for pytest.

Current state: checked-in GDACS RSS/API GeoJSON, ReliefWeb disaster/report, WHO DON, ECDC RSS,
USGS earthquake, NHC RSS, UN News RSS and UN Press RSS fixtures exercise offline parser and
`news-scan` persistence paths. Smithsonian GVP, IAEA, broader news and remaining health/failure
variants are pending.

### GDACS Feed Parser

Status: completed 2026-10-15.

Build a fixture-first GDACS feed parser for GLOBAL scope. Preserve alert id, event type, country or
region, event name, alert level, severity fields when source-provided, published/update time,
source URL, geometry or bounding metadata when available, and official-alert ranking evidence.

Verified against the official GDACS RSS endpoint shape on 2026-10-15. The dedicated GLOBAL parser
preserves event and episode IDs, alert and severity, country, dates, report URL, point and bounding
metadata, and official-alert ranking evidence. Offline fixture and `news-scan` persistence tests pass;
live GDACS HTTP remains disabled.

### GDACS API Fixture Parser

Status: completed 2026-10-15.

Build a fixture-first GDACS API parser after endpoint behavior is verified. Preserve disaster id,
event type, severity, alert level, affected geography, coordinates or geometry when available,
start/update time, source URL, and source-health evidence. Keep live API access disabled by default.

Verified against the official GDACS API Search GeoJSON response shape on 2026-10-15. The dedicated
GLOBAL parser preserves event and episode IDs, alert/severity, affected country, point/bounding
metadata, start/update time, report URL, and fixture source-health evidence. Offline fixture and
`news-scan` persistence tests pass; live GDACS HTTP remains disabled.

### ReliefWeb Disasters API Parser

Status: completed 2026-10-15 for fixture-first parser; live source remains blocked.

Build a fixture-first parser for ReliefWeb disaster records. Preserve disaster id, name, status,
country list, disaster type, primary dates, source URL, related reports count where available, and
humanitarian ranking evidence. Store metadata only and avoid report body ingestion.

Current state: parser accepts documented ReliefWeb v2 `data[].fields` disaster metadata, preserves
ID, status, countries/types, event/create/update dates, canonical URL, optional source-provided
report count, and humanitarian ranking evidence. Offline fixture and persistence tests pass. Live
API response could not be sampled: ReliefWeb requires a pre-approved `appname` from 2025-11-01;
an unapproved 2026-10-15 request returned 403. Registered disaster/update sources now require
configured appname before any file or network access. No live ReliefWeb allowlist exists.

### ReliefWeb Reports API Parser

Status: completed 2026-10-15 for fixture-first parser; live source remains blocked.

Build a fixture-first parser for ReliefWeb reports and updates with strict filters for active
disasters, official sources, humanitarian relevance, bounded descriptions, source organization,
country list, publication time, report URL, and retention expiration. Prevent report volume from
flooding GLOBAL attention.

Current state: a fixture-first parser requires explicit configured active-disaster IDs, reviewed
source names, humanitarian theme names, a 1-25 item cap, and 1-7 day retention. It retains bounded
headline summary, source/country/disaster evidence and publication time, and ignores full report
bodies. A mixed fixture verifies exclusions and scan persistence/expiration. Active IDs are a
curated input; automatic synchronization from ReliefWeb disasters remains future correlation work.
ReliefWeb's pre-approved appname rule and absent live allowlist keep live updates blocked.

### WHO Disease Outbreak News Parser

Status: completed 2026-10-15 for fixture-first parser; live source remains disabled.

Build a fixture-first WHO Disease Outbreak News parser. Preserve outbreak title, disease or hazard
label, affected country or region, publication/update time, source URL, bounded summary, official
public-health evidence, and outbreak ranking features. Do not infer case counts unless the source
provides structured values.

Current state: the WHO OData DON response shape and an article URL were verified against official
WHO endpoints on 2026-10-15. The parser retains title, publication/modification time, a bounded
summary, official URL, and clearly marked title-derived hazard/geography labels. It ignores full
article fields and does not infer case counts. Offline fixture and scan persistence tests pass;
there is no WHO live HTTP allowlist.

### ECDC RSS Parser

Status: completed 2026-10-15 for fixture-first parser; live source remains disabled.

Build a fixture-first ECDC RSS parser after feed shape is verified. Preserve title, published time,
URL, category when provided, bounded description, public-health source evidence, and Europe/global
impact tags. Keep it lower priority than WHO DON unless convergence or severity warrants elevation.

The official ECDC RSS index links to a News/press releases RSS 2.0 feed. The fixture-first parser
preserves title, official URL, publication time, optional category, creator/GUID, and bounded
plain-text description. It labels Europe/GLOBAL public-health context without inventing event
impact geography or severity. The disabled `ecdc_rss` registry entry now names the verified feed
URL and retains priority 50 versus WHO DON's 100. Offline fixture, scan/health, policy, and
ranking regressions pass; [verification notes](docs/project/GLOBAL_ECDC_RSS_SOURCE_VERIFICATION.md)
record the observed shape. No ECDC HTTP URL is allowlisted for app ingest.

### WMO CAP Warning Source Verification

Status: first-pass source verification complete; CAP parser and exact-feed ingest remain open.

Verify WMO severe weather source references, CAP availability, national meteorological service
links, ownership, policy notes, parser shape, refresh interval, and source-health behavior before
implementation. Do not scrape warning maps or dashboards.

The official SWIC source directory names issuing national services and links to exact CAP feeds.
Australian BoM's WMO-hosted RSS and linked CAP 1.2 warning shape were inspected; DWD's official
RSS channel was reachable but had no current items. The SWIC dashboard and directory are now
reference-only health entries, never alert adapters, with an offline scan regression proving no
file or HTTP ingest. The [verification notes](docs/project/GLOBAL_WMO_CAP_SOURCE_VERIFICATION.md)
record issuer attribution, parser fields, tentative feed-specific cadence, and policy/health gates.
No CAP URL is live-allowlisted by the app.

### USGS Global Earthquake GeoJSON Parser

Status: completed 2026-10-15 for fixture-first parser; live source remains disabled.

Build a fixture-first parser for USGS global earthquake GeoJSON with configured magnitude,
tsunami, depth, felt, intensity, country/region, and time-window filters. Preserve event id,
magnitude, depth, place, time, update time, source URL, tsunami flag, and seismic ranking evidence.

The existing USGS GeoJSON adapter now has a GLOBAL-specific filter and uses
`global.earthquake_min_magnitude` by default. It supports tsunami-only, depth, felt, MMI,
source-place country/region term, and origin-age filters; preserves the listed official metadata;
and records `source_place_unverified` instead of inferring a country from free text. A synthetic
official-shape fixture and offline scan tests cover inclusion/exclusion, health, identity, and
ranking. [Verification notes](docs/project/GLOBAL_USGS_GEOJSON_SOURCE_VERIFICATION.md) record the
USGS documentation and live-feed candidate. No GLOBAL USGS HTTP URL was allowlisted or enabled.

### NHC RSS Parser

Status: completed 2026-10-15 for fixture-first GLOBAL parser; live source remains disabled.

Build a fixture-first parser for National Hurricane Center RSS/global tropical weather candidates
after source scope is verified. Preserve basin, storm id/name when present, advisory type,
watch/warning terms, published/update time, source URL, and tropical-cyclone ranking evidence.

The official Atlantic, Eastern Pacific, and Central Pacific basin XML feeds were inspected, and
the Eastern Pacific feed supplied active summary/Public Advisory shapes. The dedicated parser
retains explicit ATCF identity, basin, storm name/type, advisory number, source time/URL, and
watch/warning terms while excluding outlooks and inactive placeholders. It marks watch geography
unverified and uses a summary only when the corresponding Public Advisory is absent. A synthetic
official-shape fixture verifies offline ingest, global event identity/type, source health, and
no inferred affected country. [Verification notes](docs/project/GLOBAL_NHC_RSS_SOURCE_VERIFICATION.md)
record exact URLs and limitations. No NHC HTTP URL is allowlisted by the app.

### Smithsonian GVP Weekly Report Parser

Status: partially researched; official RSS XML access blocked from this environment.

Build a fixture-first parser for Smithsonian Global Volcanism Program weekly report candidates.
Preserve volcano name, country/region, activity type when structured, report window, source URL,
and volcano ranking evidence. Keep parser conservative where page structure is not stable.

The official weekly report page links `https://volcano.si.edu/news/WeeklyVolcanoRSS.xml` and
documents report categories, weekly cadence, and preliminary status. A bounded direct request to
that exact RSS URL returned HTTP 403 on 2026-10-15, so its item XML shape remains unverified.
Keep the parser row open until a legitimate official sample can be inspected; do not bypass the
site access control or infer feed fields from the HTML page. The report page remains a reference
source only.

### NASA FIRMS API Review And Filtered Fixture Parser

Status: not implemented.

Review NASA FIRMS access, key requirements, terms, rate limits, area filters, retention, and
appropriate global wildfire/smoke use before implementation. If allowed, build only a filtered
fixture parser with explicit geography and severity controls. Keep live FIRMS access disabled by
default and require explicit local configuration.

### UN News RSS Parser

Status: completed 2026-10-15 for fixture-first parser; live source remains disabled.

Build a fixture-first UN News RSS parser for institution and global public-impact signals. Preserve
headline, URL, published time, category when present, bounded description, source family, and
diplomacy/institution ranking evidence. Suppress routine speeches and low-impact feature stories.

The official RSS endpoint and item shape were inspected. The parser stores official story GUIDs,
feed links, publication time, optional categories, source label, bounded plain-text descriptions,
and institution identity. Narrow roundup/feature/routine-remarks exclusions avoid low-value
entries without claiming that every remaining story has public impact. The website registry row
is reference-only; the RSS row names the exact feed and remains disabled for HTTP. Offline fixture
scan and source-health tests pass. [Verification notes](docs/project/GLOBAL_UN_NEWS_RSS_SOURCE_VERIFICATION.md)
record the observed shape and limitations.

### UN Press RSS Parser

Status: implemented for filtered offline fixture ingest; live remains disabled.

The exact official UN Press RSS channel and item fields were checked on 2026-10-15. A dedicated
GLOBAL parser requires configured active-crisis terms, suppresses routine remarks and schedule
items, and preserves bounded press metadata, official URL/GUID, publication time, cautious
title-derived organ label, and institution evidence. Synthetic fixture and offline scan tests
pass. See `docs/project/GLOBAL_UN_PRESS_RSS_SOURCE_VERIFICATION.md`.

Build a fixture-first UN Press RSS parser with filters for Security Council, General Assembly,
humanitarian, sanctions, emergency sessions, peacekeeping, and active crisis terms. Preserve title,
URL, publication time, organ/category where available, and official institution evidence.

### IAEA RSS Parser

Status: implemented for first-pass GLOBAL fixture ingest; live disabled.

The official IAEA Top News RSS endpoint and its numeric GUID, HTTP article URL, category-when-
available, and timezone-free publication date shape were checked. `iaea_rss` canonicalizes official
article links to HTTPS, stores a bounded description and explicit day-precision date evidence,
and retains narrow nuclear emergency titles or Director General situation updates matching a
configured active crisis. Routine training, science, and institutional content is suppressed.
The parser stores source, institution, and cautious nuclear-safety ranking evidence; a synthetic
fixture and offline scan test pass. See `docs/project/GLOBAL_IAEA_RSS_SOURCE_VERIFICATION.md`.

Build a fixture-first IAEA RSS parser for nuclear safety and international nuclear institution
signals. Preserve title, URL, publication time, category when available, bounded description,
source family, and nuclear-safety ranking evidence. Suppress routine institutional content unless
configured.

### Humanitarian Source Evidence Contract

Status: implemented for first-pass GLOBAL ReliefWeb disaster and report items.

Persisted `evidence.humanitarian` now carries source identity/family/status, affected countries,
disaster IDs, event type, publication and local observation times, bounded description, report and
source URLs, retention expiry, policy notes, and an explicit omitted people-at-risk value. Offline
scan tests verify both source shapes and no report body leakage. See
`docs/project/GLOBAL_HUMANITARIAN_EVIDENCE_CONTRACT.md`.

Define and test evidence payloads for humanitarian GLOBAL items. Include source id, source family,
official or humanitarian status, affected countries, disaster/crisis id where available, event
type, source publication time, first/last seen, bounded description, report URL, retention
expiration, policy notes, and whether people-at-risk metadata is source-provided or omitted.

### Conflict-Humanitarian Sensitivity Rules

Status: implemented for the first-pass explicit-evidence policy.

GLOBAL sources now have validated conflict-sensitive and sensitivity-flag policy. Ranking caps
unconfirmed conflict/rumor context unless an official source or two independently corroborated
families support elevation. Graphic/private/speculative/source-laundered flags suppress clusters;
identifying headline and description fields are redacted before storage for personal/graphic
cases. Ranking evidence stores flags, confirmation basis and cautious labels. Offline tests verify
redaction and no attention cluster. See
`docs/project/GLOBAL_CONFLICT_HUMANITARIAN_SENSITIVITY_RULES.md`.

Add deterministic rules for conflict and humanitarian signals that avoid war-ticker behavior,
graphic violence amplification, rumor elevation, casualty speculation, targeted-person tracking,
private distress, doxxing, and source laundering. Require official or multi-family convergence for
elevation and preserve cautious labels for conflict-adjacent items.

### GDELT Policy Review And Strict Allowlist Design

Status: not implemented.

Review GDELT access, terms, API behavior, rate limits, data volume, retention, and risk before any
implementation. Design a strict allowlist that treats GDELT only as a low-weight trend echo, never
as primary evidence, and keeps it disabled by default.

### ACLED Policy/Auth/Attribution Review

Status: not implemented.

Review ACLED access requirements, licensing, attribution, auth, rate limits, permitted use,
retention sensitivity, conflict-risk handling, and source-health behavior before any implementation.
Keep ACLED disabled by default and do not run it without explicit local credentials and policy
approval.

### World Bank / IMF / OWID Configured-Indicator Design

Status: not implemented.

Design global economic and development indicators as configured allowlists, not broad data pulls.
Cover World Bank, IMF, OWID, and similar sources with explicit indicator ids, refresh cadence,
retention, source-health states, ranking use, and non-goals that prevent investment advice,
commodity speculation, and unbounded open-data ingestion.

### Global News RSS Parser

Status: not implemented.

Build a fixture-first RSS/Atom parser for verified global news, wire, public-media, broadcaster,
regional-global, and nonprofit feeds. Store headline metadata only, bound descriptions, preserve
publisher/source family, detect duplicate or syndicated stories, and prevent duplicated articles
from inflating independent convergence.

### GLOBAL Deterministic Event Correlation

Status: partially implemented.

Implement deterministic GLOBAL event matching by source family, event type, time window,
normalized title tokens, affected countries or regions, disaster id, outbreak terms, storm id,
earthquake id, volcano name, institution, transport sector, cyber identifiers, and impact tags. Do
not use LLMs, embeddings, or hidden cloud calls.

Current state: GLOBAL cluster rebuilding uses a deterministic matcher for shared GDACS,
ReliefWeb-disaster/report, and WHO DON identifiers or cross-family event-type, verified-country,
title-token, and 96-hour convergence. Same-family title similarity alone cannot corroborate an
event. Cluster evidence records matched item pairs and basis, known source families, identifiers,
countries, event types, and source-reported versus independently corroborated confidence.
Cluster evidence keeps only the strongest base item score from each family for audit; the event
ranking uses independent family count and a duplicate-family penalty, so repeated same-family
items cannot create extra convergence credit. A complete-link guard rejects a broad item that
would bridge otherwise incompatible events. The matcher also accepts parser-supplied verified
regions, basins, storm and
earthquake IDs, volcano names, disease, institution, transport, cyber, and impact-tag context;
USGS event IDs are recognized from parsed evidence. Remaining work: populate and validate those
fields in the relevant future source parsers and fixtures, test convergence with their actual
records, and broaden GLOBAL versus domestic scope-routing coverage.

### GLOBAL Deterministic Ranking

Status: completed 2026-10-15 for first-pass algorithm.

Implement explainable GLOBAL ranking with recency, official severity, independent source
diversity, temporal proximity, public impact, affected geography, humanitarian sensitivity,
source priority, cluster size, local/regional/national impact tags, duplicate-family penalty,
stale-source penalty, low-confidence penalty, low-public-value penalty, and out-of-scope penalty.
Store score features and ranking reasons in JSON evidence.

Current state: GLOBAL clusters now use a bounded stored-metadata score with recency, official
severity, independent family diversity, temporal proximity, verified geography, active alert,
public and humanitarian impact, source priority, cluster size, and explicit U.S./national,
regional, and local impact tags. The result subtracts duplicate-family, stale-at-ingest,
low-confidence, low-public-value, out-of-scope, and rumor penalties. Each factor and reason is
stored in cluster and linked item evidence and shown in the cluster drawer. Tests cover official
alert, convergence, duplicates, recency/geography, humanitarian impact, source priority, cluster
size, confidence, policy penalties, and refusal to infer impact from a dramatic headline. The
remaining source-specific fixture evidence belongs to the corresponding adapter and policy rows;
the ranking contract treats missing evidence as zero rather than inventing it.

### GLOBAL Low-Public-Value, Rumor, And Public-Impact Rules

Status: partially implemented.

Add deterministic GLOBAL rules that suppress routine diplomatic statements, generic political
punditry, single-source social chatter, rumor, graphic violence amplification, private distress,
routine institutional content, routine economic releases, duplicate syndicated stories, and
unconfigured domestic politics. Elevate official alerts, high-severity disasters, major outbreaks,
tsunami/tropical-cyclone hazards, global transport disruption, nuclear safety alerts, and verified
multi-source public-impact events.

Current state: the GLOBAL event scorer recognizes explicit parser-provided routine/background,
rumor, out-of-scope, and domestic-impact tags and records bounded penalties or boosts. It uses
official GDACS alert, USGS earthquake/tsunami, and active ReliefWeb disaster evidence for
first-pass public-impact scores. It does not infer impact from headline wording. A pre-storage
`global_policy.py` classifier now labels routine diplomatic/institutional/economic headlines,
opinion, domestic politics without international evidence, and single-source social background;
explicit rumor and graphic/private-person language set sensitivity evidence, and graphic content
is redacted before storage. Official alert metadata prevents a routine headline from suppressing
an active alert. Direct and offline scan tests verify those rules. Remaining work: source-specific
coverage for broader public-impact categories, duplicate syndication across source families,
and additional low-value/sensitive fixture variants.

### GLOBAL UI Disabled States

Status: completed 2026-10-15 for first-pass acceptance.

Replace GLOBAL placeholders only after storage/config support exists. Show honest states for
disabled, not configured, configured but disabled, never scanned, stale, policy blocked, parser
failed, auth required, rate limited, social disabled, homepage extraction disabled, heavy open-data
disabled, token/account source not configured, and manual-review-only sources. Do not show fake
headlines.

The shared GLOBAL page renders real, unexpired stored items without placeholder headlines. It
shows disabled/not-configured/configured-disabled/never-run scope states, stored stale/failure and
policy states, and dedicated heavy/homepage gate counts. The first six source cards are followed
by an expandable list of every remaining configured source with its health state and message.
Expired items and their cluster traces are hidden before the next scan.

### GLOBAL Source Health States

Status: completed 2026-10-15 for first-pass acceptance.

Implement source health states for GLOBAL: `disabled`, `not_configured`, `configured_never_run`,
`healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`, `robots_blocked`,
`auth_required`, `rate_limited`, `unsupported`, `manual_review_only`,
`heavy_open_data_disabled`, `social_disabled`, and `homepage_extract_disabled`. Surface these
states in SYSTEM later and summarize them on GLOBAL.

GLOBAL source cards, overflow list, API, and SYSTEM scope-readiness counts surface the configured
source-health states. The GLOBAL/SYSTEM GET regression covers disabled/not-configured/never-run,
healthy/stale/failing/parser-failed/policy-blocked/rate-limited/robots-blocked/unsupported outcomes;
the gated-source regression covers auth-required, manual-review-only, heavy-data-disabled,
social-disabled, and homepage-extraction-disabled outcomes with fetch-run evidence.

### GLOBAL Evidence Drawer Contract

Status: implemented for first pass.

Define and test evidence payloads for GLOBAL items and events. Include source ids, names, families,
classes, item URLs, canonical URLs, official flags, published times, first/last seen, fetch run ids,
parser names, source health, ranking features, affected countries/regions, public impact basis,
source diversity basis, retention expiration, matching tokens, event type, event confidence, policy
notes, sensitivity notes, low-public-value penalty, out-of-scope penalty, and impact tags.

Current state: fixture-ingested GLOBAL items persist a versioned `evidence.global` payload with
source identity/class/official status, URL and seen/published times, fetch/parser/health context,
parser-provided geography and event type, attention-policy and sensitivity notes, retention expiry,
matching, score factors, source-provided public-impact basis, and explicit penalty evidence. The
item drawer displays these fields. GLOBAL clusters include pairwise match reasons, event ranking,
and a bounded snapshot of each member's item contract, including policy and redaction evidence;
the cluster drawer shows source, confidence, geography, impact, expiry, match, and ranking details.
Offline scan/page and sensitive-content regressions verify persistence and presentation. Future
adapters still need their own source-specific event and impact evidence before admission.

### GLOBAL Official-Source Live Ingest Phase, Disabled By Default

Status: implemented for the first exact official source. The USGS M4.5+
past-week GeoJSON feed is opt-in for GLOBAL with a M6+ default threshold,
30-minute minimum interval, bounded transport, offline tests, and an isolated
successful live smoke. [Endpoint signoff](docs/project/GLOBAL_USGS_LIVE_SOURCE_SIGNOFF.md).
GDACS and other GLOBAL endpoints remain disabled pending individual signoff.

After fixtures, correlation, ranking, retention, source health, and tests exist, add opt-in live
ingest for one safe official GLOBAL source at a time. First candidates are GDACS feed/API,
ReliefWeb disasters, WHO Disease Outbreak News, USGS global earthquake GeoJSON, NHC RSS, UN News
RSS, UN Press RSS, and IAEA RSS after verification. Require explicit commands and no page-load
fetches.

### GLOBAL News RSS Ingest Phase, Disabled By Default

Status: not implemented.

Add opt-in RSS/Atom ingest for verified global news, wire, public-media, broadcaster,
regional-global, and nonprofit feeds only after source verification. Store headline metadata only,
bound descriptions, avoid article bodies, avoid paywall bypass, and prevent duplicate syndicated
articles from inflating independent convergence.

### GLOBAL Heavy Open-Data Phase, Disabled By Default

Status: not implemented.

Add any heavy open-data source only after explicit policy, access, rate-limit, storage, retention,
and value review. Require configured indicators, explicit source allowlists, fixture tests, and
source-health states proving no heavy source runs without explicit local configuration.

### GLOBAL Social Source Policy Review, Disabled By Default

Status: not implemented.

Review Reddit official API or permitted feed access, X official API rules, Bluesky AT Protocol, and
official social-account use before implementing any GLOBAL social adapter. Keep social disabled by
default, require explicit local configuration, use short retention, never scrape HTML to bypass
platform restrictions, and never treat social as primary evidence.

### Documentation For Source Verification

Status: completed 2026-10-15 for first-pass GLOBAL verification workflow.

Document the later GLOBAL source verification workflow: confirm endpoint ownership, access method,
source terms, robots/policy notes, parser shape, auth/key requirements, rate limits, retention
sensitivity, privacy risk, verification status, geography/relevance filters, source-health
behavior, and whether the source is official, media, nonprofit, platform, open-data, or manual
review only.

Current state: `docs/project/GLOBAL_SOURCE_VERIFICATION_WORKFLOW.md` captures the shared
verification checklist, registry fields, geography/relevance and source-type filters, per-endpoint
signoff record, exact live promotion gates, and evidence-linked walkthroughs for GDACS, WHO,
ReliefWeb, USGS, UN and IAEA. Each walkthrough states fixture-only status and its distinct live
release work.

### Tests For No Page-Load External Fetches

Status: completed 2026-10-15 for first-pass acceptance.

Add tests proving GET routes and page renders read SQLite/config only and never call GLOBAL network
fetchers. Include disabled/not configured/stale/failing/auth-required/policy-blocked/parser-failed,
heavy-open-data-disabled, social-disabled, homepage-extraction-disabled, and manual-review-only
state tests for GLOBAL and SYSTEM source health.

GLOBAL and SYSTEM page GETs plus GLOBAL scope/summary/source API GETs run under scanner fixture
and official-HTTP access traps across unstarted, stored-health, and five gated-source states.
The routes render SQLite/config state only. No GET invokes a scan or fetch.

### Tests For No Heavy Source Running Without Explicit Config

Status: completed 2026-10-15.

Add tests proving HDX/HAPI, NASA FIRMS, GDELT, OWID, World Bank, IMF, ArcGIS, catalog, CSV, and
other heavy open-data candidates cannot run unless explicitly enabled in local config. Tests should
assert no network calls and clear disabled source-health states.

All 20 current heavy GLOBAL registry candidates are configured as enabled with nonexistent local
fixtures and no heavy-data gate. Scan records `heavy_open_data_disabled` or `auth_required` before
file/network access; zero items are stored. This includes HDX/HAPI, NASA FIRMS, GDELT, OWID,
World Bank, IMF, ArcGIS, catalogs, and CSV candidates.

### Tests For No Token/Account Source Running Without Config

Status: completed 2026-10-15 for known registry candidates.

Add tests proving ACLED, Reddit, X, Bluesky, NASA FIRMS if key-required, IMF if key-required, and
any other token/account source cannot run without explicit local configuration. The tests should
assert clear `auth_required` or policy-disabled source-health state and no network calls.

The known auth-required registry set plus Reddit, X, and Bluesky candidates are scanned with
nonexistent local fixtures and no account material. They produce `auth_required`, social-disabled,
heavy-disabled, or manual-review states before file/network access; zero items are stored.

## ORBITAL Space Recent Signal Layer

Architecture reference:

- `docs/project/ORBITAL_SPACE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### ORBITAL Source Registry Design Implementation

Status: implemented as disabled planning inventory.

All 136 ORBITAL design-table entries are checked into `orbital_registry.json` with source/family,
class, exact or reference URL, access, adapter, interval, priority, status, risks, phase, and
planned health behavior. The loader validates enums, URL exceptions, key uniqueness, priority,
and cadence; config inherits registry defaults, all entries remain disabled, and explicit scan
syncs the inventory to SQLite and summary. Reference-only rows cannot ingest even with an
overridden local file URL. The ORBITAL policy tree and candidate gates follow in RS-090; this
registry does not admit live HTTP.

Implement the ORBITAL source registry from the design document with explicit `source_key`,
`source_name`, `source_family`, `source_class`, `scope`, `raw_url`, access kind, adapter type,
refresh interval, priority, official status, privacy risk, policy risk, parser risk, retention
sensitivity, verification status, source-health behavior, and future phase fields. Validate enum
values and keep every ORBITAL source disabled until explicitly configured.

### Disabled-By-Default ORBITAL Config

Status: completed 2026-10-15 for the first-pass policy tree and candidate gates.

Add an `orbital:` or equivalent ORBITAL config tree that defaults to disabled. Include flags for
space weather, aurora, NEO close approaches, fireballs, launches, crewed spaceflight, ISS,
reentries, debris, satellite catalog, conjunction awareness, space agency news, spaceflight news,
astronomy transients, social sources, and restricted/auth sources. Reject social, auth-required,
restricted, tactical, and homepage-extraction sources unless explicit local flags are set.

Current state: `orbital:` defaults to disabled and validates the inclusion and sensitive-source
flags. The ORBITAL scope remains disabled in source health until the parent flag is enabled.
Source policy blocks social, auth-required, restricted, tactical, homepage, and disabled topic
classes before file or HTTP access. Registry candidates without a verified parser remain
manual-review-only, including sensitive tracking classes even if their flags are enabled.
The example config documents the flags. No ORBITAL source is live allowlisted.

### ORBITAL SQLite Schema Or Extension

Status: completed 2026-10-15 for first-pass shared storage and indexed ORBITAL facets.

Add or extend SQLite storage for ORBITAL source registry state, fetch runs, normalized items,
`orbital_events` or scoped clusters, source health, ranking explanations, safety and sensitivity
flags, local/global impact tags, retention purge evidence, and source verification metadata. Use
JSON-heavy columns and indexes for latest by scope, event ranking, source health, source family,
event type, source object or mission id, and `expires_at` purge. Do not store full article bodies,
bulk satellite catalogs, or long-term social archives by default.

Current state: the shared scoped registry, fetch, item, health, cluster, and retention tables
persist ORBITAL state with source verification, ranking and expiry evidence in bounded JSON fields.
ORBITAL item facets index only explicit source family, event type, object and mission IDs, true
safety/sensitivity flags, and named impact tags. Indexed queries exclude inactive and expired
items. Reinitialization backfills missing facets, refresh replaces old facet values, and expiry
purge cascades to facets. No full article body or bulk catalog storage was added. Dedicated
ORBITAL parsers and event correlation follow in separate rows.

### ORBITAL Fixture Pack

Status: partially implemented.

Create local-only fixtures for SWPC alerts JSON, SWPC NOAA scales JSON, SWPC Kp JSON, SWPC aurora
JSON, JPL CNEOS close approach JSON, JPL CNEOS fireball JSON, JPL Sentry or Scout JSON, MPC MPEC
metadata, Launch Library upcoming launch JSON, Spaceflight News API JSON, NASA RSS, ESA RSS,
CelesTrak tiny allowlisted GP JSON, restricted Space-Track source-health state, reentry candidates
after verification, source-health states, disabled sources, stale sources, auth-required sources,
policy-blocked sources, and parser failures. Fixture ingest must not perform network calls and
must be safe for pytest.

Current state: small official-shape SWPC alerts, NOAA scales, planetary and Boulder K-index, and
OVATION aurora and JPL CAD JSON fixtures cover warning, cancelled watch, incomplete row, current
and forecast scale, zero state, K-index thresholds, a tiny aurora grid, close-approach thresholds,
and fireball energy/location variants, plus NASA and ESA RSS relevance cases. Their parsers and offline scans are
tested. Remaining ORBITAL products and
source-health variants are pending in this pack.

### SWPC Alerts JSON Parser

Status: completed 2026-10-15 for fixture-first ingest.

Build a fixture-first parser for SWPC alerts, watches, and warnings JSON. Preserve product id,
message type, NOAA scale when provided, issue time, valid period, severity terms, affected systems
when source-provided, source URL, and parser/source-health evidence. Handle missing fields and
schema changes fail-soft.

Current state: verified the official JSON array shape and added a dedicated ORBITAL parser for
bounded product identity, issue and validity times, message kind, NOAA scale, source-provided
potential-impact lines, cancellation state, official URL, and indexed event identity. Incomplete
rows skip; malformed top-level JSON fails clearly. The registry names the parser but remains
disabled, and no live HTTP allowlist entry was added. See
`docs/project/ORBITAL_SWPC_ALERTS_SOURCE_VERIFICATION.md`.

### SWPC NOAA Scales Parser

Status: completed 2026-10-15 for fixture-first ingest.

Build a fixture-first parser for SWPC NOAA G/R/S scale JSON. Preserve geomagnetic, radio blackout,
and radiation storm scale state, observed or update time, source URL, and ranking features used for
official severity. Do not invent impacts beyond source-provided scale meanings.

Current state: verified the official period-keyed JSON shape and added a dedicated ORBITAL parser
for nonzero G/R/S scale entries, source text, probabilities, timestamp, current/forecast distinction,
official URL, indexed event identity, and ranking input evidence. Missing or malformed rows fail
soft; a missing current period fails clearly. The registry names the parser but remains disabled;
no live HTTP allowlist entry was added. See
`docs/project/ORBITAL_SWPC_SCALES_SOURCE_VERIFICATION.md`.

### SWPC Kp And Aurora Fixture Parsers

Status: completed 2026-10-15 for fixture-first products and configured location summaries.

Build fixture-first parsers for SWPC planetary K-index, Boulder K-index, and OVATION aurora JSON
candidates. Preserve timestamp, Kp or aurora metadata, product source URL, local/regional aurora
interest evidence, and stale-source behavior. Keep local aurora tags configurable and disabled
until ORBITAL is explicitly enabled.

Current state: dedicated parsers keep the latest qualifying planetary Kp, minute-level estimated
Kp, or Boulder K-index measurement with exact official provenance and a configurable threshold.
The designed summary URL returned 404 and was replaced in the registry with NOAA's verified
planetary product. The OVATION parser reads a bounded grid, retains only modeled peak and sample
count near explicitly configured LOCAL/REGIONAL coordinates, and never stores the grid or claims
visibility. Config validates coordinates, radius, and minimum value; no locations are set by
default. Source health reports staleness, and offline fixture scans make no HTTP request. See
`docs/project/ORBITAL_SWPC_KP_AURORA_SOURCE_VERIFICATION.md`.

### JPL CNEOS Close Approach Parser

Status: completed 2026-10-15 for fixture-first ingest.

Build a fixture-first JPL SSD/CNEOS close approach parser. Preserve object designation, approach
time, miss distance, lunar distance, relative velocity, estimated diameter when available, source
URL, official risk framing, and ranking evidence. Suppress distant low-risk objects unless
configured.

Current state: the NASA/JPL CAD v1.5 field-array parser preserves designation, TDB approach
time, nominal and uncertainty-bound distance, lunar-distance conversion, velocity, optional
diameter/H, official URL, and explicit no-impact-inference framing. A configurable five-lunar-
distance and 0.05 km diameter filter suppresses distant small/unknown objects. Version and row
shape are checked, and a local-only scan tests persistence and indexed object identity. The
candidate remains disabled and has no live HTTP allowlist entry. See
`docs/project/ORBITAL_JPL_CAD_SOURCE_VERIFICATION.md`.

### JPL CNEOS Fireball Parser

Status: completed 2026-10-15 for fixture-first ingest.

Build a fixture-first JPL/CNEOS fireball parser. Preserve event time, source-provided location,
altitude, velocity, energy, source URL, and official fireball evidence. Apply configured energy and
freshness thresholds so the dashboard does not become a firehose.

Current state: the NASA/JPL Fireball API v1.2 parser preserves UTC peak-brightness time,
source-provided location and altitude, radiated and estimated impact energies in their source
units, optional entry velocity components and derived magnitude, official URL, and explicit
no-ground-damage-inference wording. Configurable energy and age filters suppress routine or
stale rows. Version, bounded row shape, local-only scan, and indexed event identity are tested.
The candidate remains disabled with no live HTTP allowlist entry. See
`docs/project/ORBITAL_JPL_FIREBALL_SOURCE_VERIFICATION.md`.

### JPL Sentry And Scout Source Verification

Status: not implemented.

Verify JPL Sentry and Scout endpoint ownership, query shape, rate limits, policy notes, parser
fields, source-health behavior, and risk-language rules before implementation. Store official
source framing only and avoid panic language or inferred impact claims.

### MPC MPEC And NEOCP Source Verification

Status: not implemented.

Verify Minor Planet Center MPEC, recent MPEC, NEOCP, observations, orbits, designation, and
obscode source behavior before implementation. Define strict filters, retention, source-health
states, and metadata-only storage. Avoid high-volume observation ingestion unless explicitly
configured and justified.

### Launch Library 2 Fixture Parser

Status: not implemented.

Build a fixture-first Launch Library 2 parser for launch and event metadata. Preserve launch id,
event id, provider, vehicle, payload, pad, launch window, status, update time, webcast URL if
source-provided, source URL, and status-change evidence. Keep live Launch Library access disabled
until throttling, source-health, and no-page-load-fetch tests exist.

### Spaceflight News API Fixture Parser

Status: not implemented.

Build a fixture-first Spaceflight News API parser for headline metadata and launch/event
correlation. Preserve article id, title, URL, publisher, publication time, summary bounded by local
limits, and source family. Do not let Spaceflight News API outrank official agency, SWPC, JPL, MPC,
or launch-provider sources without convergence.

### NASA RSS Parser

Status: partially implemented.

Build a fixture-first RSS/Atom parser for verified NASA, JPL, NASA blog, Kennedy, Space Station,
Artemis, mission, and science feeds. Store headline metadata only, bound descriptions, preserve
agency/source family, mission labels where available, and filter routine feature stories unless
they have recent-signal value.

Current state: NASA's RSS directory was verified as an HTML index and the registry candidate now
points to its exact news releases feed. Five additional Station, Artemis, and Kennedy mission/blog
RSS endpoints were observed and added as disabled exact-feed candidates. The source-specific parser
validates each NASA channel and official article path, keeps canonical URL, GUID, time, categories
and bounded description, and requires an ORBITAL title action. Unrelated Earth science, education
and routine stories are suppressed in offline tests. No live HTTP allowlist entry was added.
JPL's linked feed returned HTTP 403 here and the NASA Science candidate did not return parseable
RSS; those paths remain open. See `docs/project/ORBITAL_NASA_RSS_SOURCE_VERIFICATION.md`.

### ESA RSS Parser

Status: completed 2026-10-15 for fixture-first ORBITAL ingest.

Build a fixture-first RSS/Atom parser for verified ESA feeds. Preserve headline metadata, source
URL, publication time, bounded description, source family, mission/safety/debris labels where
available, and source-health evidence. Keep ESA reentry and debris pages separate until endpoint
and policy review are complete.

Current state: ESA's RSS directory and exact Top News and Human Spaceflight feeds were verified.
The disabled registry candidates now point to those feeds. The dedicated parser validates each
channel and official article URL, preserves headline, opaque GUID, timezone-aware publication
time, bounded description, source URL and explicit mission label, and filters routine media and
unrelated stories. Reentry/debris headlines remain outside this parser pending their separate
review; no safety impact is inferred from generic feed metadata. Offline scans and indexed
mission/source tests pass. Both exact feeds now have disabled-by-default live HTTP allowlist
entries with seven-day freshness, source and parent gates, and mocked scan coverage. See
`docs/project/ORBITAL_ESA_RSS_SOURCE_VERIFICATION.md`.

### Official Launch Provider Source Verification

Status: completed 2026-10-15 for first-pass source classification.

Verify SpaceX, Blue Origin, Rocket Lab, ULA, Arianespace, ISRO, JAXA, CSA, ESA, CNSA, and other
official launch provider or agency pages before implementation. Confirm feed availability,
per-source selectors if no feed exists, robots/policy notes, refresh limits, parser stability,
and whether homepage extraction is allowed. Keep provider pages disabled by default.

Current state: `docs/project/ORBITAL_LAUNCH_PROVIDER_SOURCE_VERIFICATION.md` classifies ten
provider/agency groups, corrects stale Rocket Lab, ULA, Arianespace, and ISRO registry URLs, and
keeps unparsed pages manual/source-health-only. No HTML selectors, robots/terms clearance, or
polling cadence was verified, so no homepage extraction or live allowlist was added. ESA's
separately verified RSS remains the only listed agency opt-in in this group.

### ISS And Crewed-Spaceflight Source Verification

Status: completed 2026-10-15 for first-pass source classification.

Verify NASA Space Station blog, NASA humans-in-space pages, Commercial Crew, ESA ISS, JAXA ISS,
CSA ISS, Spot the Station, and related crewed-spaceflight sources before implementation. Define
which signals are recent operational events, mission context, local sky-interest events, or
source-health-only references.

Current state: `docs/project/ORBITAL_CREWED_SOURCE_VERIFICATION.md` classifies NASA Station/blog
and ESA Human Spaceflight RSS as verified opt-in sources, NASA Commercial Crew RSS as a parser
candidate, NASA Humans in Space as context, JAXA and CSA pages as source-health references, and
Spot the Station as local sky-interest reference rather than a tracking feed. It defines
operational events, context, source independence, and date/schedule evidence. The registry points
to the current JAXA page, exact NASA Commercial Crew feed candidate, and honest non-feed states.

### CelesTrak Public GP Safety Review And Tiny Allowlisted Fixture Parser

Status: not implemented.

Review CelesTrak GP, SATCAT, supplemental, and SOCRATES source policies, data volume, sensitivity,
refresh intervals, object-group filters, and safe display rules before any implementation. If
allowed, build only a tiny allowlisted fixture parser first. Do not create tactical tracking,
object-by-object surveillance, or broad catalog archive behavior.

### Space-Track Auth-Required Policy Design

Status: not implemented.

Design Space-Track handling as auth-required and disabled by default. Require credentials outside
the repo, explicit user configuration, terms review, source-health `auth_required` state when
credentials are absent, and no attempts to bypass login, account controls, or API restrictions.

### ESA Reentry Source Verification

Status: completed 2026-10-15 for first-pass access classification.

Verify ESA reentry prediction source ownership, access method, policy notes, parser shape,
machine-readable endpoint availability, rate limits, uncertainty fields, and source-health states.
Do not scrape dashboards or complex pages until a safe machine-readable path is verified.

Current state: ESA's own front-end guide and press page confirm actual predictions require an
account; public pages are background. No permitted machine-readable prediction endpoint or API
contract was established. `esa_reentry` is now `restricted_auth_required`, disabled, and shown as
`auth_required` without access. `docs/project/ORBITAL_ESA_REENTRY_SOURCE_VERIFICATION.md` records
the endpoint, uncertainty, rate, retention, and safety gaps for any later adapter.

### NASA Orbital Debris Source Verification

Status: completed 2026-10-15 for first-pass source classification.

Verify NASA Orbital Debris Program, Quarterly News, reentry, and related debris/sustainability
sources before implementation. Define whether each source is source-health-only, RSS/metadata,
manual-review-only, or a parser candidate. Store metadata only and avoid debris fear-dashboard
behavior.

Current state: NASA's Orbital Debris Program Office, Quarterly News PDF index, and reentry
methods page are verified as official reference/source-health entries in
`docs/project/ORBITAL_NASA_DEBRIS_SOURCE_VERIFICATION.md`. No current event feed or reentry
prediction API was established. The registry now labels the quarterly page as a manual PDF index
instead of an RSS parser candidate; all three stay disabled and out of the live HTTP allowlist.

### ORBITAL Deterministic Event Correlation

Status: partially implemented.

Implement deterministic ORBITAL event matching by source family, event type, time window, product
id, NOAA scale, Kp window, mission name, launch id, launch vehicle, payload, provider, NEO
designation, CNEOS event id, MPC designation, reentry object, safe satellite identifiers, fireball
time/location, normalized title tokens, and impact tags. Do not use LLMs, embeddings, or hidden
cloud calls.

Current state: `orbital_events.py` builds deterministic, complete-link event groups from stored
ORBITAL identity, type, source family, time, title tokens, and available structured context. The
scanner persists match basis, member ids, independent families, and confidence in item and cluster
evidence. Shared official identity can deduplicate same-family records without claiming independent
corroboration; unrelated event types and observations outside 96 hours stay separate. Fixture
integration and matcher tests pass. Remaining work: populate mission, launch, Kp, reentry, safe
satellite, and impact identities in verified future adapters; test their real parsed records; and
refine cross-product space-weather correlation without joining separate forecast periods.

### ORBITAL Deterministic Ranking

Status: completed 2026-10-15 for first-pass algorithm.

Implement explainable ORBITAL ranking with recency, official severity, source diversity, temporal
proximity, operational impact, public impact, active alert or launch windows, source priority,
cluster size, local/global impact tags, duplicate-family penalty, stale-source penalty,
low-confidence penalty, low-public-value penalty, out-of-scope penalty, sensitivity penalty, and
rumor penalty. Store score features and ranking reasons in JSON evidence.

Current state: ORBITAL clusters use a bounded stored-metadata score with recency, source-backed
SWPC severity, independent family diversity, temporal proximity, operational and public impact,
active alert/launch-window signals, source priority, cluster size, explicit local/global tags,
and the specified duplicate, stale, confidence, low-value, out-of-scope, sensitivity, and rumor
penalties. Factors and reasons are persisted in linked item and cluster evidence. JPL close
approach distance alone does not create a threat score. Hard tactical/restricted flags suppress
clusters and hide items from scope and direct-detail views. Tests cover each major score class,
duplicate handling, non-inferred NEO risk, and stored sensitive-item rendering.

### ORBITAL Safety And Sensitivity Rules

Status: completed 2026-10-15 for first-pass deterministic rules.

Add deterministic rules that block or de-emphasize tactical satellite tracking, restricted/auth
data, classified-activity inference, broad satellite catalog firehoses, Space-Track use without
credentials and terms review, social-only claims, launch rumors, NEO panic language, reentry panic
language, and debris fear-dashboard behavior. Prefer official public metadata and short retention.

Current state: source-policy gates block restricted and sensitive catalog candidates before ingest.
`orbital_safety.py` classifies bounded title/description and source metadata for tactical tracking,
restricted data, classified inference, private operator monitoring, social-only claims, launch
rumors, NEO panic wording, reentry panic wording, and debris fear framing. Hard-sensitive text is
redacted before storage and hidden from scope, cluster, and direct-detail output; soft flags and
rumor carry ranking penalties. ORBITAL retention is capped at seven days and redacted records at
one day. Tests cover ordinary official alerts and close approaches remaining unflagged as well as
blocked and redacted cases. The wording rules are intentionally narrow and remain reviewable.

### ORBITAL Local And Global Impact Tag Rules

Status: completed 2026-10-15 for first-pass source-backed rules.

Define ORBITAL impact tags for `GLOBAL_IMPACT`, `NATIONAL_IMPACT`, `REGIONAL_IMPACT`,
`LOCAL_IMPACT`, `SKY`, `RADIO`, `GPS`, `AVIATION`, `SATELLITE`, `POWER`, `AURORA`, `CREWED`,
`NEO`, `REENTRY`, and `DEBRIS`. Keep canonical scope ORBITAL while allowing evidence-backed local,
regional, national, and global impact tags.

Current state: `orbital_impact.py` defines the canonical tag set and derives tags only from parsed
official impact systems, configured OVATION location boxes, source-reported geography, and verified
event records. A Kp value or HF impact alone cannot imply visibility or geographic reach. The
scanner stores each tag's field-level basis in item evidence, adds the tags to cards, and keeps the
item in ORBITAL. Ranking reads the canonical geographic tags. Tests cover SWPC alert and aurora
facts, NEO identity, unsupported geography, and persisted scan output.

### ORBITAL UI Disabled States

Status: completed 2026-10-15 for first-pass state presentation.

Replace ORBITAL placeholders only after storage/config support exists. Show honest states for
disabled, not configured, configured but disabled, never scanned, stale, policy blocked, parser
failed, auth required, rate limited, restricted source disabled, social disabled, homepage
extraction disabled, manual-review-only, token/account source not configured, and source-health
only. Do not show fake headlines.

Current state: the shared ORBITAL and SYSTEM pages read SQLite/config, show honest empty and
source-health states, and render ORBITAL item and cluster evidence. ORBITAL counts distinguish
restricted disabled, sensitivity blocked, terms review, scope filter needed, and source-health
only, alongside auth, parser, social, homepage, rate, robots, and ordinary failure states. Tests
exercise disabled, not configured, configured disabled, stale, parser failed, rate limited,
failing, restricted, sensitivity, manual review, auth, policy, homepage, social, and health-only
views without GET-time fetch or fixture access. No synthetic headline is rendered.

### ORBITAL Source Health States

Status: completed 2026-10-15 for first-pass state taxonomy.

Implement source health states for ORBITAL: `disabled`, `not_configured`,
`configured_never_run`, `healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`,
`robots_blocked`, `auth_required`, `rate_limited`, `unsupported`, `manual_review_only`,
`restricted_source_disabled`, `needs_terms_review`, `needs_scope_filter`, and
`sensitivity_blocked`. Surface these states in SYSTEM later and summarize them on ORBITAL.

Current state: ORBITAL policy and storage now expose distinct restricted-source-disabled,
needs-terms-review, needs-scope-filter, sensitivity-blocked, and source-health-only states in
addition to the shared health taxonomy. Restricted Space-Track and broad tactical catalogs remain
gated even with broad allowance flags. ORBITAL counters and SYSTEM readiness surface the states;
tests cover policy precedence, persisted stale/parser/rate/failure states, and blocked access.

### ORBITAL Evidence Drawer Contract

Status: completed 2026-10-15 for first-pass evidence contract.

Define and test evidence payloads for ORBITAL items and events. Include source ids, source names,
families, classes, URLs, official flags, published times, first/last seen, fetch run ids, parser
names, source health, ranking features, operational impact basis, public impact basis, source
diversity basis, local/global impact basis, sensitivity decision, retention expiration, matching
tokens, event type, event confidence, policy notes, low-public-value penalty, sensitivity penalty,
rumor penalty, out-of-scope penalty, mission/object labels, and safe satellite/reentry metadata.

Current state: `orbital_evidence.py` builds a bounded persisted item contract with source
identity/name/family/class/URL/official status, timestamps, fetch run, parser and source health,
ranking features/reasons, source-backed operational/public impact basis, family-diversity basis,
canonical impact tags and field/geography basis, sensitivity decision, retention, match tokens and
basis, event type/confidence, policy notes, penalties, mission/object labels, and optional safe
satellite/reentry identifiers. The ORBITAL item and cluster drawers render the core fields. A
fixture scan tests the direct item-detail payload and HTML without GET-time fetching.

### ORBITAL Official-Source Live Ingest Phase, Disabled By Default

Status: implemented for first pass.

After fixtures, correlation, ranking, retention, source health, and tests exist, add opt-in live
ingest for one safe official ORBITAL source at a time. First candidates are SWPC alerts JSON, SWPC
NOAA scales JSON, SWPC Kp JSON, SWPC aurora JSON, JPL CNEOS close approach API, JPL CNEOS fireball
API, NASA RSS, ESA RSS, and JPL RSS after verification. Require explicit commands and no page-load
fetches.

Current state: NOAA SWPC alerts, NOAA scales, planetary Kp summary/one-minute, Boulder K-index
one-minute, OVATION aurora JSON, six exact NASA RSS feeds, and two exact ESA RSS feeds are
allowlisted ORBITAL endpoints.
Their headers were rechecked on 2026-10-15; explicit parent/news/HTTP/source enablement and
`verification_status: verified` are required. Live alerts outside 72 hours are discarded; scales
have six-hour/96-hour current/forecast windows; K-index keeps latest measurements within six
hours/one hour and requires K >= 5. OVATION requires configured LOCAL/REGIONAL coordinate windows
with modeled intensity >= 50, stores no grid, makes no visibility claim, and uses a two-hour
observation freshness window. NASA RSS keeps only seven-day-old or newer source-dated orbital
stories; ESA RSS uses the same seven-day freshness window. NASA/JPL and ESA channel variants
do not create false independent corroboration. Alert
validity and cancellation affect active-alert scoring. Mocked-transport tests cover source gates,
200/304 handling, provenance, freshness, and offline GET. An isolated explicit NOAA SWPC alerts
scan on 2026-10-15 returned HTTP 200 and stored three ORBITAL items in temporary state.
Defaults remain disabled. Remaining candidates need endpoint, parser, response size, freshness,
and policy review; JPL RSS remains unverified here.

### ORBITAL Launch/Event API Ingest Phase, Disabled By Default

Status: not implemented.

Add opt-in Launch Library 2 and Spaceflight News API ingest only after fixture parsers, throttling,
source-health states, policy review, and no-page-load-fetch tests exist. Store metadata only,
handle launch status changes as updates, and prevent launch/event APIs from running unless
explicitly enabled in local config.

### ORBITAL Space News RSS Ingest Phase, Disabled By Default

Status: not implemented.

Add opt-in RSS/Atom ingest for verified space news, public media, specialist journalism, and
nonprofit feeds only after source verification. Store headline metadata only, bound descriptions,
avoid article bodies, avoid paywall bypass, and prevent duplicate syndicated articles from
inflating independent convergence.

### ORBITAL Restricted/Auth Source Policy Review, Disabled By Default

Status: not implemented.

Review Space-Track, restricted satellite sources, API-key sources, account-required services,
platform APIs, heavy open-data archives, and any source with terms or sensitivity risk before
implementation. Keep restricted/auth sources disabled by default, require explicit local
configuration, and expose clear source-health states without attempting live access.

### ORBITAL Social Source Policy Review, Disabled By Default

Status: not implemented.

Review Bluesky AT Protocol, Reddit official API or permitted feed access, X official API rules,
and official social-account use before implementing any ORBITAL social adapter. Keep social
disabled by default, require explicit local configuration, use short retention, never scrape HTML
to bypass platform restrictions, and never treat social as primary evidence.

### Documentation For ORBITAL Source Verification

Status: completed 2026-10-15 for first-pass verification workflow.

Document the later ORBITAL source verification workflow: confirm endpoint ownership, access method,
source terms, robots/policy notes, parser shape, auth/key requirements, rate limits, retention
sensitivity, privacy risk, verification status, source family, source class, orbital domain
filters, source-health behavior, tactical/sensitivity review, and whether the source is official,
provider, media, nonprofit, platform, restricted, open-data, or manual review only.

Current state: `docs/project/ORBITAL_SOURCE_VERIFICATION_WORKFLOW.md` captures the shared
verification checklist, required registry fields, source-health behavior, a per-endpoint signoff
record, and walkthroughs for SWPC, ESA, NASA/JPL RSS, and JPL CNEOS APIs. It distinguishes
reference-only, fixture-only, and live-opt-in decisions and lists the exact gates for promotion.
Source-specific evidence lives in the linked verification documents.

### Tests For No Page-Load External Fetches

Status: completed 2026-10-15 for first-pass ORBITAL/SYSTEM routes.

Add tests proving GET routes and page renders read SQLite/config only and never call ORBITAL
network fetchers. Include disabled/not configured/stale/failing/auth-required/policy-blocked,
restricted-source-disabled, social-disabled, homepage-extraction-disabled, source-health-only, and
parser-failed state tests for ORBITAL and SYSTEM source health.

Current state: `tests/test_orbital_safety_gates.py` and
`tests/test_orbital_source_health_states.py` exercise ORBITAL and SYSTEM GET/API routes with
fetch and fixture access forbidden. The tests cover disabled, not configured, configured disabled,
stale, failing, parser failed, rate limited, auth required, policy/restricted/sensitivity blocked,
social and homepage disabled, manual review, and source-health-only presentations.

### Tests For No Restricted Source Running Without Explicit Config

Status: completed 2026-10-15 for first-pass safety gate.

Add tests proving Space-Track, CelesTrak restricted/sensitive candidates, conjunction-awareness
sources, restricted satellite sources, account-required sources, and policy-sensitive reentry or
debris candidates cannot run unless explicitly enabled in local config and policy-approved. Tests
should assert no network calls and clear disabled or auth-required source-health states.

Current state: `tests/test_orbital_safety_gates.py` verifies Space-Track, CelesTrak, NASA
conjunction/debris, ESA reentry, and ArcGIS reentry candidates stop before fixture or network
access and expose their auth-required, policy-blocked, or unsupported states.

### Tests For No API-Key Source Running Without Config

Status: completed 2026-10-15 for first-pass safety gate.

Add tests proving NASA APIs, platform APIs, Space-Track, any future API-key source, and any
account/token source cannot run without explicit local configuration. Tests should assert clear
`auth_required`, `not_configured`, or policy-disabled source-health state and no network calls.

Current state: NASA Open APIs, Space-Track, and arbitrary future API-key/token sources have
explicit missing-credential tests. The NASA registry candidate now declares an empty local key
slot and reports `auth_required`; the tests assert no fixture or network access.

### Tests For No Tactical Satellite Tracking Output

Status: completed 2026-10-15 for first-pass rendering gate.

Add tests proving ORBITAL does not render tactical satellite tracking output, broad catalog
firehose rows, sensitive military satellite inference, private operator monitoring, or
object-by-object surveillance. The UI should show aggregate, source-backed event metadata and
honest disabled/sensitivity-blocked states instead.

Current state: the CelesTrak elements, SATCAT, and SOCRATES candidates remain manual-review-only
even when topic and restricted-source flags are set. A stored tactical record is also hidden from
ORBITAL scope cards, clusters, and direct item detail. Regression tests forbid network access and
check both candidate and stored-item paths.

## Solar System and Beyond Recent Signal Layer

Architecture reference:

- `docs/project/SYSTEM_SOLAR_SYSTEM_BEYOND_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### Resolve SYSTEM Naming Collision

Status: completed 2026-10-15 for route and storage naming.

Decide whether app-health SYSTEM remains the source-health/app-health scope and Solar System and
Beyond becomes COSMIC, SOLAR, DEEP, DEEP SPACE, SKY, BEYOND, or another label. Do not implement tab
or route changes until this decision is explicit. If SYSTEM is repurposed, design app-health
migration to CONSOLE or HEALTH first.

Decision: preserve `SYSTEM` for app/source health and expose the science layer as `COSMIC`.
`SYSTEM_SOLAR` remains the internal SQLite/config scope key; `/COSMIC` and
`/api/news/scopes/COSMIC` map to it. The two routes render separate panels, with no page-load
fetches. Offline route and disabled-parent tests pass.

### Decide Final UI Label For Solar System And Beyond

Status: completed 2026-10-15 with COSMIC as the first-pass UI label.

Choose the final user-facing label and route plan for the Solar System and Beyond layer. Preserve
the existing `SYSTEM` app-health meaning unless the user explicitly requests a migration. Update
docs, tests, routes, templates, and source-health references only in the future implementation pass.

The assistant proposed COSMIC in a preference request and proceeded with that working choice
after no reply. Navigation displays `COSMIC`; the internal scope stays `SYSTEM_SOLAR` to preserve
the current registry and event contracts. A later user preference can rename the tab and route
without reusing app-health `SYSTEM` or migrating stored science rows.

### Disabled-By-Default Solar System And Beyond Config

Status: completed 2026-10-15 for the scope config foundation.

Add a `solar_system_beyond:` or chosen-scope config tree that defaults to disabled. Include flags
for planetary science, interplanetary missions, exoplanets, telescope science, major space-agency
science, transients, GCN, TNS, gravitational waves, neutrino alerts, catalog archives, literature
metadata, social sources, and large archive queries. Reject social, auth-required, heavy archive,
literature, and homepage extraction sources unless explicit local flags are set.

Current state: `solar_system_beyond` now has a disabled default tree and example config with
science topic and attention flags. Normalization validates booleans and attention enums; TNS,
catalog/large archive, literature, and social categories require their explicit corresponding
local allow flags. `news.scopes.SYSTEM_SOLAR` and `/COSMIC` now exist but remain disabled by
default; enabling this tree alone does not cause a fetch or display invented items.

### Solar System And Beyond Source Registry Design Implementation

Status: completed 2026-10-15 for the disabled first-pass registry.

Implement the source registry from the design document with explicit `source_key`, `source_name`,
`source_family`, `source_class`, `scope`, `raw_url`, access kind, adapter type, refresh interval,
priority, official status, privacy risk, policy risk, parser risk, retention sensitivity,
verification status, source-health behavior, and future phase fields. Validate enum values and keep
every source disabled until explicitly configured.

Current state: `console1701/news/science_registry.json` preserves all 170 source candidates from
the design table plus four later RSS candidates and narrow Exoplanet Archive, MAST, and PDS
candidates,
under the internal `SYSTEM_SOLAR` working name. `science_registry.py` validates
unique keys, required fields, URL shape, enums, intervals, and priorities, and derives a disabled
source-health behavior for each candidate. A COSMIC route and internal news scope now exist. All
registry candidates remain disabled by default; the exact ESA Space Science RSS feed has a
separate opt-in live adapter. Focused tests check inventory isolation and invalid entries.

### Solar System And Beyond SQLite Schema Or Extension

Status: completed 2026-10-15 for the first-pass storage contract.

Add or extend SQLite storage for source registry state, fetch runs, normalized items,
`solar_system_beyond_events` or scoped clusters, source health, ranking explanations, source naming
collision state, hype/suppression flags, archive query bounds, auth-required evidence, retention
purge evidence, and source verification metadata. Use JSON-heavy columns and indexes for latest by
scope, event ranking, source health, source family, event type, object/mission/transient ids, and
`expires_at` purge. Do not store full article bodies, papers, sky maps, science products, or bulk
catalog rows by default.

Current state: the existing scope-aware `news_source_registry`, `news_sources`,
`news_fetch_runs`, `news_items`, and `news_source_health` tables cover science source metadata,
fetch and health history, bounded item metadata, and JSON evidence. `science_events` adds an
indexed scoped event store for identity, ranking, query bounds, policy flags, label-decision
state, and expiry. Disabled science registry rows sync on `news-scan` without creating fetchable
sources. Retention purges expired science events and records a science event count; fixture tests
verify registry sync, no configured science fetch sources, migration idempotence, and purge.

### Solar System And Beyond Fixture Pack

Status: partially implemented.

Create local-only fixtures for NASA/JPL RSS, ESA RSS, Hubble/JWST RSS, NASA Exoplanet Archive tiny
metadata, MAST tiny metadata, PDS tiny metadata, GCN notice, GCN circular, ATel RSS, TNS
auth-required source health, GraceDB/LIGO public alert policy state, science news RSS, malformed
feeds, oversized payloads, source-health states, disabled sources, stale sources, auth-required
sources, heavy-archive-blocked sources, and hype-blocked items. Fixture ingest must not perform
network calls.

Current state: `tests/fixtures/science/nasa_jpl_science.rss` covers NASA-hosted JPL astrophysics,
exoplanet, Earth-only, launch, and nonofficial-link cases. The ESA fixture covers a science
article, launch, image-only link, and nonofficial host. ESA telescope fixtures cover science
releases, photo releases, and nonofficial links. The tiny Exoplanet Archive JSON fixture covers
two bounded PS parameter updates. The MAST fixture covers two JWST observation metadata rows
with complete paging. The PDS fixture covers one collection metadata record. The GCN fixture
covers an official-schema notice, coordinates, test gates, update, and retraction. The other fixture
families and source-health/policy states are pending.

The first offline `news-scan` integration now ingests configured NASA JPL and ESA RSS fixtures,
persists COSMIC items and events, and rejects nonexact source identities. A scan and page-render
test assert no network call, while a repeat scan confirms event rebuild idempotence. The remaining
fixture families and blocked-state matrix still need end-to-end coverage.

A parameterized scan regression also exercises the Hubble, Webb, Exoplanet Archive, MAST, PDS,
and GCN fixture adapters through the real scanner, with local-only input, stored event evidence,
and no product-download flags. `docs/project/COSMIC_FIXTURE_INGEST.md` gives the exact local
configuration shape. ATel and the broader source-health/policy matrix remain pending.

### NASA/JPL RSS Parser

Status: completed 2026-10-15 for fixture-first NASA-hosted JPL science RSS.

Build a fixture-first RSS/Atom parser for verified NASA and JPL science feeds. Preserve title, URL,
published time, bounded description, categories, source family, mission/object tokens where
available, and official science evidence. Store headline metadata only and do not fetch article
bodies.

Current state: `science_rss.py` parses only the exact NASA-hosted JPL channel and URL under the
internal science scope. It requires a source-provided science category and nonoperational title,
rejects unrelated hosts and malformed/oversized XML, and keeps bounded headline metadata,
publication time, categories, official provenance, and no-download evidence. Synthetic fixtures
cover scope filtering and safety. The registry candidate stays disabled for live fetch; a COSMIC
route and explicit local fixture ingest exist.

### ESA RSS Parser

Status: completed 2026-10-15 for fixture-first ESA Space Science RSS.

Build a fixture-first ESA RSS parser after feed shape is verified. Preserve title, URL, published
time, source family, bounded description, science/mission labels where available, and official
agency evidence. Keep it disabled by default and metadata-only.

Current state: `science_rss.py` parses the exact official ESA Space Science feed and channel,
accepts only ESA Space Science article paths, rejects launch and image-only links, preserves the
source path's mission label when present, and stores bounded headline metadata and no-download
evidence. Focused fixtures cover endpoint/channel and payload gates. The registry source remains
disabled by default. Its separately gated live RSS path now uses the same bounded parser and
COSMIC route.

### Hubble/JWST RSS Parser

Status: completed 2026-10-15 for fixture-first ESA Hubble and Webb science releases.

Build a fixture-first parser for verified Hubble and JWST feeds. Preserve telescope, instrument
when source-provided, release id or URL, published time, bounded description, source family, and
telescope-science ranking evidence. Do not download images or data products.

Current state: ESA Hubble and Webb publisher pages link RSS feeds hosted by FeedBurner; their
parseable channels and official story hosts are recorded in `science_rss.py`. The exact-source
fixture parser accepts `Science Release` entries with validated Hubble/Webb release IDs,
preserves telescope and publication metadata, leaves instrument unset when the feed omits it,
and never downloads images or products. Photo releases and unrelated hosts are excluded.
Both registry candidates remain policy blocked for live access because FeedBurner is a third-party
feed host; the advertised Webb direct URL returned 404, and no redirect bypass is used.

### NASA Exoplanet Archive Tiny Metadata Parser

Status: completed 2026-10-15 for fixture-first tiny PS table metadata.

Build a fixture-first parser for tiny allowlisted NASA Exoplanet Archive metadata responses. Preserve
planet name, host star, confirmed/candidate status when source-provided, discovery method, update
time, source URL or query evidence, row cap, and exoplanet ranking features. Reject broad catalog
downloads.

Current state: `science_exoplanets.py` requires the exact NASA Exoplanet Archive TAP endpoint,
`ps` table, seven allowlisted columns, default parameter rows, a positive cap of at most ten,
and a date window of at most seven days. A two-row public probe returned JSON with planet/host,
method, year, `rowupdate`, and `soltype`; the parser keeps only those fields, records exact
query bounds, and labels the date as a parameter update rather than a new discovery. Oversized,
malformed, over-cap, extra-column, and out-of-window fixture data fail closed. The exact tiny
`ps` query now has a separate opt-in live signoff; broad archive queries remain blocked.

### MAST Tiny Metadata Parser

Status: completed 2026-10-15 for fixture-first CAOM observation metadata.

Build a fixture-first MAST metadata parser for narrow configured queries only. Preserve mission,
collection, dataset id, object/target labels where provided, query bounds, row cap, source URL, and
no-science-product-download evidence. Keep live MAST disabled by default.

Current state: `science_mast.py` requires exact `Mast.Caom.Filtered` JSON, six selected metadata
columns, a named JWST/HST target, a seven-day MJD observation window, a positive cap of at most
ten, a 15-second timeout ceiling, and a complete first page. A bounded JWST/TRAPPIST-1 query
returned three rows in a one-day window; the two-row fixture exercises field and paging shape.
The parser preserves mission, observation/dataset IDs, target, instrument, query bounds, and
observation-time semantics. It rejects extra product columns, incomplete paging, broad queries,
and out-of-window rows. No product endpoint is called; the registry candidate stays disabled.

### PDS Metadata-Only Parser

Status: completed 2026-10-15 for fixture-first single-collection metadata.

Build a fixture-first NASA PDS metadata parser for scoped collection/release checks. Preserve
collection id, mission, target body, release time, product-count metadata only if source-provided,
source URL, query bounds, row cap, and no-data-product-download evidence.

Current state: `science_pds.py` parses one `Product_Collection` resolved by an explicitly
allowlisted PDS LID. A bounded official Search API response returned collection ID/version,
mission, target, and registry harvest time; the parser records that timestamp as registry
harvest, not science release. It stores a product count only when explicitly present, and
rejects mismatched IDs, observational products, broad IDs, oversized payloads, or long
retention/timeout contracts. It never traverses collection members or downloads label,
inventory, or science files. The registry candidate remains disabled.

### GCN Notice Fixture Parser

Status: completed 2026-10-15 for local unified-schema notice fixtures.

Build a fixture-first NASA GCN notice parser. Preserve notice type, event id, coordinates if
provided, event time, instrument, preliminary/update/retraction status, source URL, and transient
ranking evidence. Do not add Kafka or other dependencies without explicit approval.

Current state: `science_gcn.py` parses one fixture JSON object with an official GCN notice
schema URL, source-provided event/trigger ID, mission/instrument, trigger and alert times,
optional paired ICRS coordinates, and explicit initial/update/retraction status. It blocks
test/injection/planned notices, invalid coordinates and schema hosts, oversized payloads, and
non-fixture use. Sky-map fields and raw notice bodies are not retained. No Kafka, email,
live notice adapter, or event-specific permalink is claimed; the disabled registry remains
reference/source-health only.

### GCN Circular Source Verification

Status: completed 2026-10-15 for first-pass access and metadata classification.

Verify GCN Circular machine-readable access, policy terms, parser shape, rate limits, retention
needs, and source-health behavior before implementation. Store metadata only, preserve circular id,
event id, follow-up basis, source URL, and preliminary status.

Current state: `docs/project/SCIENCE_GCN_CIRCULAR_SOURCE_VERIFICATION.md` records NASA GCN
ownership, public archive and schema, circular/event IDs and time fields, inferred-event and
privacy limits, and the absence of a verified narrow public metadata API. The daily full archive
is too large for Recent Signal; Kafka/email need separate auth/policy work. No live adapter is
enabled, and the future fixture/parser must retain preliminary/follow-up/retraction semantics.

### ATel RSS Parser

Status: blocked on feed access; not implemented.

Build a fixture-first Astronomers Telegram RSS parser. Preserve ATel number, title, URL, published
time, object/transient tokens, bounded description if allowed, source family, and preliminary
astronomy communication labels. Do not store full telegram bodies unless source policy and config
explicitly allow bounded storage.

Access check 2026-10-15: the official homepage advertises
`https://www.astronomerstelegram.org/?rss` and a `?listxml` Feeds page, but both `www` and
non-`www` HTTPS RSS requests returned HTTP 200 with an HTML "We're Sorry!" page rather than
XML. The Feeds page returned the same error. This is a source-side access failure, not a valid
empty feed. Keep the adapter disabled and avoid inventing a fixture schema until the official
RSS response, fields, and policy can be verified.

### TNS Auth/Policy Design

Status: not implemented.

Review Transient Name Server access, auth/account requirements, API terms, attribution,
rate-limits, allowed fields, retention, and source-health behavior. Keep TNS disabled by default,
require credentials outside the repo, and represent missing credentials as `auth_required`.

### GraceDB/LIGO Public Alert Policy Design

Status: completed 2026-10-15 for first-pass public-alert policy.

Review GraceDB/LIGO/Virgo/KAGRA public-alert access, auth requirements, API/client needs, terms,
rate limits, public alert fields, retraction handling, and sky-map download policy. Keep it disabled
by default, preserve preliminary/update/retraction state, and do not download sky maps unless a
future explicit config allows metadata-only references.

Current state: `docs/project/SCIENCE_GRACEDB_PUBLIC_ALERT_POLICY.md` records public-only
unauthenticated REST access, bounded superevent query requirements, Kafka credential/dependency
separation, preliminary/update/retraction semantics, row/rate/source-health gates, and a strict
no-sky-map-download rule. No live adapter or Kafka dependency is enabled.

### Minor Planet Center Science-Context Source Verification

Status: completed 2026-10-15 for first-pass MPC access classification.

Verify MPC MPEC, NEOCP, observations, orbit, and designation API candidates for endpoint ownership,
usage guidance, rate limits, parser shape, field stability, and ORBITAL overlap behavior. Keep
hazard/close-approach operations canonical in ORBITAL and use this layer only for science context.

Current state: `docs/project/SCIENCE_MPC_SOURCE_VERIFICATION.md` records official MPEC, orbit,
observation/NEOCP, and list API shapes, MPC's five-requests-per-second ceiling, row-volume and
tracking risks, a narrow MPEC metadata candidate, and the ORBITAL CNEOS boundary. Production
response, terms, caching and parser gates remain before any live opt-in; no MPC adapter is enabled.

### HEASARC Metadata Source Verification

Status: completed 2026-10-15 for first-pass HEASARC access classification.

Verify HEASARC machine-readable metadata endpoints, usage policy, query shape, row caps, relevant
high-energy mission filters, source-health behavior, and retention before implementation. Keep
HEASARC disabled until narrow fixture tests exist.

Current state: `docs/project/SCIENCE_HEASARC_SOURCE_VERIFICATION.md` records official Xamin,
TAP, and cone interfaces, a two-row live Xamin/VOTable probe, required positive caps and
overflow handling, mission-specific usage conditions, bounded source-health and retention
rules, and a disabled-by-default promotion contract. No HEASARC adapter is enabled.

### SIMBAD/VizieR/Gaia Heavy-Archive Policy Design

Status: not implemented.

Design SIMBAD, VizieR, Gaia, ESASky, ESO Archive, and other TAP/ADQL catalog access as disabled by
default and heavy-archive-blocked unless explicit allowlists, row caps, timeouts, and query bounds
exist. Prefer source-health-only or narrow object lookup; do not ingest catalogs.

### ADS Literature Metadata Policy Design, Disabled And Auth-Required

Status: not implemented.

Review NASA ADS API token requirements, terms, rate limits, metadata fields, retention, and
permitted use. Keep ADS disabled by default, require credentials outside the repo, store metadata
only if explicitly enabled, and never download papers or bypass paywalls.

### Deterministic Event Correlation For Transients, Exoplanets, Missions, And Telescope Releases

Status: completed 2026-10-15 for the first-pass fixture runtime.

Implement deterministic matching by source family, time window, normalized title tokens, mission,
telescope, instrument, object name, solar-system body, exoplanet system, transient name, GCN event
id, ATel number, TNS name, GraceDB superevent id, coordinates, DOI/bibcode if enabled, archive
collection id, and dataset id. Do not use LLMs, embeddings, or hidden cloud calls.

Current state: `console1701/news/science_events.py` provides complete-link, 96-hour deterministic
grouping for stored `SYSTEM_SOLAR` metadata. It recognizes GCN, exoplanet, MAST, PDS and future
explicit identity fields; it treats recurring mission/object names as context, requires shared
title tokens and independent source families for non-ID matches, and records the match basis.
Focused tests cover retraction continuity, unrelated releases, independent corroboration,
time-window separation, event-kind separation and scope exclusion. The COSMIC fixture scan calls
this module and persists groups in `science_events`, `news_clusters`, and item evidence.

### Deterministic Ranking For Official Science And Rarity

Status: completed 2026-10-15 for the first-pass fixture runtime.

Implement explainable ranking with recency, official science provenance, scientific significance,
source diversity, mission relevance, rarity, transient status, public interest, source priority,
cluster size, local/global/orbital impact tags, duplicate-family penalty, stale-source penalty,
low-confidence penalty, low-public-value penalty, hype penalty, out-of-scope penalty, and
archive-firehose penalty. Store score features and ranking reasons in JSON evidence.

Current state: `science_ranking.py` scores stored source-backed science groups with bounded
recency, official provenance, explicit scientific significance, independent families, mission
relevance, explicit rarity, preliminary transient status, public interest, source priority,
cluster size and impact tags. It records duplicate-family, stale, confidence, low-value, hype,
out-of-scope, archive and retraction penalties as factors and reasons. Archive parameter updates,
observation times, and harvest dates receive no release-recency bonus; dramatic titles alone do
not create scientific significance. Focused tests cover those semantics. The COSMIC fixture scan
calls this ranker and persists the score and explanations on events, clusters, and items.

### Hype And Speculation Suppression Rules

Status: implemented for current first-pass COSMIC sources.

Add deterministic rules that suppress or carefully label alien-life claims, UFO material,
sensationalized astronomy headlines, social rumors, image-only clickbait, generic astronomy
explainers, old papers resurfaced as new, unsupported "life found" language, and unreviewed
preprint hype if literature sources are ever enabled. Do not infer scientific meaning beyond source
metadata.

Current state: `science_policy.py` runs before COSMIC item persistence. Explicit UFO/UAP,
unsupported alien-life discovery, and unverified social-rumor claims are dropped; sensational,
image-led, generic explainer, and explicitly old-study headlines retain bounded metadata with
background attention evidence and a low-public-value rank penalty. Unreviewed preprint claims
are background, and Exoplanet Archive, MAST, and PDS metadata-only items are background even
when freshly updated. No scientific discovery is inferred from headline wording or an archive
update timestamp. Any future literature or social source needs a separate fixture/policy review
before enablement.

### Archive Firehose Blocking Rules

Status: completed 2026-10-15 for the current COSMIC source allowlist.

Add deterministic blocking for broad SIMBAD, VizieR, Gaia, MAST, PDS, HEASARC, Exoplanet Archive,
ESO Archive, ESASky, ADS, TAP/ADQL, and catalog queries unless explicit source allowlists, row caps,
timeouts, retention, and query bounds are configured. Source health should report
`archive_firehose_blocked` or `heavy_archive_disabled`.

Current state: exact COSMIC config validation rejects every heavy-archive and astronomy-catalog
registry candidate, even when broad-category flags are enabled. Exoplanet Archive, MAST, and PDS
fixture parsers enforce named tables/collections/targets, exact columns, row caps, time windows,
and response shape. Query-contract or overbroad-response violations raise a distinct archive
firehose error that `news-scan` records as `archive_firehose_blocked` source health before storing
any item. One exact Exoplanet Archive tiny metadata query now has app-owned pre-request bounds
and a separate live signoff. Broad TAP/catalog and all other archive transports remain blocked.

### UI Disabled States After Naming Decision

Status: implemented for first-pass COSMIC source set.

After the user chooses a scope label, add UI states for disabled, not configured, configured but
disabled, never scanned, stale, policy blocked, parser failed, auth required, rate limited, social
disabled, heavy archive disabled, manual review only, hype blocked, archive firehose blocked, and
SYSTEM naming collision unresolved. Do not show fake headlines.

Current state: `/COSMIC` and the overview render truthful `disabled` and `not_configured`
states using the internal `SYSTEM_SOLAR` scope. The API alias and existing `SYSTEM` app-health
page remain distinct, and page loads do not fetch. A configured science source is skipped when
`solar_system_beyond.enabled` is false. Configured NASA JPL and ESA fixture sources show stored
items, events, and evidence. The remaining policy/auth/health-specific states and source summary
need a source-gating pass.

The COSMIC state card now separates configured-source health from the disabled science registry
candidate inventory. It counts the two verified opt-in sources as off by default, not as heavy
archive blocks. It shows heavy archives, auth-required, social, and manual-review candidates,
plus current hype/archive-query blocked sources. A SQLite state matrix covers every reachable
first-pass health state, including disabled, never-run, stale, parser/rate/auth/policy/robots,
terms/scope, hype, and archive-firehose cases without GET fetches. The earlier
`naming_collision_unresolved` state is impossible because RS-117 resolved the name before the
COSMIC route was enabled. New adapters need their own source-specific gates.

### Source Health States

Status: implemented for first-pass COSMIC sources and disabled inventory.

Implement source health states for the chosen Solar System and Beyond scope: `disabled`,
`not_configured`, `configured_never_run`, `healthy`, `stale`, `failing`, `parser_failed`,
`policy_blocked`, `robots_blocked`, `auth_required`, `rate_limited`, `unsupported`,
`manual_review_only`, `heavy_archive_disabled`, `needs_terms_review`, `needs_scope_filter`,
`naming_collision_unresolved`, `hype_blocked`, and `archive_firehose_blocked`. Surface these states
in app-health SYSTEM later and summarize them in the candidate scope.

Current state: configured fixture sources use the shared source-health table and COSMIC/API cards.
An all-rejected fixture records `hype_blocked` without storing its claims. Disabled registry
candidates are summarized separately, including heavy archive, auth, social, manual-review,
unsupported, and health-only behaviors. Parser/rate/auth/policy/stale and archive-firehose states
render from SQLite and appear in app-health SYSTEM. Broad archive fixture queries now produce a
real `archive_firehose_blocked` state. The signed-off ESA and Exoplanet Archive sources move
through disabled, policy-blocked, never-run, healthy, stale, and failure states using the shared
health table. Candidate inventory remains a separate disabled-by-default summary. Future source
admissions require new runtime gates and tests.

### Evidence Drawer Contract

Status: completed 2026-10-15 for current COSMIC fixture and ESA live adapters.

Define and test evidence payloads for Solar System and Beyond items/events. Include source ids,
names, families, classes, URLs, canonical URLs, official flags, source published times, first/last
seen, fetch run ids, parser names, source health, ranking features, object/mission/telescope/
transient match basis, preliminary/confirmed/retracted status, archive query bounds, auth-required
status, retention expiration, policy notes, hype penalty, low-public-value penalty,
archive-firehose penalty, out-of-scope penalty, and no-data-product-download evidence.

Current state: item and event drawers render source identity, family/class, official endpoint and
verification, item/canonical URLs, source publication and first/last seen, fetch mode/run, prior
health, parser, auth requirement, policy and retention, event confidence/match basis/identifiers,
mission/telescope/object/target, transient status, query bounds, ranking factors/penalties,
attention notes, and explicit metadata-only/no-product-request evidence. The no-download wording
is accurate for both fixtures and the ESA live feed. Future source adapters must extend this
contract with their own metadata, especially any auth or archive query semantics.

### Official RSS Live Ingest Phase, Disabled By Default

Status: completed 2026-10-15 for the first verified ESA science RSS source.

After fixtures, ranking, retention, and source health exist, add opt-in live ingest for one verified
official RSS feed at a time. First candidates are JPL RSS, ESA RSS, NASA RSS, Hubble/JWST RSS, and
ATel RSS if policy-safe. Require explicit command/config and no page-load fetches.

Current state: ESA's dedicated Space Science RSS endpoint is exact-allowlisted only under
`SYSTEM_SOLAR` with the verified parser, official URL, explicit `fixture_only: false`, science
parent/scope/source flags, and global official-HTTP opt-in. A bounded 2026-10-15 read returned
HTTP 200, `application/rss+xml`, the `ESA Space Science` channel, and 15 entries. Live scans keep
only source-dated items within 14 days, cap the response at 1 MiB, require at least 60 minutes
between successful fetches, and retain science items at most seven days. Mocked transport tests
cover exact identity, disabled gates, stale rejection, and metadata-only storage. JPL direct,
NASA Science, Hubble/Webb FeedBurner, and ATel remain blocked by their recorded endpoint or
hosting-policy limitations.

### Official Small API Live Ingest Phase, Disabled By Default

Status: implemented for the first exact tiny API source.

After fixture tests and query caps exist, add opt-in small metadata API ingest for NASA Exoplanet
Archive, PDS, MAST, JPL SSD/MPC science context, HEASARC, or GWOSC one source at a time. Require
explicit allowlists, row caps, timeouts, no data-product downloads, no bulk catalog queries, and no
page-load fetches.

Current state: the NASA Exoplanet Archive `ps` TAP source has an app-built seven-day,
ten-row, seven-column, default-solution JSON query. It is exact allowlisted and disabled by
default, with a 64 KiB cap, 24-hour minimum cadence, no product download, archive-update
semantics, and offline gate tests. An isolated explicit scan returned HTTP 200, parsed ten rows,
and stored eight distinct COSMIC items. See
[`COSMIC_EXOPLANET_TAP_LIVE_SIGNOFF.md`](docs/project/COSMIC_EXOPLANET_TAP_LIVE_SIGNOFF.md).
MAST, PDS, HEASARC, broad TAP/catalog queries, and other API sources remain blocked pending
their own signoff.

### Transient Alert Ingest Phase, Disabled By Default

Status: not implemented.

Add opt-in transient alert ingest for GCN notices/circulars, ATel, TNS, and GraceDB/LIGO only after
fixture parsers, policy/auth review, source health, preliminary/update/retraction handling, and
retention tests exist. Do not download sky maps by default.

### Heavy Archive Phase, Disabled By Default

Status: not implemented.

Add any heavy archive, TAP, ADQL, catalog, or observatory archive source only after explicit policy,
row cap, query allowlist, timeout, storage, retention, and value review. Prefer source-health-only
or narrow metadata lookup. Never bulk ingest catalogs.

### Literature Metadata Phase, Disabled By Default

Status: not implemented.

Add literature metadata only after ADS/API policy review, auth handling, fixture tests, retention
rules, and user opt-in. Store metadata only, do not download papers, do not bypass paywalls, and do
not turn console-1701 into a literature review engine.

### Social Source Policy Review, Disabled By Default

Status: not implemented.

Review Reddit official API or permitted feed access, X official API rules, and Bluesky AT Protocol
before implementing any social/community adapter. Keep social disabled by default, require explicit
local configuration, use short retention, never scrape HTML to bypass platform restrictions, and
never treat social as primary evidence.

### Documentation For Source Verification

Status: completed 2026-10-15 for first-pass science verification workflow.

Document the later Solar System and Beyond source verification workflow: confirm endpoint
ownership, access method, source terms, robots/policy notes, parser shape, auth/key requirements,
rate limits, retention sensitivity, privacy risk, verification status, object/mission/scope
filters, source-health behavior, and whether the source is official, archive, alert network,
publisher, public media, social, auth-required, heavy archive, or manual review only.

Current state: `docs/project/SYSTEM_SOLAR_SYSTEM_BEYOND_SOURCE_VERIFICATION_WORKFLOW.md`
captures the shared checklist, registry fields, scope filters, source-health states, per-endpoint
signoff record, exact live promotion gates, and walkthroughs for NASA Science RSS, JPL direct and
NASA-hosted RSS, ESA RSS, and NASA Photojournal. It records malformed XML/403 blockers honestly
and separates ORBITAL parser approval from future science routing.

### Tests For No Page-Load External Fetches

Status: completed 2026-10-15 for the first-pass COSMIC page/API path.

Add tests proving GET routes and page renders read SQLite/config only and never call Solar System
and Beyond network fetchers. Include disabled, not configured, stale, failing, auth-required,
policy-blocked, parser-failed, heavy-archive-disabled, social-disabled, hype-blocked,
archive-firehose-blocked, and naming-collision-unresolved state tests.

Current tests replace both network and fixture fetchers with failures during COSMIC GET rendering,
then exercise disabled/not-configured, stored healthy/stale/failing/parser/rate/auth/policy,
social/heavy-archive/hype/archive-firehose states, and the separate app-health SYSTEM route.
The naming collision is resolved by the COSMIC alias; a page/API assertion prevents the internal
`SYSTEM_SOLAR` key from leaking into the rendered COSMIC page.

### Tests For No Heavy Archive Source Running Without Explicit Config

Status: completed 2026-10-15 for the first-pass COSMIC fixture gate.

Add tests proving SIMBAD, VizieR, Gaia, ESASky, ESO Archive, MAST, PDS, HEASARC, Exoplanet Archive,
ADS, TAP/ADQL, and catalog candidates cannot run unless explicitly enabled with local config,
allowlists, row caps, and query bounds. Tests should assert no network calls and clear disabled or
blocked source-health states.

The COSMIC configuration test iterates every heavy-archive and astronomy-catalog registry
candidate and confirms exact fixture-source validation rejects it, even with heavy-archive flags
enabled. This release has no heavy-archive or live archive transport. Source-specific
blocked health states remain part of RS-138/140.

### Tests For No Auth Source Running Without Config

Status: completed 2026-10-15 for the first-pass COSMIC allowlist.

Add tests proving TNS, ADS, GraceDB if auth-required, Reddit, X, Bluesky, NASA API if key-required,
and any other token/account source cannot run without explicit local configuration. Tests should
assert clear `auth_required` or policy-disabled source-health state and no network calls.

Every science registry candidate marked auth-required is checked for its disabled
`auth_required` behavior and rejected by the exact COSMIC source config gate, even with broad
category flags enabled. A configured fixture with declared but missing auth produces an
`auth_required` source-health row before file or HTTP access. New auth-backed adapters must add
their own credential and policy tests before admission.

### Tests For No Data Product Downloads

Status: completed 2026-10-15 for the current COSMIC fixture adapters.

Add tests proving MAST, PDS, HEASARC, Gaia, ESO Archive, ESASky, TAP/ADQL, GraceDB sky maps, and
other archive sources do not download science products, sky maps, papers, images, or article bodies
by default. Parsers should store metadata only and evidence should explicitly record no data product
downloads.

End-to-end scans of all eight permitted science fixture adapters assert local-only ingest and
persisted metadata. The relevant Exoplanet, MAST, PDS, GCN, and telescope evidence records
explicit false download/product-request flags; parser unit tests reject broader payloads and
product fields. Extend this gate before any new live or archive adapter is admitted.

### Tests For No Alien-Life Or UFO Hype Leakage

Status: completed 2026-10-15 for the first-pass COSMIC fixture path.

Add tests proving UFO content is out of scope, social-only alien-life claims are suppressed,
"life found" wording is blocked unless source metadata directly says it, generic hype is penalized,
and science journalism cannot become primary evidence without official or scientific convergence.

Direct policy tests and an offline `news-scan` SQLite test verify that explicit alien-life/life-found,
UFO/UAP, and unverified-rumor claims are discarded before persistence, while generic/sensational
headlines carry background attention and a low-public-value rank penalty. Exact science source
identity validation rejects a journalism source in the configured COSMIC scan path. This gate
will need extension if later source families are admitted.

## High Priority

### Historical Live Sensor Graphs

Status: implemented.

The top sensor lane keeps five minutes of in-browser buffers for scan health, CPU, RAM, memory PSI,
network RX/TX, root filesystem usage, I/O PSI, and thermal maximum when available. It renders
compact SVG sparklines only after real `/api/live` samples arrive. High-frequency live samples are
not persisted and are lost on page reload.

Polling policy:

- External power + foreground tab: every 3 seconds.
- Battery + foreground tab: every 5 seconds.
- Not foreground, screen locked, screen off, hidden tab, frozen page, or blurred window: live
  polling and header clock updates are paused until foreground resumes.

Follow-up options:

- Tune visual density after watching it under real load for a few sessions.
- Add browser-level tests if a UI smoke-test runner is introduced.
- Consider persisted low-resolution history only after a storage policy exists.

### Broken Action Interactions

Status: implemented.

The top System/Caution box now targets the alert action list (`attention-delta-area`) instead of
the top of the alert module. Static JS is cache-busted with the page version, manual scan shows a
busy state and watches for a fresh host snapshot, and terminal candidates prefer maximized terminal
launch flags where supported.

### WebSocket Or SSE Live Stream

Status: not implemented.

`/api/live` currently uses lightweight polling. Consider Server-Sent Events or WebSocket only if it
reduces jitter and keeps the implementation local/simple.

Constraints:

- No external broker.
- No telemetry.
- Must degrade to polling if streaming is unsupported.

### Configurable Sensor Thresholds

Status: implemented as a shared deterministic rules module; user-configurable overrides remain
deferred until a concrete need and validation contract are defined.

The CPU/RAM and filesystem/pressure decisions now live in `static/live_rules.js`, loaded before
`app.js`. The UI derives state and its threshold help text from that one module; isolated boundary
tests exercise its output without actual host metrics. Defaults remain conservative:

- Filesystem: root warning `>=85%`, critical `>=95%`; home warning `>=90%`, critical `>=95%`.
- CPU/RAM: CPU warning `>=75%`, critical `>=90%`; load/core warning `>=1`, critical `>=1.5`;
  MemAvailable warning `<15%`, critical `<5%`; memory PSI avg10 warning `>=10%`, critical `>=30%`.
- Network: route/address/carrier/error derived, not bandwidth-capacity derived.

Completed acceptance:

- Threshold values appear in evidence or help text.
- Tests cover the rule output independent of actual host metrics.

### Per-Interface Network Details And Capacity

Status: implemented.

The live network readout retains LAN IP, gateway, WAN status, primary RX/TX rates, carrier, and
interface errors/drops. Its expandable local interface list now shows every non-loopback interface,
IPv4, state/carrier, sysfs speed and duplex when available, RX/TX/error rates, and directional
throughput as a percentage of reported link capacity. Wi-Fi quality and signal level appear from
`/proc/net/wireless` when available; they are raw local readings, not a synthetic percentage.
Unknown or unsupported capacity is labeled as such. No external WAN/public-IP lookup was added.

The primary ribbon bars remain visual rate traces, while the expandable per-interface rows provide
capacity-relative percentages. If a future browser smoke runner is introduced, add an interaction
test for the expandable list and its sample-to-sample rate updates.

### Stronger B2 Services/Systems Dashboard

Status: partially implemented.

The B2 bay summarizes failed system/user services and provides evidence. It does not yet behave
like a proper service operations dashboard.

Future work:

- Track configured critical services from config and expose their expected/actual state.
- Add systemd timers, sockets, enabled units, failed units, and degraded state summaries.
- Surface restart counts and recent failure timestamps when readable.
- Add per-unit click targets with status, logs, and suggested next read-only commands.
- Add deterministic classification for "should be running" versus "installed but irrelevant."

### Stronger B3 Debian Dashboard

Status: partially implemented.

The B3 bay shows release/package/log basics. It does not yet cover Debian maintenance posture.

Future work:

- Apt update recency if readable from local logs/cache only.
- Pending upgrades from local apt metadata only if safe and no network update is triggered.
- Reboot-required details.
- Broken/half-configured package evidence.
- Source list summary and third-party repo visibility.
- Kernel package/current kernel comparison.
- Security update posture only from local metadata, no external calls by default.

### Stronger B4 Hardware Dashboard

Status: partially implemented.

The B4 bay shows DMI/CPU/memory/storage/power/thermal/link facts. It is not yet a full hardware
instrumentation panel.

Future work:

- Thermal trip point interpretation in the UI.
- Per-zone live temperature meters.
- Battery health/cycle data if sysfs exposes it.
- NVMe/SATA SMART-like health only if a safe read-only command exists and is already installed;
  no package installation.
- GPU detection only from naturally available local read-only sources.
- USB/PCI inventory only if privacy and noise are handled.

### Local Weather Bay

Status: blocked by local-only contract.

Requested: show local weather for the next 7 days in a bay. A real forecast requires an external
weather provider or a pre-existing local weather data source. Under current constraints,
console-1701 must not make cloud calls or hidden network requests by default.

Safe implementation shape if explicitly approved later:

- Add config such as `weather.enabled: false`, `weather.provider`, and `weather.location`.
- Keep disabled by default.
- Show "not configured" in the UI unless explicitly enabled.
- Use short timeouts, no telemetry, no scraping beyond the selected forecast payload, and clear
  evidence showing provider, location, request time, and failure mode.
- Never infer or transmit precise location without explicit config.

## Medium Priority

### Changes Since Last Scan

Status: partially implemented for persisted host snapshots.

The latest/previous host-snapshot comparison now identifies interface appearances/disappearances,
default-route interface or gateway changes, DNS resolver-set changes, newly failed and recovered
system/user services, and root-filesystem crossings of the existing 85% warning and 95% critical
thresholds. Older snapshots without per-unit lists retain the failed-count fallback. No new probes
or external requests are involved.

Remaining work:

- Kernel/OS/session and tool-version changes beyond the existing kernel comparison.
- Link each change to the evidence section that proves it.
- Broader filesystem threshold transitions beyond the root mount.

### Evidence UX

Status: partially implemented.

Future work:

- Add per-section "copy evidence" buttons.
- Add compact JSON path labels.
- Add evidence search/filter on raw snapshot.
- Keep raw JSON hidden by default except where the user explicitly wants expanded state.
- Make black evidence drawers fill available panel space without wasting empty layout area.

### Alert Action UX

Status: partially implemented.

Future work:

- Add a visible fallback command when terminal launch is unavailable.
- Record terminal launch attempts in local state for auditability.
- Add per-alert action labels that are clearer than an icon-only affordance.
- Keep action strictly user-clicked; no hidden Codex runs.

### Local Work / Repo Section

Status: demoted and preserved.

Future work:

- Make repo cards denser with one-line state and evidence drawers.
- Add clearer separation between machine alerts and repo/workflow alerts.
- Keep handoff packet features available without making them homepage-dominant.

### API Coverage

Status: basic host APIs implemented.

Future work:

- Optional `/host` detail page if the homepage becomes overloaded.
- `/api/live/history` only if high-frequency data persistence is intentionally designed.
- Compact endpoints for failed units, interfaces, filesystems, and process samples if the UI needs
  independent refreshes.

## Low Priority / Deferred

### Optional External Connectivity Checks

Status: config exists for persisted scan path; disabled by default.

Do not add default external WAN/IP checks. If implemented, require explicit config:

```yaml
system_probe:
  allow_external_connectivity_checks: true
```

Use HEAD or minimal requests, short timeout, no payload scraping, and show exactly what was tested.

### Browser Cache Busting

Status: manual query-string versioning.

Consider a small helper or static asset version constant to avoid manually bumping
`/static/app.css?v=...`.

### Accessibility Pass

Status: basic semantic HTML exists.

Future work:

- Keyboard focus pass for dense panels.
- Screen-reader labels for sensor lamps and meters.
- Reduced-motion handling for flashing timers and critical lamps.

### Test Expansion

Status: parser, API, template, terminal action, and scan basics covered.

Future work:

- Unit tests for live sensor threshold classification if moved out of JS.
- Browser-level smoke test for timer/countdown behavior.
- Tests for missing `/proc/pressure` and missing sysfs thermal paths.
- Tests for network error/drop classification.

## Intentionally Out Of Scope Unless Explicitly Requested

- React, Vite, Electron, Tailwind, or another frontend framework.
- Cloud metrics, hosted telemetry, or remote dashboards.
- Automatic git fetch/pull/push/merge/rebase/reset/clean.
- Sudo-based probes.
- Package installation.
- Writing into watched repos.
- Fake charts with no real data.
- External public IP lookup by default.
