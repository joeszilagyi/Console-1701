# Caretaking Log

## 2026-10-08 12:54 PDT - local per-interface network details

- Selected the high-priority per-interface network backlog item after confirming `/api/live`
  already collected every interface's counters but exposed only the primary link in the sensor UI.
- Added local read-only sysfs speed/duplex, per-interface IPv4, and `/proc/net/wireless` quality
  evidence to the live probe. An expandable INTERNAL network list shows every non-loopback link,
  sample-to-sample RX/TX/errors, and capacity-relative throughput where speed is known.
- Kept WAN lookup disabled, used DOM text nodes for interface data, added no service or package
  dependency, and kept default page loads free of external requests. Added mocked probe tests and
  a template assertion; BACKLOG now records this item as implemented.

## 2026-10-08 12:22 PDT - shared live sensor threshold rules

- Selected the high-priority live threshold task because CPU/RAM and filesystem decisions were
  hard-coded in `static/app.js`, making boundary behavior difficult to test independently.
- Moved those decisions and conservative limits into pure `static/live_rules.js`; the browser uses
  the returned state and derives green/help threshold text from the same values. The app still
  polls local `/api/live` and makes no new network calls or state writes.
- Added isolated Node-backed pytest boundary cases for each warning/critical cutoff, missing and
  invalid values, and script load order. Node is optional at runtime and no package is installed.
- Updated BACKLOG to mark the shared-module implementation complete while leaving optional
  user-configurable overrides deferred pending a concrete validation contract.

## 2026-10-08 12:13 PDT - public REGIONAL WSDOT highway alerts

- Selected the blocked WSDOT live-feed path. Official WSDOT docs show that its JSON Highway Alerts
  API needs an access code; the same official index links a public no-auth RSS feed. Verified the
  exact HTTPS RSS URL with a bounded no-redirect request: HTTP 200, `application/rss+xml`, 154,671
  bytes, 189 items, no validators. Kept the JSON API candidate disabled rather than inventing a
  credential or using an unverified endpoint.
- Added a separate disabled-by-default REGIONAL RSS registry entry and exact scope/id/URL/kind/parser
  allowlist. Its parser requires the official channel, numeric unique IDs, matching WSDOT link
  `refnum`, and update timestamps; removes embedded markup, bounds text, retains route/impact
  evidence, and uses official IDs for deterministic event clusters. An empty/malformed snapshot
  fails soft instead of retiring all active alerts.
- Added only this source to the on-machine 30-minute news config/timer. Explicit `news-scan`
  fetched and stored 189 REGIONAL items, with healthy source status; LOCAL page showed a WSDOT item
  under clearly labeled REGIONAL context and WSDOT source health. LOCAL WSDOT stays off because
  the RSS does not provide trustworthy Seattle-specific geography. Legacy per-alert links redirect
  to WSDOT's general alerts page, so a link-quality follow-up remains in BACKLOG.
- Added synthetic RSS, transport-policy, parser, event-ID, interval, and registry regressions.
  Ruff and 193 pytest tests passed. Repository defaults/new installs remain disabled; no external
  fetch runs during page loads or tests.

## 2026-10-08 11:51 PDT - live LOCAL page and snapshot lifecycle

- Selected the already verified LOCAL/REGIONAL Washington NWS alert and REGIONAL USGS earthquake
  sources. Corrected a live-snapshot lifecycle gap before scheduling them: after a successful HTTP
  200, items absent from that source's current parsed snapshot become inactive with retirement
  evidence, their active clusters are rebuilt, and orphaned LOCAL events become inactive. HTTP 304
  and failed parses leave the prior snapshot intact; reappearing items reactivate by URL identity.
- Added explicitly labeled REGIONAL items and source health to the LOCAL page, a 60-second
  SQLite-only visible-page refresh, and an accurate "Prior health at ingest" evidence label.
  Page loads still never fetch official feeds.
- Enabled only the three exact allowlisted sources in this machine's untracked standing config,
  each at a 30-minute interval aligned to the separately enabled 30-minute news timer. The first
  explicit scan found zero Seattle-matching NWS alerts, two REGIONAL NWS advisories, and zero
  in-region USGS earthquakes; all source states were healthy. Other candidate feeds stay off.
- Added lifecycle and page-render tests; Ruff and the full pytest suite passed (190 tests).
  Verified the running LOCAL page and next news timer firing. Repository defaults/new installs
  remain disabled; WSDOT and county endpoint signoff remains pending.

## 2026-10-08 11:20 PDT - first distinct REGIONAL USGS live feed

- Verified USGS's documented M2.5+ past-day GeoJSON summary endpoint and its live shape (HTTP 200,
  JSON `FeatureCollection`, `Last-Modified`, no redirect). Replaced the REGIONAL registry's docs-page
  placeholder with the exact feed URL and marked it verified; recorded endpoint, policy, filter,
  retention, failure, and opt-in signoff separately.
- Extended the official JSON allowlist only to REGIONAL `usgs_eq_geojson` at that URL. Live
  admission rejects configured magnitudes below the feed's 2.5 floor. The existing parser now
  excludes non-earthquake feature types before assigning earthquake event identity.
- Mocked tests cover altered URL/source/parser/verification, regional/HTTP/threshold gates, JSON
  transport, fixture event persistence, interval skip, and conditional `Last-Modified`/304. No live
  network call was added to pytest.
- A one-time explicit live scan returned HTTP 200, 19,438 bytes, healthy state, and zero events
  matching current REGIONAL bounds/magnitude. Its immediate repeat was interval-skipped. Disabled
  and removed the temporary opt-in afterward; the standing config and disabled news timer were
  unchanged. Live 304 and a live in-region earthquake remain unobserved; WSDOT signoff is next.

## 2026-10-08 11:11 PDT - scoped REGIONAL NWS live path

- Extended the exact verified Washington NWS URL allowlist to its disabled REGIONAL registry
  identity; REGIONAL live requests require `regional.enabled` plus the existing news, scope,
  source, and HTTP gates. No other URL or source family was added.
- Found that independent LOCAL and REGIONAL fetching could double-request the same NWS endpoint.
  Added per-scan response/error sharing, URL-level interval/backoff, and an unconditional first
  response when an enabled scope has no prior live success. Each scope still parses and records
  items, health, and event evidence independently.
- Mocked regressions cover both policy gates, one request for dual-scope ingest and 304, shared
  rate-limit failures, a newly enabled scope waiting for the URL interval, and a blocked LOCAL
  source not throttling an allowed REGIONAL source.
- A one-time REGIONAL-only operational scan returned HTTP 200, 8,185 bytes, and an ETag; it stored
  two Washington NWS items in separate official-ID clusters. A repeat was interval-skipped.
  Disabled and removed the temporary opt-in afterward; the standing config and disabled news
  timer were not changed. Live 304 remains unobserved; USGS/WSDOT endpoint signoff is still next.

## 2026-10-08 11:00 PDT - first controlled live NWS scan

- Selected the deployed NWS Washington alerts ingestion path for a one-time operational check.
  The standing web config and disabled news timer were left unchanged; a temporary console-config
  file explicitly enabled only the verified NWS source for `news-scan`.
- The fetch returned HTTP 200 with 8,185 bytes and an ETag. SQLite recorded one successful fetch
  run, healthy source state, zero Seattle-area matching items, and zero retention deletions. A
  second immediate command skipped the source under its ten-minute interval without another fetch.
- Disabled the temporary opt-ins, persisted the source as disabled, then removed the temporary
  file. The source remains off in the standing config; no live REGIONAL source was enabled.
- Found `news-scan --help` still claimed the command never makes network calls. Corrected its
  description to state the explicit allowlisted-HTTPS behavior. HTTP 304 and a live matching alert
  are not yet observed; the backlog and source signoff retain that limit.

## 2026-10-08 10:49 PDT - effective GitHub gate and REGIONAL event contract

- After PR #18's `tests-and-lint` check passed and the merged `main` push passed, updated the
  existing GitHub `main-protection` ruleset to target the default branch and require that check
  from the GitHub Actions app. Kept PR, deletion, and non-fast-forward rules; removed the dormant
  linear-history rule to preserve the repository's merge-commit practice. The effective branch
  rules endpoint now reports all four intended rules for `main`.
- Selected scoped `news_clusters` for REGIONAL events rather than adding a parallel table. USGS,
  NWS, and WSDOT fixture items now carry stable official-ID event keys, structured geography,
  confidence, matching, source, privacy, and public-impact evidence. Unverified RSS headlines are
  isolated by source and URL instead of being merged on similar title text.
- Rebuilds now record member IDs, source keys/families, duplicate-family counts, corroboration, and
  explainable regional ranking adjustments. A repeated scan recalculates dynamic factors without
  compounding them. REGIONAL NWS fixtures now require Washington zone/area evidence.
- Added parser/event, duplicate-family, ranking-idempotence, and REGIONAL source-health matrix
  regressions. Live REGIONAL ingest remains disabled and cross-family semantic/time-window matching
  remains in BACKLOG.

## 2026-10-08 10:41 PDT - add a read-only pull-request CI check

- Selected `.github/workflows/ci.yml` after the first official HTTP ingest slice: GitHub had no
  workflow or automated check, so the next feature expansion would still rely only on local tests.
- Added one GitHub-hosted Python 3.11 job for Ruff and pytest on PRs and pushes to `main`. Its token
  has read-only repository permission, checkout does not persist credentials, and it performs no
  application deployment, source fetching, or production state access.
- The existing `main-protection` ruleset still targets no branch at this commit. After the new job
  passes on its PR and lands on `main`, target the default branch, preserve current merge-commit
  history by dropping its dormant linear-history rule, and require the `tests-and-lint` check.
- The first GitHub run exposed a preexisting test that assumed Pacific local time; the application
  intentionally formats timestamps in the host's local timezone. Corrected the assertion to
  compare against the runner's local-time conversion, preserving the no-suffix contract.

## 2026-10-08 10:38 PDT - explicit official-feed boundary and first NWS transport

- Selected the foundational live-ingest blocker: the backlog called for public official feeds but
  the standing local-only notes did not distinguish those opt-in requests from cloud services.
  Clarified that only a separate explicit news command may request allowlisted official feeds;
  page loads, host scans, tests, SaaS, telemetry, LLM, and arbitrary URLs remain outside the bound.
- Verified the NWS Washington active-alert endpoint against NWS documentation and an HTTP HEAD
  response (200, GeoJSON, ETag, no redirect). Recorded the source signoff and changed the disabled
  registry seed to that exact area-filtered URL with verified status.
- Added default-off `allow_official_http` and an exact-source allowlist. The first transport has a
  bounded timeout/payload, no proxy inheritance or redirects, identifying User-Agent, conditional
  requests, interval/backoff, rate-limit status, and fail-soft source health. It releases the SQLite
  write transaction before network I/O and does not store raw responses.
- Added mocked first-fetch, 304, throttling, 429, default-block, URL-allowlist, and payload-cap
  tests. No production source or news timer was enabled.

## 2026-10-08 10:16 PDT - first REGIONAL USGS earthquake fixture slice

- Selected the first unimplemented official earthquake parser in the REGIONAL backlog after the
  operational recovery and GitHub catch-up. The USGS GeoJSON summary contract documents feature
  ids, magnitude, place, millisecond event time, official URL, felt/intensity fields, and point
  coordinates; this implementation uses a synthetic local fixture with that shape.
- Added `usgs_earthquake_geojson` to the REGIONAL registry and parser dispatch. The parser applies
  configurable coordinate bounds and minimum magnitude, preserves event, geography, source, and
  public-impact evidence, and rejects malformed feed shape or non-USGS event URLs.
- Added a capped `regional_seismic_boost` to stored deterministic ranking factors and reasons.
  This first factor does not claim to implement full REGIONAL event convergence or live ingest.
- Added parser, filter, registry, and SQLite ingest regressions. The fixture excludes one
  out-of-region earthquake and one below the magnitude threshold; no external fetch occurs.
- Extended the shared GET-route regression to render REGIONAL and read its scope API with a missing
  fixture path, proving that enabled REGIONAL sources do not trigger ingest on page load.
- Updated README and BACKLOG to mark the parser and REGIONAL ranking partially implemented while
  keeping radius-based geography, other regional fixtures, full ranking, and live ingest pending.

## 2026-10-08 10:11 PDT - recover live console and bound scan history

- Selected the running console installation and its scheduled test loop for recovery after a
  four-month gap. The May 11 web process returned HTTP 500 for `/` because old Python code was
  rendering newer templates; `/api/news/summary` was absent from that process. Scheduled scans
  had reported the same three SQLite lock failures since June 5.
- Created and integrity-checked a consistent 2,091,438,080-byte SQLite backup under
  `~/.local/state/console-1701/backups/` and preserved the local config there before maintenance.
- Added a suite-wide temporary-state fixture and committed the scanner's write transaction before
  executing repo tests. A regression proves a second SQLite writer can start at that point.
- Added 90-day scan-history retention for host, repo, test, interpretation, log, and scan-run rows.
  The latest host and per-repo evidence survives the cutoff. Normal scans prune a bounded batch;
  `prune-history` previews or applies all batches and can compact the database. Attention, handoff,
  and news retention remain separate.
- Stopped the web service and scan timer, removed expired rows after backing up, and vacuumed the
  database from 2,091,438,080 to 773,484,544 bytes. SQLite `PRAGMA quick_check` returned `ok`.
  Reinstalled current systemd units, restarted the web service and scan timer, and left the news
  timer disabled. The homepage, health, host, news summary, and LOCAL scope routes returned 200.
- Removed the missing `~/wiki` root, explicit repo, log, and project entries from the active and
  default config. The final live scan completed six repos with no warnings and recorded 159 passing
  tests in 2.626 seconds. Its previously red test-failure attention item resolved.
- Corrected the backlog's false claim that live API/RSS ingest exists. The news scanner still
  accepts only `file://` fixture inputs.
- During the initial diagnostic run before isolation was repaired, an existing test touched the
  live database and the scheduled disabled-news purge removed 49 expired fetch runs, four expired
  items, 58 expired health rows, and three expired local events. Those rows predated their configured
  retention cutoffs. The backup was taken after this event; no speculative restoration was made.
  The suite now redirects every test to temporary state.
- Verification: `159 passed`, Ruff clean, `git diff --check` clean, SQLite quick check `ok`, live
  scan complete with no errors, and current HTTP routes 200. The off-limits `Upkeeper.sh` symlink
  was not opened or modified.

## 2026-06-05 16:00 PDT - LOCAL source-health state follow-up

- Extended LOCAL source-health resolution so `rate_limited`, `robots_blocked`, and `unsupported`
  states are now classified explicitly instead of falling through to the generic
  `configured_never_run` bucket.
- Updated the LOCAL and SYSTEM source-state summaries so the new blocking states contribute to the
  failing counts and are visible in the scope readouts.
- Added regression coverage for the new health-state vocabulary and kept the local-only safety
  envelope intact: no live fetch changes, no network calls from the application itself, and no
  changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:54 PDT - LOCAL source-family weighting follow-up

- Added a capped `local_source_family_boost` to LOCAL event-correlation ranking so trusted
  official and local-news families contribute an explicit, explainable score term alongside the
  existing diversity and privacy adjustments.
- Covered the new factor with a direct ranking regression and a registry-backed NWS ingest
  assertion so the stored evidence path and the helper contract stay aligned.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:47 PDT - news item-detail adapter fallback follow-up

- Aligned the item-detail `source.adapter` fallback with the evidence block so both use the same
  adapter-derived value when the source policy does not carry one explicitly.
- Kept the item-detail API regression covered with the same focused tests and reverified the full
  suite after the payload shape cleanup.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:46 PDT - news item-detail adapter follow-up

- Restored the missing `source_adapter` argument when `get_news_item_detail` calls the shared
  source-state resolver, which was causing `/api/news/items/{item_id}` lookups to fail.
- Made the item-detail payload self-consistent by surfacing the resolved adapter in the source
  evidence block as well as the top-level source object.
- Extended the item-detail regression so the API now locks in the adapter field alongside the
  existing source-key and health evidence checks.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:41 PDT - dev_server python-venv failure follow-up

- Wrapped the dev-server virtualenv creation step so it now reports a clear
  `python3-venv`-style failure message instead of surfacing only the raw subprocess failure.
- Added a temp-tree regression that simulates a broken `PYTHON_BIN` venv creation path and asserts
  the helper exits with the new explicit error.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:40 PDT - install_user_service python preflight follow-up

- Added a `PYTHON_BIN` override and explicit preflight to `scripts/install_user_service.sh` so the
  installer fails fast with a clear message if Python 3 is missing.
- Kept the explicit repo-local venv binary workflow from the previous pass and extended the
  regression test to lock in the `PYTHON_BIN` contract alongside the existing service-install
  behavior.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:39 PDT - disabled news-scan retention follow-up

- Changed `run_news_scan` so a disabled recent-signal config still runs retention purge and records
  `news.last_purge` / `news.last_scan_result` evidence instead of returning before cleanup.
- Added a regression that seeds an expired item, disables ingest, and proves the disabled scan
  still clears stale rows and persists the purge summary.
- Rechecked the API wrapper behavior so `/api/news/scan` still reports `disabled` while the
  underlying purge path runs.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:36 PDT - install_user_service venv binary follow-up

- Removed activation-dependent `console-1701` and `python` calls from
  `scripts/install_user_service.sh` in favor of explicit repo-local venv binaries.
- Added preflight checks so the installer fails fast if the venv Python or CLI entry point is
  missing or not runnable after installation.
- Extended the systemd install-script regression test to lock in the explicit venv path contract
  and the existing disabled-news-timer behavior.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:34 PDT - scan_once CLI validation follow-up

- Hardened `scripts/scan_once.sh` so `--check` now verifies the resolved `console-1701`
  executable actually runs `--version` before reporting success.
- Added a runtime preflight so the scan helper fails with a clear message instead of trying to
  launch a broken CLI entry point.
- Added regression coverage for both the runnable and broken local CLI cases using a temp
  project tree copy of the helper script.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:25 PDT - regional fixture pack follow-up

- Updated the REGIONAL fixture pack note to reflect the concrete NWS, WSDOT, and regional RSS
  coverage that now exists in the shared local test corpus.
- Kept the remaining Washington-specific fixture file work visible instead of marking the fixture
  pack as fully complete before those source-specific files exist.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:24 PDT - regional WSDOT parser follow-up

- Added a REGIONAL ingest regression for `wsdot_traveler_api` so the Washington traveler-alert
  parser is now exercised through the registry-backed regional scan path.
- Marked the WSDOT Traveler API Fixture Parser backlog entry as partially implemented while
  keeping the remaining corridor-specific fixture and coverage work visible.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:24 PDT - regional NWS parser follow-up

- Added a REGIONAL ingest regression for `nws_active_alerts_wa` so the Washington NWS alert
  parser is now exercised through the registry-backed regional scan path.
- Marked the NWS Alert Parser For Washington backlog entry as partially implemented while keeping
  the remaining Washington-specific fixture and zone-coverage work visible.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:21 PDT - regional RSS parser follow-up

- Added `regional_news_rss` dispatch to the shared RSS parser path and covered it with a REGIONAL
  ingest regression that reuses the existing local RSS fixture corpus.
- Marked the REGIONAL fixture pack and regional news RSS parser backlog entries as partially
  implemented so the remaining Washington-specific fixture files and feed curation work stay
  visible.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:18 PDT - regional schema/state follow-up

- Exposed REGIONAL registry state through the shared news storage summary and confirmed the scan
  path persists REGIONAL registry rows into the existing SQLite registry table.
- Added a persistence regression so the REGIONAL registry entries survive a scan and show up in the
  storage summary without introducing a separate branch of storage logic.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:15 PDT - regional registry and config follow-up

- Added the first REGIONAL source registry implementation and the disabled-by-default regional
  config tree, with validation and defaults for the Washington / PNW layer.
- Added a short regional reference note so the new registry and config shape are documented in the
  repo alongside the code that now consumes them.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 15:09 PDT - LOCAL backlog catch-up follow-up

- Added backlog notes and supporting docs for LOCAL social policy, LOCAL news/blog RSS ingest,
  ArcGIS dashboard endpoint research, and the LOCAL official-source live ingest phase so the
  oldest unresolved LOCAL items are now described concretely instead of being left as vague
  pending notes.
- Surfaced manual-review-only source health in the LOCAL summary layer so policy-sensitive sources
  do not collapse into configured_never_run when they are intentionally not live-ingested.
- Kept the local-only safety envelope intact: no live fetch changes, no network calls from the
  application itself, and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 14:54 PDT - scope verification workflow documentation follow-up

- Added `docs/project/ORBITAL_SOURCE_VERIFICATION_WORKFLOW.md` and
  `docs/project/SYSTEM_SOLAR_SYSTEM_BEYOND_SOURCE_VERIFICATION_WORKFLOW.md` to capture the shared
  verification checklist, required registry fields, and honest source-health states for the two
  remaining scope families.
- Updated the ORBITAL and Solar System and Beyond backlog entries so they now point at the new
  workflow docs instead of leaving those follow-ups as vague pending notes.
- Added a short README note that the scope-specific verification workflow docs now cover
  REGIONAL, NATIONAL, GLOBAL, ORBITAL, and Solar System and Beyond guidance.
- Kept the local-only safety envelope intact: no live fetch behavior changes, no network calls,
  and no changes to the off-limits `Upkeeper.sh` file.

## 2026-06-05 14:50 PDT - source verification workflow documentation follow-up

- Added `docs/project/NEWS_SOURCE_VERIFICATION_WORKFLOW.md` to capture the shared verification
  checklist, required registry fields, and honest source-health states before any source is enabled.
- Updated README and the LOCAL backlog entry so the source verification workflow is now documented
  and the remaining per-source signoff work is called out explicitly instead of being left as a
  vague pending note.
- Kept the existing recent-signal safety envelope intact: no page-load fetching changes, no live
  network behavior, and no changes to the off-limits `Upkeeper.sh` file.
- Verified the docs/backlog edits with `git diff --check` before committing them.

## 2026-06-05 14:47 PDT - source audit metadata follow-up

- Expanded `console-1701 news-sources` so it now prints registry metadata for source family, class,
  verification status, and expected access kind alongside the existing policy and health details.
- Surfaced the same metadata in the scope-page source audit drawers so the browser and CLI now show
  matching audit context for the configured recent-signal sources.
- Updated README, CLI help, and BACKLOG wording so the source-audit workflow and remaining
  retention/config walkthrough gaps are documented in one place instead of being left as stale
  pending notes.
- Verified the touched paths with `./.venv/bin/ruff check console1701/cli.py` and
  `./.venv/bin/python -m pytest -q tests/test_news_ingest.py -k "news_sources_command_reports_policy_and_health"`
  plus `./.venv/bin/python -m pytest -q tests/test_app.py -k "news_scope_page_and_api_render_fixture_backed_state"`.

## 2026-06-05 14:44 PDT - recent-signal severity and topic-repetition follow-up

- Split LOCAL ranking into explicit source-severity and topic-repetition signals so official
  alerts no longer hide severity inside one collapsed boost and repeated local event tokens now
  feed the ranking explanation directly.
- Threaded the new local-event contract through storage and the drawer UI so the website now shows
  match score, topic repetition, and source severity for merged LOCAL events.
- Updated README and BACKLOG to match the current ranking contract and to retire the stale note
  that said source severity and topic repetition were still pending.
- Verified the touched news stack with `./.venv/bin/ruff check console1701 tests/test_news_ranking.py
  tests/test_news_ingest.py tests/test_app.py` and `./.venv/bin/python -m pytest -q tests/test_app.py`
  plus the focused `tests/test_news_ranking.py` and `tests/test_news_ingest.py` runs.

## 2026-06-05 09:17 PDT - LOCAL event correlation and privacy ranking follow-up

- Finished the interrupted LOCAL recent-signal follow-up by correcting a score-accounting bug in
  `apply_local_event_ranking_adjustments` so event bonuses and penalties are no longer added twice
  after being stored in ranking factors.
- Extended SPD blotter and SFD Fire 911 privacy evidence so stored rows now carry explicit
  `overdose_related` and `privacy_category` fields alongside the existing low-acuity redaction
  signals.
- Added direct ranking regression coverage for social-only and cross-source privacy suppression, and
  extended parser/ingest tests to assert the new privacy evidence fields.
- Updated BACKLOG status text so the LOCAL privacy-redaction entry reflects the implemented SPD/SFD
  parser coverage and current ranking behavior instead of stale pending notes.
- Cleaned the remaining lint/import tail in the same recent-signal stack and reverified with
  `./.venv/bin/ruff check console1701 tests` and `./.venv/bin/python -m pytest -q`
  (`140 passed`).

## 2026-05-12 07:41 PDT - recent-signal source transition history

- Extended recent-signal source status payloads so each source now carries short recent fetch-run
  and source-health histories rather than only the latest rows.
- Surfaced those recent transitions in the shared source audit drawers so scope and SYSTEM panels
  show how a source reached its current state.
- Added ingest/app coverage to assert that recent fetch/health history is present in the API payload
  and rendered page output.
- Updated README and BACKLOG to reflect that source audit evidence now includes recent transitions.
- Verified with `./.venv/bin/ruff check console1701 tests` and `./.venv/bin/python -m pytest -q`
  (`92 passed`).

## 2026-05-12 06:53 PDT - recent-signal evidence drawers on the website

- Extended the shared recent-signal panel partial so stored items, clusters, and source rows expose
  click-open evidence drawers instead of stopping at headlines and terse status lines.
- Surfaced ranking reasons, policy notes, retention expiry, fetch-run ids, raw fetch status, and
  source-health audit details directly in the LOCAL/REGIONAL/NATIONAL/GLOBAL/ORBITAL and SYSTEM
  panels.
- Added CSS for compact evidence grids/lists that fit the existing console styling and updated app
  coverage so the rendered scope page asserts drawer content.
- Updated README and BACKLOG to reflect that recent-signal evidence is now visible in the website,
  not only via API payloads.
- Verified with `./.venv/bin/ruff check console1701 tests` and `./.venv/bin/python -m pytest -q`
  (`91 passed`).

## 2026-05-12 06:43 PDT - recent-signal source-state contract and item evidence

- Normalized recent-signal source status into a derived contract across API, UI, and CLI so sources
  now report stable states such as `configured_never_run`, `policy_blocked`, `parser_failed`,
  `auth_required`, `stale`, and `healthy` instead of exposing only raw health rows.
- Extended the SYSTEM and scope panels with source-state counts, added per-source status notes to
  `console-1701 news-sources`, and kept no-fetch page-load behavior intact.
- Enriched stored item evidence and `/api/news/items/{id}` responses with source metadata, policy
  notes, fetch run ids, retention expiration, privacy/body-storage flags, and joined latest
  fetch/health context.
- Updated README and BACKLOG to reflect the new source-state and evidence-contract surfaces.
- Verified with `./.venv/bin/ruff check console1701 tests` and `./.venv/bin/python -m pytest -q`
  (`91 passed`).

## 2026-05-11 20:40 PDT - richer recent-signal purge audit evidence

- Expanded persisted `news.last_purge` runtime state to include before/after table counts and the cutoff timestamps used for item, fetch-run, and source-health retention.
- Surfaced the richer purge evidence in the SYSTEM recent-signal panel instead of only showing the purge timestamp.
- Extended app/news tests to verify persisted purge counts and summary exposure.
- Verified with `.venv/bin/ruff check .` and `.venv/bin/python -m pytest -q` (`89 passed`).

## 2026-05-11 20:31 PDT - recent-signal last scan result visibility

- Extended the recent-signal summary payload to expose the persisted `news.last_scan_result` runtime state alongside purge data.
- Surfaced the last recent-signal scan outcome in the SYSTEM panel so partial or successful explicit ingests are visible without opening SQLite manually.
- Added app coverage for summary API scan-result visibility and reverified with `.venv/bin/ruff check .` and `.venv/bin/python -m pytest -q` (`89 passed`).

## 2026-05-11 20:22 PDT - richer recent-signal source audit output

- Expanded `console-1701 news-sources` so each source reports item count, last success, last failure, next eligible ingest time, and the last recorded fetch timestamp instead of only a thin status line.
- Brought the same timing fields into the shared recent-signal source-status panels so the UI and terminal views stay aligned when auditing source health and scheduling.
- Verified with `.venv/bin/ruff check .` and `.venv/bin/python -m pytest -q` (`89 passed`).

## 2026-05-11 20:13 PDT - explainable recent-signal ranking factors

- Added a dedicated deterministic ranking helper for recent-signal items instead of leaving rank computation embedded as a mostly opaque integer.
- Ranking evidence now records explicit factors and reasons for source priority, recency, freshness, scope boost, official-tag boost, repeat observations, tag density, and prior source-health confidence.
- Updated the scoped news backlog state to reflect that generic deterministic ranking is partially implemented rather than absent.
- Verified with `.venv/bin/ruff check .` and `.venv/bin/python -m pytest -q` (`89 passed`).

## 2026-05-11 20:02 PDT - separate disabled news timer install path

- Added `systemd/console-1701-news-scan.service` and `systemd/console-1701-news-scan.timer` so recent-signal ingest can be scheduled separately from the host scan timer.
- Updated `scripts/install_user_service.sh` to install the news units but leave the news timer disabled by default, preserving the explicit opt-in boundary for recurring ingest.
- Updated README and BACKLOG to document the separate timer and the manual enable path.
- Added unit/install script tests covering the new files and the “installed but not enabled” behavior.
- Verified with `bash -n scripts/install_user_service.sh`, `.venv/bin/ruff check .`, and `.venv/bin/python -m pytest -q` (`89 passed`).

## 2026-05-11 19:50 PDT - recent-signal config warnings and system readiness

- Added derived recent-signal config warnings so SYSTEM can surface enabled-but-blocked fixture-phase sources, enabled scopes with no sources, disabled parent scopes, and missing auth material.
- Extended recent-signal summary output with those warnings and rendered them in the SYSTEM scope panel instead of leaving operators to infer misconfiguration from raw source rows.
- Added app coverage for SYSTEM warning rendering and summary API warning payloads.
- Verified with `.venv/bin/ruff check .` and `.venv/bin/python -m pytest -q` (`87 passed`).

## 2026-05-11 19:38 PDT - recent-signal explicit scan controls and retention evidence

- Added `POST /api/news/scan` with a separate lock from host scans so recent-signal ingest remains explicit and does not piggyback on page loads.
- Added a separate command-strip News ingest button that triggers the explicit API route and reports disabled/running states without hidden background fetching.
- Persisted `news.last_purge` and `news.last_scan_result` runtime state in SQLite `settings` so SYSTEM can show purge timing and recent ingest result details.
- Extended recent-signal summary data to include last purge evidence and SQLite DB size, then surfaced that in the SYSTEM recent-signal panel.
- Updated README and BACKLOG to reflect the explicit news scan API and the new retention/runtime evidence now visible in SYSTEM.
- Verified with `.venv/bin/ruff check .` and `.venv/bin/python -m pytest -q` (`86 passed`).

## 2026-05-11 19:10 PDT - recent-signal fixture ingest and scope UI follow-up

- Added explicit `console-1701 news-scan` fixture ingest and `console-1701 news-sources` source-status commands without introducing live external fetches.
- Implemented local fixture parsing for JSON, RSS, Atom, and homepage selector fixtures, plus SQLite writes for items, clusters, fetch runs, source health, and retention purge.
- Added source policy evaluation and exposed recent-signal read APIs for summary, per-scope views, source status, and item detail.
- Replaced non-INTERNAL placeholder scope bays with real OVERVIEW, scope, and SYSTEM recent-signal panels backed by SQLite/config only.
- Updated README and BACKLOG status to reflect fixture-only ingest, explicit commands, and current SYSTEM/source-health coverage.
- Verified with `.venv/bin/ruff check .` and `.venv/bin/python -m pytest -q` (`84 passed`).

## 2026-05-03 21:24 PDT - scripts/dev_server.sh serviceability review

- Selected `scripts/dev_server.sh` as the oldest eligible tracked tool/script file after excluding ignored generated artifacts; initial mtime was epoch `1777861238` (`2026-05-03 19:20:38 PDT`).
- Reviewed the file under P1, P3-P7, P9-P15, P17-P22. P2, P8, and P16 did not apply to the selected script/tool file.
- Fixed bootstrap supportability by replacing activation-dependent `python` and `console-1701` calls with explicit `.venv/bin/python` and `.venv/bin/console-1701` calls.
- Added `--check` validation for the venv Python and runnable CLI entry point so broken venv wrappers fail before serving.
- Added concise stderr diagnostics around venv creation, dependency installation, config initialization, and server startup.
- Verified with `bash -n scripts/dev_server.sh`, `scripts/dev_server.sh --help`, `scripts/dev_server.sh --check`, a temp-copy missing-Python failure check, `.venv/bin/ruff check .`, and `.venv/bin/python -m pytest -q`.
