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
