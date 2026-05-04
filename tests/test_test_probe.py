from __future__ import annotations

import subprocess

from console1701.test_probe import run_test_command


def test_run_test_command_combines_stdout_and_stderr(monkeypatch, tmp_path):
    def fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args="pytest",
            returncode=1,
            stdout="stdout evidence",
            stderr="stderr evidence",
        )

    monkeypatch.setattr("console1701.test_probe.subprocess.run", fake_run)

    result = run_test_command("pytest", tmp_path, timeout=10)

    assert result["status"] == "fail"
    assert result["summary"] == "Tests failed."
    assert "stdout evidence" in result["raw_tail"]
    assert "stderr evidence" in result["raw_tail"]


def test_run_test_command_timeout_preserves_captured_bytes(monkeypatch, tmp_path):
    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(
            cmd="pytest",
            timeout=1,
            output=b"partial stdout",
            stderr=b"partial stderr",
        )

    monkeypatch.setattr("console1701.test_probe.subprocess.run", fake_run)

    result = run_test_command("pytest", tmp_path, timeout=1)

    assert result["status"] == "timeout"
    assert result["summary"] == "Test command timed out after 1 seconds."
    assert "partial stdout" in result["raw_tail"]
    assert "partial stderr" in result["raw_tail"]


def test_run_test_command_os_error_reports_error_status(monkeypatch, tmp_path):
    def fake_run(*_args, **_kwargs):
        raise OSError("cannot execute")

    monkeypatch.setattr("console1701.test_probe.subprocess.run", fake_run)

    result = run_test_command("pytest", tmp_path, timeout=10)

    assert result["status"] == "error"
    assert result["summary"] == "cannot execute"
    assert result["raw_tail"] == "cannot execute"
