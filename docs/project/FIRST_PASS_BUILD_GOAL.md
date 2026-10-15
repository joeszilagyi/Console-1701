# Recent Signal First-Pass Build Goal

Status: active goal contract. Started 2026-10-15.

## Outcome

Deliver a reasonable first implementation of the currently specified Recent
Signal system across LOCAL, REGIONAL, NATIONAL, GLOBAL, ORBITAL, and Solar System
and Beyond. The target is working, truthful breadth before optional polish.

## First checkpoint

Read `AGENTS.md`, `BACKLOG.md`, the current design documents, and the existing
implementation. Create a tracked first-pass checklist that identifies the
backlog entries needed for a functional version of the specified system.
Include shared ingestion foundations, official-source adapters and fixture
parsers, scope rules, deterministic correlation and ranking, source health,
evidence, UI states, documentation, and required tests. Record why each open
entry outside the checklist is deferred. Freeze that checklist as the completion
target; do not silently shrink it to declare success.

## Work policy

- Work through the checklist in dependency order, beginning with shared
  foundations and the partially built LOCAL and REGIONAL paths.
- Implement coherent slices, verify each slice, update `BACKLOG.md` accurately,
  and keep durable progress with completed items, evidence, blockers, and the
  next item. Continue without waiting for a repeated "keep going" instruction.
- A reasonable first implementation has real data contracts, working paths,
  deterministic behavior, useful UI and evidence, and focused tests. It need
  not have exhaustive source coverage, speculative integrations, or extra
  visual polish. Never label fixture-only support as live ingestion or claim a
  source is verified without evidence.
- Preserve the local-only architecture and `AGENTS.md` constraints. Keep news
  disabled by default. Never fetch during page loads, host scans, or tests. A
  live news request must be a controlled `news-scan` against an explicitly
  enabled, exact-allowlisted public official source. Do not introduce cloud
  services, telemetry, hidden LLM calls, arbitrary crawling, or a frontend
  framework.
- Use focused branches and reviewable commits or PRs. Run relevant tests,
  Ruff, and other applicable checks for each slice. Do not bypass failing
  checks or branch protection. Do not merge a change that requires owner
  review or a new external authority decision. Continue with independent
  checklist work while another item is blocked.

## Completion and interruption

Complete the Goal only when every item on the frozen first-pass checklist is
implemented and verified. If a task cannot proceed, record the exact blocker,
evidence, and decision needed, then continue other executable tasks. If quota
or another interruption stops work, leave the progress record and worktree in
a state from which the same Goal can resume without reconstructing the plan.
