from __future__ import annotations

import shutil
import subprocess

import pytest

from console1706.git_probe import probe_repo

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
