from console1701.log_probe import probe_configured_logs, tail_file


def test_probe_configured_logs_reports_missing_log_path():
    events = probe_configured_logs({"logs": [{"name": "broken"}], "scan": {}})

    assert len(events) == 1
    assert events[0]["source"] == "broken"
    assert events[0]["source_path"] == "<missing-log-path>"
    assert events[0]["category"] == "LOG_CONFIG_ERROR"
    assert "missing a path" in events[0]["message"]


def test_probe_configured_logs_uses_default_for_invalid_tail_limit(tmp_path):
    log_path = tmp_path / "app.log"
    log_path.write_text("codex start\n", encoding="utf-8")

    events = probe_configured_logs(
        {
            "scan": {"log_tail_max_bytes": "not-an-int"},
            "logs": [{"name": "app", "path": str(log_path)}],
        }
    )

    assert len(events) == 1
    assert events[0]["source"] == "app"
    assert events[0]["category"] == "START"
    assert events[0]["message"] == "codex start"


def test_tail_file_negative_limit_is_empty(tmp_path):
    log_path = tmp_path / "app.log"
    log_path.write_text("this should not be read\n", encoding="utf-8")

    assert tail_file(log_path, -1) == ""


def test_probe_configured_logs_reports_invalid_log_entry():
    events = probe_configured_logs({"logs": ["not-a-mapping"], "scan": {}})

    assert len(events) == 1
    assert events[0]["source"] == "log"
    assert events[0]["source_path"] == "<invalid-log-config>"
    assert events[0]["category"] == "LOG_CONFIG_ERROR"


def test_probe_configured_logs_reports_invalid_logs_config():
    events = probe_configured_logs({"logs": "not-a-list", "scan": {}})

    assert len(events) == 1
    assert events[0]["source_path"] == "<invalid-logs-config>"
    assert events[0]["category"] == "LOG_CONFIG_ERROR"


def test_probe_configured_logs_reports_invalid_path_type():
    events = probe_configured_logs({"logs": [{"name": "bad", "path": 42}], "scan": None})

    assert len(events) == 1
    assert events[0]["source"] == "bad"
    assert events[0]["source_path"] == "<invalid-log-path>"
    assert events[0]["category"] == "LOG_CONFIG_ERROR"
