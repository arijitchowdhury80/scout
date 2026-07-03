(() => {
  const form = document.getElementById("hostedKeyForm");
  const result = document.getElementById("hostedKeyResult");
  const copyButton = document.getElementById("copyHostedKey");

  if (!form || !result || !copyButton) {
    return;
  }

  let latestKey = "";

  const renderResult = (message, state = "") => {
    result.dataset.state = state;
    result.textContent = message;
  };

  const setCopyEnabled = (enabled) => {
    copyButton.disabled = !enabled;
  };

  const formPayload = () => {
    const data = new FormData(form);
    return {
      email: String(data.get("email") || "").trim(),
      key_name: String(data.get("key_name") || "").trim() || "Hosted beta key",
    };
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector('button[type="submit"]');
    const payload = formPayload();

    latestKey = "";
    setCopyEnabled(false);

    if (!payload.email) {
      renderResult("Enter your email first.", "error");
      return;
    }

    submit.disabled = true;
    submit.textContent = "Generating...";
    renderResult("Creating hosted beta key...", "running");

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

      latestKey = body.raw_api_key || "";
      renderResult(
        [
          `API key: ${latestKey}`,
          "",
          `Plan: ${body.plan}`,
          `Standard credits: ${body.standard_credits_remaining}`,
          `Browser credits: ${body.browser_credits_remaining}`,
          "",
          body.warning || "Copy this key now. It is shown once.",
        ].join("\n"),
        "success",
      );
      setCopyEnabled(Boolean(latestKey));
      form.reset();
    } catch (error) {
      renderResult(error instanceof Error ? error.message : String(error), "error");
    } finally {
      submit.disabled = false;
      submit.textContent = "Generate API key";
    }
  });

  copyButton.addEventListener("click", async () => {
    if (!latestKey) {
      return;
    }
    try {
      await navigator.clipboard.writeText(latestKey);
      copyButton.textContent = "Copied";
      window.setTimeout(() => {
        copyButton.textContent = "Copy key";
      }, 1600);
    } catch (_error) {
      renderResult("Copy failed. Select and copy the key manually.", "error");
    }
  });
})();
