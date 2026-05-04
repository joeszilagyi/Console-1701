from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MAX_SCENARIO_CHARS = 16000
TERMINAL_TIMEOUT_SECONDS = 3


class TerminalLaunchError(RuntimeError):
    """Raised when a user-requested terminal action cannot be launched."""


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")[:64] or "host-alert"


def _trim(value: str, max_chars: int = MAX_SCENARIO_CHARS) -> str:
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars]}\n...[truncated by console-1701]"


def build_host_alert_prompt(scenario: dict[str, Any]) -> str:
    section = str(scenario.get("section") or "host")
    message = str(scenario.get("message") or "Host alert")
    why = str(scenario.get("why") or "No reason text was supplied.")
    next_action = str(scenario.get("next_action") or "Inspect local evidence.")
    evidence = scenario.get("evidence")
    evidence_json = json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False)

    prompt = f"""
You are in an interactive Codex session launched by console-1701 from a local host alert.

Task:
Address this local Debian machine alert. Start by explaining what failed, what evidence says, and
which read-only checks you will run. Do not use sudo, destructive commands, package installation,
network calls, git fetch, or writes outside appropriate local config/state paths unless the human in
this terminal explicitly asks for that step.

Alert:
- Section: {section}
- Message: {message}
- Why: {why}
- Suggested next command: {next_action}

Evidence JSON:
{_trim(evidence_json)}

Working rule:
Treat this as a real local machine incident. Prefer exact command output over guesses. If a fix
requires privilege or mutation, stop and ask the human before taking that action.
""".strip()
    return prompt


def _write_executable_script(path: Path, prompt_path: Path, cwd: Path, title: str) -> None:
    script = f"""#!/bin/sh
set -eu
cd {json.dumps(str(cwd))}
printf '\\033]0;{title}\\007'
echo 'console-1701 host alert -> interactive Codex'
echo 'Prompt file: {prompt_path}'
echo
if ! command -v codex >/dev/null 2>&1; then
  echo 'codex CLI was not found on PATH.'
  echo 'Install or expose codex, then retry from console-1701.'
  echo
  printf 'Press Enter to close... '
  read _answer
  exit 127
fi
codex --cd {json.dumps(str(cwd))} "$(cat {json.dumps(str(prompt_path))})"
status=$?
echo
echo "Codex exited with status $status."
printf 'Press Enter to close... '
read _answer
exit "$status"
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def prepare_host_alert_terminal_action(
    config: dict[str, Any],
    scenario: dict[str, Any],
) -> dict[str, Any]:
    state_dir = Path(config["_state_dir"]).expanduser()
    action_dir = state_dir / "terminal-actions"
    action_dir.mkdir(parents=True, exist_ok=True)

    section = str(scenario.get("section") or "host")
    timestamp = datetime.now(UTC).astimezone().strftime("%Y%m%d-%H%M%S")
    stem = f"{timestamp}-{_slug(section)}"
    title = f"console-1701 Codex {stem}"
    prompt_path = action_dir / f"{stem}.prompt.md"
    script_path = action_dir / f"{stem}.sh"
    cwd = Path.home()

    prompt_path.write_text(build_host_alert_prompt(scenario), encoding="utf-8")
    _write_executable_script(script_path, prompt_path, cwd, title)

    return {
        "status": "prepared",
        "prompt_path": str(prompt_path),
        "script_path": str(script_path),
        "cwd": str(cwd),
        "title": title,
    }


def _terminal_candidates(
    script_path: str,
    title: str = "console-1701 Codex",
) -> list[tuple[str, list[str]]]:
    candidates: list[tuple[str, list[str]]] = []
    if shutil.which("xfce4-terminal"):
        candidates.append(
            (
                "xfce4-terminal",
                [
                    "xfce4-terminal",
                    "--disable-server",
                    "--maximize",
                    "--initial-title",
                    title,
                    "--title",
                    title,
                    "--command",
                    script_path,
                ],
            )
        )
    if shutil.which("gnome-terminal"):
        candidates.append(
            (
                "gnome-terminal",
                ["gnome-terminal", "--maximize", "--title", title, "--", script_path],
            )
        )
    if shutil.which("konsole"):
        candidates.append(
            ("konsole", ["konsole", "--fullscreen", "--title", title, "-e", script_path])
        )
    if shutil.which("mate-terminal"):
        candidates.append(
            (
                "mate-terminal",
                ["mate-terminal", "--maximize", "--title", title, "--command", script_path],
            )
        )
    if shutil.which("tilix"):
        candidates.append(("tilix", ["tilix", "--maximize", "-e", script_path]))
    if shutil.which("alacritty"):
        candidates.append(
            (
                "alacritty",
                ["alacritty", "--option", "window.startup_mode=Maximized", "-e", script_path],
            )
        )
    if shutil.which("kitty"):
        candidates.append(
            ("kitty", ["kitty", "--start-as=maximized", "--title", title, script_path])
        )
    if shutil.which("wezterm"):
        candidates.append(("wezterm", ["wezterm", "start", "--", script_path]))
    if shutil.which("x-terminal-emulator"):
        candidates.append(
            (
                "x-terminal-emulator",
                ["x-terminal-emulator", "--maximize", "-T", title, "-e", script_path],
            )
        )
        candidates.append(("x-terminal-emulator", ["x-terminal-emulator", "-e", script_path]))
    if shutil.which("xdg-terminal-exec"):
        candidates.append(("xdg-terminal-exec", ["xdg-terminal-exec", script_path]))
    if shutil.which("lxterminal"):
        candidates.append(("lxterminal", ["lxterminal", "-e", script_path]))
    return candidates


def _terminal_error_allows_fallback(detail: str) -> bool:
    lowered = detail.lower()
    return any(
        marker in lowered
        for marker in (
            "unknown option",
            "unrecognized option",
            "failed to parse arguments",
            "invalid option",
        )
    )


def launch_host_alert_codex_terminal(
    config: dict[str, Any],
    scenario: dict[str, Any],
) -> dict[str, Any]:
    prepared = prepare_host_alert_terminal_action(config, scenario)
    script_path = prepared["script_path"]
    candidates = _terminal_candidates(
        script_path,
        str(prepared.get("title") or "console-1701 Codex"),
    )
    if not candidates:
        raise TerminalLaunchError(
            "No supported terminal emulator was found. Tried xdg-terminal-exec, "
            "x-terminal-emulator, gnome-terminal, konsole, xfce4-terminal, mate-terminal, "
            "lxterminal, tilix, alacritty, kitty, and wezterm."
        )

    errors = []
    setsid = shutil.which("setsid")
    for terminal_name, terminal_args in candidates:
        command = [setsid, "-f", *terminal_args] if setsid else terminal_args
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=TERMINAL_TIMEOUT_SECONDS,
                check=False,
                env=os.environ.copy(),
            )
        except subprocess.TimeoutExpired:
            prepared.update(
                {
                    "status": "launch_requested",
                    "terminal": terminal_name,
                    "command": terminal_args,
                    "note": "launch command timed out after terminal request; no fallback tried",
                }
            )
            return prepared
        except OSError as exc:
            errors.append(f"{terminal_name}: {exc}")
            continue

        if result.returncode == 0:
            prepared.update(
                {
                    "status": "launch_requested",
                    "terminal": terminal_name,
                    "command": terminal_args,
                }
            )
            return prepared

        detail = (result.stderr or result.stdout or "").strip()
        errors.append(f"{terminal_name}: exit {result.returncode} {detail}".strip())
        if not _terminal_error_allows_fallback(detail):
            raise TerminalLaunchError(
                "Terminal launch failed after attempting one terminal command. "
                + errors[-1]
            )

    raise TerminalLaunchError("Terminal launch failed. " + " | ".join(errors))
