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
