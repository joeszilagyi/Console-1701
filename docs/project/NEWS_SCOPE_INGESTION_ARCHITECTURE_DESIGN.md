# News Scope Ingestion Architecture Design

## SECTION 1: Purpose

console-1706 is currently a local Debian machine console. It should remain that. The INTERNAL scope
is the primary machine instrumentation surface for this physical host: OS, kernel, session,
hardware, storage, network, services, processes, logs, power, thermal, evidence, and local work.

The proposed addition is a recent-signal layer across the existing scope tabs. The layer would ingest
short-lived metadata from explicitly configured public sources, normalize that metadata into local
SQLite, and render dense scope-specific panels. It should answer "what is going on" without turning
the project into a crawler, archive, cloud dashboard, or content mirror.

This is not:

- A web crawler.
- A search engine.
- A news archive.
- A social media scraper.
- A surveillance tool.
- A content mirror.
- A feed reader that stores full article bodies forever.
- A hidden LLM summarizer.
- A cloud dashboard.
- A replacement for the INTERNAL host dashboard.

This is:

- A local dashboard showing recent, configured, public-source signals.
- A scope-organized "what is going on" surface.
- A short-retention metadata database.
- A source-health and evidence-first system.
- A disciplined ingest layer with explicit configuration, rate limits, source provenance, and clear
  disabled states.

The core rule is simple: page rendering reads local SQLite and config state only. Future external
fetching belongs in explicit scanner or ingest commands, or explicit user-triggered actions. It must
never happen as a hidden side effect of visiting a page.

## SECTION 2: Current app fit

The current project already has most of the shape needed for this work:

| Existing part | Fit for recent-signal design |
| --- | --- |
| `/INTERNAL` | Already the real local machine telemetry dashboard. It should remain host-focused. |
| `/` | Currently routes to the OVERVIEW scope. This should become a cross-scope synthesis layer. |
| Scope tabs | The header already supports OVERVIEW, INTERNAL, LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, and SYSTEM. |
| Non-INTERNAL placeholder bays | `console1706/templates/index.html` currently renders Placeholder 1 through Placeholder 4 for non-INTERNAL scopes. Those are the natural insertion points for future signal panels. |
| SQLite schema pattern | Existing tables are simple, durable, and JSON-friendly. Extend that pattern instead of replacing it. |
| Scanner pattern | Current scans are explicit command-path work, not page-load work. News ingest should follow that pattern. |
| Safety strip | The visible local-only safety strip must remain truthful after news features exist. |

The root OVERVIEW page should not become a clone of INTERNAL. It should synthesize LOCAL, REGIONAL,
NATIONAL, GLOBAL, ORBITAL, and SYSTEM recent signals and only refer to INTERNAL when local machine
health needs attention.

The existing scanner should not silently become an external fetcher. The safer initial approach is a
separate `console-1706 news-scan` command and a separate disabled systemd user timer. If later
desired, `console-1706 scan` can optionally call news ingest only when `news.enabled` is true and the
behavior is documented.

## SECTION 3: Scope model

Scopes define what a signal means and where it belongs. A normalized item should have exactly one
primary scope and may have secondary tags.

| Scope | Meaning | Primary answer |
| --- | --- | --- |
| OVERVIEW | Cross-scope synthesis across LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, SYSTEM, and selected INTERNAL alerts. | "What should I know first?" |
| INTERNAL | Existing Debian host dashboard. | "Is this machine healthy?" |
| LOCAL | Seattle and immediate surrounding area. | "What nearby signals affect local life right now?" |
| REGIONAL | Washington, Puget Sound, Pacific Northwest, Cascadia, and West Coast where relevant. | "What regional signals matter?" |
| NATIONAL | United States level. | "What national signals matter?" |
| GLOBAL | World level. | "What global signals matter?" |
| ORBITAL | Space, sky, NASA, launches, astronomy, satellites, space weather, NEO, and related public signals. | "What is happening above the atmosphere and in space operations?" |
| SYSTEM | console-1706 app health and ingest health. | "Is the dashboard itself honest, fresh, and configured correctly?" |

### OVERVIEW

- Cross-scope synthesis.
- Shows the highest-priority current items from LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, and
  SYSTEM.
- Clearly labels source scope for every item.
- Does not bury urgent local, system, or machine-health alerts under broad global headlines.
- Elevates items with explicit reasons: official alert, severity, source priority, recency, repeated
  topic, stale source, or local/system impact.
- Answers: "what should I know first?"

### INTERNAL

- Existing Debian host dashboard.
- Focus remains host health, services, filesystem, CPU/RAM, network, hardware, evidence, alerts, and
  local repo/workflow status.
- General news must not dilute INTERNAL.
- INTERNAL may later expose a small pointer to SYSTEM if news ingest is stale or broken, but it should
  not become a news page.

### LOCAL

- Seattle and immediate surrounding area.
- Candidate source types: local official alerts, city open data, local weather and alerts, local
  major news, local subreddits only through compliant source access, transit, utilities, fire or
  police public bulletins if officially available, and civic service interruptions.
- Avoid private scanner feeds, login-only sources, and personally sensitive incident detail.
- Never infer or transmit precise location automatically. Location must be explicitly configured.

### REGIONAL

- Washington, Puget Sound, Pacific Northwest, Cascadia, and West Coast where relevant.
- Candidate source types: state agencies, regional news, weather, fire, smoke, earthquake alerts,
  emergency management, public health, transportation, energy or grid status if public, and regional
  subreddits only through compliant access.

### NATIONAL

- United States level.
- Candidate source types: major national news feeds, federal agencies, national weather, emergency,
  security, public-health alerts where public, and national-scale social signals only through
  compliant access.

### GLOBAL

- World level.
- Candidate source types: major global news feeds, international agencies, conflict, disaster,
  public-health alerts where public, and global trend signals only through compliant access.

### ORBITAL

- Space and sky layer.
- Candidate source types: NASA APIs, NASA/JPL APIs, NOAA/NWS/SWPC where appropriate, launch
  calendars if public and compliant, astronomy alerts, space weather, near-earth object feeds, major
  space news feeds, and lawful public orbital/satellite information.
- Do not fetch any ORBITAL source until explicitly configured and enabled.

### SYSTEM

- console-1706 application health.
- Source ingest status.
- Source stale state.
- Last successful fetch by scope and source.
- Disabled sources.
- Error rates.
- Retention purge state.
- DB size and source table counts.
- Config validation warnings.
- Evidence that no hidden external fetches happen on page load.

## SECTION 4: Bay model

The current non-INTERNAL pages have four placeholder bays. Future work should replace those with
real panels, but the four-bay shape is a starting layout, not a hard-coded permanent product model.

### OVERVIEW bays

| Bay | Name | Purpose |
| --- | --- | --- |
| 1 | Attention now | Highest-priority cross-scope items. Local, INTERNAL, and SYSTEM urgent items outrank distant headlines. Shows why each item is elevated, source, scope, source kind, and observed time. |
| 2 | Local and regional pulse | Seattle/local/regional headlines and alerts. Official alerts are visually separate from general news and community chatter. |
| 3 | National and global pulse | National/global headlines, trends, public alerts, and broad context. Labels source scope and kind clearly. |
| 4 | Orbital and source health | Space/weather/sky signals plus ingest/source health. Shows "not configured" honestly when sources are absent. |

### Scope page bays

For LOCAL, REGIONAL, NATIONAL, GLOBAL, and ORBITAL, a common four-bay model should work initially:

| Bay | Name | Purpose |
| --- | --- | --- |
| 1 | Top items | Current attention items for that scope. Shows ranking reason and evidence drawer. |
| 2 | Official sources / alerts | Agency, government, emergency, weather, transit, open data, or other official channels. |
| 3 | News sources / headlines | RSS, Atom, official news feeds, or configured headline sources. |
| 4 | Community and source health | Community/social metadata where compliant, plus source state, stale warnings, parser failures, and disabled states. |

Scope-specific variations are allowed. ORBITAL may split Bay 2 into NASA/JPL/SWPC and Bay 3 into
launch or astronomy feeds. LOCAL may split Bay 2 into alerts/transit/utilities. SYSTEM should use the
same dense visual grammar but its content should be source health, config, retention, and app state.

Empty states are part of the design:

- "No LOCAL sources configured."
- "LOCAL sources configured but disabled."
- "LOCAL sources have not been scanned yet."
- "LOCAL source fetch failed: see source health."
- "External news ingest disabled by config."

Never show fake headlines or demo content.

## SECTION 5: Source acquisition policy

### Required principles

1. Disabled by default.

No external source fetch should occur unless the user explicitly configures and enables sources.

2. No page-load fetches.

The web app must not fetch external URLs while rendering pages or servicing GET API reads. The UI
reads SQLite only.

3. Prefer stable public-source interfaces.

Source type priority:

| Priority | Source type | Notes |
| --- | --- | --- |
| 1 | Official local files or local generated data | No network. Best for tests and local integrations. |
| 2 | Official API | Prefer documented public APIs with terms and rate limits. |
| 3 | RSS/Atom feed | Stable metadata-focused format. |
| 4 | Official JSON endpoint | Use source-provided metadata mappings. |
| 5 | Official open-data portal | Use explicitly configured datasets only. |
| 6 | Sitemap metadata | Useful only when allowed and bounded. |
| 7 | Configured homepage headline extraction | Last resort, disabled unless explicitly allowed. |
| Out of scope | General crawling | Do not recursively crawl or discover arbitrary links. |

4. Source-policy awareness.

Each source needs recorded policy evidence:

- Source basis: official API, RSS/Atom, open data, sitemap, configured homepage extraction, local
  file, or other.
- Whether the source is enabled.
- Whether homepage extraction is allowed by config.
- Whether robots.txt was checked when applicable.
- Robots result when applicable.
- Source policy notes and operational caveats.
- Auth requirement status.

For homepage extraction, the design requires checking robots.txt where applicable, respecting
disallow rules, and recording the check. Robots.txt is not a permission system or legal shield. It is
a minimum operational courtesy and crawler-control signal. Source terms and access restrictions still
matter.

Source-policy references:

- https://www.rfc-editor.org/rfc/rfc9309.html
- https://www.rssboard.org/rss-specification
- https://www.sitemaps.org/protocol.html
- https://schema.org/NewsArticle

5. No login bypass.

Do not bypass login walls, paywalls, API auth, bot controls, platform restrictions, or rate limits.

6. No browser automation.

Do not use Selenium, Playwright, headless browsers, or GUI scraping for this project.

7. No full-text article archive by default.

Store metadata only: URL, canonical URL, title, bounded source-provided description when available,
timestamp, scope, tags, source id, fetch evidence, and ranking features. Do not store full article
bodies by default.

8. Short retention.

Default retention should be recent-only:

| Data | Default retention | Rationale |
| --- | --- | --- |
| News items | 7 days, configurable 3 to 14 days | Dashboard awareness, not archive. |
| Raw fetch diagnostics | 7 days or less | Enough to debug current breakage. |
| Source health history | 30 days | Enough to spot source reliability patterns. |
| Raw payload debug storage | Disabled by default, 6 hour TTL if enabled | Debug only, explicit and short-lived. |

9. Rate limiting.

Each source must have its own fetch interval, timeout, backoff, and error state. No tight loops. No
aggressive crawling. One broken source should not block other sources.

10. Conditional requests.

Future HTTP fetches should support ETag and Last-Modified where sources provide them. Store sent and
received validator evidence in `news_fetch_runs`.

11. Honest user agent.

Future HTTP fetches should use an explicit local user agent string such as
`console-1706 local recent-signal monitor`. If the user wants a contact note, it should be configured
explicitly. Do not impersonate browsers.

12. No content laundering.

Every UI item must retain source name, source URL, observed time, source kind, and evidence. The
system must not strip provenance or present source metadata as generated knowledge.

## SECTION 6: Platform-specific notes

These are design notes only. Do not implement these integrations in early phases.

### Reddit

- Treat Reddit as terms-sensitive.
- Prefer official Reddit API or officially supported feeds where appropriate.
- Do not scrape Reddit HTML to bypass API restrictions.
- Do not store long-term copies of Reddit content.
- Store only short recent metadata if permitted by the configured access method.
- References:
- https://redditinc.com/policies/developer-terms
- https://redditinc.com/policies/data-api-terms

### X/Twitter

- Treat X as API/terms-sensitive and likely auth/cost constrained.
- Do not scrape X HTML.
- Do not design around bypassing auth, rate limits, or paywalls.
- If used later, require explicit config and official API access.
- Reference:
- https://docs.x.com/x-api/introduction

### Bluesky

- Treat Bluesky/AT Protocol as a better candidate for public social signal access than X, but do not
  implement now.
- Design a source adapter that could use official AT Protocol/XRPC endpoints later.
- References:
- https://docs.bsky.app/docs/api/at-protocol-xrpc-api
- https://docs.bsky.app/docs/advanced-guides/atproto

### NASA and space

- NASA APIs and NASA/JPL APIs are strong ORBITAL candidates.
- ORBITAL source categories should include NASA public APIs, JPL/CNEOS, space weather,
  launch/news feeds, and public astronomy alerts.
- Do not fetch now.
- References:
- https://api.nasa.gov/
- https://ssd-api.jpl.nasa.gov/doc/index.php
- https://data.nasa.gov/

### NWS/weather

- NWS API is a strong LOCAL, REGIONAL, and NATIONAL alert candidate.
- Design this as disabled by default and location-configured.
- Never infer or transmit exact location automatically.
- Reference:
- https://www.weather.gov/documentation/services-web-api

### Seattle

- Seattle Open Data is a strong LOCAL source candidate.
- Use explicit configured datasets, not a general harvest of all datasets.
- References:
- https://data.seattle.gov/
- https://www.seattle.gov/tech/reports-and-data/open-data

### Major news homepages

- Prefer RSS/Atom or public feeds when available.
- Homepage parsing, if ever used, must be per-source configured, bounded, and conservative.
- Do not store article bodies.
- Do not crawl article links by default.
- Do not recursively follow links.
- Do not treat homepage HTML as stable. Extract with source-specific selectors only when explicitly
  configured.

## SECTION 7: Proposed configuration shape

Do not implement this config in this design phase. Future config should remain disabled by default.
`config.example.yml` should eventually include disabled examples and no live source enabled by
default.

```yaml
news:
  enabled: false
  retention:
    items_days: 7
    fetch_runs_days: 14
    source_health_days: 30
    raw_payload_debug_enabled: false
    raw_payload_debug_ttl_hours: 6
  fetch_policy:
    global_concurrency: 2
    default_timeout_seconds: 10
    default_interval_minutes: 30
    default_backoff_minutes: 120
    max_response_bytes: 1048576
    user_agent: "console-1706 local recent-signal monitor"
    page_load_external_fetches: false
    respect_robots_txt: true
    allow_homepage_extractors: false
  scopes:
    LOCAL:
      enabled: false
      label: "Seattle"
      sources: []
    REGIONAL:
      enabled: false
      label: "Washington / PNW"
      sources: []
    NATIONAL:
      enabled: false
      label: "United States"
      sources: []
    GLOBAL:
      enabled: false
      label: "World"
      sources: []
    ORBITAL:
      enabled: false
      label: "Orbital"
      sources: []
```

Example disabled source shapes:

```yaml
news:
  scopes:
    LOCAL:
      enabled: false
      label: "Seattle"
      sources:
        - id: seattle_open_data_example
          name: "Seattle Open Data example"
          scope: LOCAL
          kind: open_data_json
          enabled: false
          url: "https://data.seattle.gov/resource/example.json"
          homepage_url: "https://data.seattle.gov/"
          robots_url: "https://data.seattle.gov/robots.txt"
          interval_minutes: 60
          timeout_seconds: 10
          retention_days: 7
          tags: ["official", "local"]
          priority: 70
          parser: "socrata_json"
          evidence_notes:
            - "Disabled example only. Do not enable without choosing a real dataset."
        - id: local_file_fixture_example
          name: "Local fixture example"
          scope: LOCAL
          kind: local_file_json
          enabled: false
          url: "file://./tests/fixtures/news/local_items.json"
          interval_minutes: 0
          retention_days: 3
          tags: ["fixture"]
          priority: 10
          parser: "generic_json_items"
    NATIONAL:
      enabled: false
      sources:
        - id: homepage_example_disabled
          name: "Homepage headlines example"
          scope: NATIONAL
          kind: homepage_headlines
          enabled: false
          url: "https://example.invalid/"
          homepage_url: "https://example.invalid/"
          robots_url: "https://example.invalid/robots.txt"
          interval_minutes: 120
          timeout_seconds: 10
          retention_days: 3
          tags: ["news"]
          priority: 20
          parser: "homepage_selectors"
          selectors:
            item: "article"
            title: "h2, h3"
            url: "a"
            description: "p"
          evidence_notes:
            - "Homepage extraction requires news.fetch_policy.allow_homepage_extractors: true."
```

Source fields:

| Field | Purpose |
| --- | --- |
| `id` | Stable source key in config. |
| `name` | Human source label. |
| `scope` | One of LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL. SYSTEM is computed from app/source health. |
| `kind` | `rss`, `atom`, `api_json`, `open_data_json`, `homepage_headlines`, `local_file_json`, `local_file_rss`. |
| `enabled` | Per-source enablement. Defaults false. |
| `url` | Fetch URL or local file URL. Must be explicitly configured. |
| `homepage_url` | Human-readable source page. |
| `robots_url` | Robots location for homepage extraction checks where applicable. |
| `interval_minutes` | Minimum interval between fetch attempts. |
| `timeout_seconds` | Per-source timeout. |
| `retention_days` | Optional per-source retention override. |
| `tags` | User and source tags used for grouping/ranking. |
| `priority` | Deterministic ranking input. |
| `parser` | Parser adapter name. |
| `selectors` | Only for `homepage_headlines`, only when explicitly allowed. |
| `auth` | Future auth reference. Do not store secrets directly in the repo. Prefer environment variable names or local ignored config paths. |
| `evidence_notes` | User-visible notes explaining why this source is acceptable or constrained. |

Validation rules:

- `news.enabled` defaults false.
- Every scope defaults disabled.
- Every source defaults disabled.
- Unknown scopes are rejected.
- Unknown source kinds are rejected.
- Homepage extractors are rejected unless `allow_homepage_extractors` is true.
- `page_load_external_fetches` must remain false. If a config attempts true, treat it as invalid.
- Secrets must not appear in `config.example.yml`.

## SECTION 8: Proposed database model

Do not implement this schema now. Future schema should extend SQLite with JSON-heavy tables and
indexes that support recent dashboard reads, source health, retention, and dedupe.

### `news_sources`

Stores normalized configured source definitions at ingest time.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY | Internal source id. |
| `source_key` | TEXT NOT NULL UNIQUE | Stable config source id. |
| `scope` | TEXT NOT NULL | LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL. |
| `name` | TEXT NOT NULL | Human label. |
| `kind` | TEXT NOT NULL | Source kind. |
| `url` | TEXT | Fetch URL or local file URL. |
| `homepage_url` | TEXT | Human source URL. |
| `enabled` | INTEGER NOT NULL | 0 or 1. |
| `config_hash` | TEXT NOT NULL | Detects config drift. |
| `priority` | INTEGER NOT NULL DEFAULT 50 | Ranking input. |
| `tags_json` | TEXT NOT NULL DEFAULT '[]' | Tags. |
| `policy_json` | TEXT NOT NULL DEFAULT '{}' | Source policy evidence and notes. |
| `created_at` | TEXT NOT NULL | Local timestamp string. |
| `updated_at` | TEXT NOT NULL | Local timestamp string. |

Indexes:

- `idx_news_sources_scope_enabled (scope, enabled)`
- `idx_news_sources_source_key (source_key)`

### `news_fetch_runs`

Stores one row per source fetch attempt.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY | Fetch run id. |
| `source_id` | INTEGER NOT NULL | References `news_sources(id)`. |
| `started_at` | TEXT NOT NULL | Attempt start. |
| `finished_at` | TEXT | Attempt finish. |
| `status` | TEXT NOT NULL | `success`, `not_modified`, `failed`, `skipped`, `blocked_policy`, `blocked_robots`, `disabled`. |
| `http_status` | INTEGER | HTTP status when applicable. |
| `item_count` | INTEGER NOT NULL DEFAULT 0 | Parsed item count. |
| `error_class` | TEXT | Exception or policy class. |
| `error_message` | TEXT | Bounded error message. |
| `robots_allowed` | INTEGER | Null when not applicable. |
| `etag_sent` | TEXT | Conditional request evidence. |
| `etag_received` | TEXT | Conditional response evidence. |
| `last_modified_sent` | TEXT | Conditional request evidence. |
| `last_modified_received` | TEXT | Conditional response evidence. |
| `duration_ms` | INTEGER | Attempt duration. |
| `evidence_json` | TEXT NOT NULL DEFAULT '{}' | Fetch, parser, policy, and size-limit evidence. |

Indexes:

- `idx_news_fetch_runs_source_started (source_id, started_at DESC)`
- `idx_news_fetch_runs_status_started (status, started_at DESC)`

### `news_items`

Stores recent item metadata. It does not store full article bodies by default.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY | Item id. |
| `source_id` | INTEGER NOT NULL | References `news_sources(id)`. |
| `scope` | TEXT NOT NULL | Primary scope. |
| `canonical_url` | TEXT | Canonical URL if known. |
| `url` | TEXT NOT NULL | Source item URL. |
| `url_hash` | TEXT NOT NULL | Normalized URL hash for dedupe. |
| `title` | TEXT NOT NULL | Bounded title. |
| `description` | TEXT | Bounded source-provided description metadata. |
| `source_published_at` | TEXT | Source timestamp when available. |
| `first_seen_at` | TEXT NOT NULL | First ingest seen. |
| `last_seen_at` | TEXT NOT NULL | Most recent ingest seen. |
| `expires_at` | TEXT NOT NULL | Retention purge cutoff. |
| `source_kind` | TEXT NOT NULL | Kind copied for fast reads. |
| `tags_json` | TEXT NOT NULL DEFAULT '[]' | Tags. |
| `rank_score` | INTEGER NOT NULL DEFAULT 0 | Deterministic ranking score. |
| `trend_score` | INTEGER NOT NULL DEFAULT 0 | Deterministic clustering/repetition score. |
| `evidence_json` | TEXT NOT NULL DEFAULT '{}' | Provenance, fetch run id, parser, ranking factors. |
| `content_hash` | TEXT | Hash of bounded metadata, not full article body. |
| `status` | TEXT NOT NULL DEFAULT 'active' | `active`, `expired`, `hidden`, `superseded`. |

Indexes:

- `idx_news_items_scope_seen (scope, last_seen_at DESC)`
- `idx_news_items_source_seen (source_id, last_seen_at DESC)`
- `idx_news_items_expires_at (expires_at)`
- `idx_news_items_url_hash (url_hash)`
- `idx_news_items_rank_scope (scope, rank_score DESC, last_seen_at DESC)`

### `news_clusters`

Stores lightweight deterministic clusters for related items.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY | Cluster id. |
| `scope` | TEXT NOT NULL | Primary scope. |
| `cluster_key` | TEXT NOT NULL | Deterministic key from normalized URLs/title tokens. |
| `title` | TEXT NOT NULL | Representative title. |
| `representative_item_id` | INTEGER | Top item id. |
| `first_seen_at` | TEXT NOT NULL | First cluster observation. |
| `last_seen_at` | TEXT NOT NULL | Most recent cluster observation. |
| `item_count` | INTEGER NOT NULL DEFAULT 0 | Active item count. |
| `score` | INTEGER NOT NULL DEFAULT 0 | Deterministic score. |
| `tags_json` | TEXT NOT NULL DEFAULT '[]' | Cluster tags. |
| `evidence_json` | TEXT NOT NULL DEFAULT '{}' | Cluster factors and member ids. |

Indexes:

- `idx_news_clusters_scope_score (scope, score DESC, last_seen_at DESC)`
- `idx_news_clusters_key (cluster_key)`

### `news_source_health`

Stores source health observations.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY | Observation id. |
| `source_id` | INTEGER NOT NULL | References `news_sources(id)`. |
| `observed_at` | TEXT NOT NULL | Health observation time. |
| `state` | TEXT NOT NULL | `disabled`, `not_configured`, `never_run`, `healthy`, `stale`, `failing`, `blocked_policy`, `blocked_robots`, `auth_required`, `rate_limited`, `parser_failed`. |
| `last_success_at` | TEXT | Last successful fetch. |
| `last_failure_at` | TEXT | Last failed fetch. |
| `consecutive_failures` | INTEGER NOT NULL DEFAULT 0 | Failure counter. |
| `stale_after` | TEXT | Timestamp after which source is stale. |
| `message` | TEXT | Bounded human explanation. |
| `evidence_json` | TEXT NOT NULL DEFAULT '{}' | Latest source evidence. |

Indexes:

- `idx_news_source_health_source_observed (source_id, observed_at DESC)`
- `idx_news_source_health_state (state, observed_at DESC)`

### Dedupe and retention rules

- Prefer normalized canonical URL for dedupe.
- If canonical URL is absent, use normalized URL hash.
- If URL is weak or unstable, fallback to source id plus normalized title plus source timestamp bucket.
- Do not store full article bodies by default.
- Source-provided descriptions may be stored only as bounded metadata.
- Raw payload debug storage should not exist initially. If later needed, use a separate disabled table
  with strict TTL and explicit config.
- Retention purge must be deterministic and testable.
- Indexes must support latest by scope, latest by source, source health, `expires_at` purge, and
  dedupe by URL hash.

## SECTION 9: Proposed module layout

Do not implement these modules now. This layout keeps news ingestion separate from host probing and
web rendering.

```text
console1706/news/
  __init__.py
  models.py
  config.py
  source_policy.py
  fetcher.py
  parsers.py
  normalize.py
  ranking.py
  cluster.py
  retention.py
  storage.py
  scanner.py
```

| Module | Responsibility |
| --- | --- |
| `models.py` | Dataclass models for source definitions, fetched payload metadata, normalized items, clusters, and source health. Use stdlib dataclasses first; avoid new dependencies. |
| `config.py` | Read and validate news config from the existing config system. Enforce disabled-by-default behavior. |
| `source_policy.py` | Source enablement, kind validation, robots decision recording, homepage extraction allowance, auth requirement checks, and source compliance notes. |
| `fetcher.py` | Future HTTP fetch logic with timeouts, conditional headers, per-source intervals, backoff, response size caps, and no hidden page-load calls. |
| `parsers.py` | RSS/Atom parsing with stdlib XML first, JSON API mapping, and homepage selector parsing only when explicitly enabled. No broad crawling. |
| `normalize.py` | URL normalization, title cleaning, timestamp handling, tag normalization, scope mapping, and bounded field lengths. |
| `ranking.py` | Deterministic ranking only. No LLM. Inputs include recency, source priority, official-source boost, repeated topic signals, tags, and alert severity. |
| `cluster.py` | Lightweight deterministic clustering by normalized title tokens and canonical URLs. No embeddings or ML dependency. |
| `retention.py` | Purge expired items and old fetch runs/source health rows. |
| `storage.py` | SQLite reads and writes for sources, fetch runs, items, clusters, and source health. |
| `scanner.py` | Command-level ingest entrypoint, separate from web rendering. |

## SECTION 10: CLI and scheduler design

Do not implement commands now.

### `console-1706 news-scan`

- Runs configured enabled news sources once.
- Reads config.
- Applies source policy.
- Fetches only enabled sources.
- Stores fetch runs, items, clusters, and source health.
- Purges expired rows.
- Exits nonzero only for systemic failure such as unreadable config or unavailable DB.
- One broken source should create a failed source health row, not fail the whole command.

### `console-1706 news-sources`

- Validates configured sources.
- Prints enabled/disabled state.
- Prints source kind and policy basis.
- Prints next eligible fetch time.
- Prints last success, last failure, stale state, and parser status.

### `console-1706 scan`

- Existing host/repo scan must remain intact.
- Prefer keeping news ingest separate at first to reduce risk.
- If `scan` later calls news ingest, it must do so only when `news.enabled` is true, document that it
  may perform external fetches, and preserve per-source fail-soft behavior.

### systemd user timers

- Existing `console-1706-scan.timer` should not silently start external fetching.
- If a future news timer exists, it should be separate and disabled unless `news.enabled` is true.
- Proposed name: `console-1706-news-scan.timer`.
- It must be user-level systemd only, not root.
- README and config examples must make the external-fetch behavior obvious before enablement.

## SECTION 11: API design

Do not implement routes now. Future routes must read SQLite only and never fetch external URLs.

| Route | Purpose | Fetch behavior |
| --- | --- | --- |
| `GET /api/news/summary` | Cross-scope counts, top items, stale source count, and last ingest time. | SQLite only. |
| `GET /api/news/scopes/{scope}` | Latest items and clusters for one scope. Supports `limit`. | SQLite only. |
| `GET /api/news/sources` | Configured sources, enabled state, health state, last success, last failure, stale status. | SQLite only. |
| `GET /api/news/items/{item_id}` | One item with evidence. No full article body unless explicitly stored as bounded metadata. | SQLite only. |
| `POST /api/news/scan` | Optional future user-clicked scan trigger. | Explicit action only, obeys config and safety rules. |

API responses should distinguish these states:

- `disabled`
- `not_configured`
- `configured_but_never_run`
- `stale`
- `healthy`
- `failing`
- `blocked_by_policy`
- `blocked_by_robots`
- `auth_required`
- `rate_limited`
- `parser_failed`

GET routes must not kick off background work. If a UI button later calls `POST /api/news/scan`, the
button must be visibly user-triggered, rate-limited, and honest about failures.

## SECTION 12: UI architecture

Do not implement UI changes in this design phase.

### Root / OVERVIEW

- Replace Placeholder 1 through Placeholder 4 with real bays in a future phase.
- If `news.enabled` is false, show honest disabled/not configured panels.
- Never show fake headlines.
- Never show demo news.
- Use compact dense rows.
- Every item should show title, source, scope, observed time, and source kind.
- Use evidence drawers.
- Show source health where relevant.
- Show last ingest and next eligible ingest when known.
- Clearly label official alerts, news, community/social, and system/source-health signals.

### Scope pages

- LOCAL, REGIONAL, NATIONAL, GLOBAL, and ORBITAL should share a common scope-news template partial
  where possible.
- Each scope can have scope-specific labels and source groups.
- Empty states should be explicit:
- "No LOCAL sources configured."
- "LOCAL sources configured but disabled."
- "LOCAL sources have not been scanned yet."
- "LOCAL source fetch failed: see source health."

### INTERNAL

- Do not replace the current INTERNAL dashboard.
- INTERNAL may later show a small link to SYSTEM/source health, but do not pollute it with general
  news.

### SYSTEM

- Show ingest/source health.
- Show stale sources.
- Show failed parsers.
- Show retention state.
- Show DB size and source table counts.
- Show config warnings.
- Show evidence that no hidden external fetches happen on page load.

### Visual style

- Preserve the existing dense high-tech console style.
- No generic SaaS cards.
- No marketing dashboard.
- No huge whitespace.
- No fake animated loading states.
- No over-bright theme reset.
- Stay compatible with existing CSS and vanilla JS.

## SECTION 13: Ranking and synthesis

Ranking must be deterministic and explainable. No LLM calls. No hidden external summarization.

Potential ranking features:

| Feature | Effect | Evidence required |
| --- | --- | --- |
| Recency | Fresh items rank higher. | Source published time, first seen, last seen. |
| Source priority | Configured source priority affects score. | Source priority value. |
| Official-source boost | Official alerts can outrank general headlines. | Source kind and tags. |
| Scope priority | LOCAL, INTERNAL, and SYSTEM urgent items outrank distant broad headlines in OVERVIEW. | Scope and ranking reason. |
| User-pinned tags | User-configured tags can elevate items. | Tag list and config source. |
| Repeated topic | Similar titles across multiple sources boost trend score. | Cluster evidence and item count. |
| Alert severity | Source-provided severity boosts alerts. | Severity field and parser evidence. |
| Item freshness | Old items decay toward expiration. | Age and expires_at. |
| Source health confidence | Stale/failing sources reduce confidence. | Source health state. |
| Always surface group | Configured source group can reserve display space. | Source config evidence. |

The architecture must avoid pretending to understand article content beyond available metadata. It can
cluster and rank headlines, but it must not invent summaries.

Allowed deterministic summary examples:

- "3 local sources are leading with transportation disruptions."
- "2 orbital sources posted solar/weather items."
- "LOCAL has one official alert and five fresh headlines."
- "GLOBAL source health stale, last successful fetch 9h ago."

These summaries should be computed from source metadata, source tags, parser fields, and title token
clusters. They should not be hidden LLM prose.

## SECTION 14: Evidence model

Everything shown must be traceable.

For each item, evidence should include:

- Source name.
- Source id.
- Source kind.
- Configured URL.
- Item URL.
- Canonical URL if known.
- First seen.
- Last seen.
- Source published timestamp if available.
- Fetch run id.
- Parser used.
- Ranking factors.
- Retention expiration.
- Policy notes.
- Robots result when applicable.
- Error if partial.

For each source, evidence should include:

- Enabled/disabled.
- Last attempted fetch.
- Last successful fetch.
- Last failure.
- Next eligible fetch time.
- Consecutive failure count.
- Latest HTTP status if applicable.
- Stale threshold.
- Policy block status.
- Auth requirement status.

For each panel, evidence drawers should show why an item or state appears:

- "Elevated because source tag `official` and severity `warning`."
- "Demoted because source health is stale."
- "Hidden because source disabled."
- "Blocked because homepage extractor is disabled."
- "Blocked because robots check disallowed configured homepage path."

## SECTION 15: Retention and non-archive policy

This system is for recent awareness, not long-term saving.

Default retention:

| Data class | Default | Configurable range |
| --- | --- | --- |
| News items | 7 days | 3 to 14 days |
| Fetch runs | 14 days | 1 to 30 days |
| Source health rows | 30 days | 7 to 90 days |
| Raw payload debug | Disabled | If enabled, 6 hours by default |
| Social metadata | 3 days by default | Shorter than general news unless source terms allow otherwise |

Rules:

- Do not store full text by default.
- Do not store social-media content long term.
- Do not store large raw payloads.
- Retention purge must run during every ingest command.
- Retention purge should be separately testable.
- SYSTEM should expose retention policy and last purge state.
- The database should stay modest enough for a local SQLite app.

## SECTION 16: Security, privacy, and local-only constraints

Safeguards:

- No external fetch unless `news.enabled` is true and the source is enabled.
- No external fetch on page load.
- No hidden LLM calls.
- No telemetry.
- No precise location inference.
- No transmission of machine identifiers.
- No secrets in repo.
- API tokens, if ever needed, should be read from environment variables or a local config path
  excluded from git.
- Config examples must not include real tokens.
- Source URLs must be allowlisted by config.
- No recursive crawling.
- No shelling out to `curl` for fetches in the app.
- Use Python HTTP facilities later if implemented.
- Use timeouts.
- Bound response sizes.
- Record failures.
- Fail soft per source.
- One broken source should not break the dashboard.
- Page loads must read local SQLite and config state only.
- Bind behavior remains `127.0.0.1:1706`.

Location rules:

- LOCAL and weather sources must require explicit configured location.
- Do not infer exact location from IP, browser state, Wi-Fi, GPS, timezone, or machine metadata.
- If a configured location is sent to a public API, evidence must show what was sent.

Secrets rules:

- Do not put tokens in `config.example.yml`.
- If future auth is needed, config should reference environment variable names or ignored local files.
- SYSTEM should report missing auth as `auth_required`, not attempt fallback scraping.

## SECTION 17: Legal and policy risk notes

This section is operational guidance, not legal advice.

- The fact that a URL is publicly reachable does not mean it should be ingested.
- Prefer APIs, RSS/Atom, open-data portals, or explicit public feeds.
- Homepage headline extraction must be configured per source and conservative.
- Do not bypass auth, login, paywalls, rate limits, or bot controls.
- Social platforms are terms-sensitive.
- Store provenance and use short retention.
- Use source-policy notes so the user can audit why a source was considered acceptable.
- Robots.txt is a crawler-control signal and minimum courtesy, not a complete permission model.
- Terms, access restrictions, and platform policies still matter.

Reference URLs for future implementers to review before source adapters:

- https://www.rfc-editor.org/rfc/rfc9309.html
- https://redditinc.com/policies/developer-terms
- https://redditinc.com/policies/data-api-terms
- https://docs.x.com/x-api/introduction
- https://docs.bsky.app/docs/api/at-protocol-xrpc-api
- https://api.nasa.gov/
- https://www.weather.gov/documentation/services-web-api
- https://data.seattle.gov/
- https://www.rssboard.org/rss-specification
- https://www.sitemaps.org/protocol.html
- https://schema.org/NewsArticle

Additional platform references:

- https://docs.bsky.app/docs/advanced-guides/atproto
- https://ssd-api.jpl.nasa.gov/doc/index.php
- https://data.nasa.gov/
- https://www.seattle.gov/tech/reports-and-data/open-data

## SECTION 18: Implementation phases

### Phase N0: design only

- This task.
- Create this design document.
- Update BACKLOG.
- No runtime behavior change.
- No network.
- No dependencies.
- No commit.

### Phase N1: config and schema scaffolding

- Add disabled-by-default config schema.
- Add SQLite tables and migration/init path.
- Add storage helpers that return disabled/not-configured states.
- Add tests proving disabled by default.
- No external fetch.

### Phase N2: local fixture ingest only

- Add parsers and storage using local test fixtures only.
- No network.
- Tests for RSS, JSON, homepage fixture parsing, dedupe, retention, and ranking.
- Homepage fixture parsing must not imply live homepage extraction is enabled.

### Phase N3: UI disabled and fixture-backed states

- Add root/scope panels that show disabled/not configured states.
- Optionally render local fixture state in tests.
- No live external fetch.
- No fake headlines.

### Phase N4: explicit enabled HTTP fetch for safe official APIs/RSS only

- Add HTTP fetcher with timeout, rate limit, conditional request, and response size cap.
- Start with one or two official public source examples only when configured.
- No homepage parsing yet.
- Tests use mocked HTTP or local test server, not live network.

### Phase N5: source health and SYSTEM page

- Show source health.
- Show staleness.
- Show fetch failures.
- Show retention and last purge.
- Show DB size and source table counts.

### Phase N6: homepage extraction adapters

- Only after RSS/API foundation is tested.
- Disabled unless `allow_homepage_extractors` is true.
- Per-source selectors only.
- No recursive crawling.
- Robots and policy evidence required.

### Phase N7: social source adapters

- Bluesky first if desired due to documented AT Protocol.
- Reddit and X only with explicit compliant access method.
- No scraping to bypass platform APIs.

### Phase N8: richer deterministic clustering and synthesis

- No LLM.
- Deterministic cluster and rank explainability.
- OVERVIEW can synthesize across scopes using stored item metadata and source health only.

## SECTION 19: Testing strategy

Future phases should add tests without relying on live external services.

### Config tests

- News disabled by default.
- Source disabled by default.
- Invalid scope rejected.
- Invalid source kind rejected.
- Homepage extraction rejected unless explicitly allowed.
- No secrets in `config.example.yml`.
- `page_load_external_fetches: true` rejected.

### DB tests

- Schema creation.
- Indexes exist.
- Dedupe works.
- Retention purge works.
- Source health updates work.
- Disabled/not-configured read helpers work with empty tables.

### Parser tests

- RSS fixture.
- Atom fixture.
- JSON API fixture.
- Homepage fixture with source-specific selectors.
- Malformed feed fails soft.
- Huge payload blocked or truncated.
- Bounded description/title lengths.

### Policy tests

- Disabled source does not fetch.
- Not configured state is visible.
- Robots disallow blocks homepage extraction.
- API/RSS policy states recorded.
- Auth-required source does not run without config.
- Homepage extractor blocked when global flag is false.

### Fetcher tests

- Timeout.
- Response size cap.
- ETag and Last-Modified.
- Per-source interval.
- Backoff after failure.
- One source failure does not stop others.
- GET API routes do not invoke fetcher.

### Ranking tests

- Recency.
- Official source boost.
- Source priority.
- Cluster count.
- Explainable score output.
- Stale source confidence penalty.

### API tests

- Routes read SQLite only.
- Disabled/not configured/stale/failing states are distinct.
- No external fetch on GET.
- Limits are enforced.
- Unknown scope returns a clear client error.

### UI tests

- No fake data.
- Empty states are clear.
- Scope labels are correct.
- Evidence drawers contain source metadata.
- OVERVIEW labels each item's source scope.
- INTERNAL dashboard remains host-focused.

### Safety tests

- No page-load network calls.
- No hidden LLM calls.
- No telemetry.
- No package install.
- No sudo.
- No shelling out to `curl`.

## SECTION 20: Backlog update requirements

This design task adds a BACKLOG section named "Scoped Recent Signal / News Ingestion". The backlog
items should remain pending until implemented in later phases. Each item should use
`Status: not implemented` until a concrete change lands.

Required backlog items:

- Disabled-by-default news config.
- News SQLite schema.
- Local fixture ingest harness.
- Parser tests.
- Source policy and robots evidence layer.
- Retention purge.
- Deterministic ranking.
- Scope page UI.
- OVERVIEW synthesis bays.
- SYSTEM source health bay.
- Official API/RSS first live ingest.
- Homepage extractor, later and disabled.
- Social adapters, later and terms-sensitive.
- Documentation update.
- Systemd user timer, separate and disabled by default.

If future design or implementation discovers a risk or follow-up that is not completed in the same
turn, update BACKLOG before finishing, per AGENTS.md.

## SECTION 21: Non-goals

- No general web crawler.
- No search index of the internet.
- No article body archive.
- No long-term social-media archive.
- No hidden LLM summarization.
- No cloud dashboard.
- No React, Tailwind, Electron, or frontend rewrite.
- No scraping behind login.
- No bypassing API restrictions.
- No aggressive polling.
- No external fetch from page render.
- No replacing INTERNAL host dashboard.
- No automatic enablement of external sources.
- No source guessing from the user's browser history or machine data.
- No source guessing from local machine identifiers.
- No exact-location inference.
- No recursive link following.
- No fake demo headlines.

## SECTION 22: Quality bar

The implementation bar for future phases:

- Blunt, inspectable behavior.
- Disabled by default.
- SQLite-first reads.
- Explicit command-path ingest.
- Deterministic ranking and explanations.
- Evidence attached to every displayed claim.
- Small schema changes with tests.
- No live network in tests.
- No new dependency unless there is a specific, reviewed reason.
- Fail soft per source.
- Keep INTERNAL host dashboard primary for machine state.
- Keep the safety strip truthful.

Phase N1 should be implementable from this document without recovering chat history. It should add
only config/schema scaffolding and tests proving disabled behavior. It should not fetch external
sources, change UI behavior, or enable any source by default.
