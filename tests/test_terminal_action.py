from __future__ import annotations

import subprocess
from pathlib import Path

from console1706.terminal_action import (
    _terminal_candidates,
    build_host_alert_prompt,
    launch_host_alert_codex_terminal,
    prepare_host_alert_terminal_action,
)


def test_build_host_alert_prompt_includes_alert_context():
    prompt = build_host_alert_prompt(
        {
            "section": "services",
            "message": "Failed system service: x11vnc.service.",
            "why": "systemctl reports x11vnc.service is failed.",
            "next_action": "systemctl status x11vnc.service --no-pager",
            "evidence": {"failed_system": [{"unit": "x11vnc.service"}]},
        }
    )

    assert "Failed system service: x11vnc.service." in prompt
    assert "systemctl reports x11vnc.service is failed." in prompt
    assert "systemctl status x11vnc.service --no-pager" in prompt
    assert "Do not use sudo" in prompt
    assert '"unit": "x11vnc.service"' in prompt


def test_prepare_host_alert_terminal_action_writes_prompt_and_script(tmp_path: Path):
    result = prepare_host_alert_terminal_action(
        {"_state_dir": str(tmp_path)},
        {
            "section": "services",
            "message": "Failed system service: x11vnc.service.",
            "why": "Result=exit-code",
            "next_action": "journalctl -u x11vnc.service -n 80 --no-pager",
            "evidence": {"unit": "x11vnc.service"},
        },
    )

    prompt_path = Path(result["prompt_path"])
    script_path = Path(result["script_path"])

    assert prompt_path.exists()
    assert script_path.exists()
    assert "Failed system service: x11vnc.service." in prompt_path.read_text(encoding="utf-8")
    assert "codex --cd" in script_path.read_text(encoding="utf-8")
    assert script_path.stat().st_mode & 0o100


def test_terminal_candidates_prefer_maximized_terminal(monkeypatch):
    available = {"gnome-terminal": "/usr/bin/gnome-terminal"}

    monkeypatch.setattr(
        "console1706.terminal_action.shutil.which",
        lambda command: available.get(command),
    )

    candidates = _terminal_candidates("/tmp/console-1706-alert.sh")

    assert candidates == [
        (
            "gnome-terminal",
            [
                "gnome-terminal",
                "--maximize",
                "--title",
                "console-1706 Codex",
                "--",
                "/tmp/console-1706-alert.sh",
            ],
        )
    ]


def test_terminal_launch_timeout_assumes_request_and_does_not_fallback(tmp_path, monkeypatch):
    calls = []

    monkeypatch.setattr(
        "console1706.terminal_action._terminal_candidates",
        lambda script_path, title="console-1706 Codex": [
            ("xfce4-terminal", ["xfce4-terminal", "--maximize", "--command", script_path]),
            ("gnome-terminal", ["gnome-terminal", "--maximize", "--", script_path]),
        ],
    )
    monkeypatch.setattr(
        "console1706.terminal_action.shutil.which",
        lambda command: "/usr/bin/setsid" if command == "setsid" else None,
    )

    def fake_run(command, **_kwargs):
        calls.append(command)
        raise subprocess.TimeoutExpired(command, timeout=3)

    monkeypatch.setattr("console1706.terminal_action.subprocess.run", fake_run)

    result = launch_host_alert_codex_terminal(
        {"_state_dir": str(tmp_path)},
        {"section": "services", "message": "Failed system service: x11vnc.service."},
    )

    assert result["status"] == "launch_requested"
    assert result["terminal"] == "xfce4-terminal"
    assert len(calls) == 1
