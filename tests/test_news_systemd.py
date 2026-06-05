from __future__ import annotations

from pathlib import Path


def test_news_systemd_units_exist_and_run_news_scan():
    project_root = Path(__file__).resolve().parents[1]
    service_text = (
        project_root / "systemd" / "console-1701-news-scan.service"
    ).read_text(encoding="utf-8")
    timer_text = (
        project_root / "systemd" / "console-1701-news-scan.timer"
    ).read_text(encoding="utf-8")

    assert "Description=console-1701 recent-signal fixture ingest" in service_text
    assert "ExecStart=__PROJECT_DIR__/.venv/bin/console-1701 news-scan" in service_text
    assert "Unit=console-1701-news-scan.service" in timer_text
    assert "WantedBy=timers.target" in timer_text


def test_install_script_installs_but_does_not_enable_news_timer():
    project_root = Path(__file__).resolve().parents[1]
    script_text = (project_root / "scripts" / "install_user_service.sh").read_text(
        encoding="utf-8"
    )

    assert "console-1701-news-scan.service" in script_text
    assert "console-1701-news-scan.timer" in script_text
    assert "enable --now console-1701-news-scan.timer" not in script_text
    assert "left disabled" in script_text
