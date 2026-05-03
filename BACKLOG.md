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
- The local delta image is displayed from `console1706/static/codex-alert-delta.png`.

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

If scheduled news ingest is added, create a separate user-level `console-1706-news-scan.timer`.
Existing `console-1706-scan.timer` must not silently start external fetching. The news timer should
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
console-1706 must not make cloud calls or hidden network requests by default.

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
