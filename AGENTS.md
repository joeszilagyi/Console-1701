# Agent Notes

This repo is a local-only Debian machine console. Preserve the current stack: Python, FastAPI,
Jinja2, SQLite, vanilla CSS, vanilla JS, pytest, ruff, and systemd user units. Do not replace it
with a frontend framework or external service dependency.

Keep the local-only safety envelope intact:

- Bind only to `127.0.0.1` on port `1701`.
- Do not add cloud calls, telemetry, hidden LLM calls, GitHub API calls, automatic git fetches,
  destructive commands, sudo, package installation, or writes outside console-1701 state/config
  paths.
- Treat host probes as read-only and timeout-protected.
- Preserve existing repo scan behavior while keeping the Debian machine as the homepage focus.
- The repo-root `Upkeeper.sh` symlink is off limits: do not read it, follow it, execute it, edit it,
  chmod it, delete it, stage it, or otherwise interact with it.

Backlog maintenance rule:

- If a requested idea, follow-up, risk, missing capability, or implementation detail comes up and
  is not completed in the same change, update `BACKLOG.md` before finishing the turn.
- If a backlog item is completed, mark it done or move it to a completed/history note instead of
  leaving stale work listed as pending.
- Keep backlog entries concrete enough that the next agent can implement them without recovering
  context from chat history.

Caretaking/history rule:

- When running caretaking or review prompts, preserve the outcome in tracked Git history. Use a
  detailed commit body and PR body that state the selected file, findings, changes, rationale,
  verification, and final status.
- For non-trivial caretaking changes, append a concise entry to `CARETAKING.md` before committing
  so future humans and LLM agents can understand what happened without the chat transcript.
- Avoid vague summaries like "bulk cleanup" or "serviceability fixes" unless concrete details are
  included nearby.
