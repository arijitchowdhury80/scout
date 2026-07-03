(function () {
  const form = document.getElementById("hostedAccountForm");
  const keyInput = document.getElementById("hostedAccountKey");
  const status = document.getElementById("hostedAccountStatus");
  const summary = document.getElementById("hostedAccountSummary");
  const usageLedger = document.getElementById("hostedUsageLedger");
  const purchaseLedger = document.getElementById("hostedPurchaseLedger");
  const billingPortalButton = document.getElementById("hostedBillingPortalButton");
  let currentApiKey = "";

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const apiKey = String(keyInput?.value || "").trim();
    if (!apiKey) {
      setStatus("Enter a hosted API key.", "error");
      return;
    }
    currentApiKey = "";
    setBillingPortalEnabled(false);
    setStatus("Loading hosted account...", "loading");
    try {
      const [account, usage, purchases] = await Promise.all([
        getHosted("/v1/hosted/me", apiKey),
        getHosted("/v1/hosted/usage?limit=25", apiKey),
        getHosted("/v1/hosted/purchases?limit=25", apiKey),
      ]);
      renderSummary(account);
      renderUsage(usage);
      renderPurchases(purchases);
      currentApiKey = apiKey;
      setBillingPortalEnabled(true);
      setStatus("Account loaded. API key was not stored.", "success");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not load account.";
      setStatus(message, "error");
    }
  });

  billingPortalButton?.addEventListener("click", async () => {
    if (!currentApiKey) {
      setStatus("Check account before opening billing.", "error");
      return;
    }
    setBillingPortalEnabled(false);
    setStatus("Creating Stripe billing portal session...", "loading");
    try {
      const payload = await postHosted("/v1/billing/stripe/customer-portal-session", currentApiKey);
      const portalUrl = String(payload.portal_url || "");
      if (!portalUrl) {
        throw new Error(payload.reason || "Scout did not return a billing portal URL.");
      }
      setStatus("Redirecting to Stripe billing portal...", "success");
      window.location.assign(portalUrl);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not open billing portal.";
      setStatus(message, "error");
      setBillingPortalEnabled(true);
    }
  });

  async function getHosted(path, apiKey) {
    const response = await fetch(path, {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Scout returned HTTP ${response.status}.`);
    }
    return payload;
  }

  async function postHosted(path, apiKey) {
    const response = await fetch(path, {
      method: "POST",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Scout returned HTTP ${response.status}.`);
    }
    return payload;
  }

  function renderSummary(account) {
    if (!summary) return;
    const balance = account.balance || {};
    const limits = account.limits || {};
    const usage = account.usage_summary || {};
    const purchases = account.purchase_summary || {};
    summary.innerHTML = [
      card(
        "Plan",
        escapeHtml(account.plan || "unknown"),
        `Status: ${escapeHtml(account.account_status || "unknown")}`,
      ),
      card(
        "Standard credits",
        Number(balance.standard_credits_remaining || 0).toLocaleString(),
        `Plan limit: ${Number(limits.standard_credits || 0).toLocaleString()}`,
      ),
      card(
        "Browser credits",
        Number(balance.browser_credits_remaining || 0).toLocaleString(),
        `Plan limit: ${Number(limits.browser_credits || 0).toLocaleString()}`,
      ),
      card(
        "Usage",
        `${Number(usage.standard_credits_used || 0).toLocaleString()} standard used`,
        `${Number(usage.total_events || 0).toLocaleString()} ledger events`,
      ),
      card(
        "Purchases",
        `${Number(purchases.total_purchases || 0).toLocaleString()} purchases`,
        `${formatMoney(purchases.total_amount_cents || 0)} total`,
      ),
    ].join("");
  }

  function renderUsage(payload) {
    if (!usageLedger) return;
    const rows = Array.isArray(payload.usage) ? payload.usage : [];
    usageLedger.innerHTML = rows.length
      ? rows.map((row) => ledgerRow(row.action, `${row.credits} ${row.credit_type}`, row.created_at)).join("")
      : "No usage events yet.";
  }

  function renderPurchases(payload) {
    if (!purchaseLedger) return;
    const rows = Array.isArray(payload.purchases) ? payload.purchases : [];
    purchaseLedger.innerHTML = rows.length
      ? rows
          .map((row) =>
            ledgerRow(
              row.package_id,
              `${formatMoney(row.amount_total_cents)} ${String(row.currency || "").toUpperCase()}`,
              row.created_at,
            ),
          )
          .join("")
      : "No purchases yet.";
  }

  function card(label, title, body) {
    return `
      <article>
        <span class="status-tag status-tag--primary">${escapeHtml(label)}</span>
        <h3>${escapeHtml(title)}</h3>
        <p>${escapeHtml(body)}</p>
      </article>
    `;
  }

  function ledgerRow(title, meta, date) {
    return `
      <div class="ledger-row">
        <strong>${escapeHtml(title || "event")}</strong>
        <span>${escapeHtml(meta || "")}</span>
        <small>${escapeHtml(date || "")}</small>
      </div>
    `;
  }

  function setStatus(message, state) {
    if (!status) return;
    status.textContent = message;
    status.dataset.state = state;
  }

  function setBillingPortalEnabled(enabled) {
    if (!billingPortalButton) return;
    billingPortalButton.disabled = !enabled;
  }

  function formatMoney(cents) {
    const dollars = Number(cents || 0) / 100;
    return `$${Number.isInteger(dollars) ? dollars : dollars.toFixed(2)}`;
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
