from __future__ import annotations

import json
import os
import platform
import re
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_COMMAND_TIMEOUT_SECONDS = 3
MAX_EVIDENCE_CHARS = 12000
VIRTUAL_FS_TYPES = {
    "autofs",
    "binfmt_misc",
    "bpf",
    "cgroup",
    "cgroup2",
    "configfs",
    "debugfs",
    "devpts",
    "devtmpfs",
    "efivarfs",
    "fusectl",
    "hugetlbfs",
    "mqueue",
    "nsfs",
    "overlay",
    "proc",
    "pstore",
    "ramfs",
    "rpc_pipefs",
    "securityfs",
    "sysfs",
    "tmpfs",
    "tracefs",
}
SENSITIVE_KEY_TERMS = (
    "machine id",
    "machine-id",
    "boot id",
    "boot-id",
    "uuid",
    "serial",
    "mac address",
    "disk serial",
)
SENSITIVE_LINE_RE = re.compile(
    r"(?im)^(\s*(?:machine id|boot id|product uuid|system uuid|uuid|"
    r"serial number|serial|disk serial|hardware serial)\s*:?\s*).+$"
)
MAC_ADDRESS_RE = re.compile(r"\b[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5}\b")
UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


def _trim(value: str | None, max_chars: int = MAX_EVIDENCE_CHARS) -> str:
    if not value:
        return ""
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars]}\n...[truncated]"


def _trim_inline(value: str | None, max_chars: int = 240) -> str:
    text = " ".join((value or "").split())
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}..."


def _read_text(
    path: str | Path,
    errors: list[dict[str, str]],
    max_chars: int = 65536,
) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError as exc:
        errors.append({"section": "files", "message": f"Could not read {path}: {exc}"})
        return None


def _read_optional_text(path: str | Path, max_chars: int = 65536) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return None


def _read_sysfs_value(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None


def _human_bytes(value: int | float | None) -> str | None:
    if value is None:
        return None
    number = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB", "PiB"):
        if abs(number) < 1024 or unit == "PiB":
            return f"{number:.1f} {unit}" if unit != "B" else f"{int(number)} B"
        number /= 1024
    return f"{number:.1f} PiB"


def _percent(used: int | float, total: int | float) -> float | None:
    if not total:
        return None
    return round((float(used) / float(total)) * 100, 1)


def _format_uptime(seconds: float | None) -> str | None:
    if seconds is None:
        return None
    total = int(seconds)
    days, remainder = divmod(total, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _seconds = divmod(remainder, 60)
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _redact_mac(value: str | None, show_sensitive: bool) -> str | None:
    if not value:
        return None
    if show_sensitive:
        return value
    if value == "00:00:00:00:00:00":
        return value
    return "hidden"


def _maybe_sensitive(value: str | None, show_sensitive: bool) -> str | None:
    if not value:
        return value
    return value if show_sensitive else "hidden"


def _is_sensitive_key(key: str | None) -> bool:
    if not key:
        return False
    normalized = key.lower().replace("_", " ").replace("-", " ")
    return any(term.replace("-", " ") in normalized for term in SENSITIVE_KEY_TERMS)


def _redact_sensitive_text(value: str) -> str:
    redacted = SENSITIVE_LINE_RE.sub(r"\1hidden", value)
    redacted = MAC_ADDRESS_RE.sub("hidden", redacted)
    return UUID_RE.sub("hidden", redacted)


def _redact_sensitive_identifiers(value: Any, key: str | None = None) -> Any:
    if _is_sensitive_key(key):
        return None if value is None else "hidden"
    if isinstance(value, dict):
        return {
            item_key: _redact_sensitive_identifiers(item_value, str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_redact_sensitive_identifiers(item) for item in value]
    if isinstance(value, str):
        return _redact_sensitive_text(value)
    return value


def parse_os_release(text: str | None) -> dict[str, str]:
    if not text:
        return {}
    data: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        data[key] = value
    return data


def parse_uptime(text: str | None) -> dict[str, float | None]:
    if not text:
        return {"uptime_seconds": None, "idle_seconds": None}
    parts = text.split()
    try:
        uptime = float(parts[0])
    except (IndexError, ValueError):
        uptime = None
    try:
        idle = float(parts[1])
    except (IndexError, ValueError):
        idle = None
    return {"uptime_seconds": uptime, "idle_seconds": idle}


def parse_meminfo(text: str | None) -> dict[str, Any]:
    raw: dict[str, int] = {}
    for line in (text or "").splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        match = re.search(r"(\d+)", rest)
        if match:
            raw[key] = int(match.group(1))

    total_kb = raw.get("MemTotal")
    available_kb = raw.get("MemAvailable", raw.get("MemFree"))
    free_kb = raw.get("MemFree")
    swap_total_kb = raw.get("SwapTotal", 0)
    swap_free_kb = raw.get("SwapFree", 0)
    used_kb = total_kb - available_kb if total_kb is not None and available_kb is not None else None
    swap_used_kb = swap_total_kb - swap_free_kb

    total_bytes = total_kb * 1024 if total_kb is not None else None
    available_bytes = available_kb * 1024 if available_kb is not None else None
    used_bytes = used_kb * 1024 if used_kb is not None else None
    swap_total_bytes = swap_total_kb * 1024
    swap_used_bytes = swap_used_kb * 1024

    return {
        "raw_kb": raw,
        "total_kb": total_kb,
        "available_kb": available_kb,
        "free_kb": free_kb,
        "used_kb": used_kb,
        "swap_total_kb": swap_total_kb,
        "swap_free_kb": swap_free_kb,
        "swap_used_kb": swap_used_kb,
        "total_bytes": total_bytes,
        "available_bytes": available_bytes,
        "used_bytes": used_bytes,
        "swap_total_bytes": swap_total_bytes,
        "swap_used_bytes": swap_used_bytes,
        "used_percent": _percent(used_kb or 0, total_kb or 0),
        "available_percent": _percent(available_kb or 0, total_kb or 0),
        "human_total": _human_bytes(total_bytes),
        "human_available": _human_bytes(available_bytes),
        "human_used": _human_bytes(used_bytes),
    }


def parse_cpuinfo(text: str | None) -> dict[str, Any]:
    processors: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in (text or "").splitlines():
        if not line.strip():
            if current:
                processors.append(current)
                current = {}
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current[key.strip()] = value.strip()
    if current:
        processors.append(current)

    model = None
    vendor = None
    physical_ids: set[str] = set()
    core_ids: set[tuple[str, str]] = set()
    for processor in processors:
        model = model or processor.get("model name") or processor.get("Processor")
        vendor = vendor or processor.get("vendor_id") or processor.get("CPU implementer")
        physical_id = processor.get("physical id")
        core_id = processor.get("core id")
        if physical_id is not None:
            physical_ids.add(physical_id)
        if physical_id is not None and core_id is not None:
            core_ids.add((physical_id, core_id))

    return {
        "model": model,
        "vendor": vendor,
        "threads": len(processors) or None,
        "sockets": len(physical_ids) or None,
        "cores": len(core_ids) or None,
    }


def parse_loadavg(text: str | None) -> dict[str, Any]:
    parts = (text or "").split()
    result: dict[str, Any] = {
        "one": None,
        "five": None,
        "fifteen": None,
        "running": None,
        "processes": None,
        "last_pid": None,
    }
    try:
        result["one"] = float(parts[0])
        result["five"] = float(parts[1])
        result["fifteen"] = float(parts[2])
    except (IndexError, ValueError):
        pass
    if len(parts) >= 4 and "/" in parts[3]:
        running, processes = parts[3].split("/", 1)
        try:
            result["running"] = int(running)
            result["processes"] = int(processes)
        except ValueError:
            pass
    if len(parts) >= 5:
        try:
            result["last_pid"] = int(parts[4])
        except ValueError:
            pass
    return result


def parse_mounts(text: str | None) -> list[dict[str, Any]]:
    mounts: list[dict[str, Any]] = []
    for line in (text or "").splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        device, mountpoint, fstype, options = parts[:4]
        mounts.append(
            {
                "device": device.replace("\\040", " "),
                "mountpoint": mountpoint.replace("\\040", " "),
                "fstype": fstype,
                "options": options.split(","),
                "virtual": fstype in VIRTUAL_FS_TYPES,
            }
        )
    return mounts


def parse_lsblk_json(payload: str | dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {"blockdevices": []}
    if isinstance(payload, str):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return {"blockdevices": []}
    else:
        data = payload
    devices = data.get("blockdevices") if isinstance(data, dict) else []
    if not isinstance(devices, list):
        devices = []
    return {"blockdevices": [_clean_lsblk_device(device) for device in devices]}


def _clean_lsblk_device(device: Any) -> dict[str, Any]:
    if not isinstance(device, dict):
        return {}
    allowed = {
        "name",
        "type",
        "size",
        "mountpoint",
        "mountpoints",
        "fstype",
        "model",
        "tran",
        "rota",
        "rm",
        "state",
    }
    cleaned = {key: device.get(key) for key in allowed if key in device}
    children = device.get("children")
    if isinstance(children, list):
        cleaned["children"] = [_clean_lsblk_device(child) for child in children]
    return cleaned


def parse_df_pt(text: str | None) -> list[dict[str, Any]]:
    filesystems: list[dict[str, Any]] = []
    lines = (text or "").splitlines()
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 7:
            continue
        filesystem, fstype, blocks, used, available, capacity = parts[:6]
        mountpoint = " ".join(parts[6:])
        try:
            total_bytes = int(blocks) * 1024
            used_bytes = int(used) * 1024
            available_bytes = int(available) * 1024
            use_percent = float(capacity.rstrip("%"))
        except ValueError:
            continue
        filesystems.append(
            {
                "device": filesystem,
                "fstype": fstype,
                "mountpoint": mountpoint,
                "total_bytes": total_bytes,
                "used_bytes": used_bytes,
                "available_bytes": available_bytes,
                "use_percent": use_percent,
                "human_total": _human_bytes(total_bytes),
                "human_used": _human_bytes(used_bytes),
                "human_available": _human_bytes(available_bytes),
                "virtual": fstype in VIRTUAL_FS_TYPES,
            }
        )
    return filesystems


def parse_ip_addr_json(
    payload: str | list[Any] | None,
    *,
    show_sensitive: bool = False,
) -> list[dict[str, Any]]:
    if not payload:
        return []
    if isinstance(payload, str):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return []
    else:
        data = payload
    if not isinstance(data, list):
        return []

    interfaces: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        addresses = []
        for address in item.get("addr_info") or []:
            if not isinstance(address, dict):
                continue
            family = address.get("family")
            local = address.get("local")
            if family in {"inet", "inet6"} and local:
                addresses.append(
                    {
                        "family": family,
                        "local": local,
                        "prefixlen": address.get("prefixlen"),
                        "scope": address.get("scope"),
                    }
                )
        interfaces.append(
            {
                "ifname": item.get("ifname"),
                "operstate": item.get("operstate"),
                "flags": item.get("flags") or [],
                "address": _redact_mac(item.get("address"), show_sensitive),
                "addresses": addresses,
            }
        )
    return interfaces


def parse_ip_route_json(payload: str | list[Any] | None) -> list[dict[str, Any]]:
    if not payload:
        return []
    if isinstance(payload, str):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return []
    else:
        data = payload
    if not isinstance(data, list):
        return []
    routes = []
    for item in data:
        if not isinstance(item, dict):
            continue
        routes.append(
            {
                "dst": item.get("dst"),
                "gateway": item.get("gateway"),
                "dev": item.get("dev"),
                "protocol": item.get("protocol"),
                "scope": item.get("scope"),
                "prefsrc": item.get("prefsrc"),
                "metric": item.get("metric"),
            }
        )
    return routes


def interpret_filesystem_health(filesystems: list[dict[str, Any]]) -> list[dict[str, Any]]:
    penalties: list[dict[str, Any]] = []
    root = next((fs for fs in filesystems if fs.get("mountpoint") == "/"), None)
    if root and root.get("use_percent") is not None:
        usage = float(root["use_percent"])
        if usage >= 95:
            penalties.append(
                {
                    "severity": "red",
                    "section": "storage",
                    "message": f"Root filesystem is critically full at {usage:.1f}%.",
                    "penalty": 45,
                    "evidence": {"mountpoint": "/", "use_percent": usage},
                }
            )
        elif usage >= 85:
            penalties.append(
                {
                    "severity": "amber",
                    "section": "storage",
                    "message": f"Root filesystem is above 85% used ({usage:.1f}%).",
                    "penalty": 20,
                    "evidence": {"mountpoint": "/", "use_percent": usage},
                }
            )

    for fs in filesystems:
        mountpoint = fs.get("mountpoint")
        if fs.get("virtual") or mountpoint == "/" or fs.get("use_percent") is None:
            continue
        if mountpoint not in {"/home", "/boot", "/boot/efi", "/var"}:
            continue
        usage = float(fs["use_percent"])
        if usage >= 90:
            penalties.append(
                {
                    "severity": "amber",
                    "section": "storage",
                    "message": f"{mountpoint} is above 90% used ({usage:.1f}%).",
                    "penalty": 15,
                    "evidence": {"mountpoint": mountpoint, "use_percent": usage},
                }
            )
    return penalties


def _explain_penalty(penalty: dict[str, Any]) -> dict[str, Any]:
    section = str(penalty.get("section") or "host")
    message = str(penalty.get("message") or "")
    defaults = {
        "storage": (
            "Filesystem pressure can break updates, logs, package operations, "
            "and application writes.",
            "Inspect filesystem usage and remove or move data before continuing heavy work.",
        ),
        "identity": (
            "The console needs host, OS, and kernel facts before it can make a "
            "trustworthy machine readout.",
            "Open probe evidence and check local files such as /etc/os-release and platform data.",
        ),
        "network": (
            "Local route and DNS state determine whether this machine can reach "
            "local and external services.",
            "Inspect interface, route, and DNS evidence before assuming connectivity is healthy.",
        ),
        "memory": (
            "Low available memory can cause stalls, swapping, failed builds, "
            "and service instability.",
            "Inspect top memory processes and close or restart the process causing pressure.",
        ),
        "cpu": (
            "Load above available CPU capacity means work is queued and the "
            "machine may feel stuck.",
            "Inspect top CPU processes and decide whether the load is expected.",
        ),
        "services": (
            "A failed service is a concrete systemd failure, not just a warning metric.",
            "Open failed unit evidence and inspect the named unit before trusting host health.",
        ),
        "power": (
            "Battery state affects whether the machine can keep running without external power.",
            "Connect power or reduce load before starting long work.",
        ),
        "thermal": (
            "High thermal readings can throttle the machine or indicate cooling problems.",
            "Inspect thermal zones and reduce load if temperatures keep rising.",
        ),
        "probe": (
            "Probe failures mean the console may be missing evidence needed for a correct readout.",
            "Open raw probe errors and fix the local read or command problem.",
        ),
    }
    why, next_action = defaults.get(
        section,
        (
            "This condition crossed a deterministic host-health threshold.",
            "Open the section evidence and inspect the collected local facts.",
        ),
    )
    if "failed" in message.lower():
        why = "A failed unit or command is direct failure evidence from the local machine."
        next_action = (
            "Inspect the named failure and its logs before treating the system as healthy."
        )
    penalty.setdefault("why", why)
    penalty.setdefault("next", next_action)
    return penalty


def _run_command(
    label: str,
    args: list[str],
    *,
    timeout: int,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    commands = evidence.setdefault("commands", {})
    executable = shutil.which(args[0])
    if not executable:
        result = {"available": False, "command": args}
        commands[label] = result
        return result

    started = time.monotonic()
    try:
        completed = subprocess.run(
            [executable, *args[1:]],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        result = {
            "available": True,
            "command": args,
            "returncode": completed.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": _trim(completed.stdout),
            "stderr": _trim(completed.stderr, 4000),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        result = {
            "available": True,
            "command": args,
            "returncode": 124,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": _trim(exc.stdout if isinstance(exc.stdout, str) else ""),
            "stderr": _trim(exc.stderr if isinstance(exc.stderr, str) else ""),
            "timed_out": True,
        }
    except OSError as exc:
        result = {
            "available": True,
            "command": args,
            "returncode": 127,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
        }
    commands[label] = result
    return result


def _parse_key_value_lines(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _parse_equals_lines(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _collect_identity(
    *,
    os_data: dict[str, str],
    kernel_data: dict[str, Any],
    evidence: dict[str, Any],
    show_sensitive: bool,
) -> dict[str, Any]:
    dmi_dir = Path("/sys/class/dmi/id")
    dmi_fields = [
        "sys_vendor",
        "product_name",
        "product_version",
        "board_vendor",
        "board_name",
        "chassis_type",
        "product_serial",
        "board_serial",
        "product_uuid",
    ]
    dmi: dict[str, str] = {}
    if dmi_dir.exists():
        for field in dmi_fields:
            value = _read_sysfs_value(dmi_dir / field)
            if not value:
                continue
            if field.endswith("serial") or field == "product_uuid":
                dmi[field] = _maybe_sensitive(value, show_sensitive) or "hidden"
            else:
                dmi[field] = value
    evidence.setdefault("sysfs", {})["dmi"] = dmi

    return {
        "hostname": socket.gethostname(),
        "fqdn": socket.getfqdn(),
        "dmi_vendor": dmi.get("sys_vendor"),
        "dmi_product": dmi.get("product_name"),
        "chassis_type": dmi.get("chassis_type"),
        "os_id": os_data.get("ID"),
        "kernel_release": kernel_data.get("release"),
    }


def _collect_session(
    uptime_text: str | None,
    *,
    evidence: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    uptime = parse_uptime(uptime_text)
    timezone_name = _read_optional_text("/etc/timezone", max_chars=256)
    timedate = _run_command(
        "timedatectl",
        ["timedatectl", "show", "--property=Timezone", "--value"],
        timeout=timeout,
        evidence=evidence,
    )
    if timedate.get("returncode") == 0 and timedate.get("stdout"):
        timezone_name = timedate["stdout"].strip()
    return {
        "uptime_seconds": uptime["uptime_seconds"],
        "uptime_human": _format_uptime(uptime["uptime_seconds"]),
        "idle_seconds": uptime["idle_seconds"],
        "session_type": os.environ.get("XDG_SESSION_TYPE"),
        "desktop": os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION"),
        "timezone": timezone_name.strip() if timezone_name else None,
        "user": os.environ.get("USER"),
    }


def _collect_cpu(
    cpuinfo_text: str | None,
    loadavg_text: str | None,
    *,
    evidence: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    cpu = parse_cpuinfo(cpuinfo_text)
    loadavg = parse_loadavg(loadavg_text)
    lscpu = _run_command("lscpu", ["lscpu"], timeout=timeout, evidence=evidence)
    if lscpu.get("returncode") == 0:
        parsed_lscpu = _parse_key_value_lines(lscpu.get("stdout") or "")
        cpu["lscpu"] = parsed_lscpu
        cpu["model"] = cpu.get("model") or parsed_lscpu.get("Model name")
        if cpu.get("threads") is None:
            try:
                cpu["threads"] = int(parsed_lscpu.get("CPU(s)", ""))
            except ValueError:
                pass
    threads = cpu.get("threads") or os.cpu_count()
    cpu["threads"] = threads
    cpu["load_average"] = loadavg
    cpu["load_per_thread"] = (
        round(float(loadavg["one"]) / float(threads), 2)
        if loadavg.get("one") is not None and threads
        else None
    )
    return cpu


def _filesystem_usage_from_mounts(mounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    filesystems: list[dict[str, Any]] = []
    for mount in mounts:
        mountpoint = mount["mountpoint"]
        if mountpoint in seen:
            continue
        seen.add(mountpoint)
        try:
            usage = shutil.disk_usage(mountpoint)
        except OSError:
            continue
        filesystems.append(
            {
                "device": mount["device"],
                "fstype": mount["fstype"],
                "mountpoint": mountpoint,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "available_bytes": usage.free,
                "use_percent": _percent(usage.used, usage.total),
                "human_total": _human_bytes(usage.total),
                "human_used": _human_bytes(usage.used),
                "human_available": _human_bytes(usage.free),
                "virtual": mount["virtual"],
            }
        )
    return filesystems


def _collect_storage(
    mounts_text: str | None,
    *,
    evidence: dict[str, Any],
    timeout: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    mounts = parse_mounts(mounts_text)
    df = _run_command("df", ["df", "-PT"], timeout=timeout, evidence=evidence)
    filesystems = parse_df_pt(df.get("stdout")) if df.get("returncode") == 0 else []
    if not filesystems:
        filesystems = _filesystem_usage_from_mounts(mounts)

    lsblk = _run_command(
        "lsblk",
        [
            "lsblk",
            "-J",
            "-o",
            "NAME,TYPE,SIZE,MOUNTPOINTS,FSTYPE,MODEL,TRAN,ROTA,RM,STATE",
        ],
        timeout=timeout,
        evidence=evidence,
    )
    block_devices = (
        parse_lsblk_json(lsblk.get("stdout")).get("blockdevices", [])
        if lsblk.get("returncode") == 0
        else []
    )

    root = next((fs for fs in filesystems if fs.get("mountpoint") == "/"), None)
    home = next((fs for fs in filesystems if fs.get("mountpoint") == "/home"), None)
    important = [
        fs
        for fs in filesystems
        if not fs.get("virtual") and fs.get("mountpoint") in {"/", "/home", "/boot", "/var"}
    ]
    return (
        {
            "root": root,
            "home": home,
            "important": important,
            "block_devices": block_devices,
            "block_device_count": len(block_devices),
        },
        {"items": filesystems, "mounts": mounts},
    )


def _parse_resolv_conf(text: str | None) -> dict[str, Any]:
    servers = []
    searches = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts[0] == "nameserver" and len(parts) > 1:
            servers.append(parts[1])
        if parts[0] in {"search", "domain"} and len(parts) > 1:
            searches.extend(parts[1:])
    return {
        "servers": servers,
        "server_count": len(servers),
        "search": searches,
        "detected": bool(servers),
    }


def _interfaces_from_sysfs(*, show_sensitive: bool) -> list[dict[str, Any]]:
    interfaces = []
    net_dir = Path("/sys/class/net")
    if not net_dir.exists():
        return interfaces
    for iface_dir in sorted(net_dir.iterdir()):
        if not iface_dir.is_dir():
            continue
        name = iface_dir.name
        interfaces.append(
            {
                "ifname": name,
                "operstate": _read_sysfs_value(iface_dir / "operstate"),
                "carrier": _read_sysfs_value(iface_dir / "carrier"),
                "address": _redact_mac(_read_sysfs_value(iface_dir / "address"), show_sensitive),
                "mtu": _read_sysfs_value(iface_dir / "mtu"),
                "speed": _read_sysfs_value(iface_dir / "speed"),
                "source": "sysfs",
            }
        )
    return interfaces


def _merge_interface_data(
    sysfs_interfaces: list[dict[str, Any]],
    ip_interfaces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_name = {item.get("ifname"): dict(item) for item in sysfs_interfaces if item.get("ifname")}
    for ip_iface in ip_interfaces:
        name = ip_iface.get("ifname")
        if not name:
            continue
        merged = by_name.setdefault(name, {"ifname": name})
        for key, value in ip_iface.items():
            if value not in (None, [], ""):
                merged[key] = value
    return sorted(by_name.values(), key=lambda item: item.get("ifname") or "")


def _parse_nmcli_general(text: str | None) -> dict[str, str | None]:
    if not text:
        return {"running": None, "state": None}
    parts = text.strip().split(":")
    return {
        "running": parts[0] if parts else None,
        "state": parts[1] if len(parts) > 1 else None,
    }


def _parse_nmcli_devices(text: str | None) -> list[dict[str, str | None]]:
    devices = []
    for line in (text or "").splitlines():
        parts = line.split(":")
        while len(parts) < 4:
            parts.append("")
        devices.append(
            {
                "device": parts[0] or None,
                "type": parts[1] or None,
                "state": parts[2] or None,
                "connection": parts[3] or None,
            }
        )
    return devices


def _external_checks(config: dict[str, Any]) -> dict[str, Any]:
    probe_cfg = config.get("system_probe", {})
    if not probe_cfg.get("allow_external_connectivity_checks", False):
        return {
            "tested": False,
            "message": "External reachability not tested. Local route and DNS are used instead.",
            "results": [],
        }
    timeout = int(probe_cfg.get("external_check_timeout_seconds", 3))
    urls = probe_cfg.get("external_check_urls") or ["https://www.debian.org/"]
    results = []
    for url in urls[:5]:
        request = urllib.request.Request(str(url), method="HEAD")
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                results.append(
                    {
                        "url": str(url),
                        "ok": 200 <= response.status < 400,
                        "status": response.status,
                        "duration_seconds": round(time.monotonic() - started, 3),
                    }
                )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            results.append(
                {
                    "url": str(url),
                    "ok": False,
                    "error": str(exc),
                    "duration_seconds": round(time.monotonic() - started, 3),
                }
            )
    return {"tested": True, "results": results}


def _collect_network(
    config: dict[str, Any],
    *,
    evidence: dict[str, Any],
    timeout: int,
    show_sensitive: bool,
) -> dict[str, Any]:
    sysfs_interfaces = _interfaces_from_sysfs(show_sensitive=show_sensitive)
    ip_addr = _run_command("ip_addr", ["ip", "-j", "addr"], timeout=timeout, evidence=evidence)
    ip_interfaces = (
        parse_ip_addr_json(ip_addr.get("stdout"), show_sensitive=show_sensitive)
        if ip_addr.get("returncode") == 0
        else []
    )
    interfaces = _merge_interface_data(sysfs_interfaces, ip_interfaces)

    ip_route = _run_command("ip_route", ["ip", "-j", "route"], timeout=timeout, evidence=evidence)
    routes = parse_ip_route_json(ip_route.get("stdout")) if ip_route.get("returncode") == 0 else []
    default_route = next((route for route in routes if route.get("dst") == "default"), None)

    dns = _parse_resolv_conf(_read_optional_text("/etc/resolv.conf", max_chars=12000))
    resolvectl = _run_command(
        "resolvectl",
        ["resolvectl", "status"],
        timeout=timeout,
        evidence=evidence,
    )
    if resolvectl.get("returncode") == 0 and resolvectl.get("stdout"):
        dns["resolvectl_available"] = True
    else:
        dns["resolvectl_available"] = bool(resolvectl.get("available"))

    nmcli_general = _run_command(
        "nmcli_general",
        ["nmcli", "-t", "-f", "RUNNING,STATE", "general"],
        timeout=timeout,
        evidence=evidence,
    )
    nmcli_devices = _run_command(
        "nmcli_devices",
        ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"],
        timeout=timeout,
        evidence=evidence,
    )
    network_manager = {
        "available": bool(nmcli_general.get("available")),
        "general": (
            _parse_nmcli_general(nmcli_general.get("stdout"))
            if nmcli_general.get("returncode") == 0
            else {"running": None, "state": None}
        ),
        "devices": (
            _parse_nmcli_devices(nmcli_devices.get("stdout"))
            if nmcli_devices.get("returncode") == 0
            else []
        ),
    }
    wifi_ssid = next(
        (
            device.get("connection")
            for device in network_manager["devices"]
            if device.get("type") == "wifi"
            and device.get("state") == "connected"
            and device.get("connection")
            and device.get("connection") != "--"
        ),
        None,
    )

    up_non_loopback = [
        iface
        for iface in interfaces
        if iface.get("ifname") != "lo"
        and (
            iface.get("operstate") == "UP"
            or iface.get("carrier") == "1"
            or "UP" in (iface.get("flags") or [])
        )
    ]
    primary_name = default_route.get("dev") if default_route else None
    primary = next((iface for iface in interfaces if iface.get("ifname") == primary_name), None)
    if primary is None and up_non_loopback:
        primary = up_non_loopback[0]
    primary_address = None
    for address in (primary or {}).get("addresses") or []:
        if address.get("family") == "inet":
            primary_address = address.get("local")
            break

    return {
        "interfaces": interfaces,
        "up_non_loopback_count": len(up_non_loopback),
        "primary_interface": primary,
        "primary_address": primary_address,
        "routes": routes,
        "default_route": default_route,
        "gateway": default_route.get("gateway") if default_route else None,
        "dns": dns,
        "network_manager": network_manager,
        "wifi_ssid": wifi_ssid,
        "external_reachability": _external_checks(config),
    }


def _collect_power(*, show_sensitive: bool) -> dict[str, Any]:
    power_dir = Path("/sys/class/power_supply")
    supplies = []
    if not power_dir.exists():
        return {"supplies": [], "batteries": [], "ac_online": None, "battery_percent": None}
    for supply_dir in sorted(power_dir.iterdir()):
        if not supply_dir.is_dir():
            continue
        data = {
            "name": supply_dir.name,
            "type": _read_sysfs_value(supply_dir / "type"),
            "status": _read_sysfs_value(supply_dir / "status"),
            "capacity": _read_sysfs_value(supply_dir / "capacity"),
            "online": _read_sysfs_value(supply_dir / "online"),
            "manufacturer": _read_sysfs_value(supply_dir / "manufacturer"),
            "model_name": _read_sysfs_value(supply_dir / "model_name"),
            "serial_number": _maybe_sensitive(
                _read_sysfs_value(supply_dir / "serial_number"),
                show_sensitive,
            ),
        }
        try:
            data["capacity_percent"] = (
                int(data["capacity"]) if data.get("capacity") is not None else None
            )
        except ValueError:
            data["capacity_percent"] = None
        supplies.append(data)
    batteries = [supply for supply in supplies if supply.get("type") == "Battery"]
    ac_supplies = [
        supply
        for supply in supplies
        if supply.get("type") in {"Mains", "USB", "USB_C", "USB_PD"} or supply.get("online")
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
    return {
        "supplies": supplies,
        "batteries": batteries,
        "ac_online": ac_online,
        "battery_percent": battery_percent,
        "battery_status": battery_status,
    }


def _collect_thermal() -> dict[str, Any]:
    thermal_dir = Path("/sys/class/thermal")
    zones = []
    if not thermal_dir.exists():
        return {"zones": [], "max_celsius": None}
    for zone_dir in sorted(thermal_dir.glob("thermal_zone*")):
        temp_text = _read_sysfs_value(zone_dir / "temp")
        if temp_text is None:
            continue
        try:
            raw_temp = float(temp_text)
        except ValueError:
            continue
        celsius = raw_temp / 1000 if raw_temp > 1000 else raw_temp
        zones.append(
            {
                "name": zone_dir.name,
                "type": _read_sysfs_value(zone_dir / "type"),
                "temp_celsius": round(celsius, 1),
                "path": str(zone_dir),
            }
        )
    max_celsius = max((zone["temp_celsius"] for zone in zones), default=None)
    return {"zones": zones, "max_celsius": max_celsius}


def _parse_systemctl_failed(text: str | None) -> list[dict[str, str]]:
    units = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("0 loaded units"):
            continue
        parts = stripped.split(None, 4)
        if len(parts) < 4:
            continue
        units.append(
            {
                "unit": parts[0],
                "load": parts[1],
                "active": parts[2],
                "sub": parts[3],
                "description": parts[4] if len(parts) > 4 else "",
            }
        )
    return units


def _safe_command_label(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:80] or "unit"


def _annotate_failed_units(
    units: list[dict[str, Any]],
    *,
    scope: str,
    evidence: dict[str, Any],
    timeout: int,
) -> list[dict[str, Any]]:
    annotated = []
    prefix = ["systemctl", "--user"] if scope == "user" else ["systemctl"]
    journal_prefix = ["journalctl", "--user"] if scope == "user" else ["journalctl"]
    properties = (
        "Id,Description,LoadState,ActiveState,SubState,Result,ExecMainCode,"
        "ExecMainStatus,FragmentPath"
    )
    for unit in units:
        enriched = dict(unit)
        unit_name = unit.get("unit")
        if unit_name:
            label = f"systemctl_show_{scope}_{_safe_command_label(unit_name)}"
            result = _run_command(
                label,
                [*prefix, "show", unit_name, f"--property={properties}"],
                timeout=timeout,
                evidence=evidence,
            )
            if result.get("returncode") == 0:
                enriched["diagnostics"] = _parse_equals_lines(result.get("stdout") or "")
            journal = _run_command(
                f"journalctl_{scope}_{_safe_command_label(unit_name)}",
                [
                    *journal_prefix,
                    "-u",
                    unit_name,
                    "-n",
                    "12",
                    "--no-pager",
                    "--output=short-iso",
                ],
                timeout=timeout,
                evidence=evidence,
            )
            if journal.get("returncode") == 0:
                lines = [
                    line
                    for line in (journal.get("stdout") or "").splitlines()
                    if line.strip()
                ]
                enriched["recent_logs"] = lines[-5:]
        annotated.append(enriched)
    return annotated


def _describe_failed_units(
    units: list[dict[str, Any]],
    *,
    scope: str,
) -> tuple[str, str, str]:
    names = [unit.get("unit") for unit in units if unit.get("unit")]
    if not names:
        label = f"Failed {scope} service detected."
    elif len(names) == 1:
        label = f"Failed {scope} service: {names[0]}."
    else:
        preview = ", ".join(names[:3])
        more = f" and {len(names) - 3} more" if len(names) > 3 else ""
        label = f"Failed {scope} services: {preview}{more}."

    first = units[0] if units else {}
    diagnostics = first.get("diagnostics") or {}
    description = first.get("description") or diagnostics.get("Description")
    active = diagnostics.get("ActiveState") or first.get("active")
    sub = diagnostics.get("SubState") or first.get("sub")
    result = diagnostics.get("Result")
    exec_status = diagnostics.get("ExecMainStatus")
    state_bits = [part for part in [active, sub] if part]
    result_bits = [
        part
        for part in [
            f"Result={result}" if result else "",
            f"ExecMainStatus={exec_status}" if exec_status else "",
        ]
        if part
    ]
    why_parts = []
    if first.get("unit"):
        why_parts.append(f"systemctl reports {first['unit']}")
    if state_bits:
        why_parts.append(f"is {'/'.join(state_bits)}")
    if result_bits:
        why_parts.append(f"({', '.join(result_bits)})")
    if description:
        why_parts.append(f"Description: {description}.")
    recent_logs = first.get("recent_logs") or []
    if recent_logs:
        why_parts.append(f"Recent log: {_trim_inline(recent_logs[-1])}")
    why = " ".join(why_parts) or "systemctl returned a failed unit."

    if first.get("unit"):
        if scope == "user":
            next_action = (
                f"Run: systemctl --user status {first['unit']} --no-pager; "
                f"journalctl --user -u {first['unit']} -n 80 --no-pager"
            )
        else:
            next_action = (
                f"Run: systemctl status {first['unit']} --no-pager; "
                f"journalctl -u {first['unit']} -n 80 --no-pager"
            )
    else:
        next_action = "Open failed unit evidence and inspect the systemctl result."
    return label, why, next_action


def _collect_services(
    config: dict[str, Any],
    *,
    evidence: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    system = _run_command(
        "systemctl_failed",
        ["systemctl", "--failed", "--no-legend", "--plain", "--all"],
        timeout=timeout,
        evidence=evidence,
    )
    user = _run_command(
        "systemctl_user_failed",
        ["systemctl", "--user", "--failed", "--no-legend", "--plain", "--all"],
        timeout=timeout,
        evidence=evidence,
    )
    failed_system = (
        _parse_systemctl_failed(system.get("stdout")) if system.get("returncode") == 0 else []
    )
    failed_user = _parse_systemctl_failed(user.get("stdout")) if user.get("returncode") == 0 else []
    failed_system = _annotate_failed_units(
        failed_system[:10],
        scope="system",
        evidence=evidence,
        timeout=timeout,
    )
    failed_user = _annotate_failed_units(
        failed_user[:10],
        scope="user",
        evidence=evidence,
        timeout=timeout,
    )
    critical = set(config.get("system_probe", {}).get("critical_services") or [])
    critical_failed = [
        unit for unit in [*failed_system, *failed_user] if unit.get("unit") in critical
    ]
    return {
        "failed_system": failed_system,
        "failed_user": failed_user,
        "failed_system_count": len(failed_system),
        "failed_user_count": len(failed_user),
        "critical_failed": critical_failed,
        "systemctl_available": bool(system.get("available")),
        "user_systemctl_available": bool(user.get("available")),
    }


def _parse_ps(text: str | None) -> list[dict[str, Any]]:
    rows = []
    for line in (text or "").splitlines()[1:]:
        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        try:
            rows.append(
                {
                    "pid": int(parts[0]),
                    "ppid": int(parts[1]),
                    "command": parts[2],
                    "cpu_percent": float(parts[3]),
                    "memory_percent": float(parts[4]),
                    "rss_kb": int(parts[5]),
                    "rss_human": _human_bytes(int(parts[5]) * 1024),
                }
            )
        except ValueError:
            continue
    return rows


def _collect_processes(*, evidence: dict[str, Any], timeout: int) -> dict[str, Any]:
    top_cpu = _run_command(
        "ps_top_cpu",
        ["ps", "-eo", "pid,ppid,comm,%cpu,%mem,rss", "--sort=-%cpu"],
        timeout=timeout,
        evidence=evidence,
    )
    top_mem = _run_command(
        "ps_top_memory",
        ["ps", "-eo", "pid,ppid,comm,%cpu,%mem,rss", "--sort=-%mem"],
        timeout=timeout,
        evidence=evidence,
    )
    return {
        "top_cpu": _parse_ps(top_cpu.get("stdout"))[:8] if top_cpu.get("returncode") == 0 else [],
        "top_memory": (
            _parse_ps(top_mem.get("stdout"))[:8] if top_mem.get("returncode") == 0 else []
        ),
    }


def _collect_dev_tools(*, evidence: dict[str, Any], timeout: int) -> dict[str, Any]:
    specs = [
        ("python", ["python3", "--version"]),
        ("git", ["git", "--version"]),
        ("node", ["node", "--version"]),
        ("npm", ["npm", "--version"]),
        ("sqlite", ["sqlite3", "--version"]),
        ("ripgrep", ["rg", "--version"]),
        ("docker", ["docker", "--version"]),
    ]
    tools = []
    for name, args in specs:
        result = _run_command(f"tool_{name}", args, timeout=timeout, evidence=evidence)
        output = (result.get("stdout") or result.get("stderr") or "").splitlines()
        tools.append(
            {
                "name": name,
                "command": args[0],
                "available": bool(result.get("available")),
                "version": output[0] if result.get("available") and output else None,
            }
        )
    return {
        "tools": tools,
        "codex_marker": {
            "cli_available": shutil.which("codex") is not None,
            "config_dir_present": (Path.home() / ".codex").exists(),
        },
    }


def _collect_logs(*, evidence: dict[str, Any], timeout: int) -> dict[str, Any]:
    system = _run_command(
        "journalctl_system_warnings",
        ["journalctl", "-p", "warning..alert", "-n", "25", "--no-pager", "--output=short-iso"],
        timeout=timeout,
        evidence=evidence,
    )
    user = _run_command(
        "journalctl_user_warnings",
        [
            "journalctl",
            "--user",
            "-p",
            "warning..alert",
            "-n",
            "25",
            "--no-pager",
            "--output=short-iso",
        ],
        timeout=timeout,
        evidence=evidence,
    )
    system_lines = (
        [line for line in (system.get("stdout") or "").splitlines() if line.strip()]
        if system.get("returncode") == 0
        else []
    )
    user_lines = (
        [line for line in (user.get("stdout") or "").splitlines() if line.strip()]
        if user.get("returncode") == 0
        else []
    )
    return {
        "system_warning_count": len(system_lines),
        "user_warning_count": len(user_lines),
        "system_warnings": system_lines[-10:],
        "user_warnings": user_lines[-10:],
        "journalctl_available": bool(system.get("available") or user.get("available")),
    }


def build_host_health(snapshot: dict[str, Any]) -> dict[str, Any]:
    penalties: list[dict[str, Any]] = []
    penalties.extend(
        interpret_filesystem_health(snapshot.get("filesystems", {}).get("items") or [])
    )

    identity = snapshot.get("identity") or {}
    os_info = snapshot.get("os") or {}
    kernel = snapshot.get("kernel") or {}
    if not identity.get("hostname") or not os_info.get("pretty_name") or not kernel.get("release"):
        penalties.append(
            {
                "severity": "red",
                "section": "identity",
                "message": "Host, OS, or kernel identity could not be collected.",
                "penalty": 60,
                "evidence": {
                    "hostname": identity.get("hostname"),
                    "os": os_info.get("pretty_name"),
                    "kernel": kernel.get("release"),
                },
            }
        )

    network = snapshot.get("network") or {}
    if network.get("up_non_loopback_count", 0) == 0:
        penalties.append(
            {
                "severity": "red",
                "section": "network",
                "message": "No non-loopback network interface appears up.",
                "penalty": 40,
                "evidence": {"interfaces": network.get("interfaces", [])},
            }
        )
    elif not network.get("default_route"):
        penalties.append(
            {
                "severity": "amber",
                "section": "network",
                "message": "No default network route was detected.",
                "penalty": 20,
                "evidence": {"routes": network.get("routes", [])},
            }
        )
    if not (network.get("dns") or {}).get("detected"):
        penalties.append(
            {
                "severity": "amber",
                "section": "network",
                "message": "DNS configuration was not detected.",
                "penalty": 10,
                "evidence": {"dns": network.get("dns")},
            }
        )

    memory = snapshot.get("memory") or {}
    available_percent = memory.get("available_percent")
    if available_percent is not None and float(available_percent) < 10:
        penalties.append(
            {
                "severity": "amber",
                "section": "memory",
                "message": f"Available memory is low ({available_percent:.1f}%).",
                "penalty": 15,
                "evidence": {
                    "available_percent": available_percent,
                    "human_available": memory.get("human_available"),
                },
            }
        )

    cpu = snapshot.get("cpu") or {}
    load = (cpu.get("load_average") or {}).get("one")
    threads = cpu.get("threads") or 1
    if load is not None and threads and float(load) > float(threads) * 2:
        penalties.append(
            {
                "severity": "amber",
                "section": "cpu",
                "message": f"Load average is high for {threads} threads ({load}).",
                "penalty": 15,
                "evidence": {"load_one": load, "threads": threads},
            }
        )

    services = snapshot.get("services") or {}
    failed_system = int(services.get("failed_system_count") or 0)
    failed_user = int(services.get("failed_user_count") or 0)
    if failed_system:
        message, why, next_action = _describe_failed_units(
            services.get("failed_system") or [],
            scope="system",
        )
        penalties.append(
            {
                "severity": "amber",
                "section": "services",
                "message": message,
                "why": why,
                "next": next_action,
                "penalty": min(25, 10 + failed_system * 5),
                "evidence": {"failed_system": services.get("failed_system")},
            }
        )
    if failed_user:
        message, why, next_action = _describe_failed_units(
            services.get("failed_user") or [],
            scope="user",
        )
        penalties.append(
            {
                "severity": "amber",
                "section": "services",
                "message": message,
                "why": why,
                "next": next_action,
                "penalty": min(20, 8 + failed_user * 4),
                "evidence": {"failed_user": services.get("failed_user")},
            }
        )
    if services.get("critical_failed"):
        penalties.append(
            {
                "severity": "red",
                "section": "services",
                "message": "A configured critical service is failed.",
                "penalty": 50,
                "evidence": {"critical_failed": services.get("critical_failed")},
            }
        )

    power = snapshot.get("power") or {}
    battery_percent = power.get("battery_percent")
    battery_status = (power.get("battery_status") or "").lower()
    if battery_percent is not None and battery_status == "discharging":
        if int(battery_percent) <= 8:
            severity = "red"
            penalty = 30
            message = f"Battery is critically low ({battery_percent}%)."
        elif int(battery_percent) <= 20:
            severity = "amber"
            penalty = 12
            message = f"Battery is low ({battery_percent}%)."
        else:
            severity = ""
            penalty = 0
            message = ""
        if penalty:
            penalties.append(
                {
                    "severity": severity,
                    "section": "power",
                    "message": message,
                    "penalty": penalty,
                    "evidence": {
                        "battery_percent": battery_percent,
                        "battery_status": power.get("battery_status"),
                    },
                }
            )

    thermal = snapshot.get("thermal") or {}
    max_celsius = thermal.get("max_celsius")
    if max_celsius is not None:
        if float(max_celsius) >= 90:
            severity = "red"
            penalty = 35
            message = f"Thermal zone reports critical heat ({max_celsius:.1f} C)."
        elif float(max_celsius) >= 80:
            severity = "amber"
            penalty = 15
            message = f"Thermal zone reports high heat ({max_celsius:.1f} C)."
        else:
            severity = ""
            penalty = 0
            message = ""
        if penalty:
            penalties.append(
                {
                    "severity": severity,
                    "section": "thermal",
                    "message": message,
                    "penalty": penalty,
                    "evidence": {"max_celsius": max_celsius, "zones": thermal.get("zones")},
                }
            )

    blocking_errors = [
        error
        for error in snapshot.get("probe_errors", [])
        if error.get("section") in {"identity", "os", "kernel"}
    ]
    if blocking_errors:
        penalties.append(
            {
                "severity": "red",
                "section": "probe",
                "message": "Basic host probe errors block a trustworthy interpretation.",
                "penalty": 50,
                "evidence": {"errors": blocking_errors},
            }
        )

    penalties = [_explain_penalty(penalty) for penalty in penalties]

    score = max(0, 100 - sum(int(item.get("penalty", 0)) for item in penalties))
    worst = "green"
    if any(item["severity"] == "red" for item in penalties):
        state = "BROKEN"
        worst = "red"
    elif penalties:
        state = "CAUTION"
        worst = "amber"
    else:
        state = "OK"

    os_name = (snapshot.get("os") or {}).get("pretty_name") or "this Debian install"
    kernel_release = (snapshot.get("kernel") or {}).get("release") or "unknown kernel"
    memory_total = (snapshot.get("memory") or {}).get("human_total") or "unknown memory"
    root = (snapshot.get("storage") or {}).get("root") or {}
    root_pressure = (
        f"root filesystem at {root.get('use_percent'):.1f}%"
        if root.get("use_percent") is not None
        else "unknown storage pressure"
    )
    route_text = "default route present" if network.get("default_route") else "no default route"
    if penalties:
        lead = penalties[0]["message"]
        next_action = f"Review {penalties[0]['section']} evidence first."
    else:
        lead = "No host-level issue crossed the current thresholds."
        next_action = "No immediate host action needed."

    return {
        "state": state,
        "score": score,
        "severity": worst,
        "headline": lead,
        "summary": (
            f"{os_name} is up on kernel {kernel_release}, with {memory_total} memory, "
            f"{root_pressure}, and {route_text}. {lead}"
        ),
        "next_sane_action": next_action,
        "penalties": penalties,
        "checks": {
            "failed_system_services": failed_system,
            "failed_user_services": failed_user,
            "default_route": bool(network.get("default_route")),
            "dns_detected": bool((network.get("dns") or {}).get("detected")),
            "root_use_percent": root.get("use_percent"),
            "memory_available_percent": available_percent,
        },
    }


def _unavailable_snapshot(message: str) -> dict[str, Any]:
    return {
        "identity": {},
        "os": {},
        "kernel": {},
        "session": {},
        "cpu": {},
        "memory": {},
        "storage": {},
        "filesystems": {"items": [], "mounts": []},
        "network": {},
        "power": {},
        "thermal": {},
        "services": {},
        "processes": {},
        "dev_tools": {},
        "logs": {},
        "health": {
            "state": "UNKNOWN",
            "score": None,
            "severity": "gray",
            "headline": message,
            "summary": "The host probe failed before collecting enough evidence.",
            "next_sane_action": "Open probe errors and fix the local read/probe problem.",
            "penalties": [],
            "checks": {},
        },
        "evidence": {"commands": {}, "files": {}, "sysfs": {}, "notes": []},
        "probe_errors": [{"section": "probe", "message": message}],
    }


def probe_system(config: dict[str, Any]) -> dict[str, Any]:
    probe_cfg = config.get("system_probe", {})
    timeout = int(probe_cfg.get("command_timeout_seconds", DEFAULT_COMMAND_TIMEOUT_SECONDS))
    show_sensitive = bool(probe_cfg.get("show_sensitive_identifiers", False))
    evidence: dict[str, Any] = {"commands": {}, "files": {}, "sysfs": {}, "notes": []}
    errors: list[dict[str, str]] = []

    try:
        os_release_text = _read_text("/etc/os-release", errors)
        uptime_text = _read_text("/proc/uptime", errors)
        meminfo_text = _read_text("/proc/meminfo", errors)
        cpuinfo_text = _read_text("/proc/cpuinfo", errors)
        loadavg_text = _read_text("/proc/loadavg", errors)
        mounts_text = _read_text("/proc/mounts", errors, max_chars=262144)

        evidence["files"] = {
            "/etc/os-release": _trim(os_release_text, 4000),
            "/proc/uptime": _trim(uptime_text, 1000),
            "/proc/meminfo": _trim(meminfo_text, 12000),
            "/proc/cpuinfo": _trim(cpuinfo_text, 12000),
            "/proc/loadavg": _trim(loadavg_text, 1000),
            "/proc/mounts": _trim(mounts_text, 12000),
        }

        uname = platform.uname()
        kernel = {
            "system": uname.system,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
            "processor": uname.processor,
            "architecture": platform.machine(),
        }
        uname_cmd = _run_command("uname", ["uname", "-a"], timeout=timeout, evidence=evidence)
        if uname_cmd.get("returncode") == 0:
            kernel["uname"] = uname_cmd.get("stdout")

        os_release = parse_os_release(os_release_text)
        os_info = {
            "pretty_name": os_release.get("PRETTY_NAME"),
            "name": os_release.get("NAME"),
            "id": os_release.get("ID"),
            "version": os_release.get("VERSION"),
            "version_id": os_release.get("VERSION_ID"),
            "variant": os_release.get("VARIANT"),
            "raw": os_release,
        }

        hostnamectl = _run_command(
            "hostnamectl",
            ["hostnamectl"],
            timeout=timeout,
            evidence=evidence,
        )
        if hostnamectl.get("returncode") == 0:
            os_info["hostnamectl"] = _parse_key_value_lines(hostnamectl.get("stdout") or "")

        storage, filesystems = _collect_storage(mounts_text, evidence=evidence, timeout=timeout)
        snapshot = {
            "identity": _collect_identity(
                os_data=os_release,
                kernel_data=kernel,
                evidence=evidence,
                show_sensitive=show_sensitive,
            ),
            "os": os_info,
            "kernel": kernel,
            "session": _collect_session(uptime_text, evidence=evidence, timeout=timeout),
            "cpu": _collect_cpu(
                cpuinfo_text,
                loadavg_text,
                evidence=evidence,
                timeout=timeout,
            ),
            "memory": parse_meminfo(meminfo_text),
            "storage": storage,
            "filesystems": filesystems,
            "network": _collect_network(
                config,
                evidence=evidence,
                timeout=timeout,
                show_sensitive=show_sensitive,
            ),
            "power": _collect_power(show_sensitive=show_sensitive),
            "thermal": _collect_thermal(),
            "services": _collect_services(config, evidence=evidence, timeout=timeout),
            "processes": _collect_processes(evidence=evidence, timeout=timeout),
            "dev_tools": _collect_dev_tools(evidence=evidence, timeout=timeout),
            "logs": _collect_logs(evidence=evidence, timeout=timeout),
            "evidence": evidence,
            "probe_errors": errors,
        }
        snapshot["health"] = build_host_health(snapshot)
        if not show_sensitive:
            snapshot = _redact_sensitive_identifiers(snapshot)
        return snapshot
    except Exception as exc:
        return _unavailable_snapshot(f"Unhandled host probe failure: {exc}")
