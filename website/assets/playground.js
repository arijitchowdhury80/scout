(() => {
  const form = document.getElementById("playgroundForm");
  const statusEl = document.getElementById("playgroundStatus");
  const resultsEl = document.getElementById("playgroundResults");
  const jsonButton = document.getElementById("playgroundDownloadJson");
  const markdownButton = document.getElementById("playgroundDownloadMarkdown");

  if (!form || !statusEl || !resultsEl || !jsonButton || !markdownButton) {
    return;
  }

  let latestDownloads = null;
  let latestFilenames = null;

  const setStatus = (message, state = "") => {
    statusEl.textContent = message;
    statusEl.dataset.state = state;
  };

  const setDownloadsEnabled = (enabled) => {
    jsonButton.disabled = !enabled;
    markdownButton.disabled = !enabled;
  };

  const renderPreview = (payload) => {
    const selectedFormat = payload.output_format;
    const body =
      selectedFormat === "markdown"
        ? payload.downloads.markdown
        : JSON.stringify(
            {
              workflow: payload.workflow,
              url: payload.url,
              limits: payload.limits,
              summary: payload.summary,
              records: payload.records,
              blocked_pages: payload.blocked_pages,
            },
            null,
            2,
          );
    resultsEl.textContent = body || "Scout returned no previewable content.";
  };

  const download = (kind) => {
    if (!latestDownloads || !latestFilenames) {
      return;
    }
    const content = latestDownloads[kind] || "";
    const filename = latestFilenames[kind] || `scout-playground.${kind === "json" ? "json" : "md"}`;
    const type = kind === "json" ? "application/json" : "text/markdown";
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector('button[type="submit"]');
    const data = new FormData(form);
    const workflow = String(data.get("workflow") || "products");
    const url = String(data.get("url") || "").trim();
    const outputFormat = String(data.get("output_format") || "json");

    latestDownloads = null;
    latestFilenames = null;
    setDownloadsEnabled(false);

    if (!url) {
      setStatus("Enter a public URL first.", "error");
      resultsEl.textContent = "The playground needs a public URL to run.";
      return;
    }

    submit.disabled = true;
    setStatus("Running hosted Scout demo...", "running");
    resultsEl.textContent = "Scout is acquiring the page and preparing a capped preview.";

    try {
      const response = await fetch("/v1/playground/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow,
          url,
          output_format: outputFormat,
          max_items: workflow === "products" ? 10 : 5,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || payload.error || `Scout returned HTTP ${response.status}`);
      }

      latestDownloads = payload.downloads;
      latestFilenames = payload.download_filenames;
      renderPreview(payload);
      setDownloadsEnabled(true);
      const count = payload.summary.record_count || payload.summary.page_count || 0;
      const blocked = payload.summary.blocked_count || 0;
      setStatus(`Complete: ${count} item(s), ${blocked} blocked page(s).`, "success");
    } catch (error) {
      setStatus("Playground run failed.", "error");
      resultsEl.textContent = error instanceof Error ? error.message : String(error);
    } finally {
      submit.disabled = false;
    }
  });

  jsonButton.addEventListener("click", () => download("json"));
  markdownButton.addEventListener("click", () => download("markdown"));
})();
