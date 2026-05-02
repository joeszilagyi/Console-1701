from __future__ import annotations

from pathlib import Path

from console1706.terminal_action import (
    build_host_alert_prompt,
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
