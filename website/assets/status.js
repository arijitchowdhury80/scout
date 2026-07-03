(function () {
  const section = document.getElementById("liveHostedReadiness");
  if (!section) return;

  const endpoint = section.dataset.statusEndpoint || "/v1/billing/stripe/status";
  const summary = document.getElementById("liveReadinessSummary");
  const cards = document.getElementById("liveReadinessCards");
  const missingKeys = document.getElementById("liveMissingKeys");
  const operatorActions = document.getElementById("liveOperatorActions");

  fetch(endpoint, { headers: { accept: "application/json" } })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Readiness endpoint returned HTTP ${response.status}.`);
      }
      return response.json();
    })
    .then(renderStatus)
    .catch((error) => {
      const message =
        error instanceof Error
          ? error.message
          : "Could not load live hosted readiness.";
      setText(summary, `Live readiness unavailable. ${message}`);
      if (cards) {
        cards.innerHTML = cardHtml(
          "Unavailable",
          "Live readiness could not be loaded",
          "Use the CLI readiness command if this browser cannot reach the endpoint.",
          "limited",
        );
      }
    });

  function renderStatus(status) {
    const betaKeyReady = status.ready_for_beta_key_delivery === true;
    const betaCheckoutReady = status.ready_for_beta_checkout === true;
    const paidReady = status.ready_for_paid_key_delivery === true;
    const allReady = betaKeyReady && betaCheckoutReady && paidReady;

    setText(
      summary,
      allReady
        ? "Hosted beta signup, beta Stripe setup, and paid checkout are ready."
        : "Hosted service is online, but at least one self-service gate is still blocked.",
    );

    if (cards) {
      cards.innerHTML = [
        cardHtml(
          betaKeyReady ? "Ready" : "Blocked",
          "Beta key email delivery",
          betaKeyReady
            ? "Name/email registration can provision and email beta API keys."
            : "Beta registration cannot complete until SMTP key delivery is configured.",
          betaKeyReady ? "primary" : "blocker",
        ),
        cardHtml(
          betaCheckoutReady ? "Ready" : "Blocked",
          "$0 beta Stripe setup",
          betaCheckoutReady
            ? "Stripe setup-mode beta checkout can collect a card and trigger provisioning."
            : "Card-backed beta setup is waiting on Stripe, webhook, and key delivery readiness.",
          betaCheckoutReady ? "primary" : "blocker",
        ),
        cardHtml(
          paidReady ? "Ready" : "Blocked",
          "Paid credit checkout",
          paidReady
            ? "Paid packages can be purchased and provisioned through Stripe."
            : "Paid checkout is still gated by Stripe price/webhook and key delivery readiness.",
          paidReady ? "primary" : "limited",
        ),
      ].join("");
    }

    renderList(missingKeys, status.missing_environment_keys, "No missing environment keys reported.");
    renderList(operatorActions, status.operator_next_actions, "No operator actions reported.");
  }

  function cardHtml(label, title, body, tone) {
    return `
      <article>
        <span class="status-tag status-tag--${tone}">${escapeHtml(label)}</span>
        <h3>${escapeHtml(title)}</h3>
        <p>${escapeHtml(body)}</p>
      </article>
    `;
  }

  function renderList(element, values, emptyText) {
    if (!element) return;
    const items = Array.isArray(values) ? values.filter(Boolean) : [];
    element.innerHTML =
      items.length > 0
        ? items.map((item) => `<li><code>${escapeHtml(String(item))}</code></li>`).join("")
        : `<li>${escapeHtml(emptyText)}</li>`;
  }

  function setText(element, text) {
    if (element) element.textContent = text;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
})();
