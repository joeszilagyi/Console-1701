from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _copy_scan_once_script(tmp_path: Path) -> tuple[Path, Path, Path]:
    project_root = tmp_path / "project"
    script_dir = project_root / "scripts"
    venv_bin_dir = project_root / ".venv" / "bin"
    script_dir.mkdir(parents=True)
    venv_bin_dir.mkdir(parents=True)

    source_script = Path(__file__).resolve().parents[1] / "scripts" / "scan_once.sh"
    target_script = script_dir / "scan_once.sh"
    shutil.copy2(source_script, target_script)

    return project_root, target_script, venv_bin_dir / "console-1701"


def _write_cli(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def test_scan_once_check_reports_runnable_cli(tmp_path):
    project_root, script_path, cli_path = _copy_scan_once_script(tmp_path)
    _write_cli(
        cli_path,
        """#!/usr/bin/env bash
if [[ ${1:-} == --version ]]; then
  printf 'console-1701 0.0\n'
  exit 0
fi
exit 0
""",
    )

    result = subprocess.run(
        ["bash", str(script_path), "--check"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Project:" in result.stdout
    assert "CLI:" in result.stdout
    assert "(runnable)" in result.stdout
    assert result.stderr == ""


def test_scan_once_check_rejects_broken_cli(tmp_path):
    project_root, script_path, cli_path = _copy_scan_once_script(tmp_path)
    _write_cli(
        cli_path,
        """#!/usr/bin/env bash
exit 1
""",
    )

    result = subprocess.run(
        ["bash", str(script_path), "--check"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "present but not runnable" in result.stdout
    assert result.stderr == ""
