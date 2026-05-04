from __future__ import annotations

import fcntl
import ipaddress
import os
import shutil
import socket
import struct
import time
from pathlib import Path
from typing import Any


def _read_text(path: str | Path, max_chars: int = 262144) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return ""


def _human_bytes(value: int | float | None) -> str | None:
    if value is None:
        return None
    number = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(number) < 1024 or unit == "TiB":
            return f"{number:.1f} {unit}" if unit != "B" else f"{int(number)} B"
        number /= 1024
    return f"{number:.1f} TiB"


def _percent(used: int | float, total: int | float) -> float | None:
    if not total:
        return None
    return round(float(used) / float(total) * 100, 1)


def _parse_cpu() -> dict[str, Any]:
    line = next(
        (item for item in _read_text("/proc/stat", 8192).splitlines() if item.startswith("cpu ")),
        "",
    )
    parts = line.split()[1:]
    values = [int(part) for part in parts if part.isdigit()]
    idle = (values[3] if len(values) > 3 else 0) + (values[4] if len(values) > 4 else 0)
    total = sum(values)
    return {"total": total, "idle": idle, "busy": total - idle}


def _parse_loadavg() -> dict[str, Any]:
    parts = _read_text("/proc/loadavg", 256).split()
    return {
        "one": float(parts[0]) if len(parts) > 0 else None,
        "five": float(parts[1]) if len(parts) > 1 else None,
        "fifteen": float(parts[2]) if len(parts) > 2 else None,
        "processes": parts[3] if len(parts) > 3 else None,
    }


def _parse_pressure(resource: str) -> dict[str, Any] | None:
    parsed: dict[str, Any] = {}
    for line in _read_text(f"/proc/pressure/{resource}", 1024).splitlines():
        parts = line.split()
        if not parts:
            continue
        series = {}
        for item in parts[1:]:
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            try:
                series[key] = float(value)
            except ValueError:
                continue
        parsed[parts[0]] = series
    return parsed or None


def _parse_meminfo() -> dict[str, Any]:
    raw = {}
    for line in _read_text("/proc/meminfo").splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        number = rest.strip().split(maxsplit=1)[0]
        if number.isdigit():
            raw[key] = int(number)

    total_kb = raw.get("MemTotal", 0)
    available_kb = raw.get("MemAvailable", raw.get("MemFree", 0))
    used_kb = max(total_kb - available_kb, 0)
    swap_total_kb = raw.get("SwapTotal", 0)
    swap_free_kb = raw.get("SwapFree", 0)
    swap_used_kb = max(swap_total_kb - swap_free_kb, 0)
    return {
        "total_bytes": total_kb * 1024,
        "available_bytes": available_kb * 1024,
        "used_bytes": used_kb * 1024,
        "used_percent": _percent(used_kb, total_kb),
        "available_percent": _percent(available_kb, total_kb),
        "swap_total_bytes": swap_total_kb * 1024,
        "swap_used_bytes": swap_used_kb * 1024,
        "swap_used_percent": _percent(swap_used_kb, swap_total_kb),
        "human_total": _human_bytes(total_kb * 1024),
        "human_available": _human_bytes(available_kb * 1024),
        "human_used": _human_bytes(used_kb * 1024),
    }


def _decode_gateway(hex_value: str) -> str | None:
    try:
        return socket.inet_ntoa(int(hex_value, 16).to_bytes(4, byteorder="little"))
    except (OSError, ValueError):
        return None


def _default_route() -> dict[str, Any] | None:
    for line in _read_text("/proc/net/route").splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        iface, destination, gateway, flags = parts[:4]
        try:
            flag_value = int(flags, 16)
        except ValueError:
            flag_value = 0
        if destination == "00000000" and flag_value & 0x2:
            return {"interface": iface, "gateway": _decode_gateway(gateway)}
    return None


def _interface_ipv4(iface: str | None) -> str | None:
    if not iface:
        return None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            packed = struct.pack("256s", iface[:15].encode("utf-8"))
            result = fcntl.ioctl(sock.fileno(), 0x8915, packed)
            return socket.inet_ntoa(result[20:24])
    except OSError:
        return None


def _public_ip_from_local_address(address: str | None) -> str | None:
    if not address:
        return None
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return None
    return address if parsed.is_global else None


def _net_dev() -> dict[str, Any]:
    interfaces = []
    for line in _read_text("/proc/net/dev").splitlines()[2:]:
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        iface_name = name.strip()
        fields = rest.split()
        if len(fields) < 16:
            continue
        interfaces.append(
            {
                "name": iface_name,
                "rx_bytes": int(fields[0]),
                "rx_packets": int(fields[1]),
                "rx_errors": int(fields[2]),
                "rx_dropped": int(fields[3]),
                "tx_bytes": int(fields[8]),
                "tx_packets": int(fields[9]),
                "tx_errors": int(fields[10]),
                "tx_dropped": int(fields[11]),
                "operstate": _read_text(f"/sys/class/net/{iface_name}/operstate", 64).strip()
                or None,
                "carrier": _read_text(f"/sys/class/net/{iface_name}/carrier", 64).strip()
                or None,
            }
        )
    route = _default_route()
    primary_name = (route or {}).get("interface") or next(
        (iface["name"] for iface in interfaces if iface["name"] != "lo"),
        None,
    )
    primary = next((iface for iface in interfaces if iface["name"] == primary_name), None)
    lan_ip = _interface_ipv4(primary_name)
    return {
        "interfaces": interfaces,
        "primary_interface": primary_name,
        "primary": primary,
        "lan_ip": lan_ip,
        "gateway": (route or {}).get("gateway"),
        "wan_ip": _public_ip_from_local_address(lan_ip),
        "wan_ip_status": (
            "local public interface"
            if _public_ip_from_local_address(lan_ip)
            else "not tested; external lookup disabled"
        ),
    }


def _filesystem(path: str) -> dict[str, Any] | None:
    try:
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    return {
        "path": path,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "available_bytes": usage.free,
        "used_percent": _percent(usage.used, usage.total),
        "human_total": _human_bytes(usage.total),
        "human_used": _human_bytes(usage.used),
        "human_available": _human_bytes(usage.free),
    }


def _thermal() -> dict[str, Any]:
    zones = []
    for zone in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        temp_text = _read_text(zone / "temp", 64).strip()
        if not temp_text:
            continue
        try:
            raw_temp = float(temp_text)
        except ValueError:
            continue
        temp_celsius = raw_temp / 1000 if raw_temp > 1000 else raw_temp
        trip_points = []
        for trip_temp in sorted(zone.glob("trip_point_*_temp")):
            index = trip_temp.name.removeprefix("trip_point_").removesuffix("_temp")
            trip_text = _read_text(trip_temp, 64).strip()
            try:
                raw_trip = float(trip_text)
            except ValueError:
                continue
            trip_celsius = raw_trip / 1000 if raw_trip > 1000 else raw_trip
            if trip_celsius < 0:
                continue
            trip_points.append(
                {
                    "index": index,
                    "type": _read_text(zone / f"trip_point_{index}_type", 128).strip()
                    or None,
                    "temp_celsius": round(trip_celsius, 1),
                }
            )
        zones.append(
            {
                "name": zone.name,
                "type": _read_text(zone / "type", 128).strip() or None,
                "temp_celsius": round(temp_celsius, 1),
                "trip_points": trip_points,
            }
        )
    return {
        "zones": zones,
        "max_celsius": max((zone["temp_celsius"] for zone in zones), default=None),
    }


def _power() -> dict[str, Any]:
    supplies = []
    power_dir = Path("/sys/class/power_supply")
    if not power_dir.exists():
        return {
            "supplies": [],
            "battery_present": False,
            "ac_online": None,
            "battery_percent": None,
            "battery_status": None,
            "on_battery": False,
            "source": "not_detected",
        }

    for supply_dir in sorted(power_dir.iterdir()):
        if not supply_dir.is_dir():
            continue
        supply = {
            "name": supply_dir.name,
            "type": _read_text(supply_dir / "type", 64).strip() or None,
            "status": _read_text(supply_dir / "status", 64).strip() or None,
            "capacity": _read_text(supply_dir / "capacity", 64).strip() or None,
            "online": _read_text(supply_dir / "online", 64).strip() or None,
        }
        try:
            supply["capacity_percent"] = (
                int(supply["capacity"]) if supply["capacity"] is not None else None
            )
        except ValueError:
            supply["capacity_percent"] = None
        supplies.append(supply)

    batteries = [supply for supply in supplies if supply.get("type") == "Battery"]
    ac_supplies = [
        supply
        for supply in supplies
        if supply.get("type") in {"Mains", "USB", "USB_C", "USB_PD"}
    ]
    ac_online = any(supply.get("online") == "1" for supply in ac_supplies) if ac_supplies else None
    battery_percent = next(
        (
            battery.get("capacity_percent")
            for battery in batteries
            if battery.get("capacity_percent") is not None
        ),
        None,
    )
    battery_status = next(
        (battery.get("status") for battery in batteries if battery.get("status")),
        None,
    )
    battery_present = bool(batteries)
    on_battery = battery_present and (
        ac_online is False or str(battery_status).lower() == "discharging"
    )
    if on_battery:
        source = "battery"
    elif ac_online is True:
        source = "external"
    elif battery_present:
        source = "battery_state_unknown"
    else:
        source = "no_battery_detected"
    return {
        "supplies": supplies,
        "battery_present": battery_present,
        "ac_online": ac_online,
        "battery_percent": battery_percent,
        "battery_status": battery_status,
        "on_battery": on_battery,
        "source": source,
    }


def read_live_snapshot() -> dict[str, Any]:
    home = str(Path.home())
    filesystems = {"root": _filesystem("/"), "home": _filesystem(home)}
    if filesystems["home"] and filesystems["root"]:
        if filesystems["home"]["total_bytes"] == filesystems["root"]["total_bytes"]:
            filesystems["home"] = None
    return {
        "timestamp": time.time(),
        "monotonic_seconds": time.monotonic(),
        "cpu": {
            "times": _parse_cpu(),
            "load": _parse_loadavg(),
            "count": os.cpu_count(),
            "pressure": _parse_pressure("cpu"),
        },
        "memory": _parse_meminfo(),
        "network": _net_dev(),
        "filesystems": filesystems,
        "pressure": {
            "memory": _parse_pressure("memory"),
            "io": _parse_pressure("io"),
        },
        "thermal": _thermal(),
        "power": _power(),
    }
