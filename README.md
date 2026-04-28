# console-1706

`console-1706` is a local-only homepage for a Debian laptop. It scans configured local repos, selected logs, and durable SQLite history, then turns those facts into plain-English operational readouts with evidence underneath.

Main goal:

```text
Tell me what the hell is going on across my local repos, logs, workflows, and Codex-assisted work, in human language, with evidence underneath.
```

It is not a Scrum dashboard, Jira clone, productivity score, GitHub dashboard, raw git status dump, or fake real-time wallboard. It does not use themed product labels. The UI has a dark, geometric console feel, but the language stays plain.

## Install on Debian 13

Install local dependencies:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git sqlite3 ripgrep jq curl xdg-utils
```

Install the app from the repo:

```bash
cd ~/projects/console-1706
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

From `~/projects/console-1706`:

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
4. Discover repos from `explicit_repos` and `repo_roots`.
5. Probe each repo with safe local Git commands and timeouts.
6. Probe configured logs.
7. Detect tests, but do not run them unless explicitly allowed.
8. Store snapshots.
9. Run deterministic interpretation rules.
10. Upsert attention items with fingerprint dedupe.
11. Mark absent attention items resolved.

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

From the UI, use `Build Codex packet` on a repo card.

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
