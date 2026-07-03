(() => {
  const CAPABILITIES = {
    scrape: {
      label: "Scrape",
      help: "Fetch one page and return clean markdown plus evidence metadata.",
      maxItems: 1,
      placeholder: "https://example.com",
    },
    crawl: {
      label: "Crawl",
      help: "Crawl one public site level and return up to five pages.",
      maxItems: 5,
      placeholder: "https://example.com",
    },
    map: {
      label: "Map",
      help: "Discover public site URLs without extracting every page body.",
      maxItems: 5,
      placeholder: "https://example.com",
    },
    screenshot: {
      label: "Screenshot",
      help: "Capture one rendered page screenshot and basic evidence metadata.",
      maxItems: 1,
      placeholder: "https://example.com",
    },
    products: {
      label: "Products",
      help: "Extract up to ten product records with source citations when available.",
      maxItems: 10,
      placeholder: "https://www.example.com/category",
    },
    company: {
      label: "Company intelligence",
      help: "Build company overview, about, leadership, social, and URL evidence records.",
      maxItems: 10,
      placeholder: "https://www.algolia.com",
    },
    investor: {
      label: "Investor intelligence",
      help: "Find investor pages, reports, presentations, filings, and events where public.",
      maxItems: 10,
      placeholder: "https://www.adobe.com/investor-relations.html",
    },
    careers: {
      label: "Careers and hiring",
      help: "Find career pages, ATS hints, departments, and hiring signals.",
      maxItems: 10,
      placeholder: "https://www.adobe.com/careers.html",
    },
    news: {
      label: "News and blogs",
      help: "Extract recent newsroom or blog entries with dates and source URLs when visible.",
      maxItems: 10,
      placeholder: "https://www.algolia.com/blog",
    },
    social: {
      label: "Social profiles",
      help: "Normalize public social profile links discovered from the target site.",
      maxItems: 10,
      placeholder: "https://www.nike.com",
    },
    locations: {
      label: "Locations",
      help: "Extract store, office, or location page signals when public pages expose them.",
      maxItems: 10,
      placeholder: "https://www.homedepot.com",
    },
  };

  const form = document.getElementById("playgroundForm");
  const workflowEl = document.getElementById("playgroundWorkflow");
  const urlEl = document.getElementById("playgroundUrl");
  const queryEl = document.getElementById("playgroundQuery");
  const outputFormatEl = document.getElementById("playgroundOutputFormat");
  const helpEl = document.getElementById("playgroundCapabilityHelp");
  const statusEl = document.getElementById("playgroundStatus");
  const jsonButton = document.getElementById("playgroundDownloadJson");
  const markdownButton = document.getElementById("playgroundDownloadMarkdown");
  const panels = Array.from(document.querySelectorAll("[data-playground-panel]"));
  const tabButtons = Array.from(document.querySelectorAll("[data-playground-tab]"));
  const previewEl = document.getElementById("playgroundResults");
  const jsonEl = document.getElementById("playgroundJson");
  const markdownEl = document.getElementById("playgroundMarkdown");
  const curlEl = document.getElementById("playgroundCurl");

  if (
    !form ||
    !workflowEl ||
    !urlEl ||
    !queryEl ||
    !outputFormatEl ||
    !helpEl ||
    !statusEl ||
    !jsonButton ||
    !markdownButton ||
    !previewEl ||
    !jsonEl ||
    !markdownEl ||
    !curlEl
  ) {
    return;
  }

  let latestDownloads = null;
  let latestFilenames = null;
  let latestPayload = null;
  let runningTimer = null;

  const activeCapability = () => CAPABILITIES[workflowEl.value] || CAPABILITIES.scrape;

  const normalizePublicUrl = (value) => {
    const trimmed = value.trim();
    if (!trimmed) {
      return "";
    }
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(trimmed)) {
      return trimmed;
    }
    return `https://${trimmed}`;
  };

  const setStatus = (message, state = "") => {
    statusEl.textContent = message;
    statusEl.dataset.state = state;
  };

  const setDownloadsEnabled = (enabled) => {
    jsonButton.disabled = !enabled;
    markdownButton.disabled = !enabled;
  };

  const setPanelText = (element, text) => {
    element.textContent = text || "";
  };

  const clearRunningTimer = () => {
    if (runningTimer) {
      window.clearInterval(runningTimer);
      runningTimer = null;
    }
  };

  const switchTab = (tabName) => {
    tabButtons.forEach((button) => {
      const isActive = button.dataset.playgroundTab === tabName;
      button.setAttribute("aria-selected", String(isActive));
    });
    panels.forEach((panel) => {
      panel.hidden = panel.dataset.playgroundPanel !== tabName;
    });
  };

  const buildPayload = () => {
    const capability = activeCapability();
    return {
      workflow: workflowEl.value,
      url: normalizePublicUrl(urlEl.value),
      query: queryEl.value.trim(),
      output_format: outputFormatEl.value,
      max_items: capability.maxItems,
    };
  };

  const buildCurl = (payload) => {
    const body = JSON.stringify(payload);
    return [
      'curl -X POST "https://scout.chowmes.com/v1/playground/run" \\',
      '  -H "Content-Type: application/json" \\',
      `  -d '${body}'`,
    ].join("\n");
  };

  const updateCapabilityCopy = () => {
    const capability = activeCapability();
    helpEl.textContent = capability.help;
    urlEl.placeholder = capability.placeholder;
    setPanelText(curlEl, buildCurl(buildPayload()));
  };

  const renderPreview = (payload) => {
    const records = Array.isArray(payload.records) ? payload.records : [];
    const blocked = Array.isArray(payload.blocked_pages) ? payload.blocked_pages : [];
    const summary = payload.summary || {};
    const lines = [
      `Capability: ${CAPABILITIES[payload.workflow]?.label || payload.workflow}`,
      `URL: ${payload.url}`,
      `Records: ${summary.record_count ?? records.length}`,
      `Blocked pages: ${summary.blocked_count ?? blocked.length}`,
      `Capped demo: ${summary.capped === false ? "no" : "yes"}`,
      "",
    ];

    if (records.length) {
      lines.push("Sample records:");
      records.slice(0, 5).forEach((record, index) => {
        const title = record.name || record.title || record.url || record.objectID || `Record ${index + 1}`;
        const source = record.source_url || record.url || record.website || "";
        lines.push(`${index + 1}. ${title}${source ? ` (${source})` : ""}`);
      });
    } else if (blocked.length) {
      lines.push("No records were returned, but blocked/fallback evidence was captured:");
      blocked.slice(0, 5).forEach((page, index) => {
        lines.push(`${index + 1}. ${page.url || "Unknown URL"} - ${page.reason || page.status || "blocked"}`);
      });
    } else {
      lines.push("Scout returned no records for this capped run.");
    }

    setPanelText(previewEl, lines.join("\n"));
  };

  const renderPayload = (payload) => {
    latestPayload = payload;
    latestDownloads = payload.downloads || {};
    latestFilenames = payload.download_filenames || {};
    renderPreview(payload);
    setPanelText(jsonEl, latestDownloads.json || JSON.stringify(payload, null, 2));
    setPanelText(markdownEl, latestDownloads.markdown || "No Markdown returned.");
    setPanelText(curlEl, buildCurl(buildPayload()));
    setDownloadsEnabled(Boolean(latestDownloads.json || latestDownloads.markdown));
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
    const payload = buildPayload();

    latestPayload = null;
    latestDownloads = null;
    latestFilenames = null;
    setDownloadsEnabled(false);
    setPanelText(curlEl, buildCurl(payload));

    if (!payload.url) {
      setStatus("Enter a public URL first.", "error");
      setPanelText(previewEl, "The playground needs a public URL to run.");
      switchTab("preview");
      return;
    }

    submit.disabled = true;
    submit.textContent = "Running Scout...";
    statusEl.setAttribute("aria-busy", "true");
    const startedAt = Date.now();
    const capabilityLabel = activeCapability().label;
    const updateRunningCopy = () => {
      const elapsed = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
      setStatus(
        `Running ${capabilityLabel} demo for ${payload.url}. Elapsed ${elapsed}s. Still working...`,
        "running"
      );
      setPanelText(
        previewEl,
        [
          "Scout is acquiring evidence and preparing a capped preview.",
          "",
          `Capability: ${capabilityLabel}`,
          `Target: ${payload.url}`,
          `Elapsed: ${elapsed}s`,
          "",
          "Still working. Crawl, product, and intelligence demos can take 20-30 seconds on live websites.",
        ].join("\n")
      );
    };
    updateRunningCopy();
    runningTimer = window.setInterval(updateRunningCopy, 1000);
    switchTab(outputFormatEl.value === "markdown" ? "markdown" : "preview");

    try {
      const response = await fetch("/v1/playground/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const responsePayload = await response.json();
      if (!response.ok) {
        throw new Error(responsePayload.detail || responsePayload.error || `Scout returned HTTP ${response.status}`);
      }

      renderPayload(responsePayload);
      const count = responsePayload.summary?.record_count ?? responsePayload.records?.length ?? 0;
      const blocked = responsePayload.summary?.blocked_count ?? responsePayload.blocked_pages?.length ?? 0;
      setStatus(`Complete: ${count} record(s), ${blocked} blocked page(s).`, "success");
      switchTab(outputFormatEl.value === "markdown" ? "markdown" : "preview");
    } catch (error) {
      setStatus("Playground run failed.", "error");
      setPanelText(previewEl, error instanceof Error ? error.message : String(error));
      switchTab("preview");
    } finally {
      clearRunningTimer();
      submit.disabled = false;
      submit.textContent = "Run Scout Playground";
      statusEl.removeAttribute("aria-busy");
    }
  });

  workflowEl.addEventListener("change", updateCapabilityCopy);
  urlEl.addEventListener("input", () => setPanelText(curlEl, buildCurl(buildPayload())));
  queryEl.addEventListener("input", () => setPanelText(curlEl, buildCurl(buildPayload())));
  outputFormatEl.addEventListener("change", () => {
    setPanelText(curlEl, buildCurl(buildPayload()));
    if (latestPayload) {
      switchTab(outputFormatEl.value === "markdown" ? "markdown" : "preview");
    }
  });
  tabButtons.forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.playgroundTab || "preview"));
  });
  jsonButton.addEventListener("click", () => download("json"));
  markdownButton.addEventListener("click", () => download("markdown"));

  updateCapabilityCopy();
})();
