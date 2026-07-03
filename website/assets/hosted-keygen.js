(function () {
  const form = document.getElementById("hostedKeyForm");
  const statusEl = document.getElementById("hostedKeyStatus");

  if (!form || !statusEl) {
    return;
  }

  const endpoint = form.dataset.endpoint || "/v1/hosted/beta-key";
  const statusEndpoint = form.dataset.statusEndpoint || "/v1/billing/stripe/status";
  const readyFlag = form.dataset.readyFlag || "ready_for_beta_key_delivery";

  checkReadiness();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = form.querySelector("button[type='submit']");
    const formData = new FormData(form);
    const name = String(formData.get("name") || "").trim();
    const email = String(formData.get("email") || "").trim();
    const keyName = String(formData.get("key_name") || "Hosted beta key").trim();

    if (!name) {
      setStatus("Enter your name or app name for API key registration.", "error");
      return;
    }

    if (!email) {
      setStatus("Enter an email address for API key delivery.", "error");
      return;
    }

    setStatus("Registering your beta key and sending the email...", "running");
    if (submitButton) submitButton.disabled = true;

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({ name, email, key_name: keyName || "Hosted beta key" }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || "Hosted beta key registration is not ready yet.");
      }
      setStatus(
        `Scout emailed your beta tester API key to ${email}. Check your inbox and keep the key private.`,
        "success",
      );
      form.reset();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Hosted beta key registration is not ready yet.";
      setStatus(message, "error");
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  });

  async function checkReadiness() {
    const submitButton = form.querySelector("button[type='submit']");
    try {
      const response = await fetch(statusEndpoint, { headers: { accept: "application/json" } });
      if (!response.ok) return;
      const status = await response.json();
      if (status[readyFlag] !== true) {
        if (submitButton) submitButton.disabled = true;
        setStatus(
          "Hosted beta key registration is paused until API-key email delivery is configured. Existing keys still work.",
          "error",
        );
      }
    } catch {
      // Static previews cannot reach the API; keep the form interactive there.
    }
  }

  function setStatus(message, state) {
    statusEl.textContent = message;
    statusEl.dataset.state = state;
  }
})();
