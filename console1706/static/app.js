const toast = document.querySelector("#toast");
let previousLive = null;
let scanMonitor = null;
let scanMonitorPreviousLastScan = null;
let scanMonitorDeadline = null;
let livePollTimer = null;
let scanClockTimer = null;
let liveReadoutInFlight = null;
const livePower = {
  onBattery: false,
  source: "unknown",
};
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
const HISTORY_WINDOW_MS = 5 * 60 * 1000;
const SCOPE_STORAGE_KEY = "console1706.scopeNav";
const liveHistory = {
  "system-score": [],
  "net-rx": [],
  "net-tx": [],
  cpu: [],
  memory: [],
  "memory-pressure": [],
  "fs-root": [],
  "io-pressure": [],
  thermal: [],
};

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("visible");
  window.setTimeout(() => toast.classList.remove("visible"), 4500);
}

function setScanButtonBusy(isBusy) {
  const button = document.querySelector("#scan-button");
  if (!button) return;
  button.disabled = isBusy;
  button.textContent = isBusy ? "Scanning..." : "Manual scan";
  button.classList.toggle("is-busy", isBusy);
}

function pageIsForeground() {
  return document.visibilityState === "visible" && document.hasFocus();
}

function monitorManualScan(previousLastScan) {
  if (scanMonitor) {
    window.clearTimeout(scanMonitor);
  }
  scanMonitorPreviousLastScan = previousLastScan;
  scanMonitorDeadline = scanMonitorDeadline || Date.now() + 120000;
  setScanButtonBusy(true);
  if (!pageIsForeground()) {
    setLiveText("poll-policy", "Not foreground: live polling and scan watching paused.");
    scanMonitor = null;
    return;
  }
  scanMonitor = window.setTimeout(async () => {
    await updateLiveReadouts();
    if (scanTiming.lastScan && scanTiming.lastScan !== previousLastScan) {
      window.clearTimeout(scanMonitor);
      scanMonitor = null;
      scanMonitorPreviousLastScan = null;
      scanMonitorDeadline = null;
      setScanButtonBusy(false);
      showToast("Scan complete. Host readouts updated.");
      return;
    }
    if (Date.now() > scanMonitorDeadline) {
      window.clearTimeout(scanMonitor);
      scanMonitor = null;
      scanMonitorPreviousLastScan = null;
      scanMonitorDeadline = null;
      setScanButtonBusy(false);
      showToast("Scan did not report a new host snapshot within two minutes.");
      return;
    }
    monitorManualScan(previousLastScan);
  }, 2000);
}

document.querySelector("#scan-button")?.addEventListener("click", async () => {
  const previousLastScan = scanTiming.lastScan;
  setScanButtonBusy(true);
  try {
    const response = await fetch("/api/scan", { method: "POST" });
    const payload = await response.json();
    if (payload.status === "started") {
      showToast("Scan started. Waiting for fresh host snapshot.");
      scanMonitorDeadline = Date.now() + 120000;
      monitorManualScan(previousLastScan);
    } else {
      showToast("Scan is already running. Watching for fresh host snapshot.");
      scanMonitorDeadline = Date.now() + 120000;
      monitorManualScan(previousLastScan);
    }
  } catch (error) {
    setScanButtonBusy(false);
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

function setSelectedScope(scope) {
  document.querySelectorAll("[data-scope-nav]").forEach((link) => {
    const isSelected = link.dataset.scopeNav === scope;
    link.classList.toggle("is-selected", isSelected);
    if (isSelected) {
      link.setAttribute("aria-current", "page");
    } else {
      link.removeAttribute("aria-current");
    }
  });
}

function initScopeNav() {
  const links = document.querySelectorAll("[data-scope-nav]");
  if (!links.length) return;
  const activeScope = document.body.dataset.activeScope || "LOCAL";
  window.localStorage.setItem(SCOPE_STORAGE_KEY, activeScope);
  setSelectedScope(activeScope);
  links.forEach((link) => {
    link.addEventListener("click", () => {
      window.localStorage.setItem(SCOPE_STORAGE_KEY, link.dataset.scopeNav || "LOCAL");
      setSelectedScope(link.dataset.scopeNav || "LOCAL");
    });
  });
}

document.querySelectorAll("[data-codex-scenario]").forEach((button) => {
  button.addEventListener("click", async () => {
    if (button.dataset.launching === "1") return;
    const originalTitle = button.getAttribute("title") || "Open Codex terminal";
    button.dataset.launching = "1";
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
      delete button.dataset.launching;
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

function setTrendState(name, value) {
  document.querySelectorAll(`[data-trend-state="${name}"]`).forEach((node) => {
    node.textContent = value;
  });
}

function pushHistory(name, value) {
  if (
    !Object.prototype.hasOwnProperty.call(liveHistory, name) ||
    value === null ||
    value === undefined
  ) {
    return;
  }
  const number = Number(value);
  if (!Number.isFinite(number)) return;
  const now = Date.now();
  liveHistory[name].push({ t: now, value: number });
  while (liveHistory[name].length && now - liveHistory[name][0].t > HISTORY_WINDOW_MS) {
    liveHistory[name].shift();
  }
}

function sparklineDomain(values, scale) {
  if (scale === "percent") return { min: 0, max: 100 };
  if (scale === "celsius") return { min: 0, max: Math.max(100, ...values) };
  const max = Math.max(...values, 1);
  return { min: 0, max };
}

function renderSparkline(name) {
  const samples = liveHistory[name] || [];
  const svgNodes = document.querySelectorAll(`[data-sparkline="${name}"]`);
  if (!svgNodes.length) return;
  if (samples.length < 2) {
    const stateNode = document.querySelector(`[data-trend-state="${name}"]`);
    const emptyLabel = stateNode?.dataset.emptyLabel || "collecting";
    setTrendState(name, samples.length ? `collecting ${samples.length}/2` : emptyLabel);
    svgNodes.forEach((svg) => {
      svg.classList.add("is-empty");
      svg.querySelector("polyline")?.setAttribute("points", "");
    });
    return;
  }

  const values = samples.map((sample) => sample.value);
  svgNodes.forEach((svg) => {
    const { min, max } = sparklineDomain(values, svg.dataset.scale || "dynamic");
    const span = max - min || 1;
    const points = values
      .map((value, index) => {
        const x = (index / (values.length - 1)) * 100;
        const y = 25 - ((Math.max(min, Math.min(max, value)) - min) / span) * 24;
        return `${x.toFixed(2)},${y.toFixed(2)}`;
      })
      .join(" ");
    svg.classList.remove("is-empty");
    svg.querySelector("polyline")?.setAttribute("points", points);
  });
  setTrendState(name, `${samples.length} samples`);
}

function renderAllSparklines() {
  Object.keys(liveHistory).forEach(renderSparkline);
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

function updatePowerPolicy(power) {
  const onBattery = Boolean(power?.on_battery);
  livePower.onBattery = onBattery;
  livePower.source = power?.source || "unknown";
  if (!pageIsForeground()) {
    setLiveText("poll-policy", "Not foreground: live polling paused until this page is active.");
  } else if (onBattery) {
    setLiveText("poll-policy", "Battery + foreground: live polling every 5s.");
  } else {
    setLiveText("poll-policy", "External power + foreground: live polling every 3s.");
  }
}

function livePollDelay() {
  if (!pageIsForeground()) return null;
  return livePower.onBattery ? 5000 : 3000;
}

function scheduleLiveReadout(delayOverride = undefined) {
  if (livePollTimer) {
    window.clearTimeout(livePollTimer);
    livePollTimer = null;
  }
  const delay = delayOverride ?? livePollDelay();
  if (delay === null) {
    updatePowerPolicy({ on_battery: livePower.onBattery, source: livePower.source });
    return;
  }
  livePollTimer = window.setTimeout(async () => {
    if (!pageIsForeground()) {
      scheduleLiveReadout();
      return;
    }
    await updateLiveReadouts();
    scheduleLiveReadout();
  }, delay);
}

function scheduleScanClock() {
  if (scanClockTimer) {
    window.clearTimeout(scanClockTimer);
    scanClockTimer = null;
  }
  if (!pageIsForeground()) return;
  scanClockTimer = window.setTimeout(() => {
    updateScanTimers();
    scheduleScanClock();
  }, 1000);
}

function pauseLiveActivity() {
  if (livePollTimer) {
    window.clearTimeout(livePollTimer);
    livePollTimer = null;
  }
  if (scanClockTimer) {
    window.clearTimeout(scanClockTimer);
    scanClockTimer = null;
  }
  if (scanMonitor) {
    window.clearTimeout(scanMonitor);
    scanMonitor = null;
  }
  updatePowerPolicy({ on_battery: livePower.onBattery, source: livePower.source });
}

function resumeLiveActivity() {
  if (!pageIsForeground()) {
    pauseLiveActivity();
    return;
  }
  updateLiveReadouts().finally(() => {
    scheduleScanClock();
    scheduleLiveReadout();
    if (scanMonitorPreviousLastScan !== null && scanMonitorDeadline !== null) {
      monitorManualScan(scanMonitorPreviousLastScan);
    }
  });
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

function thermalMax(live) {
  const value = live.thermal?.max_celsius;
  return value === null || value === undefined ? null : Number(value);
}

function updateLiveHistory(live, cpu, rates) {
  const score = live.scan_timing?.score ?? scanTiming.score;
  const memoryPressure = pressureAvg10(live.pressure?.memory);
  const ioPressure = pressureAvg10(live.pressure?.io);
  pushHistory("system-score", score);
  pushHistory("net-rx", rates.rx);
  pushHistory("net-tx", rates.tx);
  pushHistory("cpu", cpu);
  pushHistory("memory", live.memory?.used_percent);
  pushHistory("memory-pressure", memoryPressure);
  pushHistory("fs-root", live.filesystems?.root?.used_percent);
  pushHistory("io-pressure", ioPressure);
  pushHistory("thermal", thermalMax(live));
  renderAllSparklines();
}

async function updateLiveReadouts() {
  if (!pageIsForeground()) return null;
  if (liveReadoutInFlight) return liveReadoutInFlight;
  liveReadoutInFlight = (async () => {
    const response = await fetch("/api/live", { cache: "no-store" });
    if (!response.ok) throw new Error(response.statusText);
    const live = await response.json();
    updatePowerPolicy(live.power);
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
    updateLiveHistory(live, cpu, rates);
    updateScanTimers();
    previousLive = live;
    return live;
  })();

  try {
    return await liveReadoutInFlight;
  } catch (error) {
    setLiveText("net-rx-rate", "live off");
    setLiveText("net-tx-rate", "live off");
    return null;
  } finally {
    liveReadoutInFlight = null;
  }
}

initScopeNav();
updateScanTimers();
resumeLiveActivity();
document.addEventListener("visibilitychange", () => {
  if (pageIsForeground()) {
    resumeLiveActivity();
  } else {
    pauseLiveActivity();
  }
});
window.addEventListener("focus", resumeLiveActivity);
window.addEventListener("blur", pauseLiveActivity);
window.addEventListener("pagehide", pauseLiveActivity);
window.addEventListener("pageshow", resumeLiveActivity);
document.addEventListener("freeze", pauseLiveActivity);
document.addEventListener("resume", resumeLiveActivity);
