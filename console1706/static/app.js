const toast = document.querySelector("#toast");
let previousLive = null;
const scanTiming = {
  lastScan: document.querySelector("[data-last-scan]")?.dataset.lastScan || null,
  intervalSeconds: Number(
    document.querySelector("[data-scan-interval-seconds]")?.dataset.scanIntervalSeconds,
  ) || 1800,
  serverOffsetMs: 0,
  state: null,
  score: null,
  penaltyCount: 0,
};

const SENSOR_CLASSES = ["sensor-ok", "sensor-warning", "sensor-critical", "sensor-unknown"];

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("visible");
  window.setTimeout(() => toast.classList.remove("visible"), 4500);
}

document.querySelector("#scan-button")?.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/scan", { method: "POST" });
    const payload = await response.json();
    showToast(payload.status === "started" ? "Scan started." : "Scan is already running.");
  } catch (error) {
    showToast(`Scan request failed: ${error}`);
  }
});

document.querySelectorAll("[data-scroll-target]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = document.querySelector(button.dataset.scrollTarget || "");
    const topBar = document.querySelector(".command-strip");
    if (!target) return;
    const offset = (topBar?.getBoundingClientRect().height || 0) + 2;
    const top = target.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top, behavior: "smooth" });
  });
});

document.querySelectorAll("[data-codex-scenario]").forEach((button) => {
  button.addEventListener("click", async () => {
    const originalTitle = button.getAttribute("title") || "Open Codex terminal";
    button.disabled = true;
    button.setAttribute("title", "Launching terminal...");
    try {
      const scenario = JSON.parse(button.dataset.codexScenario || "{}");
      const response = await fetch("/api/host/actions/codex", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scenario),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || response.statusText);
      }
      showToast(`Codex terminal launch requested via ${payload.terminal}.`);
    } catch (error) {
      showToast(`Codex terminal launch failed: ${error}`);
    } finally {
      button.disabled = false;
      button.setAttribute("title", originalTitle);
    }
  });
});

function setLiveText(name, value) {
  document.querySelectorAll(`[data-live="${name}"]`).forEach((node) => {
    node.textContent = value;
  });
}

function setLiveBar(name, percent) {
  const width = Math.max(0, Math.min(100, Number(percent) || 0));
  document.querySelectorAll(`[data-live-bar="${name}"]`).forEach((node) => {
    node.style.width = `${width}%`;
  });
}

function setSensorState(name, state, message) {
  const normalized = ["ok", "warning", "critical"].includes(state) ? state : "unknown";
  document.querySelectorAll(`[data-sensor-cell="${name}"]`).forEach((node) => {
    node.classList.remove(...SENSOR_CLASSES);
    node.classList.add(`sensor-${normalized}`);
  });
  if (message) {
    setLiveText(`${name}-health`, message);
  }
}

function formatPercent(value, digits = 0) {
  return value === null || value === undefined || Number.isNaN(Number(value))
    ? "--%"
    : `${Number(value).toFixed(digits)}%`;
}

function formatRate(bytesPerSecond) {
  const value = Math.max(0, Number(bytesPerSecond) || 0);
  const units = ["B/s", "KiB/s", "MiB/s", "GiB/s"];
  let number = value;
  let index = 0;
  while (number >= 1024 && index < units.length - 1) {
    number /= 1024;
    index += 1;
  }
  return `${number >= 10 || index === 0 ? number.toFixed(0) : number.toFixed(1)} ${units[index]}`;
}

function ratePercent(bytesPerSecond) {
  if (!bytesPerSecond) return 0;
  return Math.min(100, Math.log10(bytesPerSecond + 1) * 14);
}

function formatClock(date) {
  if (!date) return "--:--:--";
  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

function formatDuration(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  return [hours, minutes, secs].map((part) => String(part).padStart(2, "0")).join(":");
}

function formatAge(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  if (total < 10) return "just now";
  if (total < 60) return `${total}s ago`;
  const minutes = Math.floor(total / 60);
  if (minutes < 120) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m ago`;
}

function parsedScanDate() {
  if (!scanTiming.lastScan) return null;
  const parsed = new Date(scanTiming.lastScan);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function currentServerDate() {
  return new Date(Date.now() + scanTiming.serverOffsetMs);
}

function updateScanTimers() {
  const lastScan = parsedScanDate();
  const lastUpdated = document.querySelector('[data-live="last-updated-age"]');
  const nextUpdate = document.querySelector('[data-live="next-update-countdown"]');
  const nextReadout = nextUpdate?.closest(".timer-readout");
  if (!lastScan) {
    setLiveText("last-updated-age", "never");
    setLiveText("last-updated-clock", "--:--:--");
    setLiveText("next-update-countdown", "--:--:--");
    setLiveText("next-update-clock", "--:--:--");
    nextReadout?.classList.remove("timer-warning", "timer-critical", "timer-pulse");
    return;
  }

  const now = currentServerDate();
  const elapsedSeconds = Math.floor((now.getTime() - lastScan.getTime()) / 1000);
  const nextScan = new Date(lastScan.getTime() + scanTiming.intervalSeconds * 1000);
  const remainingSeconds = Math.ceil((nextScan.getTime() - now.getTime()) / 1000);
  setLiveText("last-updated-age", formatAge(elapsedSeconds));
  setLiveText("last-updated-clock", formatClock(lastScan));
  setLiveText(
    "next-update-countdown",
    remainingSeconds <= 0 ? "due now" : formatDuration(remainingSeconds),
  );
  setLiveText("next-update-clock", formatClock(nextScan));

  lastUpdated?.setAttribute("title", scanTiming.lastScan);
  nextReadout?.classList.remove("timer-warning", "timer-critical", "timer-pulse");
  if (remainingSeconds <= 10) {
    nextReadout?.classList.add("timer-critical");
  } else if (remainingSeconds <= 60) {
    nextReadout?.classList.add("timer-warning");
    if (remainingSeconds % 10 === 0) {
      nextReadout?.classList.add("timer-pulse");
    }
  }
}

function cpuPercent(current, previous) {
  if (!current || !previous) return null;
  const totalDelta = current.total - previous.total;
  const idleDelta = current.idle - previous.idle;
  if (totalDelta <= 0) return null;
  return Math.max(0, Math.min(100, ((totalDelta - idleDelta) / totalDelta) * 100));
}

function primaryNetworkRate(current, previous) {
  const primaryName = current?.network?.primary_interface;
  const currentIface = current?.network?.primary;
  if (!primaryName || !currentIface || !previous) return { rx: 0, tx: 0, errors: 0 };
  const previousIface = (previous.network?.interfaces || []).find((iface) => iface.name === primaryName);
  const seconds = Math.max(0.001, (current.monotonic_seconds || 0) - (previous.monotonic_seconds || 0));
  if (!previousIface) return { rx: 0, tx: 0, errors: 0 };
  const currentErrors =
    (currentIface.rx_errors || 0) +
    (currentIface.tx_errors || 0) +
    (currentIface.rx_dropped || 0) +
    (currentIface.tx_dropped || 0);
  const previousErrors =
    (previousIface.rx_errors || 0) +
    (previousIface.tx_errors || 0) +
    (previousIface.rx_dropped || 0) +
    (previousIface.tx_dropped || 0);
  return {
    rx: Math.max(0, (currentIface.rx_bytes - previousIface.rx_bytes) / seconds),
    tx: Math.max(0, (currentIface.tx_bytes - previousIface.tx_bytes) / seconds),
    errors: Math.max(0, (currentErrors - previousErrors) / seconds),
  };
}

function pressureAvg10(pressure, kind = "some") {
  const value = pressure?.[kind]?.avg10;
  return value === undefined || value === null ? null : Number(value);
}

function updateSystemSensor(live) {
  const state = live.scan_timing?.state || scanTiming.state || "UNKNOWN";
  const score =
    live.scan_timing?.score ?? scanTiming.score ?? (state === "OK" ? 100 : state === "CAUTION" ? 68 : state === "BROKEN" ? 20 : 0);
  const penaltyCount = live.scan_timing?.penalty_count ?? scanTiming.penaltyCount;
  let sensorState = "unknown";
  if (state === "OK") sensorState = "ok";
  if (state === "CAUTION") sensorState = "warning";
  if (state === "BROKEN") sensorState = "critical";
  setLiveText("system-state", state);
  setLiveText("system-alerts", penaltyCount);
  setLiveText("system-score", state === "UNKNOWN" ? "--" : score);
  setLiveBar("system", score);
  setSensorState(
    "system",
    sensorState,
    state === "OK"
      ? "Green: latest full scan found no host-level issue past thresholds."
      : `${state}: ${penaltyCount} scan-derived attention item${penaltyCount === 1 ? "" : "s"}; open Attention stack.`,
  );
}

function updateNetworkSensor(live, rates) {
  const network = live.network || {};
  const primary = network.primary || {};
  const hasInterface = Boolean(network.primary_interface);
  const hasLan = Boolean(network.lan_ip);
  const hasGateway = Boolean(network.gateway);
  const carrierDown = primary.carrier === "0" || primary.operstate === "down";
  const cumulativeErrors =
    (primary.rx_errors || 0) +
    (primary.tx_errors || 0) +
    (primary.rx_dropped || 0) +
    (primary.tx_dropped || 0);

  let state = "ok";
  let message = "Green: local interface, LAN address, and gateway are present. WAN lookup is disabled.";
  if (!hasInterface || (!hasLan && !hasGateway)) {
    state = "critical";
    message = "Red: no usable non-loopback interface with local address or gateway is visible.";
  } else if (!hasGateway || !hasLan || carrierDown || rates.errors > 0 || cumulativeErrors > 0) {
    state = "warning";
    const reasons = [];
    if (!hasGateway) reasons.push("default gateway missing");
    if (!hasLan) reasons.push("LAN address missing");
    if (carrierDown) reasons.push("carrier/link down");
    if (rates.errors > 0) reasons.push("new interface errors/drops");
    else if (cumulativeErrors > 0) reasons.push("interface errors/drops exist since boot");
    message = `Yellow: ${reasons.join(", ")}.`;
  }

  setSensorState("network", state, message);
}

function updateCpuRamSensor(live, cpu) {
  const count = Math.max(1, Number(live.cpu?.count) || 1);
  const loadOne = Number(live.cpu?.load?.one);
  const loadRatio = Number.isFinite(loadOne) ? loadOne / count : null;
  const memoryAvailable = live.memory?.available_percent;
  const memoryUsed = live.memory?.used_percent;
  const memoryPressure = pressureAvg10(live.pressure?.memory);
  const cpuPressure = pressureAvg10(live.cpu?.pressure);
  const critical =
    (cpu !== null && cpu >= 90) ||
    (loadRatio !== null && loadRatio >= 1.5) ||
    (memoryAvailable !== null && memoryAvailable !== undefined && memoryAvailable < 5) ||
    (memoryPressure !== null && memoryPressure >= 30);
  const warning =
    critical ||
    (cpu !== null && cpu >= 75) ||
    (loadRatio !== null && loadRatio >= 1) ||
    (memoryAvailable !== null && memoryAvailable !== undefined && memoryAvailable < 15) ||
    (memoryPressure !== null && memoryPressure >= 10) ||
    (cpuPressure !== null && cpuPressure >= 20);

  let message = "Green: CPU <75%, load/core <1, and MemAvailable >=15%.";
  if (critical) {
    message = `Red: CPU ${formatPercent(cpu)}, load/core ${loadRatio?.toFixed(2) ?? "--"}, MemAvailable ${formatPercent(memoryAvailable, 1)}.`;
  } else if (warning) {
    message = `Yellow: CPU ${formatPercent(cpu)}, load/core ${loadRatio?.toFixed(2) ?? "--"}, MemAvailable ${formatPercent(memoryAvailable, 1)}.`;
  }

  setLiveText("cpu-percent-inline", formatPercent(cpu));
  setLiveText("mem-used-inline", formatPercent(memoryUsed, 1));
  setLiveText("load-ratio", loadRatio === null ? "--" : `${loadRatio.toFixed(2)}x`);
  setLiveBar("load", loadRatio === null ? 0 : loadRatio * 100);
  setSensorState("cpu-ram", critical ? "critical" : warning ? "warning" : "ok", message);
}

function updateFilesystemSensor(live) {
  const root = live.filesystems?.root;
  const home = live.filesystems?.home;
  const rootUsed = root?.used_percent;
  const homeUsed = home?.used_percent;
  const ioPressure = pressureAvg10(live.pressure?.io);
  const critical =
    (rootUsed !== null && rootUsed !== undefined && rootUsed >= 95) ||
    (homeUsed !== null && homeUsed !== undefined && homeUsed >= 95) ||
    (ioPressure !== null && ioPressure >= 30);
  const warning =
    critical ||
    (rootUsed !== null && rootUsed !== undefined && rootUsed >= 85) ||
    (homeUsed !== null && homeUsed !== undefined && homeUsed >= 90) ||
    (ioPressure !== null && ioPressure >= 10);
  let message = "Green: root <85%, home <90%, and I/O PSI avg10 <10%.";
  if (critical) {
    message = `Red: root ${formatPercent(rootUsed, 1)}, home ${formatPercent(homeUsed, 1)}, I/O pressure ${formatPercent(ioPressure, 1)}.`;
  } else if (warning) {
    message = `Yellow: root ${formatPercent(rootUsed, 1)}, home ${formatPercent(homeUsed, 1)}, I/O pressure ${formatPercent(ioPressure, 1)}.`;
  }

  setLiveText("fs-root-used-inline", formatPercent(rootUsed, 1));
  setLiveText("fs-home-used-inline", home ? formatPercent(homeUsed, 1) : "--");
  setLiveText("io-pressure", ioPressure === null ? "--" : `${ioPressure.toFixed(1)}%`);
  setLiveBar("io-pressure", ioPressure === null ? 0 : ioPressure);
  setSensorState("filesystem", critical ? "critical" : warning ? "warning" : "ok", message);
}

async function updateLiveReadouts() {
  try {
    const response = await fetch("/api/live", { cache: "no-store" });
    if (!response.ok) throw new Error(response.statusText);
    const live = await response.json();
    if (live.scan_timing) {
      scanTiming.lastScan = live.scan_timing.last_scan || scanTiming.lastScan;
      scanTiming.intervalSeconds = live.scan_timing.interval_seconds || scanTiming.intervalSeconds;
      scanTiming.state = live.scan_timing.state || scanTiming.state;
      scanTiming.score = live.scan_timing.score ?? scanTiming.score;
      scanTiming.penaltyCount = live.scan_timing.penalty_count ?? scanTiming.penaltyCount;
      if (live.scan_timing.server_epoch_seconds) {
        scanTiming.serverOffsetMs = live.scan_timing.server_epoch_seconds * 1000 - Date.now();
      }
    }
    const cpu = cpuPercent(live.cpu?.times, previousLive?.cpu?.times);
    const rates = primaryNetworkRate(live, previousLive);
    const memoryUsed = live.memory?.used_percent;
    const root = live.filesystems?.root;
    const home = live.filesystems?.home;

    setLiveText("lan-ip", live.network?.lan_ip || "not detected");
    setLiveText("gateway", live.network?.gateway || "not detected");
    setLiveText("wan-ip", live.network?.wan_ip || "not tested");
    setLiveText("net-rx-rate", formatRate(rates.rx));
    setLiveText("net-tx-rate", formatRate(rates.tx));
    setLiveText("net-errors", rates.errors > 0 ? `${rates.errors.toFixed(1)}/s` : "0");
    setLiveText("cpu-percent", formatPercent(cpu));
    setLiveText("load-one", live.cpu?.load?.one ?? "?");
    setLiveText("mem-used", memoryUsed === null || memoryUsed === undefined ? "unknown" : `${memoryUsed.toFixed(1)}%`);
    setLiveText("mem-avail", live.memory?.human_available || "unknown");
    setLiveText("fs-root-used", root?.used_percent === null || root?.used_percent === undefined ? "unknown" : `${root.used_percent.toFixed(1)}%`);
    setLiveText("fs-root-free", root?.human_available || "unknown");
    setLiveText("fs-home-used", home?.used_percent === null || home?.used_percent === undefined ? "same/unknown" : `${home.used_percent.toFixed(1)}%`);

    setLiveBar("net-rx", ratePercent(rates.rx));
    setLiveBar("net-tx", ratePercent(rates.tx));
    setLiveBar("net-errors", rates.errors > 0 ? 100 : 0);
    setLiveBar("cpu", cpu || 0);
    setLiveBar("memory", memoryUsed || 0);
    setLiveBar("fs-root", root?.used_percent || 0);
    setLiveBar("fs-home", home?.used_percent || 0);
    updateSystemSensor(live);
    updateNetworkSensor(live, rates);
    updateCpuRamSensor(live, cpu);
    updateFilesystemSensor(live);
    updateScanTimers();
    previousLive = live;
  } catch (error) {
    setLiveText("net-rx-rate", "live off");
    setLiveText("net-tx-rate", "live off");
  }
}

updateScanTimers();
updateLiveReadouts();
window.setInterval(updateScanTimers, 1000);
window.setInterval(updateLiveReadouts, 2000);
