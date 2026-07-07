(function () {
  const form = document.getElementById("hostedRegisterForm");
  const statusEl = document.getElementById("hostedRegStatus");
  const cardButton = document.getElementById("hostedRegCardBtn");
  const emailButton = document.getElementById("hostedRegEmailBtn");
  const reissueForm = document.getElementById("hostedKeyReissueForm");
  const reissueStatusEl = document.getElementById("hostedKeyReissueStatus");

  if (!form && !reissueForm) {
    return;
  }

  const endpoint = form?.dataset.endpoint || "/v1/hosted/beta-key";
  const statusEndpoint = form?.dataset.statusEndpoint || "/v1/billing/stripe/status";
  const reissueEndpoint =
    reissueForm?.dataset.reissueEndpoint || "/v1/hosted/beta-key/reissue";
  const checkoutEndpoint =
    form?.dataset.checkoutEndpoint || "/v1/billing/stripe/checkout-session";
  const checkoutReadyFlag = form?.dataset.readyFlag || "ready_for_beta_checkout";

  // Status stays empty until the user submits, no on-load "checking…" text.

  cardButton?.addEventListener("click", async () => {
    if (!form || !validateForm()) return;

    const { name, email } = readFormValues();
    const packageId = String(new FormData(form).get("package_id") || "beta_trial").trim();

    setStatus("Checking card-backed beta setup readiness...", "running");
    setButtonsDisabled(true);

    try {
      const readiness = await fetchRegistrationReadiness();
      if (readiness && readiness[checkoutReadyFlag] !== true) {
        throw new Error(
          readinessDetailsMessage(readiness) ||
            "Card-backed beta setup is not ready yet. Use email registration or try again after Stripe is configured.",
        );
      }
      const response = await fetch(checkoutEndpoint, {
        method: "POST",
        headers: { "content-type": "application/json", accept: "application/json" },
        body: JSON.stringify({ name, email, package_id: packageId || "beta_trial" }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || "Card-backed beta setup is not ready yet.");
      }
      if (!payload.checkout_url) {
        throw new Error("Stripe did not return a beta checkout URL.");
      }
      setStatus("Redirecting to Stripe for $0 beta setup...", "running");
      window.location.assign(payload.checkout_url);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Card-backed beta setup is not ready yet.";
      setStatus(message, "error");
      setButtonsDisabled(false);
    }
  });

  emailButton?.addEventListener("click", async () => {
    if (!form || !validateForm()) return;

    const { name, email } = readFormValues();
    const keyName = String(new FormData(form).get("key_name") || "Hosted beta key").trim();

    setStatus("Checking beta registration readiness...", "running");
    setButtonsDisabled(true);

    try {
      const readiness = await fetchRegistrationReadiness();
      if (readiness && readiness.beta_signup_enabled !== true) {
        throw new Error(
          readinessDetailsMessage(readiness) ||
            "Hosted beta registration is not open yet. Existing keys still work.",
        );
      }

      setStatus("Registering beta tester and preparing API-key email delivery...", "running");
      await submitEmailRegistration({ name, email, keyName });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Hosted beta key registration is not ready yet.";
      setStatus(message, "error");
    } finally {
      setButtonsDisabled(false);
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

  function readFormValues() {
    const formData = new FormData(form);
    return {
      name: String(formData.get("name") || "").trim(),
      email: String(formData.get("email") || "").trim(),
    };
  }

  function validateForm() {
    if (!form) return false;
    if (typeof form.reportValidity === "function" && !form.reportValidity()) {
      return false;
    }
    const { name, email } = readFormValues();
    if (!name) {
      setStatus("Enter your name or app name for API key registration.", "error");
      return false;
    }
    if (!email) {
      setStatus("Enter an email address for API key delivery.", "error");
      return false;
    }
    return true;
  }

  function setButtonsDisabled(disabled) {
    if (cardButton) cardButton.disabled = disabled;
    if (emailButton) emailButton.disabled = disabled;
  }

  async function checkReadiness() {
    try {
      const response = await fetch(statusEndpoint, { headers: { accept: "application/json" } });
      if (!response.ok) return;
      const status = await response.json();

      const emailReady = status.beta_signup_enabled === true;
      const cardReady = status[checkoutReadyFlag] === true;

      if (emailButton) emailButton.disabled = !emailReady;
      if (cardButton) cardButton.disabled = !cardReady;

      if (cardReady) {
        setStatus(
          "Card-backed beta setup is ready. Stripe will collect a payment method and charge $0.",
          "success",
        );
      } else if (emailReady && status.ready_for_beta_key_delivery === true) {
        setStatus(
          "Hosted beta registration and email delivery are ready. Register and Scout will email your API key.",
          "success",
        );
      } else if (emailReady) {
        setStatus(
          readinessDetailsMessage(status) ||
            "Hosted beta registration is open, but email delivery is not configured. Scout will record your request for follow-up.",
          "error",
        );
      } else {
        setStatus(
          readinessDetailsMessage(status) ||
            "Hosted beta registration is not open yet. Existing keys still work.",
          "error",
        );
      }
    } catch {
      // Static previews cannot reach the API; keep the form interactive there.
    }
  }

  async function fetchRegistrationReadiness() {
    try {
      const response = await fetch(statusEndpoint, { headers: { accept: "application/json" } });
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }

  function readinessDetailsMessage(status) {
    const blocking_reasons = Array.isArray(status.blocking_reasons)
      ? status.blocking_reasons
      : [];
    const operator_next_actions = Array.isArray(status.operator_next_actions)
      ? status.operator_next_actions
      : [];
    const reasons = blocking_reasons.filter(Boolean).join(" ");
    const actions = operator_next_actions.filter(Boolean).join(" ");

    if (!reasons && !actions) {
      return "";
    }
    if (reasons && actions) {
      return `${reasons} Next: ${actions}`;
    }
    return reasons || `Next: ${actions}`;
  }

  async function submitEmailRegistration({ name, email, keyName }) {
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
        `Scout recorded your beta request for ${email}. The API key will be emailed after delivery is configured.`,
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
    if (!statusEl) return;
    statusEl.textContent = message;
    statusEl.dataset.state = state;
  }

  function setReissueStatus(message, state) {
    if (!reissueStatusEl) return;
    reissueStatusEl.textContent = message;
    reissueStatusEl.dataset.state = state;
  }

  function reissueMessage(payload) {
    return (
      payload.message ||
      "If a hosted Scout account exists for this email, Scout will email a replacement API key."
    );
  }
})();
