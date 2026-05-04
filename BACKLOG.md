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

## Scoped Recent Signal / News Ingestion

Architecture reference:

- `docs/project/NEWS_SCOPE_INGESTION_ARCHITECTURE_DESIGN.md`

### Disabled-By-Default News Config

Status: not implemented.

Add a `news:` config tree that defaults to fully disabled. Include retention, fetch policy, scope,
and source definitions. Reject page-load external fetching, unknown scopes, unknown source kinds,
and homepage extraction unless explicitly allowed. Update `config.example.yml` with disabled example
sources only and no live source enabled by default.

### News SQLite Schema

Status: not implemented.

Add JSON-heavy SQLite tables for recent signal state:

- `news_sources`
- `news_fetch_runs`
- `news_items`
- `news_clusters`
- `news_source_health`

Include indexes for latest-by-scope, latest-by-source, source health, retention purge by
`expires_at`, and dedupe by normalized URL hash. Do not store full article bodies by default.

### Local Fixture Ingest Harness

Status: not implemented.

Create a news ingest path that reads local RSS/Atom/JSON/homepage fixtures only. This phase must not
make network calls. It should normalize fixture items into SQLite, update source health, run
retention purge, and provide deterministic evidence for each item.

### Parser Tests

Status: not implemented.

Add tests for RSS fixtures, Atom fixtures, JSON API fixtures, homepage fixture selectors,
malformed feeds, huge payload rejection/truncation, bounded title/description lengths, timestamp
normalization, and fail-soft parser errors.

### Source Policy And Robots Evidence Layer

Status: not implemented.

Add a policy module that records source basis, source kind, enablement, auth requirement state,
homepage-extractor allowance, robots decisions when applicable, and policy notes. Homepage extraction
must be blocked unless explicitly enabled and must record robots evidence when used. Robots handling
is an operational courtesy, not a legal shield.

### Retention Purge

Status: not implemented.

Add deterministic purge logic for expired news items, old fetch runs, old source health rows, and any
future raw-payload debug rows. Default intent: recent awareness, not archive. Expose retention policy
and last purge evidence in SYSTEM.

### Deterministic Ranking

Status: not implemented.

Add explainable ranking with no LLM calls. Candidate factors: recency, source priority, official
source boost, scope priority, user-pinned tags, repeated topic/cluster count, source-provided alert
severity, item freshness, and source health confidence. Store ranking factors in evidence.

### Scope Page UI

Status: not implemented.

Replace non-INTERNAL placeholder bays with real disabled/not-configured/source-backed panels when
news support exists. LOCAL, REGIONAL, NATIONAL, GLOBAL, and ORBITAL should share a compact template
partial where possible. Do not show fake headlines or demo data.

### OVERVIEW Synthesis Bays

Status: not implemented.

Turn OVERVIEW into a cross-scope synthesis surface with four initial bays: Attention now, Local and
regional pulse, National and global pulse, and Orbital and source health. Local, INTERNAL, and SYSTEM
urgent items should not be buried under broad distant headlines.

### SYSTEM Source Health Bay

Status: not implemented.

Add SYSTEM panels for source ingest status, stale sources, failed parsers, disabled sources, last
successful fetch by source/scope, retention state, DB size, source table counts, config validation
warnings, and evidence that page loads do not perform external fetches.

### Official API/RSS First Live Ingest

Status: not implemented.

After fixture ingest and tests exist, add explicit enabled HTTP fetch for safe official APIs/RSS only.
Use timeouts, response size caps, per-source intervals, backoff, ETag/Last-Modified support, honest
user agent, and fail-soft per-source behavior. Tests must use mocked HTTP or a local test server, not
live network.

### Homepage Extractor Later And Disabled

Status: not implemented.

Add homepage headline extraction only after API/RSS support is stable. Keep it disabled unless
`allow_homepage_extractors` is true. Require per-source selectors, no recursive crawling, bounded
payloads, robots/policy evidence, and no article body archive.

### Social Adapters Later And Terms-Sensitive

Status: not implemented.

Treat social sources as terms-sensitive. Bluesky/AT Protocol is the preferred first candidate if
social signals are needed. Reddit and X require explicit compliant access methods. Do not scrape HTML
to bypass platform APIs, auth, paywalls, rate limits, or bot controls. Keep retention short.

### Documentation Update

Status: not implemented.

When news scaffolding exists, update README, config documentation, safety notes, and command help to
explain disabled-by-default behavior, page-load SQLite-only reads, explicit ingest commands,
retention, source policy, and how to audit source health.

### Separate Disabled Systemd News Timer

Status: not implemented.

If scheduled news ingest is added, create a separate user-level `console-1701-news-scan.timer`.
Existing `console-1701-scan.timer` must not silently start external fetching. The news timer should
be disabled unless news ingest is explicitly configured and enabled.

## LOCAL Seattle Recent Signal Layer

Architecture reference:

- `docs/project/LOCAL_SEATTLE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### LOCAL Source Registry Design Implementation

Status: not implemented.

Implement the LOCAL source registry from the design document with explicit `source_key`,
`source_family`, `source_class`, adapter, scope, priority, policy risk, parser risk, privacy risk,
retention sensitivity, verification status, and future phase fields. Validate enum values and keep
all sources disabled until explicitly configured.

### Disabled-By-Default LOCAL Config

Status: not implemented.

Add a LOCAL config shape that defaults to disabled, with `include_airport`, `include_port`,
`include_king_county_transit`, `include_wsdot_seattle_corridors`, `include_ferries`,
`hazard_radius_miles`, `earthquake_min_magnitude`, `allow_neighborhood_blogs`, and
`allow_social_sources`. Reject social sources unless explicitly allowed. Reject homepage extraction
unless a future `allow_homepage_extractors` flag is explicitly true.

### LOCAL SQLite Schema Or Extension

Status: not implemented.

Add SQLite storage for LOCAL source registry state, fetch runs, normalized items, event clusters or
`local_events`, source health, ranking explanations, and retention purge evidence. Use JSON-heavy
columns and indexes for latest-by-scope, source health, event ranking, source family, and
`expires_at` purge. Do not store full article bodies by default.

### LOCAL Fixture Pack

Status: not implemented.

Create local-only fixtures for SFD Socrata JSON, AlertSeattle RSS, King County Metro RSS, NWS alert
JSON, WSDOT alert JSON, local blog RSS, City Light outage data, and FAA/SEA airport status. Fixture
ingest must not perform network calls and must be safe for pytest.

### Socrata Parser For SFD Fire 911

Status: not implemented.

Build a `socrata_json` fixture parser for Seattle Real-Time Fire 911 metadata. Preserve dataset ID,
row ID, incident type, observed timestamp, unit count if present, location tokens, source URL, and
privacy redaction evidence. Low-acuity medical/private calls must not automatically elevate.

### RSS/Atom Parser For Official And Local Feeds

Status: not implemented.

Build an RSS/Atom parser for fixture feeds first, covering AlertSeattle, SPD Blotter, SDOT Blog,
Metro, local news, and neighborhood blogs where feeds verify later. Parse title, URL, published
timestamp, bounded description, categories, source id, and evidence. Never fetch article bodies.

### NWS Alert Fixture Parser

Status: not implemented.

Build a fixture parser for NWS active alert JSON filtered to Seattle, King County, Puget Sound, and
configured nearby hazard zones. Preserve severity, urgency, certainty, event type, affected zones,
effective/expiration times, and active-alert ranking evidence.

### WSDOT Official API Fixture Parser

Status: not implemented.

Build a fixture parser for WSDOT traveler information affecting Seattle corridors, ferries, bridges,
passes, routes, or regional access. Preserve route/facility tokens, closure/delay severity, published
time, source URL, and public-impact scoring evidence.

### Metro RSS Parser

Status: not implemented.

Build a fixture parser for King County Metro service advisories RSS. Preserve route IDs, affected
service area, advisory title, published time, source URL, and transit-impact ranking evidence.

### FAA/SEA Airport Status Research

Status: not implemented.

Verify which FAA, NAS Status, Port of Seattle, or SEA Airport endpoints provide lawful,
machine-readable operational metadata for SEA ground stops, delays, closures, checkpoint impacts, or
traveler advisories. Do not implement live fetch until endpoint and policy review are complete.

### City Light Outage Endpoint Research

Status: not implemented.

Identify whether Seattle City Light outage data has a stable official endpoint behind the public
outage pages or maps. Prefer official APIs or feature services. Do not scrape ArcGIS/Experience map
HTML. If no suitable endpoint exists, keep the source `manual_review_only` or
`source_health_probe_only`.

### SPD Call Data Privacy Review

Status: not implemented.

Review SPD Call Data and Significant Incident Report sources for privacy, preliminary-report caveats,
address handling, retention, and display rules. Ordinary minor calls and exact private locations must
not be elevated without public-impact justification.

### ArcGIS Dashboard Underlying Endpoint Research

Status: not implemented.

Research underlying official feature services for SPD dashboards, City Light outage maps, and SDOT
traffic/camera maps. Do not screen scrape dashboards. Mark sources `manual_review_only` or
`source_health_probe_only` when no stable official endpoint is available.

### LOCAL Deterministic Event Correlation

Status: not implemented.

Implement deterministic LOCAL event matching by time window, source family, normalized title tokens,
route/facility tokens, neighborhood, intersection, weather zone, airport/port facility, utility
area, and privacy-safe location tokens. Do not use LLMs, embeddings, or hidden cloud calls.

### LOCAL Deterministic Ranking

Status: not implemented.

Implement explainable LOCAL ranking with recency, official severity, source diversity, public
impact, source priority, active alert state, cluster size, privacy penalty, duplicate-family
penalty, stale-source penalty, and low-confidence penalty. Store score features and ranking reasons
in JSON evidence.

### LOCAL Privacy Redaction Rules

Status: not implemented.

Add deterministic redaction rules for public safety data. Suppress exact addresses for low-acuity
medical calls, overdose calls, private residential aid, single-source minor police calls, and
low-public-value private distress. Prefer neighborhood or intersection-level display unless an
official source frames the incident as public-impact.

### LOCAL UI Disabled States

Status: not implemented.

Replace LOCAL placeholders only after storage/config support exists. Show honest states for disabled,
not configured, configured but disabled, never scanned, stale, policy blocked, parser failed, social
disabled, and homepage extraction disabled. Do not show fake headlines.

### LOCAL Source Health States

Status: not implemented.

Implement source health states for LOCAL: `disabled`, `not_configured`, `configured_never_run`,
`healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`, `robots_blocked`,
`auth_required`, `rate_limited`, `unsupported`, and `manual_review_only`. Surface these states in
SYSTEM later and summarize them on LOCAL.

### LOCAL Evidence Drawer Contract

Status: not implemented.

Define and test evidence payloads for LOCAL items and events. Include source ids, source names,
families, classes, item URLs, canonical URLs, official flags, source published times, first/last
seen, fetch run ids, parser names, source health, ranking features, privacy redaction decision,
retention expiration, matching tokens, geographic basis, event confidence, and policy notes.

### LOCAL Official-Source Live Ingest Phase

Status: not implemented.

After fixture parsing, correlation, ranking, retention, and tests exist, add opt-in live ingest for
one safe official source at a time. First candidates are SFD Fire 911 Socrata, NWS alerts, King
County Metro RSS, and WSDOT API. Keep every source disabled by default and require an explicit
command. No page-load fetches.

### LOCAL News/Blog RSS Ingest Phase

Status: not implemented.

Add opt-in RSS/Atom ingest for local news and neighborhood blogs only after source verification.
Store headline metadata only, bound descriptions, avoid article bodies, avoid paywall bypass, and
prevent duplicate syndicated articles from inflating independent convergence.

### LOCAL Social Source Policy Review

Status: not implemented.

Review Bluesky AT Protocol, Reddit official API or permitted feed access, and X official API rules
before implementing any community/social adapter. Keep social disabled by default, require explicit
configuration, use short retention, and never scrape HTML to bypass platform restrictions.

### Documentation For Source Verification

Status: not implemented.

Document the later source verification workflow: confirm endpoint ownership, access method, source
terms, robots/policy notes, parser shape, rate limits, retention sensitivity, privacy risk,
verification status, and source-health behavior before enabling any source.

### Tests For No Page-Load External Fetches

Status: not implemented.

Add tests proving GET routes and page renders read SQLite/config only and never call network fetchers.
Include disabled/not configured/stale/failing state tests for LOCAL and SYSTEM source health.

## REGIONAL Pacific Northwest Recent Signal Layer

Architecture reference:

- `docs/project/REGIONAL_PNW_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### REGIONAL Source Registry Design Implementation

Status: not implemented.

Implement the REGIONAL source registry from the design document with explicit `source_key`,
`source_family`, `source_class`, adapter, scope, priority, official status, policy risk, parser
risk, privacy risk, retention sensitivity, verification status, and future phase fields. Validate
enum values and keep all REGIONAL sources disabled until explicitly configured.

### Disabled-By-Default REGIONAL Config

Status: not implemented.

Add a `regional_sources:` or equivalent REGIONAL config tree that defaults to disabled. Include
geography flags for Washington, Puget Sound, Cascadia hazards, Oregon relevance, BC relevance,
transport corridors, wildfire/smoke, seismic/volcano, public health, state government, regional
news, and social sources. Reject social sources unless explicitly allowed and reject homepage
extraction unless a future `allow_homepage_extractors` flag is true.

### REGIONAL SQLite Schema Or Extension

Status: not implemented.

Add or extend SQLite storage for REGIONAL source registry state, fetch runs, normalized items,
`regional_events` or scoped clusters, source health, ranking explanations, geographic labels, and
retention purge evidence. Use JSON-heavy columns and indexes for latest-by-scope, event ranking,
source health, source family, geographic filters, and `expires_at` purge. Do not store full article
bodies by default.

### REGIONAL Fixture Pack

Status: not implemented.

Create local-only fixtures for NWS active alert JSON, WSDOT travel alert JSON, WSF bulletin/API
shape, WA DNR wildfire data after endpoint verification, NWCC feed shape after verification, USGS
earthquake GeoJSON, USGS water/hydrology data, King County emergency feed, Ecology/AirNow AQI,
regional news RSS, and verified outage data if an official endpoint is found. Fixture ingest must
not perform network calls and must be safe for pytest.

### NWS Alert Parser For Washington

Status: not implemented.

Build a fixture-first NWS alert parser filtered to Washington, Puget Sound, configured counties,
weather zones, and regional hazard rules. Preserve alert id, event type, severity, urgency,
certainty, affected zones, counties, effective time, expiration time, source URL, instruction URL,
and official-alert ranking evidence.

### WSDOT Traveler API Fixture Parser

Status: not implemented.

Build a fixture parser for WSDOT traveler information affecting regional corridors, mountain
passes, bridges, border crossings, and major Washington routes. Preserve route, direction, milepost
or facility tokens, closure/delay severity, source update time, source URL, and transport-impact
ranking evidence.

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

Status: not implemented.

Build a fixture-first parser for USGS earthquake GeoJSON filtered to Washington, Puget Sound,
Cascadia, and configured radius/magnitude rules. Preserve event id, magnitude, depth, place, time,
felt/intensity fields where present, source URL, bounding basis, and seismic ranking evidence.

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

Status: not implemented.

Build a fixture-first parser for King County Emergency News if a feed endpoint is verified.
Preserve title, URL, published timestamp, bounded description, categories/tags, emergency/alert
classification, county geography, source URL, and county-emergency ranking evidence.

### County Emergency Alert Source Verification

Status: not implemented.

Verify Snohomish, Pierce, Thurston, Whatcom, Skagit, Kitsap, Clallam, Jefferson, and other regional
county emergency sources before implementation. Record source ownership, feed/API availability,
access method, parser risk, policy notes, privacy risk, source-health behavior, and fallback state.

### Regional News RSS Parser

Status: not implemented.

Build a fixture-first RSS/Atom parser for verified regional news, public media, local TV/radio, and
nonprofit feeds. Store headline metadata only, bound descriptions, preserve publisher/source
family, detect duplicate or syndicated stories, and prevent duplicated articles from inflating
independent convergence.

### REGIONAL Deterministic Event Correlation

Status: not implemented.

Implement deterministic REGIONAL event matching by source family, time window, normalized title
tokens, event type, county, city, route, mountain pass, ferry route, airport, port, river basin,
weather zone, fire incident name, volcano, seismic region, AQI station, and public-health
jurisdiction. Do not use LLMs, embeddings, or hidden cloud calls.

### REGIONAL Deterministic Ranking

Status: not implemented.

Implement explainable REGIONAL ranking with recency, official severity, source diversity, temporal
proximity, public impact, geographic relevance, active alert state, source priority, cluster size,
privacy penalty, duplicate-family penalty, stale-source penalty, low-confidence penalty, and
out-of-region penalty. Store score features and ranking reasons in JSON evidence.

### REGIONAL Privacy And Public-Impact Rules

Status: not implemented.

Add deterministic REGIONAL privacy and public-impact rules. Suppress exact private addresses for
low-value incidents, avoid amplifying residential outages below threshold, keep routine
public-safety and social-only reports low priority, and prefer county, corridor, zone, basin,
facility, or regional labels unless official public-impact evidence requires more detail.

### REGIONAL UI Disabled States

Status: not implemented.

Replace REGIONAL placeholders only after storage/config support exists. Show honest states for
disabled, not configured, configured but disabled, never scanned, stale, policy blocked, parser
failed, social disabled, homepage extraction disabled, and manual-review-only sources. Do not show
fake headlines.

### REGIONAL Source Health States

Status: not implemented.

Implement source health states for REGIONAL: `disabled`, `not_configured`,
`configured_never_run`, `healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`,
`robots_blocked`, `auth_required`, `rate_limited`, `unsupported`, and `manual_review_only`. Surface
these states in SYSTEM later and summarize them on REGIONAL.

### REGIONAL Evidence Drawer Contract

Status: not implemented.

Define and test evidence payloads for REGIONAL items and events. Include source ids, names,
families, classes, item URLs, canonical URLs, official flags, published times, first/last seen,
fetch run ids, parser names, source health, ranking features, geographic match basis, public impact
basis, source diversity basis, privacy redaction decision, retention expiration, matching tokens,
event type, event confidence, and policy notes.

### REGIONAL Official-Source Live Ingest Phase

Status: not implemented.

After fixtures, correlation, ranking, retention, source health, and tests exist, add opt-in live
ingest for one safe official source at a time. First candidates are NWS alerts for Washington,
WSDOT Traveler API, USGS earthquake GeoJSON, and King County Emergency News feed if valid. Keep
every source disabled by default and require an explicit command. No page-load fetches.

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

Status: not implemented.

Document the later REGIONAL source verification workflow: confirm endpoint ownership, access method,
source terms, robots/policy notes, parser shape, rate limits, retention sensitivity, privacy risk,
verification status, geography/relevance filters, and source-health behavior before enabling any
source.

### Tests For No Page-Load External Fetches

Status: not implemented.

Add tests proving GET routes and page renders read SQLite/config only and never call REGIONAL
network fetchers. Include disabled/not configured/stale/failing/policy-blocked/parser-failed state
tests for REGIONAL and SYSTEM source health.

## NATIONAL United States Recent Signal Layer

Architecture reference:

- `docs/project/NATIONAL_US_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### NATIONAL Source Registry Design Implementation

Status: not implemented.

Implement the NATIONAL source registry from the design document with explicit `source_key`,
`source_family`, `source_class`, adapter, scope, priority, official status, policy risk, parser
risk, privacy risk, retention sensitivity, verification status, and future phase fields. Validate
enum values and keep all NATIONAL sources disabled until explicitly configured.

### Disabled-By-Default NATIONAL Config

Status: not implemented.

Add a `national_sources:` or equivalent NATIONAL config tree that defaults to disabled. Include
flags for federal alerts, weather hazards, disasters, public health, recalls, transportation,
aviation, cybersecurity, energy/grid, economic releases, Federal Register, Congress, courts,
national news, social sources, and state events with national impact. Reject social sources unless
explicitly allowed and reject homepage extraction unless a future `allow_homepage_extractors` flag
is true.

### NATIONAL SQLite Schema Or Extension

Status: not implemented.

Add or extend SQLite storage for NATIONAL source registry state, fetch runs, normalized items,
`national_events` or scoped clusters, source health, ranking explanations, agency/sector/state
labels, and retention purge evidence. Use JSON-heavy columns and indexes for latest-by-scope, event
ranking, source health, source family, agency/sector/state filters, and `expires_at` purge. Do not
store full article bodies by default.

### NATIONAL Fixture Pack

Status: not implemented.

Create local-only fixtures for NWS active alert JSON, NHC advisory/RSS data, USGS earthquake
GeoJSON, CDC HAN, FDA recalls, FSIS Recall API, CPSC Recalls API, NHTSA recalls, CISA advisories,
CISA KEV, FAA NAS status, Federal Register API, BLS releases, and national news RSS. Fixture ingest
must not perform network calls and must be safe for pytest.

### NWS Active Alert Parser

Status: not implemented.

Build a fixture-first NWS active alert parser for NATIONAL scope. Preserve alert id, event type,
severity, urgency, certainty, affected states/zones, effective time, expiration time, source URL,
instruction URL, and official-alert ranking evidence.

### NHC Advisory/Feed Verification

Status: not implemented.

Verify National Hurricane Center advisory/feed endpoints before implementation. Record feed/API
ownership, advisory cycle fields, storm name/id handling, watch/warning fields, parser shape,
policy notes, refresh interval, and source-health behavior. Keep sources disabled until verified.

### USGS Earthquake GeoJSON Parser

Status: not implemented.

Build a fixture-first parser for USGS earthquake GeoJSON filtered to U.S. national relevance,
configured magnitude thresholds, territories, and felt/multi-state impact rules. Preserve event id,
magnitude, depth, place, time, felt/intensity fields where present, source URL, bounding basis, and
seismic ranking evidence.

### FEMA/OpenFEMA Disaster Declarations Research

Status: not implemented.

Research OpenFEMA disaster declarations and related FEMA data sources for stable API shapes,
declaration update behavior, incident type fields, state/FEMA region filters, retention,
source-health evidence, and ranking impact. Do not implement live fetch until endpoint behavior is
verified.

### CDC HAN Parser

Status: not implemented.

Build a fixture-first parser for CDC Health Alert Network notices after feed/page shape is verified.
Preserve alert id or URL, title, published/update time, alert type, affected population or
jurisdiction if provided, public instruction URL, preliminary status, bounded description, and
public-health ranking evidence.

### FDA Recall Endpoint/Feed Verification

Status: not implemented.

Verify FDA recall endpoint/feed options before implementation. Identify whether RSS, enforcement
report data, or another official endpoint provides stable recall metadata. Preserve endpoint
ownership, parser shape, recall class/hazard/product fields, distribution geography, policy notes,
refresh interval, and source-health behavior.

### FSIS Recall API Parser

Status: not implemented.

Build a fixture-first parser for the FSIS Recall API. Preserve recall id, product, firm, recall
class, hazard, distribution geography, public instruction URL, recall date, active/update status,
source URL, and food-safety ranking evidence.

### CPSC Recalls API Parser

Status: not implemented.

Build a fixture-first parser for the CPSC Recalls API. Preserve recall id, product, firm, hazard,
injury/death risk indicators when source-provided, recall date, URL, distribution scope, public
instruction URL, and consumer-safety ranking evidence.

### NHTSA Recalls API Parser

Status: not implemented.

Build a fixture-first parser for NHTSA recall APIs. Preserve recall campaign id, make/model/year or
equipment fields, component, safety risk, remedy, recall date, source URL, affected population
metadata where available, and vehicle-safety ranking evidence.

### FAA NAS Status Fixture Parser

Status: not implemented.

Build a fixture-first parser for FAA NAS status and airport status candidates after endpoint
behavior is verified. Preserve airport, system, event type, delay estimate, ground stop or ground
delay status, closure status, start/end times, source update time, source URL, and aviation-impact
ranking evidence.

### CISA Advisory Parser

Status: not implemented.

Build a fixture-first parser for CISA cybersecurity advisories, alerts, ICS advisories, bulletins,
and emergency directives after feed/API shapes are verified. Preserve advisory id, title, CVE ids,
vendor/product, severity where source-provided, mitigation URL, published/update time, directive
flag, source URL, and cyber ranking evidence.

### CISA KEV Endpoint Research

Status: not implemented.

Research CISA Known Exploited Vulnerabilities machine-readable endpoint options, including JSON/CSV
availability, schema fields, due date handling, update behavior, source policy, refresh interval,
and source-health behavior. Keep KEV disabled until endpoint verification and fixture tests exist.

### Federal Register API Parser With Filters

Status: not implemented.

Build a fixture-first Federal Register API parser with agency allowlists, document type allowlists,
high-impact filters, public-comment/action window fields, and low-public-value suppression. Prevent
routine notices from flooding NATIONAL attention.

### GovInfo RSS Parser

Status: not implemented.

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

Status: not implemented.

Implement deterministic NATIONAL event matching by source family, time window, normalized title
tokens, event type, agency, affected states, affected territories, FEMA region, NWS region, storm
basin, affected airports, product distribution area, infrastructure sector, affected population
group, court/federal jurisdiction, and national/multi-state labels. Do not use LLMs, embeddings, or
hidden cloud calls.

### NATIONAL Deterministic Ranking

Status: not implemented.

Implement explainable NATIONAL ranking with recency, official severity, source diversity, temporal
proximity, public impact, geographic reach, active alert state, source priority, cluster size,
local/regional impact, duplicate-family penalty, stale-source penalty, low-confidence penalty,
low-public-value penalty, and out-of-scope penalty. Store score features and ranking reasons in JSON
evidence.

### NATIONAL Low-Public-Value And Public-Impact Rules

Status: not implemented.

Add deterministic NATIONAL rules that suppress routine agency press releases, generic political
messaging, minor personnel announcements, punditry, duplicate syndicated stories, local stories with
no national impact, vague social-only reports, routine court filings, and unconfigured economic
releases. Elevate official alerts, high-risk recalls, cyber directives, aviation disruption,
federal disaster declarations, and public-health warnings with action guidance.

### NATIONAL UI Disabled States

Status: not implemented.

Replace NATIONAL placeholders only after storage/config support exists. Show honest states for
disabled, not configured, configured but disabled, never scanned, stale, policy blocked, parser
failed, auth required, rate limited, social disabled, homepage extraction disabled, and
manual-review-only sources. Do not show fake headlines.

### NATIONAL Source Health States

Status: not implemented.

Implement source health states for NATIONAL: `disabled`, `not_configured`,
`configured_never_run`, `healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`,
`robots_blocked`, `auth_required`, `rate_limited`, `unsupported`, and `manual_review_only`. Surface
these states in SYSTEM later and summarize them on NATIONAL.

### NATIONAL Evidence Drawer Contract

Status: not implemented.

Define and test evidence payloads for NATIONAL items and events. Include source ids, names,
families, classes, item URLs, canonical URLs, official flags, published times, first/last seen,
fetch run ids, parser names, source health, ranking features, geographic reach basis, public impact
basis, source diversity basis, retention expiration, matching tokens, event type, event confidence,
policy notes, low-public-value penalty, and out-of-scope penalty.

### NATIONAL Official-Source Live Ingest Phase

Status: not implemented.

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

Status: not implemented.

Document the later NATIONAL source verification workflow: confirm endpoint ownership, access
method, source terms, robots/policy notes, parser shape, auth/key requirements, rate limits,
retention sensitivity, privacy risk, verification status, agency/sector/state filters, and
source-health behavior before enabling any source.

### Tests For No Page-Load External Fetches

Status: not implemented.

Add tests proving GET routes and page renders read SQLite/config only and never call NATIONAL
network fetchers. Include disabled/not configured/stale/failing/auth-required/policy-blocked/parser
failed state tests for NATIONAL and SYSTEM source health.

### Tests For No API-Key Source Running Without Config

Status: not implemented.

Add tests proving Congress.gov, BEA, FRED, and any other API-key or auth-required source cannot run
without explicit local configuration. The tests should assert clear `auth_required` source-health
state and no network calls.

## GLOBAL World Recent Signal Layer

Architecture reference:

- `docs/project/GLOBAL_WORLD_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### GLOBAL Source Registry Design Implementation

Status: not implemented.

Implement the GLOBAL source registry from the design document with explicit `source_key`,
`source_name`, `source_family`, `source_class`, `scope`, `raw_url`, access kind, adapter type,
refresh interval, priority, official status, privacy risk, policy risk, parser risk, retention
sensitivity, verification status, source-health behavior, and future phase fields. Validate enum
values and keep every GLOBAL source disabled until explicitly configured.

### Disabled-By-Default GLOBAL Config

Status: not implemented.

Add a `global:` or equivalent GLOBAL config tree that defaults to disabled. Include flags for
disasters, humanitarian, public health, weather hazards, tropical cyclones, earthquakes, tsunamis,
volcanoes, wildfire/smoke, air quality, conflict-humanitarian, diplomacy/institutions,
transport/supply chain, cybersecurity, global economy, global news, social sources, U.S. impact
tags, and local impact tags. Reject social, auth-required, heavy open-data, and homepage extraction
sources unless explicit local flags are set.

### GLOBAL SQLite Schema Or Extension

Status: not implemented.

Add or extend SQLite storage for GLOBAL source registry state, fetch runs, normalized items,
`global_events` or scoped clusters, source health, ranking explanations, crisis sensitivity flags,
impact tags, retention purge evidence, and source verification metadata. Use JSON-heavy columns and
indexes for latest-by-scope, event ranking, source health, source family, event type, affected
country/region, and `expires_at` purge. Do not store full article bodies by default.

### GLOBAL Fixture Pack

Status: not implemented.

Create local-only fixtures for GDACS feeds/API responses, ReliefWeb disasters and reports, WHO
Disease Outbreak News, ECDC RSS, USGS earthquake GeoJSON, NHC RSS, Smithsonian GVP weekly report,
UN News RSS, UN Press RSS, IAEA RSS, global news RSS, source-health states, disabled sources, stale
sources, auth-required sources, and parser failures. Fixture ingest must not perform network calls
and must be safe for pytest.

### GDACS Feed Parser

Status: not implemented.

Build a fixture-first GDACS feed parser for GLOBAL scope. Preserve alert id, event type, country or
region, event name, alert level, severity fields when source-provided, published/update time,
source URL, geometry or bounding metadata when available, and official-alert ranking evidence.

### GDACS API Fixture Parser

Status: not implemented.

Build a fixture-first GDACS API parser after endpoint behavior is verified. Preserve disaster id,
event type, severity, alert level, affected geography, coordinates or geometry when available,
start/update time, source URL, and source-health evidence. Keep live API access disabled by default.

### ReliefWeb Disasters API Parser

Status: not implemented.

Build a fixture-first parser for ReliefWeb disaster records. Preserve disaster id, name, status,
country list, disaster type, primary dates, source URL, related reports count where available, and
humanitarian ranking evidence. Store metadata only and avoid report body ingestion.

### ReliefWeb Reports API Parser

Status: not implemented.

Build a fixture-first parser for ReliefWeb reports and updates with strict filters for active
disasters, official sources, humanitarian relevance, bounded descriptions, source organization,
country list, publication time, report URL, and retention expiration. Prevent report volume from
flooding GLOBAL attention.

### WHO Disease Outbreak News Parser

Status: not implemented.

Build a fixture-first WHO Disease Outbreak News parser. Preserve outbreak title, disease or hazard
label, affected country or region, publication/update time, source URL, bounded summary, official
public-health evidence, and outbreak ranking features. Do not infer case counts unless the source
provides structured values.

### ECDC RSS Parser

Status: not implemented.

Build a fixture-first ECDC RSS parser after feed shape is verified. Preserve title, published time,
URL, category when provided, bounded description, public-health source evidence, and Europe/global
impact tags. Keep it lower priority than WHO DON unless convergence or severity warrants elevation.

### WMO CAP Warning Source Verification

Status: not implemented.

Verify WMO severe weather source references, CAP availability, national meteorological service
links, ownership, policy notes, parser shape, refresh interval, and source-health behavior before
implementation. Do not scrape warning maps or dashboards.

### USGS Global Earthquake GeoJSON Parser

Status: not implemented.

Build a fixture-first parser for USGS global earthquake GeoJSON with configured magnitude,
tsunami, depth, felt, intensity, country/region, and time-window filters. Preserve event id,
magnitude, depth, place, time, update time, source URL, tsunami flag, and seismic ranking evidence.

### NHC RSS Parser

Status: not implemented.

Build a fixture-first parser for National Hurricane Center RSS/global tropical weather candidates
after source scope is verified. Preserve basin, storm id/name when present, advisory type,
watch/warning terms, published/update time, source URL, and tropical-cyclone ranking evidence.

### Smithsonian GVP Weekly Report Parser

Status: not implemented.

Build a fixture-first parser for Smithsonian Global Volcanism Program weekly report candidates.
Preserve volcano name, country/region, activity type when structured, report window, source URL,
and volcano ranking evidence. Keep parser conservative where page structure is not stable.

### NASA FIRMS API Review And Filtered Fixture Parser

Status: not implemented.

Review NASA FIRMS access, key requirements, terms, rate limits, area filters, retention, and
appropriate global wildfire/smoke use before implementation. If allowed, build only a filtered
fixture parser with explicit geography and severity controls. Keep live FIRMS access disabled by
default and require explicit local configuration.

### UN News RSS Parser

Status: not implemented.

Build a fixture-first UN News RSS parser for institution and global public-impact signals. Preserve
headline, URL, published time, category when present, bounded description, source family, and
diplomacy/institution ranking evidence. Suppress routine speeches and low-impact feature stories.

### UN Press RSS Parser

Status: not implemented.

Build a fixture-first UN Press RSS parser with filters for Security Council, General Assembly,
humanitarian, sanctions, emergency sessions, peacekeeping, and active crisis terms. Preserve title,
URL, publication time, organ/category where available, and official institution evidence.

### IAEA RSS Parser

Status: not implemented.

Build a fixture-first IAEA RSS parser for nuclear safety and international nuclear institution
signals. Preserve title, URL, publication time, category when available, bounded description,
source family, and nuclear-safety ranking evidence. Suppress routine institutional content unless
configured.

### Humanitarian Source Evidence Contract

Status: not implemented.

Define and test evidence payloads for humanitarian GLOBAL items. Include source id, source family,
official or humanitarian status, affected countries, disaster/crisis id where available, event
type, source publication time, first/last seen, bounded description, report URL, retention
expiration, policy notes, and whether people-at-risk metadata is source-provided or omitted.

### Conflict-Humanitarian Sensitivity Rules

Status: not implemented.

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

Status: not implemented.

Implement deterministic GLOBAL event matching by source family, event type, time window,
normalized title tokens, affected countries or regions, disaster id, outbreak terms, storm id,
earthquake id, volcano name, institution, transport sector, cyber identifiers, and impact tags. Do
not use LLMs, embeddings, or hidden cloud calls.

### GLOBAL Deterministic Ranking

Status: not implemented.

Implement explainable GLOBAL ranking with recency, official severity, independent source
diversity, temporal proximity, public impact, affected geography, humanitarian sensitivity,
source priority, cluster size, local/regional/national impact tags, duplicate-family penalty,
stale-source penalty, low-confidence penalty, low-public-value penalty, and out-of-scope penalty.
Store score features and ranking reasons in JSON evidence.

### GLOBAL Low-Public-Value, Rumor, And Public-Impact Rules

Status: not implemented.

Add deterministic GLOBAL rules that suppress routine diplomatic statements, generic political
punditry, single-source social chatter, rumor, graphic violence amplification, private distress,
routine institutional content, routine economic releases, duplicate syndicated stories, and
unconfigured domestic politics. Elevate official alerts, high-severity disasters, major outbreaks,
tsunami/tropical-cyclone hazards, global transport disruption, nuclear safety alerts, and verified
multi-source public-impact events.

### GLOBAL UI Disabled States

Status: not implemented.

Replace GLOBAL placeholders only after storage/config support exists. Show honest states for
disabled, not configured, configured but disabled, never scanned, stale, policy blocked, parser
failed, auth required, rate limited, social disabled, homepage extraction disabled, heavy open-data
disabled, token/account source not configured, and manual-review-only sources. Do not show fake
headlines.

### GLOBAL Source Health States

Status: not implemented.

Implement source health states for GLOBAL: `disabled`, `not_configured`, `configured_never_run`,
`healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`, `robots_blocked`,
`auth_required`, `rate_limited`, `unsupported`, `manual_review_only`,
`heavy_open_data_disabled`, `social_disabled`, and `homepage_extract_disabled`. Surface these
states in SYSTEM later and summarize them on GLOBAL.

### GLOBAL Evidence Drawer Contract

Status: not implemented.

Define and test evidence payloads for GLOBAL items and events. Include source ids, names, families,
classes, item URLs, canonical URLs, official flags, published times, first/last seen, fetch run ids,
parser names, source health, ranking features, affected countries/regions, public impact basis,
source diversity basis, retention expiration, matching tokens, event type, event confidence, policy
notes, sensitivity notes, low-public-value penalty, out-of-scope penalty, and impact tags.

### GLOBAL Official-Source Live Ingest Phase, Disabled By Default

Status: not implemented.

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

Status: not implemented.

Document the later GLOBAL source verification workflow: confirm endpoint ownership, access method,
source terms, robots/policy notes, parser shape, auth/key requirements, rate limits, retention
sensitivity, privacy risk, verification status, geography/relevance filters, source-health
behavior, and whether the source is official, media, nonprofit, platform, open-data, or manual
review only.

### Tests For No Page-Load External Fetches

Status: not implemented.

Add tests proving GET routes and page renders read SQLite/config only and never call GLOBAL network
fetchers. Include disabled/not configured/stale/failing/auth-required/policy-blocked/parser-failed,
heavy-open-data-disabled, social-disabled, homepage-extraction-disabled, and manual-review-only
state tests for GLOBAL and SYSTEM source health.

### Tests For No Heavy Source Running Without Explicit Config

Status: not implemented.

Add tests proving HDX/HAPI, NASA FIRMS, GDELT, OWID, World Bank, IMF, ArcGIS, catalog, CSV, and
other heavy open-data candidates cannot run unless explicitly enabled in local config. Tests should
assert no network calls and clear disabled source-health states.

### Tests For No Token/Account Source Running Without Config

Status: not implemented.

Add tests proving ACLED, Reddit, X, Bluesky, NASA FIRMS if key-required, IMF if key-required, and
any other token/account source cannot run without explicit local configuration. The tests should
assert clear `auth_required` or policy-disabled source-health state and no network calls.

## ORBITAL Space Recent Signal Layer

Architecture reference:

- `docs/project/ORBITAL_SPACE_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### ORBITAL Source Registry Design Implementation

Status: not implemented.

Implement the ORBITAL source registry from the design document with explicit `source_key`,
`source_name`, `source_family`, `source_class`, `scope`, `raw_url`, access kind, adapter type,
refresh interval, priority, official status, privacy risk, policy risk, parser risk, retention
sensitivity, verification status, source-health behavior, and future phase fields. Validate enum
values and keep every ORBITAL source disabled until explicitly configured.

### Disabled-By-Default ORBITAL Config

Status: not implemented.

Add an `orbital:` or equivalent ORBITAL config tree that defaults to disabled. Include flags for
space weather, aurora, NEO close approaches, fireballs, launches, crewed spaceflight, ISS,
reentries, debris, satellite catalog, conjunction awareness, space agency news, spaceflight news,
astronomy transients, social sources, and restricted/auth sources. Reject social, auth-required,
restricted, tactical, and homepage-extraction sources unless explicit local flags are set.

### ORBITAL SQLite Schema Or Extension

Status: not implemented.

Add or extend SQLite storage for ORBITAL source registry state, fetch runs, normalized items,
`orbital_events` or scoped clusters, source health, ranking explanations, safety and sensitivity
flags, local/global impact tags, retention purge evidence, and source verification metadata. Use
JSON-heavy columns and indexes for latest by scope, event ranking, source health, source family,
event type, source object or mission id, and `expires_at` purge. Do not store full article bodies,
bulk satellite catalogs, or long-term social archives by default.

### ORBITAL Fixture Pack

Status: not implemented.

Create local-only fixtures for SWPC alerts JSON, SWPC NOAA scales JSON, SWPC Kp JSON, SWPC aurora
JSON, JPL CNEOS close approach JSON, JPL CNEOS fireball JSON, JPL Sentry or Scout JSON, MPC MPEC
metadata, Launch Library upcoming launch JSON, Spaceflight News API JSON, NASA RSS, ESA RSS,
CelesTrak tiny allowlisted GP JSON, restricted Space-Track source-health state, reentry candidates
after verification, source-health states, disabled sources, stale sources, auth-required sources,
policy-blocked sources, and parser failures. Fixture ingest must not perform network calls and
must be safe for pytest.

### SWPC Alerts JSON Parser

Status: not implemented.

Build a fixture-first parser for SWPC alerts, watches, and warnings JSON. Preserve product id,
message type, NOAA scale when provided, issue time, valid period, severity terms, affected systems
when source-provided, source URL, and parser/source-health evidence. Handle missing fields and
schema changes fail-soft.

### SWPC NOAA Scales Parser

Status: not implemented.

Build a fixture-first parser for SWPC NOAA G/R/S scale JSON. Preserve geomagnetic, radio blackout,
and radiation storm scale state, observed or update time, source URL, and ranking features used for
official severity. Do not invent impacts beyond source-provided scale meanings.

### SWPC Kp And Aurora Fixture Parsers

Status: not implemented.

Build fixture-first parsers for SWPC planetary K-index, Boulder K-index, and OVATION aurora JSON
candidates. Preserve timestamp, Kp or aurora metadata, product source URL, local/regional aurora
interest evidence, and stale-source behavior. Keep local aurora tags configurable and disabled
until ORBITAL is explicitly enabled.

### JPL CNEOS Close Approach Parser

Status: not implemented.

Build a fixture-first JPL SSD/CNEOS close approach parser. Preserve object designation, approach
time, miss distance, lunar distance, relative velocity, estimated diameter when available, source
URL, official risk framing, and ranking evidence. Suppress distant low-risk objects unless
configured.

### JPL CNEOS Fireball Parser

Status: not implemented.

Build a fixture-first JPL/CNEOS fireball parser. Preserve event time, source-provided location,
altitude, velocity, energy, source URL, and official fireball evidence. Apply configured energy and
freshness thresholds so the dashboard does not become a firehose.

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

Status: not implemented.

Build a fixture-first RSS/Atom parser for verified NASA, JPL, NASA blog, Kennedy, Space Station,
Artemis, mission, and science feeds. Store headline metadata only, bound descriptions, preserve
agency/source family, mission labels where available, and filter routine feature stories unless
they have recent-signal value.

### ESA RSS Parser

Status: not implemented.

Build a fixture-first RSS/Atom parser for verified ESA feeds. Preserve headline metadata, source
URL, publication time, bounded description, source family, mission/safety/debris labels where
available, and source-health evidence. Keep ESA reentry and debris pages separate until endpoint
and policy review are complete.

### Official Launch Provider Source Verification

Status: not implemented.

Verify SpaceX, Blue Origin, Rocket Lab, ULA, Arianespace, ISRO, JAXA, CSA, ESA, CNSA, and other
official launch provider or agency pages before implementation. Confirm feed availability,
per-source selectors if no feed exists, robots/policy notes, refresh limits, parser stability,
and whether homepage extraction is allowed. Keep provider pages disabled by default.

### ISS And Crewed-Spaceflight Source Verification

Status: not implemented.

Verify NASA Space Station blog, NASA humans-in-space pages, Commercial Crew, ESA ISS, JAXA ISS,
CSA ISS, Spot the Station, and related crewed-spaceflight sources before implementation. Define
which signals are recent operational events, mission context, local sky-interest events, or
source-health-only references.

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

Status: not implemented.

Verify ESA reentry prediction source ownership, access method, policy notes, parser shape,
machine-readable endpoint availability, rate limits, uncertainty fields, and source-health states.
Do not scrape dashboards or complex pages until a safe machine-readable path is verified.

### NASA Orbital Debris Source Verification

Status: not implemented.

Verify NASA Orbital Debris Program, Quarterly News, reentry, and related debris/sustainability
sources before implementation. Define whether each source is source-health-only, RSS/metadata,
manual-review-only, or a parser candidate. Store metadata only and avoid debris fear-dashboard
behavior.

### ORBITAL Deterministic Event Correlation

Status: not implemented.

Implement deterministic ORBITAL event matching by source family, event type, time window, product
id, NOAA scale, Kp window, mission name, launch id, launch vehicle, payload, provider, NEO
designation, CNEOS event id, MPC designation, reentry object, safe satellite identifiers, fireball
time/location, normalized title tokens, and impact tags. Do not use LLMs, embeddings, or hidden
cloud calls.

### ORBITAL Deterministic Ranking

Status: not implemented.

Implement explainable ORBITAL ranking with recency, official severity, source diversity, temporal
proximity, operational impact, public impact, active alert or launch windows, source priority,
cluster size, local/global impact tags, duplicate-family penalty, stale-source penalty,
low-confidence penalty, low-public-value penalty, out-of-scope penalty, sensitivity penalty, and
rumor penalty. Store score features and ranking reasons in JSON evidence.

### ORBITAL Safety And Sensitivity Rules

Status: not implemented.

Add deterministic rules that block or de-emphasize tactical satellite tracking, restricted/auth
data, classified-activity inference, broad satellite catalog firehoses, Space-Track use without
credentials and terms review, social-only claims, launch rumors, NEO panic language, reentry panic
language, and debris fear-dashboard behavior. Prefer official public metadata and short retention.

### ORBITAL Local And Global Impact Tag Rules

Status: not implemented.

Define ORBITAL impact tags for `GLOBAL_IMPACT`, `NATIONAL_IMPACT`, `REGIONAL_IMPACT`,
`LOCAL_IMPACT`, `SKY`, `RADIO`, `GPS`, `AVIATION`, `SATELLITE`, `POWER`, `AURORA`, `CREWED`,
`NEO`, `REENTRY`, and `DEBRIS`. Keep canonical scope ORBITAL while allowing evidence-backed local,
regional, national, and global impact tags.

### ORBITAL UI Disabled States

Status: not implemented.

Replace ORBITAL placeholders only after storage/config support exists. Show honest states for
disabled, not configured, configured but disabled, never scanned, stale, policy blocked, parser
failed, auth required, rate limited, restricted source disabled, social disabled, homepage
extraction disabled, manual-review-only, token/account source not configured, and source-health
only. Do not show fake headlines.

### ORBITAL Source Health States

Status: not implemented.

Implement source health states for ORBITAL: `disabled`, `not_configured`,
`configured_never_run`, `healthy`, `stale`, `failing`, `parser_failed`, `policy_blocked`,
`robots_blocked`, `auth_required`, `rate_limited`, `unsupported`, `manual_review_only`,
`restricted_source_disabled`, `needs_terms_review`, `needs_scope_filter`, and
`sensitivity_blocked`. Surface these states in SYSTEM later and summarize them on ORBITAL.

### ORBITAL Evidence Drawer Contract

Status: not implemented.

Define and test evidence payloads for ORBITAL items and events. Include source ids, source names,
families, classes, URLs, official flags, published times, first/last seen, fetch run ids, parser
names, source health, ranking features, operational impact basis, public impact basis, source
diversity basis, local/global impact basis, sensitivity decision, retention expiration, matching
tokens, event type, event confidence, policy notes, low-public-value penalty, sensitivity penalty,
rumor penalty, out-of-scope penalty, mission/object labels, and safe satellite/reentry metadata.

### ORBITAL Official-Source Live Ingest Phase, Disabled By Default

Status: not implemented.

After fixtures, correlation, ranking, retention, source health, and tests exist, add opt-in live
ingest for one safe official ORBITAL source at a time. First candidates are SWPC alerts JSON, SWPC
NOAA scales JSON, SWPC Kp JSON, SWPC aurora JSON, JPL CNEOS close approach API, JPL CNEOS fireball
API, NASA RSS, ESA RSS, and JPL RSS after verification. Require explicit commands and no page-load
fetches.

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

Status: not implemented.

Document the later ORBITAL source verification workflow: confirm endpoint ownership, access method,
source terms, robots/policy notes, parser shape, auth/key requirements, rate limits, retention
sensitivity, privacy risk, verification status, source family, source class, orbital domain
filters, source-health behavior, tactical/sensitivity review, and whether the source is official,
provider, media, nonprofit, platform, restricted, open-data, or manual review only.

### Tests For No Page-Load External Fetches

Status: not implemented.

Add tests proving GET routes and page renders read SQLite/config only and never call ORBITAL
network fetchers. Include disabled/not configured/stale/failing/auth-required/policy-blocked,
restricted-source-disabled, social-disabled, homepage-extraction-disabled, source-health-only, and
parser-failed state tests for ORBITAL and SYSTEM source health.

### Tests For No Restricted Source Running Without Explicit Config

Status: not implemented.

Add tests proving Space-Track, CelesTrak restricted/sensitive candidates, conjunction-awareness
sources, restricted satellite sources, account-required sources, and policy-sensitive reentry or
debris candidates cannot run unless explicitly enabled in local config and policy-approved. Tests
should assert no network calls and clear disabled or auth-required source-health states.

### Tests For No API-Key Source Running Without Config

Status: not implemented.

Add tests proving NASA APIs, platform APIs, Space-Track, any future API-key source, and any
account/token source cannot run without explicit local configuration. Tests should assert clear
`auth_required`, `not_configured`, or policy-disabled source-health state and no network calls.

### Tests For No Tactical Satellite Tracking Output

Status: not implemented.

Add tests proving ORBITAL does not render tactical satellite tracking output, broad catalog
firehose rows, sensitive military satellite inference, private operator monitoring, or
object-by-object surveillance. The UI should show aggregate, source-backed event metadata and
honest disabled/sensitivity-blocked states instead.

## Solar System and Beyond Recent Signal Layer

Architecture reference:

- `docs/project/SYSTEM_SOLAR_SYSTEM_BEYOND_RECENT_SIGNAL_SOURCE_TARGETS_DESIGN.md`

### Resolve SYSTEM Naming Collision

Status: not implemented.

Decide whether app-health SYSTEM remains the source-health/app-health scope and Solar System and
Beyond becomes COSMIC, SOLAR, DEEP, DEEP SPACE, SKY, BEYOND, or another label. Do not implement tab
or route changes until this decision is explicit. If SYSTEM is repurposed, design app-health
migration to CONSOLE or HEALTH first.

### Decide Final UI Label For Solar System And Beyond

Status: not implemented.

Choose the final user-facing label and route plan for the Solar System and Beyond layer. Preserve
the existing `SYSTEM` app-health meaning unless the user explicitly requests a migration. Update
docs, tests, routes, templates, and source-health references only in the future implementation pass.

### Disabled-By-Default Solar System And Beyond Config

Status: not implemented.

Add a `solar_system_beyond:` or chosen-scope config tree that defaults to disabled. Include flags
for planetary science, interplanetary missions, exoplanets, telescope science, major space-agency
science, transients, GCN, TNS, gravitational waves, neutrino alerts, catalog archives, literature
metadata, social sources, and large archive queries. Reject social, auth-required, heavy archive,
literature, and homepage extraction sources unless explicit local flags are set.

### Solar System And Beyond Source Registry Design Implementation

Status: not implemented.

Implement the source registry from the design document with explicit `source_key`, `source_name`,
`source_family`, `source_class`, `scope`, `raw_url`, access kind, adapter type, refresh interval,
priority, official status, privacy risk, policy risk, parser risk, retention sensitivity,
verification status, source-health behavior, and future phase fields. Validate enum values and keep
every source disabled until explicitly configured.

### Solar System And Beyond SQLite Schema Or Extension

Status: not implemented.

Add or extend SQLite storage for source registry state, fetch runs, normalized items,
`solar_system_beyond_events` or scoped clusters, source health, ranking explanations, source naming
collision state, hype/suppression flags, archive query bounds, auth-required evidence, retention
purge evidence, and source verification metadata. Use JSON-heavy columns and indexes for latest by
scope, event ranking, source health, source family, event type, object/mission/transient ids, and
`expires_at` purge. Do not store full article bodies, papers, sky maps, science products, or bulk
catalog rows by default.

### Solar System And Beyond Fixture Pack

Status: not implemented.

Create local-only fixtures for NASA/JPL RSS, ESA RSS, Hubble/JWST RSS, NASA Exoplanet Archive tiny
metadata, MAST tiny metadata, PDS tiny metadata, GCN notice, GCN circular, ATel RSS, TNS
auth-required source health, GraceDB/LIGO public alert policy state, science news RSS, malformed
feeds, oversized payloads, source-health states, disabled sources, stale sources, auth-required
sources, heavy-archive-blocked sources, and hype-blocked items. Fixture ingest must not perform
network calls.

### NASA/JPL RSS Parser

Status: not implemented.

Build a fixture-first RSS/Atom parser for verified NASA and JPL science feeds. Preserve title, URL,
published time, bounded description, categories, source family, mission/object tokens where
available, and official science evidence. Store headline metadata only and do not fetch article
bodies.

### ESA RSS Parser

Status: not implemented.

Build a fixture-first ESA RSS parser after feed shape is verified. Preserve title, URL, published
time, source family, bounded description, science/mission labels where available, and official
agency evidence. Keep it disabled by default and metadata-only.

### Hubble/JWST RSS Parser

Status: not implemented.

Build a fixture-first parser for verified Hubble and JWST feeds. Preserve telescope, instrument
when source-provided, release id or URL, published time, bounded description, source family, and
telescope-science ranking evidence. Do not download images or data products.

### NASA Exoplanet Archive Tiny Metadata Parser

Status: not implemented.

Build a fixture-first parser for tiny allowlisted NASA Exoplanet Archive metadata responses. Preserve
planet name, host star, confirmed/candidate status when source-provided, discovery method, update
time, source URL or query evidence, row cap, and exoplanet ranking features. Reject broad catalog
downloads.

### MAST Tiny Metadata Parser

Status: not implemented.

Build a fixture-first MAST metadata parser for narrow configured queries only. Preserve mission,
collection, dataset id, object/target labels where provided, query bounds, row cap, source URL, and
no-science-product-download evidence. Keep live MAST disabled by default.

### PDS Metadata-Only Parser

Status: not implemented.

Build a fixture-first NASA PDS metadata parser for scoped collection/release checks. Preserve
collection id, mission, target body, release time, product-count metadata only if source-provided,
source URL, query bounds, row cap, and no-data-product-download evidence.

### GCN Notice Fixture Parser

Status: not implemented.

Build a fixture-first NASA GCN notice parser. Preserve notice type, event id, coordinates if
provided, event time, instrument, preliminary/update/retraction status, source URL, and transient
ranking evidence. Do not add Kafka or other dependencies without explicit approval.

### GCN Circular Source Verification

Status: not implemented.

Verify GCN Circular machine-readable access, policy terms, parser shape, rate limits, retention
needs, and source-health behavior before implementation. Store metadata only, preserve circular id,
event id, follow-up basis, source URL, and preliminary status.

### ATel RSS Parser

Status: not implemented.

Build a fixture-first Astronomers Telegram RSS parser. Preserve ATel number, title, URL, published
time, object/transient tokens, bounded description if allowed, source family, and preliminary
astronomy communication labels. Do not store full telegram bodies unless source policy and config
explicitly allow bounded storage.

### TNS Auth/Policy Design

Status: not implemented.

Review Transient Name Server access, auth/account requirements, API terms, attribution,
rate-limits, allowed fields, retention, and source-health behavior. Keep TNS disabled by default,
require credentials outside the repo, and represent missing credentials as `auth_required`.

### GraceDB/LIGO Public Alert Policy Design

Status: not implemented.

Review GraceDB/LIGO/Virgo/KAGRA public-alert access, auth requirements, API/client needs, terms,
rate limits, public alert fields, retraction handling, and sky-map download policy. Keep it disabled
by default, preserve preliminary/update/retraction state, and do not download sky maps unless a
future explicit config allows metadata-only references.

### Minor Planet Center Science-Context Source Verification

Status: not implemented.

Verify MPC MPEC, NEOCP, observations, orbit, and designation API candidates for endpoint ownership,
usage guidance, rate limits, parser shape, field stability, and ORBITAL overlap behavior. Keep
hazard/close-approach operations canonical in ORBITAL and use this layer only for science context.

### HEASARC Metadata Source Verification

Status: not implemented.

Verify HEASARC machine-readable metadata endpoints, usage policy, query shape, row caps, relevant
high-energy mission filters, source-health behavior, and retention before implementation. Keep
HEASARC disabled until narrow fixture tests exist.

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

Status: not implemented.

Implement deterministic matching by source family, time window, normalized title tokens, mission,
telescope, instrument, object name, solar-system body, exoplanet system, transient name, GCN event
id, ATel number, TNS name, GraceDB superevent id, coordinates, DOI/bibcode if enabled, archive
collection id, and dataset id. Do not use LLMs, embeddings, or hidden cloud calls.

### Deterministic Ranking For Official Science And Rarity

Status: not implemented.

Implement explainable ranking with recency, official science provenance, scientific significance,
source diversity, mission relevance, rarity, transient status, public interest, source priority,
cluster size, local/global/orbital impact tags, duplicate-family penalty, stale-source penalty,
low-confidence penalty, low-public-value penalty, hype penalty, out-of-scope penalty, and
archive-firehose penalty. Store score features and ranking reasons in JSON evidence.

### Hype And Speculation Suppression Rules

Status: not implemented.

Add deterministic rules that suppress or carefully label alien-life claims, UFO material,
sensationalized astronomy headlines, social rumors, image-only clickbait, generic astronomy
explainers, old papers resurfaced as new, unsupported "life found" language, and unreviewed
preprint hype if literature sources are ever enabled. Do not infer scientific meaning beyond source
metadata.

### Archive Firehose Blocking Rules

Status: not implemented.

Add deterministic blocking for broad SIMBAD, VizieR, Gaia, MAST, PDS, HEASARC, Exoplanet Archive,
ESO Archive, ESASky, ADS, TAP/ADQL, and catalog queries unless explicit source allowlists, row caps,
timeouts, retention, and query bounds are configured. Source health should report
`archive_firehose_blocked` or `heavy_archive_disabled`.

### UI Disabled States After Naming Decision

Status: not implemented.

After the user chooses a scope label, add UI states for disabled, not configured, configured but
disabled, never scanned, stale, policy blocked, parser failed, auth required, rate limited, social
disabled, heavy archive disabled, manual review only, hype blocked, archive firehose blocked, and
SYSTEM naming collision unresolved. Do not show fake headlines.

### Source Health States

Status: not implemented.

Implement source health states for the chosen Solar System and Beyond scope: `disabled`,
`not_configured`, `configured_never_run`, `healthy`, `stale`, `failing`, `parser_failed`,
`policy_blocked`, `robots_blocked`, `auth_required`, `rate_limited`, `unsupported`,
`manual_review_only`, `heavy_archive_disabled`, `needs_terms_review`, `needs_scope_filter`,
`naming_collision_unresolved`, `hype_blocked`, and `archive_firehose_blocked`. Surface these states
in app-health SYSTEM later and summarize them in the candidate scope.

### Evidence Drawer Contract

Status: not implemented.

Define and test evidence payloads for Solar System and Beyond items/events. Include source ids,
names, families, classes, URLs, canonical URLs, official flags, source published times, first/last
seen, fetch run ids, parser names, source health, ranking features, object/mission/telescope/
transient match basis, preliminary/confirmed/retracted status, archive query bounds, auth-required
status, retention expiration, policy notes, hype penalty, low-public-value penalty,
archive-firehose penalty, out-of-scope penalty, and no-data-product-download evidence.

### Official RSS Live Ingest Phase, Disabled By Default

Status: not implemented.

After fixtures, ranking, retention, and source health exist, add opt-in live ingest for one verified
official RSS feed at a time. First candidates are JPL RSS, ESA RSS, NASA RSS, Hubble/JWST RSS, and
ATel RSS if policy-safe. Require explicit command/config and no page-load fetches.

### Official Small API Live Ingest Phase, Disabled By Default

Status: not implemented.

After fixture tests and query caps exist, add opt-in small metadata API ingest for NASA Exoplanet
Archive, PDS, MAST, JPL SSD/MPC science context, HEASARC, or GWOSC one source at a time. Require
explicit allowlists, row caps, timeouts, no data-product downloads, no bulk catalog queries, and no
page-load fetches.

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

Status: not implemented.

Document the later Solar System and Beyond source verification workflow: confirm endpoint
ownership, access method, source terms, robots/policy notes, parser shape, auth/key requirements,
rate limits, retention sensitivity, privacy risk, verification status, object/mission/scope
filters, source-health behavior, and whether the source is official, archive, alert network,
publisher, public media, social, auth-required, heavy archive, or manual review only.

### Tests For No Page-Load External Fetches

Status: not implemented.

Add tests proving GET routes and page renders read SQLite/config only and never call Solar System
and Beyond network fetchers. Include disabled, not configured, stale, failing, auth-required,
policy-blocked, parser-failed, heavy-archive-disabled, social-disabled, hype-blocked,
archive-firehose-blocked, and naming-collision-unresolved state tests.

### Tests For No Heavy Archive Source Running Without Explicit Config

Status: not implemented.

Add tests proving SIMBAD, VizieR, Gaia, ESASky, ESO Archive, MAST, PDS, HEASARC, Exoplanet Archive,
ADS, TAP/ADQL, and catalog candidates cannot run unless explicitly enabled with local config,
allowlists, row caps, and query bounds. Tests should assert no network calls and clear disabled or
blocked source-health states.

### Tests For No Auth Source Running Without Config

Status: not implemented.

Add tests proving TNS, ADS, GraceDB if auth-required, Reddit, X, Bluesky, NASA API if key-required,
and any other token/account source cannot run without explicit local configuration. Tests should
assert clear `auth_required` or policy-disabled source-health state and no network calls.

### Tests For No Data Product Downloads

Status: not implemented.

Add tests proving MAST, PDS, HEASARC, Gaia, ESO Archive, ESASky, TAP/ADQL, GraceDB sky maps, and
other archive sources do not download science products, sky maps, papers, images, or article bodies
by default. Parsers should store metadata only and evidence should explicitly record no data product
downloads.

### Tests For No Alien-Life Or UFO Hype Leakage

Status: not implemented.

Add tests proving UFO content is out of scope, social-only alien-life claims are suppressed,
"life found" wording is blocked unless source metadata directly says it, generic hype is penalized,
and science journalism cannot become primary evidence without official or scientific convergence.

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

Status: not implemented.

Move hard-coded live threshold rules from `static/app.js` into config or a shared deterministic
rules module. Keep defaults conservative:

- Filesystem: root warning `>=85%`, critical `>=95%`; home warning `>=90%`, critical `>=95%`.
- CPU/RAM: CPU warning `>=75%`, critical `>=90%`; load/core warning `>=1`, critical `>=1.5`;
  MemAvailable warning `<15%`, critical `<5%`; memory PSI avg10 warning `>=10%`, critical `>=30%`.
- Network: route/address/carrier/error derived, not bandwidth-capacity derived.

Acceptance shape:

- Threshold values appear in evidence or help text.
- Tests cover the rule output independent of actual host metrics.

### Per-Interface Network Details And Capacity

Status: partially implemented.

Current live network readout shows LAN IP, gateway, WAN status, RX/TX rates, carrier, and
interface errors/drops. It does not normalize throughput by link capacity.

Future work:

- Read `/sys/class/net/<iface>/speed` when available.
- Show duplex where available.
- Show all non-loopback interfaces in a compact live table.
- Distinguish Wi-Fi link quality if available without sudo or new dependencies.
- Keep WAN/public IP external lookup disabled by default.

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

Improve change detection:

- Interface appeared/disappeared.
- Default route changed.
- DNS changed.
- Failed service set changed.
- Filesystem usage crossed threshold.
- Kernel/OS/session changed.
- Tool versions changed.

Each change should link to the evidence section that proves it.

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
