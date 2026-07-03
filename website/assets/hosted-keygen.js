(function () {
  const form = document.getElementById("hostedKeyForm");
  const statusEl = document.getElementById("hostedKeyStatus");
  const statusForm = document.getElementById("hostedKeyStatusForm");
  const lookupStatusEl = document.getElementById("hostedKeyLookupStatus");
  const reissueForm = document.getElementById("hostedKeyReissueForm");
  const reissueStatusEl = document.getElementById("hostedKeyReissueStatus");

  if (!form && !statusForm && !reissueForm) {
    return;
  }

  const endpoint = form?.dataset.endpoint || "/v1/hosted/beta-key";
  const checkoutEndpoint =
    form?.dataset.checkoutEndpoint || "/v1/billing/stripe/checkout-session";
  const statusEndpoint = form?.dataset.statusEndpoint || "/v1/billing/stripe/status";
  const readyFlag = form?.dataset.readyFlag || "ready_for_beta_key_delivery";
  const statusCheckEndpoint =
    statusForm?.dataset.statusCheckEndpoint || "/v1/hosted/beta-key/status";
  const reissueEndpoint =
    reissueForm?.dataset.reissueEndpoint || "/v1/hosted/beta-key/reissue";

  if (form && statusEl) {
    checkReadiness();
  }

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = form.querySelector("button[type='submit']");
    const formData = new FormData(form);
    const name = String(formData.get("name") || "").trim();
    const email = String(formData.get("email") || "").trim();
    const keyName = String(formData.get("key_name") || "Hosted beta key").trim();
    const packageId = String(formData.get("package_id") || "beta_trial").trim();

    if (!name) {
      setStatus("Enter your name or app name for API key registration.", "error");
      return;
    }

    if (!email) {
      setStatus("Enter an email address for API key delivery.", "error");
      return;
    }

    setStatus("Checking beta key delivery readiness...", "running");
    if (submitButton) submitButton.disabled = true;

    try {
      const readiness = await fetchCheckoutReadiness();
      if (readiness && readiness.beta_signup_enabled !== true) {
        throw new Error("Hosted beta registration is not open yet. Existing keys still work.");
      }

      if (readiness && readiness[readyFlag] !== true) {
        setStatus("Recording beta request for later API-key email delivery...", "running");
      }
      await submitEmailRegistration({ name, email, keyName });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Hosted beta key registration is not ready yet.";
      setStatus(message, "error");
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  });

  statusForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = statusForm.querySelector("button[type='submit']");
    const formData = new FormData(statusForm);
    const email = String(formData.get("email") || "").trim();

    if (!email) {
      setLookupStatus("Enter the email used for beta registration.", "error");
      return;
    }

    setLookupStatus("Checking beta request status...", "running");
    if (submitButton) submitButton.disabled = true;

    try {
      const response = await fetch(statusCheckEndpoint, {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({ email }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || "Could not check beta request status.");
      }
      setLookupStatus(statusMessage(payload), payload.status === "not_found" ? "error" : "success");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not check beta request status.";
      setLookupStatus(message, "error");
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  });

  reissueForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = reissueForm.querySelector("button[type='submit']");
    const formData = new FormData(reissueForm);
    const email = String(formData.get("email") || "").trim();

    if (!email) {
      setReissueStatus("Enter the email used for hosted Scout access.", "error");
      return;
    }

    setReissueStatus("Requesting a replacement API key...", "running");
    if (submitButton) submitButton.disabled = true;

    try {
      const response = await fetch(reissueEndpoint, {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({ email }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || "Could not request a replacement API key.");
      }
      setReissueStatus(reissueMessage(payload), "success");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not request a replacement API key.";
      setReissueStatus(message, "error");
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  });

  async function checkReadiness() {
    if (!form || !statusEl) return;
    const submitButton = form.querySelector("button[type='submit']");
    try {
      const response = await fetch(statusEndpoint, { headers: { accept: "application/json" } });
      if (!response.ok) return;
      const status = await response.json();
      if (status[readyFlag] === true) {
        if (submitButton) submitButton.disabled = false;
        setStatus(
          "Beta API-key email delivery is ready. Register to receive your key by email.",
          "success",
        );
        return;
      }
      if (status.beta_signup_enabled === true) {
        if (submitButton) submitButton.disabled = false;
        setStatus(
          "Beta registration is open. Scout will record your request and email the API key when delivery is configured.",
          "success",
        );
        return;
      }
      if (status[readyFlag] !== true) {
        if (submitButton) submitButton.disabled = true;
        setStatus(
          "Hosted beta registration is not open yet. Existing keys still work.",
          "error",
        );
      }
    } catch {
      // Static previews cannot reach the API; keep the form interactive there.
    }
  }

  async function fetchCheckoutReadiness() {
    try {
      const response = await fetch(statusEndpoint, { headers: { accept: "application/json" } });
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }

  async function submitEmailRegistration({ name, email, keyName }) {
    return submitEmailFallback({ name, email, keyName });
  }

  async function submitCheckout({ name, email, packageId }) {
    setStatus("Creating $0 Stripe Checkout Session...", "running");
    const response = await fetch(checkoutEndpoint, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ name, email, package_id: packageId || "beta_trial" }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || "Beta checkout verification is not ready yet.");
    }
    if (!payload.checkout_url) {
      throw new Error("Stripe did not return a checkout URL.");
    }
    setStatus("Redirecting to Stripe Checkout for $0 beta setup...", "running");
    window.location.assign(payload.checkout_url);
  }

  async function submitEmailFallback({ name, email, keyName }) {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ name, email, key_name: keyName || "Hosted beta key" }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || "Hosted beta key registration is not ready yet.");
    }
    if (payload.delivery_status === "pending_delivery") {
      setStatus(
        `Scout recorded your beta request for ${email}. The API key will be emailed when hosted key delivery is configured.`,
        "success",
      );
    } else {
      setStatus(
        `Scout emailed your beta tester API key to ${email}. Check your inbox and keep the key private.`,
        "success",
      );
    }
    form.reset();
  }

  function setStatus(message, state) {
    statusEl.textContent = message;
    statusEl.dataset.state = state;
  }

  function setLookupStatus(message, state) {
    if (!lookupStatusEl) return;
    lookupStatusEl.textContent = message;
    lookupStatusEl.dataset.state = state;
  }

  function setReissueStatus(message, state) {
    if (!reissueStatusEl) return;
    reissueStatusEl.textContent = message;
    reissueStatusEl.dataset.state = state;
  }

  function statusMessage(payload) {
    const message = payload.message || "Scout returned the current beta request status.";
    const status = payload.status ? `Status: ${payload.status}. ` : "";
    return `${status}${message}`;
  }

  function reissueMessage(payload) {
    return (
      payload.message ||
      "If a hosted Scout account exists for this email, Scout will email a replacement API key."
    );
  }
})();
