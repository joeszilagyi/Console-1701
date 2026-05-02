from __future__ import annotations

from console1706.db import connect_db, init_db
from console1706.evidence import get_host_summary, get_latest_host_snapshot
from console1706.scanner import insert_host_snapshot
from console1706.system_probe import (
    _describe_failed_units,
    _redact_sensitive_identifiers,
    _run_command,
    interpret_filesystem_health,
    parse_cpuinfo,
    parse_ip_addr_json,
    parse_lsblk_json,
    parse_meminfo,
    parse_os_release,
)


def test_parse_os_release_handles_quoted_values():
    data = parse_os_release(
        """
PRETTY_NAME="Debian GNU/Linux 13 (trixie)"
NAME="Debian GNU/Linux"
ID=debian
VERSION_ID="13"
""".strip()
    )

    assert data["PRETTY_NAME"] == "Debian GNU/Linux 13 (trixie)"
    assert data["ID"] == "debian"
    assert data["VERSION_ID"] == "13"


def test_parse_meminfo_computes_available_and_used_percent():
    memory = parse_meminfo(
        """
MemTotal:       8000000 kB
MemFree:        1000000 kB
MemAvailable:  5000000 kB
SwapTotal:      2000000 kB
SwapFree:       1500000 kB
""".strip()
    )

    assert memory["total_kb"] == 8000000
    assert memory["available_kb"] == 5000000
    assert memory["used_kb"] == 3000000
    assert memory["available_percent"] == 62.5
    assert memory["swap_used_kb"] == 500000


def test_parse_cpuinfo_returns_sane_partial_info():
    cpu = parse_cpuinfo(
        """
processor   : 0
vendor_id   : GenuineIntel
model name  : Example CPU
physical id : 0
core id     : 0

processor   : 1
vendor_id   : GenuineIntel
model name  : Example CPU
physical id : 0
core id     : 1
""".strip()
    )

    assert cpu["model"] == "Example CPU"
    assert cpu["threads"] == 2
    assert cpu["cores"] == 2
    assert cpu["sockets"] == 1


def test_parse_lsblk_json_handles_missing_fields():
    parsed = parse_lsblk_json(
        {
            "blockdevices": [
                {
                    "name": "sda",
                    "type": "disk",
                    "size": "100G",
                    "children": [{"name": "sda1", "type": "part"}],
                }
            ]
        }
    )

    assert parsed["blockdevices"][0]["name"] == "sda"
    assert parsed["blockdevices"][0]["children"][0]["name"] == "sda1"
    assert "serial" not in parsed["blockdevices"][0]


def test_parse_ip_addr_json_handles_loopback_and_ethernet_with_redacted_mac():
    parsed = parse_ip_addr_json(
        [
            {
                "ifname": "lo",
                "operstate": "UNKNOWN",
                "address": "00:00:00:00:00:00",
                "addr_info": [{"family": "inet", "local": "127.0.0.1", "prefixlen": 8}],
            },
            {
                "ifname": "enp1s0",
                "operstate": "UP",
                "address": "aa:bb:cc:dd:ee:ff",
                "addr_info": [{"family": "inet", "local": "192.168.1.22", "prefixlen": 24}],
            },
        ],
        show_sensitive=False,
    )

    assert parsed[0]["ifname"] == "lo"
    assert parsed[1]["ifname"] == "enp1s0"
    assert parsed[1]["address"] == "hidden"
    assert parsed[1]["addresses"][0]["local"] == "192.168.1.22"


def test_filesystem_health_flags_high_root_usage():
    penalties = interpret_filesystem_health(
        [
            {
                "mountpoint": "/",
                "fstype": "ext4",
                "use_percent": 96.0,
                "virtual": False,
            }
        ]
    )

    assert penalties[0]["severity"] == "red"
    assert penalties[0]["section"] == "storage"


def test_missing_optional_command_is_recorded_without_crash():
    evidence = {}
    result = _run_command(
        "missing",
        ["definitely-not-a-console1706-command"],
        timeout=1,
        evidence=evidence,
    )

    assert result["available"] is False
    assert evidence["commands"]["missing"]["available"] is False


def test_failed_unit_description_names_unit_and_reason():
    message, why, next_action = _describe_failed_units(
        [
            {
                "unit": "x11vnc.service",
                "active": "failed",
                "sub": "failed",
                "description": "VNC server for X11",
                "diagnostics": {
                    "Result": "exit-code",
                    "ExecMainStatus": "1",
                },
                "recent_logs": ["2026-05-01T12:00:00 host x11vnc[1]: display :0 unavailable"],
            }
        ],
        scope="system",
    )

    assert message == "Failed system service: x11vnc.service."
    assert "systemctl reports x11vnc.service" in why
    assert "Result=exit-code" in why
    assert "ExecMainStatus=1" in why
    assert "display :0 unavailable" in why
    assert "systemctl status x11vnc.service" in next_action


def test_sensitive_host_evidence_is_redacted():
    redacted = _redact_sensitive_identifiers(
        {
            "hostnamectl": {
                "Machine ID": "e5b64059432c44f2bf5f6e1e07c9d270",
                "Boot ID": "2e55fbfd-e964-4d01-b209-9eb58553cbe9",
            },
            "command": {
                "stdout": (
                    "Machine ID: e5b64059432c44f2bf5f6e1e07c9d270\n"
                    "Boot ID: 2e55fbfd-e964-4d01-b209-9eb58553cbe9\n"
                    "MAC: aa:bb:cc:dd:ee:ff"
                )
            },
        }
    )

    assert redacted["hostnamectl"]["Machine ID"] == "hidden"
    assert redacted["hostnamectl"]["Boot ID"] == "hidden"
    assert "e5b64059432c44f2bf5f6e1e07c9d270" not in redacted["command"]["stdout"]
    assert "2e55fbfd-e964-4d01-b209-9eb58553cbe9" not in redacted["command"]["stdout"]
    assert "aa:bb:cc:dd:ee:ff" not in redacted["command"]["stdout"]


def test_host_snapshot_insert_and_read_round_trip(tmp_path):
    conn = connect_db(tmp_path / "console.sqlite")
    init_db(conn)
    snapshot = {
        "identity": {"hostname": "demo-host"},
        "os": {"pretty_name": "Debian GNU/Linux 13"},
        "kernel": {"release": "6.12.0"},
        "session": {"uptime_seconds": 123.0},
        "health": {
            "state": "OK",
            "score": 100,
            "severity": "green",
            "headline": "No host issues",
            "summary": "Host is OK.",
            "next_sane_action": "No action needed.",
            "penalties": [],
            "checks": {},
        },
        "evidence": {"files": {"/etc/os-release": "PRETTY_NAME=Debian"}},
        "probe_errors": [],
    }

    insert_host_snapshot(conn, "2026-05-01T12:00:00-07:00", snapshot)

    latest = get_latest_host_snapshot(conn)
    summary = get_host_summary(conn)

    assert latest["hostname"] == "demo-host"
    assert latest["health_state"] == "OK"
    assert summary["state"] == "OK"
    assert summary["changes"] == ["No previous host snapshot to compare yet."]
