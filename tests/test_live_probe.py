from console1701 import live_probe


def test_parse_loadavg_tolerates_malformed_numbers(monkeypatch):
    monkeypatch.setattr(live_probe, "_read_text", lambda *_args, **_kwargs: "bad 0.25 nope 1/2 3")

    parsed = live_probe._parse_loadavg()

    assert parsed["one"] is None
    assert parsed["five"] == 0.25
    assert parsed["fifteen"] is None
    assert parsed["processes"] == "1/2"


def test_net_dev_tolerates_malformed_counters(monkeypatch):
    def fake_read(path, *_args, **_kwargs):
        path = str(path)
        if path == "/proc/net/dev":
            return (
                "Inter-| Receive | Transmit\n"
                " face |bytes packets errs drop fifo frame compressed multicast|"
                "bytes packets errs drop fifo colls carrier compressed\n"
                " eth0: bad 2 bad 4 0 0 0 0 8 bad 10 bad 0 0 0 0\n"
            )
        if path.endswith("/operstate"):
            return "up\n"
        if path.endswith("/carrier"):
            return "1\n"
        if path == "/proc/net/route":
            return ""
        return ""

    monkeypatch.setattr(live_probe, "_read_text", fake_read)
    monkeypatch.setattr(live_probe, "_interface_ipv4", lambda _iface: None)

    network = live_probe._net_dev()

    primary = network["primary"]
    assert primary["rx_bytes"] == 0
    assert primary["rx_packets"] == 2
    assert primary["rx_errors"] == 0
    assert primary["tx_bytes"] == 8
    assert primary["tx_packets"] == 0
    assert primary["tx_errors"] == 10
    assert primary["operstate"] == "up"
    assert primary["carrier"] == "1"


def test_read_live_snapshot_uses_local_only_sections(monkeypatch):
    monkeypatch.setattr(live_probe, "_parse_cpu", lambda: {"total": 1, "idle": 1, "busy": 0})
    monkeypatch.setattr(live_probe, "_parse_loadavg", lambda: {"one": 0.0})
    monkeypatch.setattr(live_probe, "_parse_pressure", lambda _resource: None)
    monkeypatch.setattr(live_probe, "_parse_meminfo", lambda: {"used_percent": 1.0})
    monkeypatch.setattr(live_probe, "_net_dev", lambda: {"interfaces": []})
    monkeypatch.setattr(live_probe, "_filesystem", lambda path: {"path": path, "total_bytes": 1})
    monkeypatch.setattr(live_probe, "_thermal", lambda: {"zones": [], "max_celsius": None})
    monkeypatch.setattr(live_probe, "_power", lambda: {"source": "not_detected"})

    snapshot = live_probe.read_live_snapshot()

    assert snapshot["cpu"]["times"] == {"total": 1, "idle": 1, "busy": 0}
    assert snapshot["network"] == {"interfaces": []}
    assert snapshot["power"]["source"] == "not_detected"
    assert "timestamp" in snapshot
    assert "monotonic_seconds" in snapshot
