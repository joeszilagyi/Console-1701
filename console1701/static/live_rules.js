// Pure live-sensor decisions. Keep thresholds and their explanations together.
(function (root) {
  "use strict";

  const thresholds = Object.freeze({
    cpu: Object.freeze({ warning: 75, critical: 90 }),
    loadPerCore: Object.freeze({ warning: 1, critical: 1.5 }),
    memoryAvailable: Object.freeze({ warningBelow: 15, criticalBelow: 5 }),
    memoryPsi: Object.freeze({ warning: 10, critical: 30 }),
    cpuPsi: Object.freeze({ warning: 20 }),
    rootUsed: Object.freeze({ warning: 85, critical: 95 }),
    homeUsed: Object.freeze({ warning: 90, critical: 95 }),
    ioPsi: Object.freeze({ warning: 10, critical: 30 }),
  });

  function numeric(value) {
    if (value === null || value === undefined || value === "") return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  function atLeast(value, limit) {
    return value !== null && value >= limit;
  }

  function below(value, limit) {
    return value !== null && value < limit;
  }

  function cpuRam(values) {
    const cpu = numeric(values.cpu);
    const loadPerCore = numeric(values.loadPerCore);
    const memoryAvailable = numeric(values.memoryAvailable);
    const memoryPsi = numeric(values.memoryPsi);
    const cpuPsi = numeric(values.cpuPsi);
    const critical =
      atLeast(cpu, thresholds.cpu.critical) ||
      atLeast(loadPerCore, thresholds.loadPerCore.critical) ||
      below(memoryAvailable, thresholds.memoryAvailable.criticalBelow) ||
      atLeast(memoryPsi, thresholds.memoryPsi.critical);
    const warning =
      critical ||
      atLeast(cpu, thresholds.cpu.warning) ||
      atLeast(loadPerCore, thresholds.loadPerCore.warning) ||
      below(memoryAvailable, thresholds.memoryAvailable.warningBelow) ||
      atLeast(memoryPsi, thresholds.memoryPsi.warning) ||
      atLeast(cpuPsi, thresholds.cpuPsi.warning);
    return { state: critical ? "critical" : warning ? "warning" : "ok", thresholds };
  }

  function filesystem(values) {
    const rootUsed = numeric(values.rootUsed);
    const homeUsed = numeric(values.homeUsed);
    const ioPsi = numeric(values.ioPsi);
    const critical =
      atLeast(rootUsed, thresholds.rootUsed.critical) ||
      atLeast(homeUsed, thresholds.homeUsed.critical) ||
      atLeast(ioPsi, thresholds.ioPsi.critical);
    const warning =
      critical ||
      atLeast(rootUsed, thresholds.rootUsed.warning) ||
      atLeast(homeUsed, thresholds.homeUsed.warning) ||
      atLeast(ioPsi, thresholds.ioPsi.warning);
    return { state: critical ? "critical" : warning ? "warning" : "ok", thresholds };
  }

  const rules = Object.freeze({ thresholds, cpuRam, filesystem });
  root.ConsoleLiveRules = rules;
  if (typeof module !== "undefined" && module.exports) module.exports = rules;
})(typeof globalThis !== "undefined" ? globalThis : this);
