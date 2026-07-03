(function () {
  const pricingSection = document.querySelector("[data-packages-endpoint]");
  const packageGrid = document.getElementById("pricingPackageGrid");
  const creditCosts = document.getElementById("pricingCreditCosts");
  const unitEconomics = document.getElementById("pricingUnitEconomics");
  const checkoutForm = document.getElementById("pricingCheckoutForm");
  const checkoutStatus = document.getElementById("pricingCheckoutStatus");

  if (!pricingSection || !packageGrid || !creditCosts || !unitEconomics) {
    return;
  }

  const endpoint = pricingSection.dataset.packagesEndpoint || "/v1/billing/packages";
  const checkoutEndpoint =
    checkoutForm?.dataset.checkoutEndpoint ||
    pricingSection.dataset.checkoutEndpoint ||
    "/v1/billing/stripe/checkout-session";

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

  checkoutForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = checkoutForm.querySelector("button[type='submit']");
    const formData = new FormData(checkoutForm);
    const email = String(formData.get("email") || "").trim();
    const packageId = String(formData.get("package_id") || "standard_1000");

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
        body: JSON.stringify({ email, package_id: packageId }),
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

    const creditEntries = Object.entries(data.credit_costs || {});
    if (creditEntries.length > 0) {
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
