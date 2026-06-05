# LOCAL Official-Source Live Ingest Phase

Use this note when planning the first opt-in live ingest path for LOCAL official sources.

## Current state

- Fixture parsing already exists for the main LOCAL official-source candidates.
- Deterministic correlation, ranking, retention, and tests already exist.
- The live ingest command path and per-source enablement flow are still absent.

## First candidate sources

- SFD Fire 911 Socrata
- NWS alerts
- King County Metro RSS
- WSDOT API

## Required behavior

- Keep every source disabled by default.
- Require an explicit command before live ingest runs.
- Do not trigger page-load fetching.
- Keep source-health states honest during rollout.

## Remaining work

- Define the live ingest command and per-source opt-in flow.
- Add per-source policy and timeout/backoff rules for the first official sources.
- Keep the live path small enough that each source can be validated independently.
