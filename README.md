# console-1706

`console-1706` is a local-only homepage for a Debian laptop. It scans the physical host first, then configured local repos, selected logs, and durable SQLite history. It turns those facts into plain-English operational readouts with evidence underneath.

Main goal:

```text
Tell me what the hell is going on with this Debian machine, plus my local repos, logs, workflows, and Codex-assisted work, in human language, with evidence underneath.
```

It is not a Scrum dashboard, Jira clone, productivity score, GitHub dashboard, raw git status dump, fake real-time wallboard, telemetry agent, or cloud monitor. It does not use themed product labels. The UI is a dense full-screen local machine console with dark technical paneling, compact telemetry modules, and collapsed click-open evidence drawers.

## Install on Debian 13

Install local dependencies:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git sqlite3 ripgrep jq curl xdg-utils
```

Install the app from the repo:

```bash
cd /path/to/console-1706
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Initialize config, scan once, and run the server:

```bash
console-1706 init-config
console-1706 scan
console-1706 serve
```

Open:

```text
http://127.0.0.1:1706
```

Manual browser command:

```bash
xdg-open http://127.0.0.1:1706
```

## One-Command User Service

From the repo root:

```bash
./scripts/install_user_service.sh
```

The script creates `.venv`, installs the package, creates config/state paths, installs systemd user units, starts the web service, enables the 30-minute scan timer, runs one initial scan, and prints the local URL.

Check service state:

```bash
systemctl --user status console-1706.service
systemctl --user status console-1706-scan.timer
curl -fsS http://127.0.0.1:1706/api/health
```

## Paths

Config:

```text
~/.config/console-1706/config.yml
```

State:

```text
~/.local/state/console-1706/
```

Database:

```text
~/.local/state/console-1706/console.sqlite
```

Handoff packets:

```text
~/.local/state/console-1706/handoffs/
```

## How Scans Work

The scanner is separate from the web app:

```bash
console-1706 scan
```

Scan sequence:

1. Load config.
2. Create state directories if missing.
3. Open SQLite with WAL and busy timeout.
4. Probe the local host with safe procfs/sysfs reads and timeout-protected read-only commands.
5. Store a host snapshot.
6. Discover repos from `explicit_repos` and `repo_roots`.
7. Probe each repo with safe local Git commands and timeouts.
8. Probe configured logs.
9. Detect tests, but do not run them unless explicitly allowed.
10. Store repo/log/test snapshots.
11. Run deterministic interpretation rules.
12. Upsert attention items with fingerprint dedupe.
13. Mark absent attention items resolved.

## Host/System Probe

The first screen is now about the Debian machine, not Git. A normal scan records one host snapshot with:

```text
identity
os
kernel
session
debian
cpu
memory
storage
filesystems
network
power
thermal
services
processes
dev_tools
logs
health
evidence
probe_errors
```

Safe local sources include:

```text
/etc/os-release
/proc/uptime
/proc/meminfo
/proc/cpuinfo
/proc/loadavg
/proc/mounts
/sys/class/dmi/id
/sys/class/net
/sys/class/power_supply
/sys/class/thermal
```

Optional commands are used only if present and every command has a timeout:

```text
uname
hostnamectl
timedatectl
lscpu
lsblk -J
df -PT
ip -j addr
ip -j route
resolvectl status
nmcli
systemctl --failed
systemctl --user --failed
ps
journalctl
git --version
python3 --version
node --version
npm --version
sqlite3 --version
rg --version
```

Missing commands fail soft and are recorded as unavailable in evidence.

The first diagnostic bay row is standards-aligned and evidence-first:

```text
B2 Services / systems: systemd state, failed units, critical units, and unit evidence.
B3 Debian: release, dpkg package count, held packages, apt history, sources, and reboot flag.
B4 Hardware: DMI model, CPU, memory, storage pressure, power, thermal, and primary link facts.
```

Each bay uses click-open evidence drawers instead of invented charts.

The live sensor lane is updated in-place from `/api/live`. It uses only local kernel and filesystem
surfaces, including `/proc/stat`, `/proc/loadavg`, `/proc/meminfo`, `/proc/net/dev`,
`/proc/net/route`, `/proc/pressure/*`, `/sys/class/net`, `/sys/class/thermal`, and
`shutil.disk_usage()`.

Sensor colors are intentionally simple and transparent:

```text
System: latest scan state OK / CAUTION / BROKEN / UNKNOWN.
Network: green when a local interface, LAN address, and gateway are present; yellow for missing route/address, carrier down, or interface errors/drops; red when no usable non-loopback local path is visible.
CPU/RAM: yellow at CPU >=75%, load/core >=1, MemAvailable <15%, memory PSI avg10 >=10%, or CPU PSI avg10 >=20%; red at CPU >=90%, load/core >=1.5, MemAvailable <5%, or memory PSI avg10 >=30%.
Filesystem: yellow at root >=85%, home >=90%, or I/O PSI avg10 >=10%; red at root/home >=95% or I/O PSI avg10 >=30%.
```

Network throughput bars are live activity meters, not health thresholds, because console-1706 does
not know WAN circuit capacity and does not perform external probes by default.

Failed service alerts name the failed unit whenever `systemctl --failed` exposes it. The probe also records bounded `systemctl show` diagnostics and a limited recent `journalctl -u ...` sample when readable, so the alert can explain the local state, result, exit status, description, and most recent log hint without requiring sudo.

Host alert rows include an explicit Codex terminal action. Clicking it writes a bounded prompt file
under console-1706 state and asks the local desktop terminal emulator to start an interactive
`codex` session with that scenario. The web process does not run Codex hidden in the background; it
only attempts the terminal launch after the user clicks the action.

External reachability checks are off by default:

```yaml
system_probe:
  allow_external_connectivity_checks: false
  external_check_urls:
    - "https://www.debian.org/"
  show_sensitive_identifiers: false
```

When external checks are disabled, the UI reports local route and DNS state only. MAC addresses, DMI serials, machine IDs, UUIDs, and disk serials are not shown in the default UI.

Page loads read SQLite only. They do not scan repos.

## Safety Limits

Hard defaults:

```text
Bind only to 127.0.0.1
Use port 1706
No cloud calls
No telemetry
No OpenAI or LLM API calls
No GitHub API calls
No automatic git fetch
No destructive Git actions
No mutation inside watched repos
No sudo
No package installation
No fake demo data
```

Allowed scanner Git commands are local read-only status/log/diff/worktree/stash queries. The UI may suggest commands or build handoff packets, but it does not commit, push, pull, merge, rebase, reset, clean, or delete.

Tests are not auto-run unless:

```text
test_policy.auto_run: true
```

and the repo name or path is listed in:

```text
test_policy.allow_repos
```

## Interpretation

The app stores raw facts first, then applies deterministic rules. Visible states include:

```text
Stable
Active work
In surgery
Needs review
Broken
Quiet
Dormant but preserved
Waiting on you
Unknown
```

Every interpretation includes:

```text
headline
meaning
why it matters
next sane action
evidence
rule ids
```

Raw counts and Git details are kept under Evidence/Under the hood instead of leading the main readout.

## Project Adapters

Adapters are deterministic pattern packs in `console1706/adapters.py`. They currently recognize broad patterns for:

```text
wiki
ufo-records
TCL
generic repos
```

To add an adapter, extend:

```text
infer_adapter()
infer_phase()
cluster_changed_files()
```

Then add or adjust tests in `tests/test_rules.py`.

## Handoff Packets

The handoff builder writes Markdown locally. It does not send the packet anywhere.

The homepage no longer shows Codex packet buttons. Local work is secondary to the machine console, while packet generation remains available from the CLI and API.

From the CLI:

```bash
console-1706 handoff --repo-id 1 --task "Review this state and tell me what remains before commit."
```

Packets are written under:

```text
~/.local/state/console-1706/handoffs/
```

Each packet includes controlled context, local evidence, constraints, the requested task, and an output contract.

## API

Implemented endpoints:

```text
GET  /                         HTML dashboard
GET  /api/health               health JSON
GET  /api/summary              system summary
GET  /api/repos                repo cards
GET  /api/repos/{id}           repo detail
GET  /api/attention            attention items
GET  /api/events               recent event stream
GET  /api/host                 latest host/system snapshot with summary and evidence
GET  /api/host/history         compact host snapshot history
GET  /api/live                 local live sensor snapshot and scan timing
POST /api/host/actions/codex   launch a user-clicked host-alert Codex terminal
GET  /api/evidence/{id}        raw interpretation evidence
GET  /api/handoffs             handoff packet list
POST /api/scan                 trigger safe manual scan
POST /api/handoffs             create handoff packet
```

If a scan is already running, `POST /api/scan` returns:

```json
{"status": "already_running"}
```

## Troubleshooting

Port already in use:

```bash
ss -ltnp | grep 1706
```

Service logs:

```bash
journalctl --user -u console-1706.service -n 100 --no-pager
```

Scan logs:

```bash
journalctl --user -u console-1706-scan.service -n 100 --no-pager
```

Timer status:

```bash
systemctl --user status console-1706-scan.timer
```

Manual scan:

```bash
~/.local/bin/console-1706 scan
```

or:

```bash
~/projects/console-1706/.venv/bin/console-1706 scan
```

Config:

```text
~/.config/console-1706/config.yml
```

Database:

```text
~/.local/state/console-1706/console.sqlite
```

## Official References

```text
Debian 13 release/update reference:
https://www.debian.org/News/2026/20260314

Python venv documentation:
https://docs.python.org/3/library/venv.html

FastAPI templates documentation:
https://fastapi.tiangolo.com/advanced/templates/

FastAPI manual deployment with Uvicorn:
https://fastapi.tiangolo.com/deployment/manually/

Uvicorn settings, host, and port:
https://www.uvicorn.org/settings/

systemd service unit documentation:
https://www.freedesktop.org/software/systemd/man/systemd.service.html

systemd timer unit documentation:
https://www.freedesktop.org/software/systemd/man/systemd.timer.html

Debian systemd service manpage:
https://manpages.debian.org/testing/systemd/systemd.service.5.en.html

SQLite WAL documentation:
https://www.sqlite.org/wal.html
```
