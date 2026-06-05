# Caretaking Log

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
