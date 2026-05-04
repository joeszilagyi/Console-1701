from __future__ import annotations

import shutil
import subprocess

import pytest

from console1701.git_probe import _run_git, probe_repo

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_git_probe_reads_dirty_repo_without_upstream(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(
        repo,
        "-c",
        "user.name=console",
        "-c",
        "user.email=console@example.invalid",
        "commit",
        "-m",
        "init",
    )
    (repo / "README.md").write_text("hello\nchanged\n", encoding="utf-8")

    result = probe_repo(repo)

    assert result["scan_error"] is None
    assert result["is_dirty"] is True
    assert result["ahead_count"] is None
    assert result["behind_count"] is None
    assert result["changed_files"] == ["README.md"]


def test_run_git_timeout_preserves_captured_byte_output(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()

    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(
            cmd=["git"],
            timeout=1,
            output=b"partial stdout",
            stderr=b"partial stderr",
        )

    monkeypatch.setattr("console1701.git_probe.subprocess.run", fake_run)

    code, stdout, stderr = _run_git(repo, ["status"], timeout=1)

    assert code == 124
    assert stdout == "partial stdout"
    assert "partial stderr" in stderr
    assert "timed out after 1 seconds" in stderr
