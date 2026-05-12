# Caretaking Log

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
