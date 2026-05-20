"""Static Scout frontend shell."""

from __future__ import annotations


def scout_app_html() -> str:
    """Return the self-educating Scout frontend HTML."""
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Scout Intelligence Platform</title>
    <style>
      :root {
        color-scheme: light;
        --ink: #17201b;
        --muted: #5d6961;
        --line: #d8ded9;
        --surface: #f8faf8;
        --panel: #ffffff;
        --accent: #0f766e;
        --accent-2: #364fc7;
        --warn: #a16207;
        --bad: #b42318;
        --good: #047857;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: var(--ink);
        background: var(--surface);
      }
      header {
        display: flex;
        justify-content: space-between;
        gap: 24px;
        align-items: center;
        padding: 18px 28px;
        border-bottom: 1px solid var(--line);
        background: var(--panel);
        position: sticky;
        top: 0;
        z-index: 2;
      }
      h1, h2, h3 { margin: 0; letter-spacing: 0; }
      h1 { font-size: 24px; }
      h2 { font-size: 18px; margin-bottom: 12px; }
      h3 { font-size: 15px; margin-bottom: 8px; }
      p { color: var(--muted); line-height: 1.5; }
      main { display: grid; grid-template-columns: 280px 1fr; min-height: calc(100vh - 70px); }
      nav {
        padding: 20px;
        border-right: 1px solid var(--line);
        background: #eef4f1;
      }
      nav button, .mode-tab, .primary, .secondary {
        border: 1px solid var(--line);
        background: var(--panel);
        color: var(--ink);
        border-radius: 8px;
        cursor: pointer;
      }
      nav button {
        display: block;
        width: 100%;
        text-align: left;
        padding: 12px;
        margin-bottom: 8px;
        font-weight: 650;
      }
      nav button.active { border-color: var(--accent); color: var(--accent); }
      section { display: none; padding: 24px; }
      section.active { display: block; }
      .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
      .panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 16px;
      }
      .mode-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
      .mode-tab { padding: 9px 12px; }
      .mode-tab.active { background: var(--accent); color: white; border-color: var(--accent); }
      label { display: block; font-size: 13px; font-weight: 700; margin: 12px 0 5px; }
      input, select, textarea {
        width: 100%;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 10px;
        font: inherit;
        background: #fff;
      }
      textarea { min-height: 86px; resize: vertical; }
      code, pre {
        background: #eef2f7;
        border-radius: 8px;
        font-family: "SFMono-Regular", Consolas, monospace;
      }
      pre { padding: 12px; overflow: auto; max-height: 340px; }
      .primary { background: var(--accent); color: white; border-color: var(--accent); padding: 10px 14px; font-weight: 750; }
      .secondary { padding: 10px 14px; font-weight: 700; }
      .status { display: inline-block; padding: 4px 8px; border-radius: 999px; background: #e5f4ef; color: var(--good); font-size: 12px; font-weight: 750; }
      .warn { background: #fef3c7; color: var(--warn); }
      .bad { background: #fee4e2; color: var(--bad); }
      table { width: 100%; border-collapse: collapse; font-size: 13px; }
      th, td { border-bottom: 1px solid var(--line); padding: 9px; text-align: left; vertical-align: top; }
      .diagram { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; align-items: center; }
      .diagram div { padding: 12px; background: #f6f8fb; border: 1px solid var(--line); border-radius: 8px; text-align: center; font-weight: 750; }
      .diagram span { color: var(--accent-2); font-weight: 900; text-align: center; }
      .architecture-wrap { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 16px; align-items: start; }
      .architecture-canvas {
        overflow-x: auto;
        background: #fbfdfc;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 18px;
      }
      .architecture-flow {
        min-width: 1180px;
        display: grid;
        grid-template-columns: 140px 32px 150px 32px 160px 32px 190px 32px 190px 32px 190px 32px 150px 32px 160px;
        gap: 14px;
        align-items: center;
      }
      .arch-column-title {
        color: #1d4ed8;
        font-size: 12px;
        font-weight: 850;
        min-height: 34px;
        text-transform: uppercase;
      }
      .arch-column-title:nth-child(1) { grid-column: 1; grid-row: 1; }
      .arch-column-title:nth-child(2) { grid-column: 3; grid-row: 1; }
      .arch-column-title:nth-child(3) { grid-column: 5; grid-row: 1; }
      .arch-column-title:nth-child(4) { grid-column: 7; grid-row: 1; }
      .arch-column-title:nth-child(5) { grid-column: 9; grid-row: 1; }
      .arch-column-title:nth-child(6) { grid-column: 11; grid-row: 1; }
      .arch-column-title:nth-child(7) { grid-column: 13; grid-row: 1; }
      .arch-column-title:nth-child(8) { grid-column: 15; grid-row: 1; }
      .architecture-flow > :nth-child(9) { grid-column: 1; grid-row: 2; }
      .architecture-flow > :nth-child(10) { grid-column: 2; grid-row: 2; }
      .architecture-flow > :nth-child(11) { grid-column: 3; grid-row: 2; }
      .architecture-flow > :nth-child(12) { grid-column: 4; grid-row: 2; }
      .architecture-flow > :nth-child(13) { grid-column: 5; grid-row: 2; }
      .architecture-flow > :nth-child(14) { grid-column: 6; grid-row: 2; }
      .architecture-flow > :nth-child(15) { grid-column: 7; grid-row: 2; }
      .architecture-flow > :nth-child(16) { grid-column: 8; grid-row: 2; }
      .architecture-flow > :nth-child(17) { grid-column: 9; grid-row: 2; }
      .architecture-flow > :nth-child(18) { grid-column: 10; grid-row: 2; }
      .architecture-flow > :nth-child(19) { grid-column: 11; grid-row: 2; }
      .architecture-flow > :nth-child(20) { grid-column: 12; grid-row: 2; }
      .architecture-flow > :nth-child(21) { grid-column: 13; grid-row: 2; }
      .architecture-flow > :nth-child(22) { grid-column: 14; grid-row: 2; }
      .architecture-flow > :nth-child(23) { grid-column: 15; grid-row: 2; }
      .arch-column-title.green { color: #166534; }
      .arch-stack { display: grid; gap: 10px; }
      .arch-card, .arch-node {
        border: 1px solid #8fb3ff;
        background: #f8fbff;
        border-radius: 8px;
        padding: 12px;
        min-height: 74px;
        box-shadow: 0 8px 20px rgba(29, 78, 216, 0.05);
      }
      .arch-node {
        width: 100%;
        color: var(--ink);
        cursor: pointer;
        text-align: left;
        font: inherit;
      }
      .arch-node strong, .arch-card strong { display: block; font-size: 14px; margin-bottom: 4px; }
      .arch-node small, .arch-card small { color: var(--muted); display: block; line-height: 1.35; }
      .arch-node:hover, .arch-node.active { border-color: var(--accent-2); outline: 2px solid rgba(54, 79, 199, 0.12); }
      .arch-green {
        border-color: #9fce9f;
        background: #f5fbf4;
        box-shadow: 0 8px 20px rgba(22, 101, 52, 0.05);
      }
      .arch-dashed { border-style: dashed; background: #fbfbfb; }
      .arch-arrow { color: #2563eb; font-weight: 900; text-align: center; }
      .arch-evidence ul, .arch-card ul {
        margin: 8px 0 0;
        padding-left: 18px;
        color: var(--muted);
        line-height: 1.55;
      }
      .arch-concerns {
        min-width: 1180px;
        display: grid;
        grid-template-columns: repeat(7, minmax(130px, 1fr));
        gap: 10px;
        margin-top: 16px;
        padding: 12px;
        border: 1px dashed #7ea6ff;
        border-radius: 8px;
        background: #f8fbff;
      }
      .concern { font-size: 12px; font-weight: 800; color: #1e3a8a; }
      .detail-panel { position: sticky; top: 96px; }
      .detail-panel code { display: block; padding: 10px; white-space: pre-wrap; }
      @media (max-width: 860px) {
        main { grid-template-columns: 1fr; }
        nav { border-right: 0; border-bottom: 1px solid var(--line); }
        .grid { grid-template-columns: 1fr; }
        .architecture-wrap { grid-template-columns: 1fr; }
        .detail-panel { position: static; }
        header { align-items: flex-start; flex-direction: column; }
      }
    </style>
  </head>
  <body>
    <header>
      <div>
        <h1>Scout Intelligence Platform</h1>
        <p>Web evidence to cited records for PRISM, products, jobs, company intel, and research.</p>
      </div>
      <span class="status">Local app</span>
    </header>
    <main>
      <nav aria-label="Scout screens">
        <button class="active" data-screen="how">How to use me</button>
        <button data-screen="run">Run Console</button>
        <button data-screen="products">Product Workbench</button>
        <button data-screen="monitor">Run Monitor</button>
        <button data-screen="evidence">Evidence Browser</button>
        <button data-screen="records">Records Explorer</button>
        <button data-screen="settings">Settings</button>
      </nav>
      <div>
        <section id="how" class="active">
          <div hidden>
            <button data-mode="auto">auto</button>
            <button data-mode="crawl4ai">crawl4ai</button>
            <button data-mode="webfetch">webfetch</button>
            <button data-mode="websearch">websearch</button>
            <button data-mode="browser">browser</button>
            <button data-mode="saved">saved</button>
            <button data-mode="api">api</button>
          </div>
          <h2>How to use me</h2>
          <p>Scout turns web evidence into cited records through a provider ladder, vertical processors, and one durable artifact contract.</p>
          <div class="architecture-wrap">
            <div class="architecture-canvas" aria-label="Scout architecture canvas">
              <div class="architecture-flow">
                <div class="arch-column-title">Front Doors<br />(Entry Points)</div>
                <div class="arch-column-title">RunRequest</div>
                <div class="arch-column-title">Orchestration</div>
                <div class="arch-column-title">Provider Modes<br />(Ordered by Preference)</div>
                <div class="arch-column-title green">Normalization</div>
                <div class="arch-column-title green">Vertical Processors</div>
                <div class="arch-column-title green">Typed Records</div>
                <div class="arch-column-title">Downstream Consumers</div>

                <div class="arch-stack">
                  <button class="arch-node" type="button" data-arch-title="CLI" data-arch-body="Terminal entry point for local runs, scripts, scheduled jobs, and power users." data-arch-example="scout run prism --query Nike --mode auto --workdir scout-runs"><strong>CLI</strong><small>scout run ...</small></button>
                  <button class="arch-node" type="button" data-arch-title="HTTP App" data-arch-body="Local REST API and self-educating frontend. Good for agents, browser workflows, and integrations." data-arch-example="POST /run/company"><strong>HTTP App</strong><small>REST API + /app</small></button>
                  <button class="arch-node" type="button" data-arch-title="Claude / Codex Skill" data-arch-body="Skill-hosted entry point that can use Scout plus host tools such as WebFetch, WebSearch, and browser evidence when available." data-arch-example="Use Scout to research Adobe"><strong>Claude / Codex Skill</strong><small>Skill / MCP</small></button>
                </div>
                <div class="arch-arrow">-&gt;</div>
                <button class="arch-node" type="button" data-arch-title="RunRequest" data-arch-body="The common request contract. It carries use case, query, targets, limits, execution mode, output directory, and optional profile/job/product inputs." data-arch-example='{"query":"Adobe","mode":"auto","output_dir":"scout-runs/adobe"}'><strong>RunRequest</strong><small>target / scope<br />constraints<br />modes / prefs<br />metadata</small></button>
                <div class="arch-arrow">-&gt;</div>
                <button class="arch-node" type="button" data-arch-title="Execution Mode Router" data-arch-body="Selects and orders providers based on mode, configuration, availability, and success heuristics. Browser fallback remains secondary." data-arch-example="auto: crawl4ai -> api -> saved -> webfetch -> websearch -> browser"><strong>Execution Mode Router</strong><small>Selects provider ladder</small></button>
                <div class="arch-arrow">-&gt;</div>
                <div class="arch-stack">
                  <button class="arch-node" type="button" data-arch-title="crawl4ai" data-arch-body="Default standalone acquisition provider for normal pages, maps, crawls, screenshots, and JS rendering." data-arch-example="scout run company --query Adobe --mode crawl4ai"><strong>crawl4ai</strong><small>Default</small></button>
                  <button class="arch-node" type="button" data-arch-title="webfetch" data-arch-body="Host-provided page fetch evidence used when the skill environment can retrieve content better than local crawling." data-arch-example="mode=webfetch"><strong>webfetch</strong><small>host page evidence</small></button>
                  <button class="arch-node" type="button" data-arch-title="websearch" data-arch-body="Host-provided discovery for finding official pages, news, blogs, investor pages, and candidate URLs." data-arch-example="mode=websearch"><strong>websearch</strong><small>discovery</small></button>
                  <button class="arch-node arch-dashed" type="button" data-arch-title="browser fallback" data-arch-body="Secondary fallback for blocked pages, JS shells, visual verification, and browser/session evidence. Not a universal bypass." data-arch-example="mode=browser"><strong>browser fallback</strong><small>Secondary / Not Default</small></button>
                  <button class="arch-node" type="button" data-arch-title="saved replay" data-arch-body="Deterministic replay of saved HTML, DOM snapshots, PDFs, and fixtures for tests or repeatable extraction." data-arch-example="mode=saved"><strong>saved replay</strong><small>fixtures and snapshots</small></button>
                  <button class="arch-node" type="button" data-arch-title="api adapters" data-arch-body="Provider APIs such as ATS boards, commerce feeds, investor feeds, and future social providers." data-arch-example="mode=api"><strong>api adapters</strong><small>provider APIs</small></button>
                </div>
                <div class="arch-arrow">-&gt;</div>
                <button class="arch-node arch-green arch-evidence" type="button" data-arch-title="Normalized Source Evidence" data-arch-body="Every provider result becomes a normalized source page with provenance, status, hashes, links, content, and citation identity." data-arch-example="source_pages.json + citations[]"><strong>Normalized Source Evidence</strong><small>with Provenance</small><ul><li>content</li><li>metadata</li><li>links</li><li>status</li><li>fingerprints</li></ul></button>
                <div class="arch-arrow">-&gt;</div>
                <div class="arch-stack">
                  <button class="arch-node arch-green" type="button" data-arch-title="Vertical Processors" data-arch-body="Domain-specific extractors convert normalized evidence into useful records for each Scout use case." data-arch-example="company, PRISM, investor, careers, jobs, products, news, research"><strong>Vertical Processors</strong><small>domain extraction</small></button>
                  <div class="arch-card arch-green"><strong>company</strong><small>overview, leaders, socials</small></div>
                  <div class="arch-card arch-green"><strong>PRISM</strong><small>prospect bundle</small></div>
                  <div class="arch-card arch-green"><strong>investor</strong><small>IR, filings, decks</small></div>
                  <div class="arch-card arch-green"><strong>careers</strong><small>ATS and hiring signals</small></div>
                  <div class="arch-card arch-green"><strong>jobs</strong><small>job matching</small></div>
                  <div class="arch-card arch-green"><strong>products</strong><small>catalog records</small></div>
                  <div class="arch-card arch-green"><strong>news</strong><small>blogs and signals</small></div>
                  <div class="arch-card arch-green"><strong>research</strong><small>generic evidence</small></div>
                </div>
                <div class="arch-arrow">-&gt;</div>
                <button class="arch-node arch-green" type="button" data-arch-title="Typed Records" data-arch-body="Validated, deduplicated, normalized structured records with schemas, stable objectIDs, citations, and confidence." data-arch-example="records.json / records.jsonl"><strong>Typed Records</strong><small>schema-backed data<br />citations included</small></button>
                <div class="arch-arrow">-&gt;</div>
                <div class="arch-stack">
                  <button class="arch-node" type="button" data-arch-title="Downstream Consumers" data-arch-body="Consumers use Scout records for Algolia indexing, PRISM signals, monitoring, reports, and agent workflows." data-arch-example="Algolia, PRISM, job monitor, reports, agents"><strong>Downstream Consumers</strong><small>where records go</small></button>
                  <div class="arch-card"><strong>ALGOLIA</strong><small>Search &amp; Index</small></div>
                  <div class="arch-card"><strong>PRISM</strong><small>Signals &amp; Insights</small></div>
                  <div class="arch-card"><strong>JOB MONITOR</strong><small>Tracking &amp; Alerts</small></div>
                  <div class="arch-card"><strong>REPORTS</strong><small>Dashboards &amp; reports</small></div>
                  <div class="arch-card"><strong>AGENTS</strong><small>Automation workflows</small></div>
                </div>
              </div>
              <div class="arch-concerns" aria-label="Cross-cutting concerns">
                <div class="concern">Security & Secrets</div>
                <div class="concern">Rate Limiting & Throttling</div>
                <div class="concern">Logging & Observability</div>
                <div class="concern">Retry & Backoff</div>
                <div class="concern">Metrics & Monitoring</div>
                <div class="concern">Storage & Artifacts</div>
                <div class="concern">Configuration & Feature Flags</div>
              </div>
            </div>
            <aside class="panel detail-panel" aria-live="polite">
              <h2 id="architectureDetailTitle">Normalized Source Evidence</h2>
              <p id="architectureDetailBody">Every provider result becomes citation-ready source evidence before a vertical processor creates records.</p>
              <h3>Example</h3>
              <code id="architectureDetailExample">source_pages.json + citations[]</code>
              <h3>Artifact lifecycle</h3>
              <pre>manifest.json
records.json
records.jsonl
source_pages.json
blocked_pages.json
validation.json
extraction_report.md</pre>
            </aside>
          </div>
        </section>

        <section id="run">
          <h2>Run Console</h2>
          <div class="mode-tabs" id="modeTabs"></div>
          <div class="grid">
            <div class="panel">
              <label for="apiKey">Scout API key</label>
              <input id="apiKey" type="password" value="dev-key" autocomplete="off" />
              <label for="useCase">Use case</label>
              <select id="useCase">
                <option>company</option><option>prism</option><option>investor</option>
                <option>careers</option><option>jobs</option><option>products</option>
                <option>news</option><option>research</option><option>docs</option>
                <option>website-quality</option><option>social</option><option>locations</option>
              </select>
              <label for="query">Query</label>
              <input id="query" value="Adobe" />
              <label for="workdir">Working directory</label>
              <input id="workdir" value="scout-runs" />
              <button class="secondary" id="pickDir" type="button">Choose folder</button>
              <button class="primary" id="runScout" type="button">Run Scout</button>
            </div>
            <div class="panel">
              <h3>Generated command</h3>
              <pre id="commandPreview"></pre>
              <h3>HTTP request</h3>
              <pre id="httpPreview"></pre>
              <h3>Latest response</h3>
              <pre id="runOutput">{}</pre>
            </div>
          </div>
        </section>

        <section id="products">
          <h2>Product Workbench</h2>
          <div class="grid">
            <div class="panel">
              <label for="productSite">Website/domain</label>
              <input id="productSite" value="esteelauder.com" />
              <label for="productQuery">Product query</label>
              <input id="productQuery" value="top skincare products" />
              <label for="startUrl">Start URL</label>
              <input id="startUrl" placeholder="https://www.esteelauder.com/products/681/product-catalog/skin-care" />
              <label for="categoryLimit">Categories</label>
              <input id="categoryLimit" type="number" value="3" min="1" />
              <label for="productLimit">Max products</label>
              <input id="productLimit" type="number" value="10" min="1" />
              <button class="primary" id="runProducts" type="button">Scrape products</button>
            </div>
            <div class="panel">
              <h3>Algolia Preparation</h3>
              <label for="algoliaApp">Algolia App ID</label>
              <input id="algoliaApp" autocomplete="off" />
              <label for="algoliaKey">Algolia API key</label>
              <input id="algoliaKey" type="password" autocomplete="off" />
              <label for="algoliaIndex">Index name</label>
              <input id="algoliaIndex" value="products_dev" />
              <button class="secondary" id="previewAlgolia" type="button">Preview Algolia readiness</button>
              <button class="secondary" type="button" disabled>Ingest to Algolia - future extension</button>
              <pre id="algoliaPreview">{}</pre>
            </div>
          </div>
          <div class="panel" style="margin-top:16px;">
            <h3>Record preview</h3>
            <div id="productSummary"><span class="status warn">No product run yet</span></div>
            <table id="productTable"><thead><tr><th>Name</th><th>Brand</th><th>Price</th><th>Completeness</th><th>Source</th></tr></thead><tbody></tbody></table>
            <pre id="productJson">[]</pre>
          </div>
        </section>

        <section id="monitor"><h2>Run Monitor</h2><div class="panel"><pre id="monitorOutput">Run a workflow to see provider attempts, warnings, blocked pages, and artifact paths.</pre></div></section>
        <section id="evidence"><h2>Evidence Browser</h2><div class="panel"><pre id="sourceOutput">Run a workflow, then load source pages and citations here.</pre></div></section>
        <section id="records"><h2>Records Explorer</h2><div class="panel"><pre id="recordsOutput">Records will appear here after a run.</pre></div></section>
        <section id="settings"><h2>Settings</h2><div class="panel"><p>Keys live in <code>.env.local</code>. Secret values are never shown here.</p><pre>SCOUT_WORKDIR=scout-runs
SCOUT_API_KEY=configured/not shown
LLM_API_KEY=configured/not shown</pre></div></section>
      </div>
    </main>
    <script>
      const modes = ["auto", "crawl4ai", "webfetch", "websearch", "browser", "saved", "api"];
      let selectedMode = "auto";
      let latestRecords = [];
      const $ = (id) => document.getElementById(id);

      document.querySelectorAll("nav button").forEach((button) => {
        button.addEventListener("click", () => {
          document.querySelectorAll("nav button").forEach((b) => b.classList.remove("active"));
          document.querySelectorAll("section").forEach((s) => s.classList.remove("active"));
          button.classList.add("active");
          $(button.dataset.screen).classList.add("active");
        });
      });

      document.querySelectorAll(".arch-node").forEach((node) => {
        node.addEventListener("click", () => {
          document.querySelectorAll(".arch-node").forEach((item) => item.classList.remove("active"));
          node.classList.add("active");
          $("architectureDetailTitle").textContent = node.dataset.archTitle || "Scout architecture";
          $("architectureDetailBody").textContent = node.dataset.archBody || "";
          $("architectureDetailExample").textContent = node.dataset.archExample || "";
        });
      });

      modes.forEach((mode) => {
        const button = document.createElement("button");
        button.className = "mode-tab" + (mode === selectedMode ? " active" : "");
        button.dataset.mode = mode;
        button.textContent = mode;
        button.addEventListener("click", () => {
          selectedMode = mode;
          document.querySelectorAll(".mode-tab").forEach((b) => b.classList.remove("active"));
          button.classList.add("active");
          updatePreviews();
        });
        $("modeTabs").appendChild(button);
      });

      ["useCase", "query", "workdir"].forEach((id) => $(id).addEventListener("input", updatePreviews));

      $("pickDir").addEventListener("click", async () => {
        if ("showDirectoryPicker" in window) {
          const dir = await window.showDirectoryPicker();
          $("workdir").value = dir.name;
        } else {
          $("workdir").focus();
        }
        updatePreviews();
      });

      $("runScout").addEventListener("click", async () => {
        const useCase = $("useCase").value;
        const body = { query: $("query").value, mode: selectedMode, output_dir: "", targets: [], max_records: 250 };
        const res = await fetch(`/run/${useCase}`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": $("apiKey").value },
          body: JSON.stringify({ ...body, output_dir: `${$("workdir").value}/${useCase}-${Date.now()}` })
        });
        const data = await res.json();
        $("runOutput").textContent = JSON.stringify(data, null, 2);
        $("monitorOutput").textContent = JSON.stringify(data.manifest || data, null, 2);
        if (data.manifest && data.manifest.run_id) {
          await loadArtifacts(data.manifest.run_id);
        }
      });

      $("runProducts").addEventListener("click", async () => {
        const res = await fetch("/products", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": $("apiKey").value },
          body: JSON.stringify({
            query: $("productQuery").value,
            site: $("productSite").value,
            start_url: $("startUrl").value,
            max_categories: Number($("categoryLimit").value),
            max_products: Number($("productLimit").value),
            persist: true,
            output_dir: `${$("workdir").value}/products-${Date.now()}`
          })
        });
        const data = await res.json();
        latestRecords = data.records || [];
        renderProducts(data);
      });

      $("previewAlgolia").addEventListener("click", async () => {
        const res = await fetch("/algolia/preview", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": $("apiKey").value },
          body: JSON.stringify({
            app_id: $("algoliaApp").value,
            api_key: $("algoliaKey").value,
            index_name: $("algoliaIndex").value,
            records: latestRecords
          })
        });
        $("algoliaPreview").textContent = JSON.stringify(await res.json(), null, 2);
      });

      async function loadArtifacts(runId) {
        const headers = { "X-API-Key": $("apiKey").value };
        const [records, sources] = await Promise.all([
          fetch(`/runs/${runId}/records`, { headers }).then((r) => r.json()),
          fetch(`/runs/${runId}/sources`, { headers }).then((r) => r.json())
        ]);
        $("recordsOutput").textContent = JSON.stringify(records, null, 2);
        $("sourceOutput").textContent = JSON.stringify(sources, null, 2);
      }

      function renderProducts(data) {
        $("productSummary").innerHTML = `<span class="status">${data.total_records || 0} records</span> <span class="status ${data.total_blocked_pages ? "bad" : ""}">${data.total_blocked_pages || 0} blocked</span>`;
        const tbody = $("productTable").querySelector("tbody");
        tbody.innerHTML = "";
        latestRecords.forEach((record) => {
          const source = record._source || record.source || {};
          const row = document.createElement("tr");
          row.innerHTML = `<td>${escapeHtml(record.name || "")}</td><td>${escapeHtml(record.brand || "")}</td><td>${record.price ?? ""}</td><td>${record.completeness_score ?? ""}</td><td>${escapeHtml(source.extractor || "")}</td>`;
          tbody.appendChild(row);
        });
        $("productJson").textContent = JSON.stringify(latestRecords, null, 2);
      }

      function updatePreviews() {
        const useCase = $("useCase").value;
        const query = $("query").value;
        const workdir = $("workdir").value;
        $("commandPreview").textContent = `scout run ${useCase} --query "${query}" --mode ${selectedMode} --workdir ${workdir}`;
        $("httpPreview").textContent = `POST /run/${useCase}\\n{\\n  "query": "${query}",\\n  "mode": "${selectedMode}",\\n  "output_dir": "${workdir}/${useCase}-<timestamp>"\\n}`;
      }

      function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[ch]));
      }

      updatePreviews();
    </script>
  </body>
</html>"""
