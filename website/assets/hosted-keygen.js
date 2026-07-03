(() => {
  const form = document.getElementById("hostedKeyForm");
  const result = document.getElementById("hostedKeyResult");

  if (!form || !result) {
    return;
  }

  const renderResult = (message, state = "") => {
    result.dataset.state = state;
    result.textContent = message;
  };

  const formPayload = () => {
    const data = new FormData(form);
    return {
      name: String(data.get("name") || "").trim(),
      email: String(data.get("email") || "").trim(),
      key_name: String(data.get("key_name") || "").trim() || "Hosted beta key",
    };
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector('button[type="submit"]');
    const payload = formPayload();

    if (!payload.name) {
      renderResult("Enter your name first.", "error");
      return;
    }
    if (!payload.email) {
      renderResult("Enter your email first.", "error");
      return;
    }

    submit.disabled = true;
    submit.textContent = "Registering...";
    renderResult("Creating your hosted beta key and sending email...", "running");

    try {
      const response = await fetch("/v1/hosted/beta-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail || `Scout returned HTTP ${response.status}`);
      }

      renderResult(
        [
          `Check your email, ${body.name || payload.name}.`,
          "",
          `Scout sent your hosted beta API key to ${body.email}.`,
          `Plan: ${body.plan}`,
          `Standard credits: ${body.standard_credits_remaining}`,
          `Browser credits: ${body.browser_credits_remaining}`,
          `Delivery: ${body.delivery_status}`,
          "",
          body.warning || "Scout emailed the key and stores only its hash.",
        ].join("\n"),
        "success",
      );
      form.reset();
    } catch (error) {
      renderResult(error instanceof Error ? error.message : String(error), "error");
    } finally {
      submit.disabled = false;
      submit.textContent = "Generate API key";
    }
  });
})();
