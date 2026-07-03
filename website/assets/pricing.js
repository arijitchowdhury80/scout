(function () {
  const pricingSection = document.querySelector("[data-packages-endpoint]");
  const packageGrid = document.getElementById("pricingPackageGrid");
  const creditCosts = document.getElementById("pricingCreditCosts");
  const unitEconomics = document.getElementById("pricingUnitEconomics");
  const checkoutForm = document.getElementById("pricingCheckoutForm");
  const checkoutStatus = document.getElementById("pricingCheckoutStatus");
  const checkoutReturnStatus = document.getElementById("pricingCheckoutReturnStatus");

  if (!pricingSection && !checkoutForm) {
    return;
  }

  const endpoint = pricingSection?.dataset.packagesEndpoint || "/v1/billing/packages";
  const checkoutEndpoint =
    checkoutForm?.dataset.endpoint ||
    checkoutForm?.dataset.checkoutEndpoint ||
    pricingSection?.dataset.checkoutEndpoint ||
    "/v1/billing/stripe/checkout-session";
  const checkoutStatusEndpoint =
    checkoutForm?.dataset.statusEndpoint ||
    pricingSection?.dataset.checkoutStatusEndpoint ||
    "/v1/billing/stripe/status";

  if (pricingSection && packageGrid && creditCosts && unitEconomics) {
    fetch(endpoint, { headers: { Accept: "application/json" } })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Pricing endpoint unavailable");
        }
        return response.json();
      })
      .then((data) => renderPricing(data))
      .catch(() => {
        packageGrid.dataset.pricingStatus = "fallback";
      });
  }

  handleCheckoutReturnState();
  checkCheckoutReadiness();
  checkoutForm
    ?.querySelector("[name='package_id']")
    ?.addEventListener("change", checkCheckoutReadiness);

  checkoutForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = checkoutForm.querySelector("button[type='submit']");
    const formData = new FormData(checkoutForm);
    const name = String(formData.get("name") || "").trim();
    const email = String(formData.get("email") || "").trim();
    const packageId = String(formData.get("package_id") || "standard_1000");

    if (!name) {
      setCheckoutStatus("Enter your name or app name for API key registration.", "error");
      return;
    }

    if (!email) {
      setCheckoutStatus("Enter an email address for API key delivery.", "error");
      return;
    }

    setCheckoutStatus("Creating Stripe Checkout Session...", "loading");
    if (submitButton) submitButton.disabled = true;

    try {
      const response = await fetch(checkoutEndpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name, email, package_id: packageId }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || "Hosted checkout is not configured yet.");
      }
      if (!payload.checkout_url) {
        throw new Error("Stripe did not return a checkout URL.");
      }
      setCheckoutStatus("Redirecting to Stripe Checkout...", "loading");
      window.location.assign(payload.checkout_url);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Hosted checkout is not configured yet.";
      setCheckoutStatus(message, "error");
      if (submitButton) submitButton.disabled = false;
    }
  });

  function renderPricing(data) {
    const packages = Array.isArray(data.packages) ? data.packages : [];
    const publicPackages = packages.filter((pkg) =>
      ["beta_trial", "standard_1000", "standard_3000", "standard_15000"].includes(
        String(pkg.package_id || ""),
      ),
    );
    if (publicPackages.length > 0) {
      packageGrid.innerHTML = publicPackages.map(packageCard).join("");
    }

    const credit_policy = Array.isArray(data.credit_policy) ? data.credit_policy : [];
    const creditEntries = Object.entries(data.credit_costs || {});
    if (credit_policy.length > 0) {
      creditCosts.innerHTML = credit_policy.map(creditPolicyCard).join("");
    } else if (creditEntries.length > 0) {
      creditCosts.innerHTML = creditEntries.map(creditCard).join("");
    }

    const standardEconomics = data.unit_economics && data.unit_economics.standard_1000;
    if (standardEconomics) {
      unitEconomics.innerHTML = unitEconomicsCards(standardEconomics);
    }
  }

  function packageCard(pkg) {
    const amount_cents = Number(pkg.amount_cents || 0);
    const price = amount_cents === 0 ? "Beta trial" : `$${formatDollars(amount_cents)}`;
    const credits = [
      `${Number(pkg.standard_credits || 0).toLocaleString()} standard credits`,
      `${Number(pkg.browser_credits || 0).toLocaleString()} browser credits`,
    ].join(" / ");
    const label = pkg.is_public_purchase ? "Pay as you go" : "Beta";
    return `
      <article>
        <span class="price">${escapeHtml(price)}</span>
        <h3>${escapeHtml(pkg.name || pkg.package_id || "Hosted package")}</h3>
        <p>${escapeHtml(pkg.customer_summary || credits)}</p>
        <p><strong>${escapeHtml(label)}:</strong> ${escapeHtml(credits)}</p>
      </article>
    `;
  }

  function creditCard([action, meaning]) {
    return `
      <article>
        <span class="status-tag status-tag--primary">${escapeHtml(action)}</span>
        <h3>${titleize(action)}</h3>
        <p>${escapeHtml(meaning)}</p>
      </article>
    `;
  }

  function creditPolicyCard(policy) {
    const action = String(policy.action || "");
    const creditType = String(policy.credit_type || "standard");
    const credits = Number(policy.credits_per_unit || 0);
    const unit = String(policy.metered_unit || "unit");
    const included = Number(policy.included_in_standard_1000 || 0);
    const includedText =
      included > 0 ? `${included.toLocaleString()} per 1,000-credit pack` : "not in standard packs";
    return `
      <article>
        <span class="status-tag status-tag--primary">${escapeHtml(creditType)}</span>
        <h3>${titleize(action)}</h3>
        <p>${credits.toLocaleString()} ${escapeHtml(creditType)} credit${
          credits === 1 ? "" : "s"
        } per ${escapeHtml(unit)}.</p>
        <p>${escapeHtml(policy.customer_description || "")}</p>
        <p><strong>Standard 1,000 pack:</strong> ${escapeHtml(includedText)}</p>
      </article>
    `;
  }

  function unitEconomicsCards(economics) {
    return [
      economicsCard(
        "$10 package",
        "1,000 standard credits",
        `Estimated cost for 1,000 standard credits: ${formatMoney(
          economics.loaded_cost_cents,
        )}.`,
      ),
      economicsCard(
        "Margin",
        "Default target is measured",
        `Estimated gross margin: ${Number(economics.gross_margin_percent).toFixed(
          1,
        )}%. Break-even: ${Number(
          economics.break_even_packages_per_month,
        ).toLocaleString()} packs/month.`,
      ),
      economicsCard(
        "Assumption",
        "Numbers are adjustable",
        "Hosting, browser, LLM, support, firewall, and payment costs can change this model.",
      ),
    ].join("");
  }

  function economicsCard(tag, title, body) {
    return `
      <article>
        <span class="status-tag status-tag--primary">${escapeHtml(tag)}</span>
        <h3>${escapeHtml(title)}</h3>
        <p>${escapeHtml(body)}</p>
      </article>
    `;
  }

  function setCheckoutStatus(message, state) {
    if (!checkoutStatus) return;
    checkoutStatus.textContent = message;
    checkoutStatus.dataset.state = state;
  }

  function handleCheckoutReturnState() {
    if (!checkoutReturnStatus) return;
    const checkoutState = new URLSearchParams(window.location.search).get("checkout");
    if (checkoutState === "success") {
      checkoutReturnStatus.hidden = false;
      checkoutReturnStatus.dataset.state = "success";
      checkoutReturnStatus.textContent =
        "Stripe payment completed. Scout will email your hosted API key after the signed webhook provisions access.";
    } else if (checkoutState === "cancelled") {
      checkoutReturnStatus.hidden = false;
      checkoutReturnStatus.dataset.state = "error";
      checkoutReturnStatus.textContent =
        "Stripe checkout was cancelled. No hosted credits were provisioned; local Scout remains available.";
    }
  }

  async function checkCheckoutReadiness() {
    if (!checkoutForm || !checkoutStatus) return;
    const submitButton = checkoutForm.querySelector("button[type='submit']");
    const packageInput = checkoutForm.querySelector("[name='package_id']");
    const packageId = packageInput ? String(packageInput.value || "") : "standard_1000";
    const readyFlag = readyFlagForPackage(packageId);
    try {
      const response = await fetch(checkoutStatusEndpoint, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return;
      const status = await response.json();
      if (status[readyFlag] === true) {
        if (submitButton) submitButton.disabled = false;
        setCheckoutStatus(checkoutReadyMessage(packageId), "success");
      } else {
        if (submitButton) submitButton.disabled = true;
        setCheckoutStatus(
          readinessDetailsMessage(status) || checkoutPausedMessage(packageId),
          "error",
        );
      }
    } catch {
      // Static file previews cannot reach the API; keep the form interactive there.
    }
  }

  function readyFlagForPackage(packageId) {
    if (checkoutForm?.dataset.readyFlag) {
      return checkoutForm.dataset.readyFlag;
    }
    return packageId === "beta_trial" ? "ready_for_beta_checkout" : "ready_for_paid_key_delivery";
  }

  function checkoutReadyMessage(packageId) {
    if (packageId === "beta_trial") {
      return "Card-backed beta checkout is ready. Continue to Stripe to complete $0 beta setup.";
    }
    return "Hosted credit checkout is ready. Continue to Stripe to buy credits.";
  }

  function checkoutPausedMessage(packageId) {
    if (packageId === "beta_trial") {
      return "Card-backed beta checkout is paused until Stripe checkout, webhook provisioning, and API-key email delivery are configured. Use the email beta key path if it is ready.";
    }
    return "Hosted checkout is paused until Stripe checkout, webhook provisioning, and API-key email delivery are configured. Existing keys still work.";
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

  function formatDollars(cents) {
    const dollars = cents / 100;
    return Number.isInteger(dollars) ? String(dollars) : dollars.toFixed(2);
  }

  function formatMoney(cents) {
    return `$${formatDollars(Number(cents || 0))}`;
  }

  function titleize(value) {
    return escapeHtml(
      String(value || "")
        .replace(/_/g, " ")
        .replace(/\b\w/g, (letter) => letter.toUpperCase()),
    );
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
})();
