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

document.querySelector("[data-toggle-evidence]")?.addEventListener("click", () => {
  document.body.classList.toggle("evidence-mode");
});

document.querySelectorAll(".handoff-form").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const repoId = Number(form.dataset.repoId);
    const task = form.querySelector("textarea[name='task']").value;
    try {
      const response = await fetch("/api/handoffs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_id: repoId, task }),
      });
      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.detail || response.statusText);
      }
      const packet = await response.json();
      showToast(`Handoff packet written: ${packet.path}`);
    } catch (error) {
      showToast(`Handoff failed: ${error}`);
    }
  });
});
