const toast = document.querySelector("#toast");

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
