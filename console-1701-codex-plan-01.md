# console-1701: local repo and workflow console

## 0. Codex instruction

Build this as a working local MVP on a Debian 13 laptop.

Do not turn this into a generic developer dashboard.
Do not use themed product labels like ship, deck, captain, Enterprise, Starfleet, or anything similar.
The visual vibe may be LCARS-inspired, but the product language must stay plain and neutral.

Use this project name and install target:

```text
Project directory: ~/projects/console-1701
Service name: console-1701
Local URL: http://127.0.0.1:1701
Config path: ~/.config/console-1701/config.yml
State path: ~/.local/state/console-1701/
Database path: ~/.local/state/console-1701/console.sqlite
Handoff path: ~/.local/state/console-1701/handoffs/
```

Main goal:

```text
Tell me what the hell is going on across my local repos, logs, workflows, and Codex-assisted work, in human language, with evidence underneath.
```

This does not need to be real time. Default scan cadence is every 30 minutes plus manual refresh.

No hidden LLM calls. No cloud calls. No telemetry. No automatic GitHub calls. No automatic `git fetch`.

The console should do the cheap local work first:

```text
Git + filesystem + logs + timestamps + SQLite + deterministic rules + templates
```

Only create an LLM/Codex handoff packet when explicitly requested.

## 1. What this is

`console-1701` is a local-only homepage for Firefox that shows a plain-English operational readout of local repos and workflows.

It should answer:

```text
What is happening?
What changed?
What looks safe?
What looks messy?
What is broken?
What needs human attention?
What did Codex probably touch?
Where am I in the workflow?
What should I look at first?
What evidence supports that interpretation?
```

The console must prioritize meaning over raw metrics.

Bad:

```text
dirty_files = 17
branch_offset = 3
churn_score = 0.72
```

Good:

```text
This repo is in the middle of surgery. The uncommitted work is clustered around exporter code, tests, and docs. Tests recently passed, so this is probably a review/commit situation, not a panic situation.
```

Bad:

```text
last_commit = 6 days ago
```

Good:

```text
This project has gone quiet. That is fine unless you expected Codex or a script to be working here.
```

Bad:

```text
pytest failed
```

Good:

```text
Tests are failing in the bibliography exporter area. Look at the latest changed exporter files and the failing test output first.
```

## 2. What this is not

Do not build:

```text
Scrum dashboard
Jira clone
velocity chart
story-point tracker
productivity score
management KPI board
generic GitHub dashboard
raw git status dump
fake real-time wallboard
Star Trek branded toy UI
```

No Scrum language.
No story points.
No velocity.
No fake productivity metrics.

## 3. Core operating philosophy

The app runs in four layers.

```text
Layer 0: Local facts
- Git commands
- file timestamps
- log tails
- test result cache
- configured workflow paths

Layer 1: Local memory
- SQLite snapshots
- deduped events
- historical attention items
- handoff packets

Layer 2: Deterministic interpretation
- rules
- templates
- path clustering
- workflow adapters
- no LLM required

Layer 3: Controlled LLM handoff
- only when user explicitly asks
- packet is generated locally
- packet includes evidence, boundaries, and output contract
- app does not call an LLM by default
```

The console must be useful even with zero API keys.

## 4. Controlled sandwich model for LLM use

LLM use is optional and must be fenced.

The app should generate Markdown handoff packets that wrap evidence and task instructions in explicit sections.

Template:

```md
# console-1701 handoff packet

Generated: {{timestamp}}
Repo: {{repo_name}}
Path: {{repo_path}}

## CONTROLLED_CONTEXT_BEGIN

### Current local interpretation

{{plain_english_summary_from_rules}}

### Local evidence

{{git_status}}
{{changed_files}}
{{recent_commits}}
{{test_results}}
{{log_tail}}
{{attention_items}}

### Constraints

- Do not delete data.
- Do not rewrite unrelated files.
- Do not run destructive Git commands.
- Do not assume network access.
- Do not invent missing evidence.
- If something is unclear, say what evidence is missing.

## CONTROLLED_CONTEXT_END

## LLM_TASK_BEGIN

{{user_selected_task}}

Examples:

- Explain the failing test in plain English.
- Tell me what remains before this can be committed.
- Produce a safe Codex task prompt from this evidence.
- Review whether this looks coherent or scattered.

## LLM_TASK_END

## OUTPUT_CONTRACT_BEGIN

Return:

1. Plain-English diagnosis.
2. Evidence you used.
3. Specific files to inspect.
4. Suggested next command or next human action.
5. What you are uncertain about.

Do not return generic advice.

## OUTPUT_CONTRACT_END
```

The app must never silently send this packet anywhere. It only writes the Markdown file and optionally provides a copy button.

## 5. Recommended stack

Use Python because this is a Debian laptop, local tooling is shell/Python friendly, and the app is mostly filesystem/Git scanning.

```text
Python 3
FastAPI
Uvicorn
Jinja2
SQLite
Vanilla JS
Vanilla CSS
systemd user service
systemd user timer
Git CLI
ripgrep if available
```

Avoid React/Vite for MVP unless absolutely necessary. The first version should be boring, durable, and easy to inspect.

Use a Python package name that works with imports:

```text
console1701
```

Use a command name that matches the product:

```text
console-1701
```

## 6. Debian 13 bootstrap target

Codex should produce a repo that can be installed like this:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git sqlite3 ripgrep jq curl xdg-utils

mkdir -p ~/projects
cd ~/projects
# Codex creates or updates this repo here:
cd ~/projects/console-1701

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

console-1701 init-config
console-1701 scan
console-1701 serve
```

Expected local URL:

```text
http://127.0.0.1:1701
```

Manual open command:

```bash
xdg-open http://127.0.0.1:1701
```

## 7. One-command user service install

Codex must provide:

```bash
./scripts/install_user_service.sh
```

After running it, these commands should work:

```bash
systemctl --user status console-1701.service
systemctl --user status console-1701-scan.timer
curl -fsS http://127.0.0.1:1701/api/health
xdg-open http://127.0.0.1:1701
```

The install script should:

```text
1. Verify it is running from ~/projects/console-1701 or print a clear warning.
2. Create .venv if missing.
3. Install the package into .venv.
4. Create ~/.config/console-1701/config.yml if missing.
5. Create ~/.local/state/console-1701/.
6. Copy systemd user units into ~/.config/systemd/user/.
7. Run systemctl --user daemon-reload.
8. Enable and start console-1701.service.
9. Enable and start console-1701-scan.timer.
10. Run one initial scan.
11. Print http://127.0.0.1:1701.
```

Do not modify Firefox profiles automatically. The README can tell the user to set the homepage manually.

## 8. Project layout

Implement this structure:

```text
console-1701/
  README.md
  pyproject.toml
  config.example.yml
  console1701/
    __init__.py
    cli.py
    app.py
    config.py
    db.py
    schema.sql
    scanner.py
    git_probe.py
    log_probe.py
    test_probe.py
    codex_probe.py
    adapters.py
    interpreter.py
    rules.py
    evidence.py
    handoff.py
    api.py
    static/
      app.css
      app.js
    templates/
      index.html
      repo.html
  scripts/
    install_user_service.sh
    dev_server.sh
    scan_once.sh
  systemd/
    console-1701.service
    console-1701-scan.service
    console-1701-scan.timer
  tests/
    test_git_probe.py
    test_rules.py
    test_interpreter.py
    test_handoff.py
```

## 9. pyproject target

Use `argparse`, not a heavy CLI dependency, unless there is a strong reason.

`pyproject.toml` should include roughly:

```toml
[project]
name = "console-1701"
version = "0.1.0"
description = "Local repo and workflow console"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.110",
  "uvicorn[standard]>=0.25",
  "jinja2>=3.1",
  "pyyaml>=6.0",
  "pydantic>=2.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "ruff>=0.5"
]

[project.scripts]
console-1701 = "console1701.cli:main"
```

## 10. Configuration

Create this file if missing:

```text
~/.config/console-1701/config.yml
```

Default config:

```yaml
server:
  host: "127.0.0.1"
  port: 1701
  browser_refresh_seconds: 60

scan:
  interval_minutes: 30
  max_repos_per_scan: 75
  overall_scan_timeout_seconds: 180
  per_repo_timeout_seconds: 20
  git_command_timeout_seconds: 5
  log_tail_max_bytes: 262144
  max_recent_commits: 8
  max_changed_files_display: 80
  dirty_stale_hours: 24
  inactive_days_warning: 14
  inactive_days_stale: 45
  allow_network: false
  allow_git_fetch: false

sqlite:
  busy_timeout_ms: 5000
  journal_mode: "WAL"

paths:
  repo_roots:
    - "~/projects"
    - "~/wiki"
  explicit_repos:
    - "~/projects/ufo-records"
    - "~/projects/TCL"
    - "~/wiki"

ignore:
  paths:
    - "**/.git/**"
    - "**/.venv/**"
    - "**/venv/**"
    - "**/node_modules/**"
    - "**/__pycache__/**"
    - "**/.pytest_cache/**"
    - "**/.mypy_cache/**"
    - "**/.ruff_cache/**"
    - "**/dist/**"
    - "**/build/**"
    - "**/vendor/**"
    - "**/archive/**"

logs:
  - name: "ufo-actions"
    path: "~/wiki/ufo-actions.log"
    type: "ufo_actions"
    enabled: true
  - name: "codex"
    path: "~/.codex"
    type: "codex"
    enabled: true

test_policy:
  auto_run: false
  default_timeout_seconds: 120
  allow_repos: []

projects:
  - name: "ufo-records"
    path: "~/projects/ufo-records"
    role: "Long-horizon UFO research database and tooling"
    category: "Research machinery"
    importance: "high"
    test_commands:
      - "python3 -m pytest tools/sqlite/tests"

  - name: "TCL"
    path: "~/projects/TCL"
    role: "Time travel constraints library and adversarial theory project"
    category: "Theory/library project"
    importance: "high"
    test_commands: []

  - name: "wiki"
    path: "~/wiki"
    role: "Working area for prompts, article drafts, logs, country runs, and source machinery"
    category: "Research workbench"
    importance: "critical"
    test_commands: []
```

Important default:

```text
The timer scan must not auto-run tests unless test_policy.auto_run is true and the repo is listed in test_policy.allow_repos.
```

## 11. No fake data rule

The dashboard must never silently show mock data.

If no repos are configured or discovered, show an empty state:

```text
No repos found yet.

Config path:
~/.config/console-1701/config.yml

Add repo_roots or explicit_repos, then run:
console-1701 scan
```

Do not create demo repos.
Do not invent statuses.
Do not show sample activity as if it is real.

## 12. Local-only safety rules

Hard requirements:

```text
Bind only to 127.0.0.1.
Use port 1701.
Do not expose on 0.0.0.0.
Do not call cloud APIs.
Do not send telemetry.
Do not call OpenAI or any LLM API.
Do not call GitHub APIs in MVP.
Do not run git fetch automatically.
Do not run destructive Git commands.
Do not mutate user repos.
```

Allowed commands from scanner:

```text
git status
git branch
git rev-parse
git log
git rev-list
git worktree list
git stash list
git diff --name-only
git diff --stat
git diff --shortstat
filesystem stat/tail/read of configured paths
```

Do not run these from UI in MVP:

```text
git commit
git reset
git clean
git push
git pull
git fetch
git merge
git rebase
rm
mv
write operations inside watched repos
```

The UI may show suggested commands and provide copy buttons.

## 13. systemd user units

Create these files.

`systemd/console-1701.service`:

```ini
[Unit]
Description=console-1701 local web UI
After=network.target

[Service]
WorkingDirectory=%h/projects/console-1701
ExecStart=%h/projects/console-1701/.venv/bin/console-1701 serve --config %h/.config/console-1701/config.yml
Restart=on-failure
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

`systemd/console-1701-scan.service`:

```ini
[Unit]
Description=console-1701 scanner

[Service]
Type=oneshot
WorkingDirectory=%h/projects/console-1701
ExecStart=%h/projects/console-1701/.venv/bin/console-1701 scan --config %h/.config/console-1701/config.yml
Environment=PYTHONUNBUFFERED=1
```

`systemd/console-1701-scan.timer`:

```ini
[Unit]
Description=Run console-1701 scanner every 30 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=30min
Persistent=true
Unit=console-1701-scan.service

[Install]
WantedBy=timers.target
```

Manual scan must also work:

```bash
console-1701 scan
```

Manual browser refresh must not trigger expensive scanning unless the user presses a specific refresh button.

## 14. SQLite data model

Use SQLite as durable local memory.

Enable WAL and busy timeout at connection setup:

```sql
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
```

Schema target:

```sql
CREATE TABLE IF NOT EXISTS repos (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  path TEXT NOT NULL UNIQUE,
  role TEXT,
  category TEXT,
  importance TEXT,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repo_snapshots (
  id INTEGER PRIMARY KEY,
  repo_id INTEGER NOT NULL,
  scanned_at TEXT NOT NULL,
  branch TEXT,
  commit_sha TEXT,
  commit_subject TEXT,
  commit_author TEXT,
  commit_time TEXT,
  is_dirty INTEGER,
  has_untracked INTEGER,
  ahead_count INTEGER,
  behind_count INTEGER,
  changed_files_json TEXT,
  path_clusters_json TEXT,
  recent_commits_json TEXT,
  diff_fingerprint TEXT,
  raw_git_status TEXT,
  scan_error TEXT,
  FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS test_snapshots (
  id INTEGER PRIMARY KEY,
  repo_id INTEGER NOT NULL,
  scanned_at TEXT NOT NULL,
  detected INTEGER NOT NULL DEFAULT 0,
  command TEXT,
  status TEXT,
  duration_seconds REAL,
  summary TEXT,
  raw_tail TEXT,
  fingerprint TEXT,
  FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS log_events (
  id INTEGER PRIMARY KEY,
  source TEXT NOT NULL,
  source_path TEXT,
  event_time TEXT,
  observed_at TEXT NOT NULL,
  severity TEXT,
  category TEXT,
  message TEXT,
  raw_line TEXT,
  fingerprint TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS interpreted_states (
  id INTEGER PRIMARY KEY,
  repo_id INTEGER,
  scope TEXT NOT NULL,
  state TEXT NOT NULL,
  severity TEXT NOT NULL,
  headline TEXT NOT NULL,
  meaning TEXT NOT NULL,
  why_it_matters TEXT NOT NULL,
  next_sane_action TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  rule_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS attention_items (
  id INTEGER PRIMARY KEY,
  fingerprint TEXT NOT NULL UNIQUE,
  repo_id INTEGER,
  severity TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  why_it_matters TEXT NOT NULL,
  next_sane_action TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  first_seen TEXT NOT NULL,
  last_seen TEXT NOT NULL,
  resolved_at TEXT,
  FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS handoff_packets (
  id INTEGER PRIMARY KEY,
  repo_id INTEGER,
  created_at TEXT NOT NULL,
  title TEXT NOT NULL,
  path TEXT NOT NULL,
  task TEXT,
  evidence_json TEXT NOT NULL,
  FOREIGN KEY(repo_id) REFERENCES repos(id)
);

CREATE TABLE IF NOT EXISTS scan_runs (
  id INTEGER PRIMARY KEY,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL,
  repos_seen INTEGER DEFAULT 0,
  repos_scanned INTEGER DEFAULT 0,
  errors_json TEXT
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

Never delete historical events by default.
Use statuses like `resolved`, `ignored`, `archived`, and `superseded`.

## 15. Scanner behavior

The scanner is separate from the web app.

Command:

```bash
console-1701 scan
```

Scanner sequence:

```text
1. Load config.
2. Create state directory if needed.
3. Open SQLite.
4. Discover repos.
5. Probe each repo within caps.
6. Probe configured logs.
7. Probe tests only if allowed.
8. Store snapshots.
9. Run deterministic interpretation rules.
10. Upsert attention items with dedupe.
11. Mark resolved items if evidence changed.
12. Exit cleanly.
```

The web app reads from SQLite.
Page loads must not perform expensive scans.

## 16. Performance caps

Hard limits:

```text
Default scan cadence: 30 minutes
Manual scan: allowed
Max repos per scan: 75
Overall scan timeout: 180 seconds
Per repo timeout: 20 seconds
Git command timeout: 5 seconds
Test command timeout: 120 seconds if explicitly enabled
Log tail max bytes per file: 256 KiB
Changed files stored for display: cap at 80, preserve full count in evidence
Recent commits: 8
```

Directory walking must skip:

```text
.git
.venv
venv
node_modules
__pycache__
.pytest_cache
.mypy_cache
.ruff_cache
dist
build
vendor
archive
```

If a cap is hit, record it as evidence:

```text
Scan capped after 75 repos.
Only first 256 KiB of log tail read.
Git command timed out after 5 seconds.
```

Do not hide caps.

## 17. Error behavior

Handle these without crashing the whole app:

```text
repo path missing
repo path not a Git repo
permission denied
malformed config
SQLite locked
git command timeout
git command failure
repo has no upstream
log file missing
log path is directory when file expected
test command timeout
test command missing
invalid JSONL line
Unicode decode issue
```

Interpretation rules:

```text
Missing repo:
State: Unknown
Meaning: This configured repo path does not exist right now.
Next: Check config path or mount/location.

Permission denied:
State: Unknown
Meaning: The scanner cannot read this path.
Next: Fix permissions or remove it from config.

No upstream:
State: Not broken
Meaning: Git has no tracking branch for ahead/behind checks.
Next: Ignore unless remote sync matters.

SQLite locked:
State: Scanner delayed
Meaning: Another process has the database briefly locked.
Next: Retry on next timer or manual scan.

Git timeout:
State: Needs attention
Meaning: Git was too slow or stuck in this repo.
Next: Inspect repo health manually.

Log missing:
State: Not broken unless required
Meaning: Configured log file was not found.
Next: Ignore if that workflow has not run yet.
```

## 18. Repo discovery

Two discovery modes:

```text
1. explicit_repos from config
2. repo_roots from config
```

Discovery should look for `.git` directories under roots, skipping ignored directories.

Do not shell out to a dangerous recursive command without caps.
Prefer Python path walking with ignore rules and max depth.

If using shell, keep it read-only and bounded.

Register parent directory of `.git` as repo.

## 19. Git probe

Collect for each repo:

```text
path
name
current branch
HEAD SHA
latest commit subject
latest commit author
latest commit time
dirty or clean
untracked present
changed files
path clusters
recent commits
ahead/behind if upstream exists locally
worktree list if available
stash count if available
diff fingerprint
raw git status
errors
```

Use local Git commands only:

```bash
git -C "$repo" status --porcelain=v1
git -C "$repo" branch --show-current
git -C "$repo" rev-parse HEAD
git -C "$repo" log -1 --format='%H%x1f%an%x1f%ai%x1f%s'
git -C "$repo" log -8 --format='%h%x1f%ai%x1f%s'
git -C "$repo" rev-list --left-right --count @{upstream}...HEAD
git -C "$repo" worktree list --porcelain
git -C "$repo" stash list
git -C "$repo" diff --name-only
git -C "$repo" diff --stat
git -C "$repo" diff --shortstat
```

If upstream check fails, do not mark broken.

## 20. Diff fingerprinting

For dirty repos, compute a cheap fingerprint from:

```text
HEAD SHA
changed file list
git diff --shortstat
git status porcelain
```

Do not store full diffs by default.
Generate full diff only on explicit Evidence request.

## 21. Test probe

Default:

```text
Do not auto-run tests.
```

Tests may be run only if:

```text
test_policy.auto_run is true
and repo path/name is listed in test_policy.allow_repos
and a test command is configured
and the repo fingerprint changed since last test
or the user explicitly runs a manual test action that is added later
```

MVP does not need manual test run endpoint.

The dashboard can still show:

```text
Tests are configured but not auto-run.
Last known result: pass, 2 hours ago.
No recent test evidence found.
```

Detect obvious test support, but do not run it unless allowed:

```text
pyproject.toml + tests/ suggests pytest
package.json suggests npm test
Makefile with test target suggests make test
```

## 22. Log probe

Probe configured logs only.

Start with:

```text
~/wiki/ufo-actions.log
~/.codex if readable and useful
repo-local logs/ directories if configured later
```

For `ufo-actions.log`, attempt to parse:

```text
timestamp
tool
language
origin
stream
event
entrypoint
args
message
```

Classify log events:

```text
START
STOP
ERROR
WARN
TEST_PASS
TEST_FAIL
EXPORT
IMPORT
BUILD_RUN
CODEX_RUN
UNKNOWN
```

Unknown lines are not errors. Store them as raw evidence only.

## 23. Codex activity detection

Do not depend on Codex internals for MVP.

Detect likely Codex activity from:

```text
recent file modifications clustered in time
commit messages mentioning Codex if present
logs mentioning codex
ufo-actions.log origin fields if present
coherent file clusters after a known work session
```

Use careful wording:

```text
Codex appears to have worked here.
This looks like a coherent agent pass.
This is a detected pattern, not proof.
```

Do not overclaim.

## 24. Interpretation engine

This is the core product.

The engine converts raw facts into plain-English states.

Repo states:

```text
Stable
Active work
In surgery
Needs review
Possibly broken
Broken
Quiet
Dormant but preserved
Waiting on you
Unknown
```

System states:

```text
OK
Working
Caution
Broken
Idle
Unknown
```

Severity values:

```text
green
blue
yellow
orange
red
gray
```

Every visible status must have:

```text
headline
meaning
why it matters
next sane action
evidence
rule ids that fired
```

If a metric cannot support those fields, hide it from Normal Mode and put it in Evidence Mode.

## 25. Interpretation rules

Implement as deterministic Python rules first.

Example rules:

```python
if tests_failed:
    state = "Broken"
    severity = "red"
    headline = "Tests are failing"
    meaning = "This repo is currently not safe to build on without review."
    why = "A failing test means recent or existing code is not matching expected behavior."
    next_action = "Open the failing test evidence and inspect the latest changed files."
```

```python
if is_dirty and changed_files_are_clustered and recent_test_pass:
    state = "Needs review"
    severity = "yellow"
    headline = "Coherent uncommitted work looks ready for review"
    meaning = "The changes appear related and tests recently passed."
    why = "This is often the point where a human should inspect output and commit if it matches intent."
    next_action = "Review the diff and generated output, then commit if it matches intent."
```

```python
if is_dirty and dirty_age_hours > 24:
    state = "Waiting on you"
    severity = "orange"
    headline = "Old uncommitted work is sitting here"
    meaning = "This may be abandoned work, unfinished Codex output, or something you meant to inspect."
    why = "Old dirty worktrees are easy to accidentally build on without knowing what changed."
    next_action = "Review the diff before starting more work in this repo."
```

```python
if not is_dirty and recent_test_pass:
    state = "Stable"
    severity = "green"
    headline = "Clean and recently tested"
    meaning = "This repo appears safe at the current commit."
    why = "Clean worktree plus recent passing tests is a strong local stability signal."
    next_action = "No action needed."
```

```python
if inactive_days > stale_threshold and importance != "critical":
    state = "Dormant but preserved"
    severity = "gray"
    headline = "Quiet but preserved"
    meaning = "No recent activity. This is not a problem unless you expected movement."
    why = "Quiet projects should not be treated as failures by default."
    next_action = "Ignore unless this project should be active."
```

```python
if code_changed and not tests_changed and not recent_test_pass:
    add_attention(
        title="Code changed without test evidence",
        severity="orange",
        body="Code changed, but no nearby tests changed and no fresh passing test was found.",
        next_sane_action="Run or review tests before trusting this work."
    )
```

```python
if files_changed_under(["schema", "migrations", "exporters", "importers"]):
    add_attention(
        title="Structural code changed",
        severity="yellow",
        body="A file in a structural area changed. Downstream output may be affected.",
        next_sane_action="Review generated output or compatibility before committing."
    )
```

## 26. File clustering

Recognize coherent vs scattered work using path groups.

Do not invent math-heavy scoring.

Group changed files by:

```text
top-level directory
second-level directory
known project adapter patterns
file extension
```

Coherent example:

```text
tools/sqlite/exporters/wikipedia_cite.py
tools/sqlite/export_bibliography.py
tools/sqlite/tests/test_export_bibliography.py
docs/sqlite.md
```

Interpretation:

```text
This looks like a coherent exporter pass.
```

Scattered example:

```text
README.md
random script
schema file
frontend file
unrelated prompt
```

Interpretation:

```text
Changes are scattered. Review more carefully before trusting this state.
```

## 27. Project adapters

Adapters are deterministic pattern packs. They should be easy to extend.

### 27.1 wiki adapter

Detect:

```text
~/wiki/ufo-actions.log
~/wiki/Places/**/runs/*.txt
~/wiki/Places/**/state/*.jsonl
~/wiki/prompts/**
UFO_Build_Place.sh
```

Show:

```text
recent country/place runs
last run per place
places with new output
places with no recent movement
catalog/state files changed
errors in ufo-actions.log
recent START/STOP events
```

Plain-English examples:

```text
The wiki workbench is active. Recent runs touched country/place output and no obvious fatal errors were found in the latest log tail.
```

```text
Run activity exists, but no catalog state changed. That may mean the gather pass found little or failed before materializing results.
```

### 27.2 ufo-records adapter

Detect:

```text
tools/sqlite/**
tools/sqlite/tests/**
schema_profiles.json
export_profiles/**
exporters/**
state/*.jsonl
```

Plain-English examples:

```text
Bibliography/export tooling is being modified.
```

```text
This looks like a schema/exporter pass. Review generated output before trusting downstream use.
```

```text
Tests passed after exporter changes. This is a good candidate for commit review.
```

### 27.3 TCL adapter

Detect:

```text
README
docs
constraints
tests
source modules
```

Plain-English examples:

```text
TCL has conceptual or documentation movement, but no fresh test signal was found.
```

```text
This repo is quiet. Treat it as preserved, not abandoned.
```

## 28. UI structure

Single-page app is fine for MVP.

Use neutral labels:

```text
Overview
System state
Attention
Under the hood
Evidence
Activity
Workflows
Repos
Handoffs
Settings
```

Do not use themed labels.

Main dashboard sections:

```text
1. Top system state strip
2. What is happening
3. Human attention
4. Repo cards
5. Workflow readout
6. Activity stream
7. Under the hood
8. Evidence drawer
9. Handoff packet builder
```

## 29. Visual style

Vibe:

```text
LCARS-inspired geometry
modern SaaS observability
local cockpit feel
dark background
large readable panels
rounded asymmetric blocks
status strips
warm orange, amber, purple, blue, red, green accents
high contrast text
```

Do not use logos, copyrighted names, or themed labels.

CSS variables:

```css
:root {
  --bg: #08080d;
  --panel: #11111a;
  --panel-2: #181828;
  --text: #f4f1ff;
  --muted: #aaa6c8;
  --accent-orange: #ff9f43;
  --accent-amber: #ffd166;
  --accent-purple: #b388ff;
  --accent-blue: #5ec8ff;
  --status-red: #ff5c7a;
  --status-green: #7ee787;
  --status-gray: #6e7681;
}
```

Avoid tiny fonts. This should be readable when tired.

## 30. Top system state strip

Must answer within five seconds:

```text
SYSTEM STATE: OK / WORKING / CAUTION / BROKEN / IDLE
HUMAN ATTENTION: YES / NO
ACTIVE AREA: exporter / pipeline / TCL / wiki / unknown
LAST SCAN: timestamp and age
LAST MEANINGFUL EVENT: plain English
NEXT SANE ACTION: review / run tests / commit / ignore / investigate
```

Example:

```text
SYSTEM STATE: CAUTION
HUMAN ATTENTION: YES
ACTIVE AREA: ufo-records bibliography exporter
LAST SCAN: 14 minutes ago
LAST MEANINGFUL EVENT: tests passed after exporter changes
NEXT SANE ACTION: review generated citation output before committing
```

## 31. What is happening panel

This is the main explanation area.

It should read like a competent engineer in Slack.

Example:

```text
ufo-records is in active work. Recent changes are clustered around the Wikipedia citation exporter, tests, schema profile, and docs. This looks coherent, not random drift. Tests recently passed, so the next useful action is review rather than panic.
```

Another:

```text
wiki is active. The configured action log has recent entries and no fatal errors were found in the latest tail. Some place output changed, so the workflow appears to be producing material.
```

## 32. Human attention panel

Show only things that matter.

Examples:

```text
RED: Tests failing in ufo-records
ORANGE: Dirty worktree older than 24 hours in TCL
YELLOW: Exporter changed without fresh sample output
YELLOW: Codex-like activity detected but no test evidence found
GRAY: Repo dormant but preserved
```

Each item must include:

```text
headline
meaning
why it matters
next sane action
evidence link
```

Dedupe repeated items by fingerprint.

## 33. Repo cards

Each repo card should show:

```text
name
role
state
meaning
risk
last meaningful event
next sane action
evidence footer
```

Example:

```text
UFO RECORDS
Role: Long-horizon research database and tooling
State: Needs review
Meaning: Coherent exporter work is present and tests recently passed.
Risk: Medium
Next: Review generated citation output before committing.
Evidence: changed files cluster under tools/sqlite, last test pass found 18 minutes ago.
```

Do not lead with raw counts.
Raw counts belong in Evidence Mode.

## 34. Modes

### Normal Mode

Default. Shows interpretation first.

### Explain Mode

Every label explains itself.

Examples:

```text
"In surgery" means this repo has active uncommitted work touching important files. It may be fine, but you should not treat it as stable yet.
```

```text
"Dirty" means Git sees local changes that are not committed.
```

```text
"Coherent change" means most changed files appear to belong to the same feature area.
```

### Evidence Mode

Shows raw support:

```text
git status
changed files
recent commits
test output tail
log lines
scanner errors
rule names that fired
```

Nothing should be magic.
Every interpretation links to evidence.

## 35. Under the hood panel

This panel shows causal chains.

Example:

```text
Why this repo is marked "Needs review":

1. It has uncommitted changes.
2. Most changes are in one feature area: tools/sqlite/exporters.
3. Tests recently passed.
4. Exporter changes can affect downstream citation output.
5. Therefore, the next useful action is human review, not debugging.
```

This is the “what is going on under the hood” readout.

## 36. Activity stream

Show meaningful events only.

Good:

```text
12:04 ufo-records: exporter files changed
12:07 ufo-records: tests passed
12:12 wiki: country/place workflow started
12:29 wiki: run output written
12:31 console: attention item resolved, tests now pass
```

Bad:

```text
12:04 scanned repo
12:05 scanned repo
12:06 scanned repo
```

Noise kills the product.

## 37. Workflow phase detection

Derive rough phases from paths and logs.

wiki phases:

```text
gather
scour
dedupe
verify
export
review
archive
idle
unknown
```

ufo-records phases:

```text
schema
import
query
export
test
docs
review
idle
unknown
```

TCL phases:

```text
concept
constraints
docs
tests
review
idle
unknown
```

Examples:

```text
Changed files under prompts/ and Places/*/runs means gather/scour activity.
Changed files under exporters and tests means export/test activity.
Changed README only means docs/review activity.
```

## 38. API endpoints

Implement:

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
POST /api/host/actions/codex   launch a user-clicked host-alert Codex terminal
GET  /api/evidence/{id}        raw evidence for interpretation
GET  /api/handoffs             handoff packet list
POST /api/scan                 trigger safe manual scan
POST /api/handoffs             create handoff packet
```

No destructive endpoints in MVP.

`POST /api/scan` should start a scan or run it safely with a lock. If a scan is already running, return:

```json
{"status":"already_running"}
```

## 39. Handoff packet builder

This is a core outcome, not a side feature.

The packet builder reduces LLM cost by letting the local console assemble high-signal context before Codex or another LLM sees anything.

Current UI rule:

```text
Do not show Codex packet buttons on the homepage.
Keep packet generation available from the CLI and local API.
Local work remains secondary to the machine console.
```

Current host bay order:

```text
B2 Services / systems
B3 Debian
B4 Hardware
```

The packet should include:

```text
plain-English current state
attention items
evidence
recent commits
changed files
test results
log tail
specific requested task
constraints
output contract
```

Example output file:

```text
~/.local/state/console-1701/handoffs/2026-04-28_ufo-records_review.md
```

## 40. Handoff packet example

```md
# console-1701 handoff: ufo-records

Generated: 2026-04-28T12:00:00-07:00
Repo: ufo-records
Path: ~/projects/ufo-records

## CONTROLLED_CONTEXT_BEGIN

### Current interpretation

This repo appears to be in active work around bibliography/export tooling. Changes are clustered under tools/sqlite/exporters, tests, docs, and schema profile. This looks coherent rather than random drift.

### Local evidence

Branch: main
Dirty: yes
Latest commit: abc123 Add wikipedia-cite exporter

Changed files:

- tools/sqlite/exporters/wikipedia_cite.py
- tools/sqlite/export_bibliography.py
- tools/sqlite/tests/test_export_bibliography.py
- tools/sqlite/schema_profiles.json

Last known test:

Command: python3 -m pytest tools/sqlite/tests
Result: pass

Attention items:

- Exporter changed. Review generated output.
- Schema/profile changed. Confirm downstream compatibility.

### Constraints

- Do not rewrite unrelated files.
- Do not delete data.
- Do not run destructive Git commands.
- Do not assume network access.
- Return exact files inspected and commands suggested.

## CONTROLLED_CONTEXT_END

## LLM_TASK_BEGIN

Review this state and tell me what remains before it can be safely committed.

## LLM_TASK_END

## OUTPUT_CONTRACT_BEGIN

Return:

1. Commit readiness diagnosis.
2. Evidence used.
3. Specific files to inspect.
4. Suggested next command or next human action.
5. Uncertainties.

## OUTPUT_CONTRACT_END
```

## 41. Caching and dedupe

Cache:

```text
repo snapshots
diff fingerprints
test fingerprints
log fingerprints
interpretations
attention item fingerprints
handoff packets
```

If a repo fingerprint has not changed, reuse interpretation.

Attention item lifecycle:

```text
open
still_present
resolved
ignored
archived
```

If the same issue remains, update `last_seen`. Do not spam duplicate items.

Resolution examples:

```text
tests now pass
repo now clean
dirty work committed
log error no longer appears in latest tail
```

## 42. Empty and stale states

If the scanner has never run:

```text
No scan has run yet.
Run: console-1701 scan
```

If last scan is old:

```text
Last scan was 2 hours ago. This page may be stale.
```

If the systemd timer is inactive:

```text
The scheduled scanner does not appear active.
Check: systemctl --user status console-1701-scan.timer
```

## 43. README requirements

README must include:

```text
What this is
What this is not
Install on Debian 13
Run locally
Install systemd user service
Manual scan
Config paths
State paths
How scans work
How interpretation works
How to add a project adapter
How to generate a Codex handoff packet
Safety limits
Troubleshooting
Official reference URLs
```

## 44. Tests

Write tests for interpretation and handoff generation.

Required test cases:

```text
clean repo + recent test pass => Stable
dirty repo + clustered exporter changes + test pass => Needs review
dirty repo + old dirty timestamp => Waiting on you
test failure => Broken
inactive repo => Dormant but preserved
code changed without tests => orange attention item
schema/exporter changed => structural attention item
same issue repeated => deduped attention item
missing repo => Unknown, not crash
no upstream => not broken
handoff packet contains CONTROLLED_CONTEXT and OUTPUT_CONTRACT sections
```

## 45. First implementation order

Do this in order:

```text
1. Create project structure.
2. Add pyproject and CLI.
3. Add config loader and init-config command.
4. Add SQLite schema and connection helper.
5. Add repo discovery with ignore rules.
6. Add safe Git probe with timeouts.
7. Store repo snapshots.
8. Add path clustering.
9. Add deterministic interpretation rules.
10. Add attention item dedupe.
11. Add basic FastAPI app.
12. Add Jinja dashboard.
13. Add CSS visual style.
14. Add Evidence Mode.
15. Add manual scan endpoint.
16. Add handoff packet generator.
17. Add systemd user units.
18. Add install script.
19. Add tests.
20. Add README.
```

Do not start with UI perfection.
Get real local data flowing first.

## 46. First milestone acceptance criteria

The first working version is acceptable if:

```text
I can open http://127.0.0.1:1701 in Firefox.
It binds only to 127.0.0.1.
It shows configured/discovered repos.
It never shows fake data.
It tells me which repos are stable, active, messy, broken, quiet, or need review.
It explains those states in plain English.
It shows evidence underneath each interpretation.
It preserves scan history in SQLite.
It scans every 30 minutes using a systemd user timer.
It supports manual refresh.
It can generate a Markdown Codex handoff packet.
It runs without cloud dependencies.
It does not call an LLM.
It does not perform destructive Git actions.
```

## 47. Troubleshooting behavior

Add a troubleshooting panel or README section for:

```text
Port already in use:
  ss -ltnp | grep 1701

Service logs:
  journalctl --user -u console-1701.service -n 100 --no-pager

Scan logs:
  journalctl --user -u console-1701-scan.service -n 100 --no-pager

Timer status:
  systemctl --user status console-1701-scan.timer

Manual scan:
  ~/.local/bin/console-1701 scan
  or
  ~/projects/console-1701/.venv/bin/console-1701 scan

Config:
  ~/.config/console-1701/config.yml

Database:
  ~/.local/state/console-1701/console.sqlite
```

## 48. Visual and language guardrails

Use these product labels:

```text
Overview
System state
Attention
Under the hood
Evidence
Activity
Workflows
Repos
Handoffs
Settings
```

Do not use these as labels:

```text
ship
deck
captain
commander
bridge
engineering deck
Starfleet
Enterprise
mission control unless used generically and sparingly
```

The vibe can be there. The words should not be cosplay.

## 49. Long-term expansion, not MVP

Later features:

```text
GitHub PR/issue awareness, opt-in only
safe local command buttons with confirmation
commit readiness checklist
visual timeline
repo dependency map
country/place run map
test trend history
Codex session ingestion if stable
local desktop notifications
nightly digest
project-specific what changed since yesterday view
```

Do not block MVP on these.

## 50. External reference URLs

These are reference URLs for implementation details. Use official docs first.

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

## 51. Final instruction to Codex

Build the first version now.

Prioritize:

```text
real local data
plain-English interpretation
evidence underneath
30-minute scans plus manual refresh
no fake data
low LLM cost
controlled handoff packets
safe local-only operation
Debian 13 user-service install
extensibility
```

Do not overbuild charts.
Do not add Scrum concepts.
Do not add cloud dependencies.
Do not make this Star Trek branded.
Do not perform destructive Git operations.
Do not call any LLM automatically.

This is a local console for one user's repos, logs, research workflows, and Codex-assisted development.
