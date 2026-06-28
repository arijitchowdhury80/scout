"""Static Scout frontend shell."""

from __future__ import annotations


def scout_app_html() -> str:
    """Return the app-first Scout frontend HTML."""
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Scout Intelligence Platform</title>
    <style>
      :root {
        color-scheme: light;
        --ink: #132033;
        --muted: #637083;
        --line: #d7e0eb;
        --soft-line: #e8eef6;
        --bg: #f7fafc;
        --panel: #ffffff;
        --teal: #007f8c;
        --teal-dark: #00606a;
        --teal-soft: #e5f7f8;
        --blue: #2764ad;
        --green: #13845b;
        --green-soft: #e3f6ec;
        --red: #c23b32;
        --red-soft: #fde8e5;
        --amber: #ce6b09;
        --amber-soft: #fff2dc;
        --shadow: 0 18px 45px rgba(25, 43, 72, 0.08);
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        background: var(--bg);
        color: var(--ink);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 14px;
      }
      button, input, select, textarea { font: inherit; }
      button { cursor: pointer; }
      button:disabled { cursor: not-allowed; opacity: 0.62; }

      .topbar {
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 20px;
        border-bottom: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.94);
      }
      .brand { display: flex; align-items: center; gap: 10px; }
      .logo {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        display: grid;
        place-items: center;
        background: var(--teal);
        color: #fff;
        font-weight: 900;
        font-size: 20px;
      }
      .brand strong { display: block; font-size: 14px; letter-spacing: 0.04em; }
      .brand span { display: block; color: var(--muted); font-size: 10px; }
      .topnav { display: flex; align-items: center; gap: 26px; font-size: 12px; font-weight: 700; color: #40506a; }
      .topnav button, .topnav a {
        border: 0;
        background: transparent;
        color: inherit;
        font: inherit;
        text-decoration: none;
        padding: 20px 0 17px;
      }
      .topnav .active { color: var(--teal); border-bottom: 2px solid var(--teal); }
      .topnav button:disabled { cursor: not-allowed; opacity: 0.45; }
      .user-pill { display: flex; align-items: center; gap: 12px; }
      .avatar { width: 28px; height: 28px; border-radius: 50%; background: #d8e0eb; display: grid; place-items: center; font-weight: 800; }

      .app-shell {
        display: grid;
        /* "auto" lets the drawer column collapse to 0 while .drawer.closed is
           display:none, so the workspace gets the freed space. */
        grid-template-columns: 96px minmax(360px, 460px) minmax(0, 1fr) auto;
        height: calc(100vh - 56px);
        overflow: hidden;
      }
      .app-shell.utility-mode {
        grid-template-columns: 96px minmax(0, 1fr) auto;
      }
      .app-shell.utility-mode .setup-pane {
        display: none;
      }
      .app-shell.running-mode {
        grid-template-columns: 96px minmax(0, 1fr);
      }
      .app-shell.running-mode .setup-pane {
        display: none;
      }
      .app-shell.running-mode .drawer {
        display: none;
      }
      .rail {
        border-right: 1px solid var(--line);
        background: #fff;
        padding: 14px 8px;
      }
      .rail button {
        width: 78px;
        min-height: 48px;
        border: 0;
        border-radius: 8px;
        background: transparent;
        color: #52627a;
        font-size: 10px;
        font-weight: 750;
        margin-bottom: 7px;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .rail button.active { background: var(--teal-soft); color: var(--teal-dark); }
      .rail button:disabled {
        cursor: not-allowed;
        opacity: 0.45;
      }
      .rail span { display: block; font-size: 17px; margin-bottom: 3px; }

      .setup-pane, .workspace, .drawer {
        padding: 18px;
        overflow-y: auto;
        min-height: 0;
      }
      .rail { overflow-y: auto; }
      .setup-pane {
        border-right: 1px solid var(--line);
        background: #fff;
      }
      .workspace { min-width: 0; }
      .drawer {
        border-left: 1px solid var(--line);
        background: #fff;
        width: 360px;
      }
      .hidden { display: none !important; }

      .card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        box-shadow: var(--shadow);
      }
      .card-pad { padding: 18px; }
      .section-title {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 16px;
      }
      h1, h2, h3, p { margin: 0; letter-spacing: 0; }
      h1 { font-size: 17px; }
      h2 { font-size: 16px; }
      h3 { font-size: 11px; letter-spacing: 0.05em; text-transform: uppercase; color: #27364b; }
      p { color: var(--muted); line-height: 1.45; }
      .subtle { color: var(--muted); font-size: 12px; }

      label.label {
        display: block;
        margin: 16px 0 7px;
        color: #29384d;
        font-size: 11px;
        font-weight: 850;
        letter-spacing: 0.045em;
        text-transform: uppercase;
      }
      input, select {
        width: 100%;
        height: 38px;
        border: 1px solid var(--line);
        border-radius: 7px;
        background: #fff;
        color: var(--ink);
        padding: 0 10px;
        outline-color: var(--teal);
      }
      .input-row { display: flex; gap: 8px; align-items: center; }
      .mode-tabs, .tabs { display: flex; align-items: center; border: 1px solid var(--line); border-radius: 7px; overflow: hidden; background: #f8fbff; }
      .mode-tabs { align-items: stretch; flex-wrap: wrap; overflow: visible; }
      .mode-tabs button, .tabs button {
        border: 0;
        border-right: 1px solid var(--line);
        background: transparent;
        min-height: 38px;
        padding: 0 13px;
        color: #334158;
        font-size: 12px;
        font-weight: 750;
        white-space: nowrap;
      }
      .mode-tabs button { flex: 1 1 92px; border-bottom: 1px solid var(--line); }
      .mode-tabs button:last-child, .tabs button:last-child { border-right: 0; }
      .mode-tabs button.active, .tabs button.active { background: var(--teal); color: #fff; }

      .settings-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 8px 0; }
      .chip {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        min-height: 32px;
        border: 1px solid #bcd2ea;
        border-radius: 6px;
        background: #eef6ff;
        color: #1f4f86;
        padding: 0 9px;
        font-size: 12px;
        font-weight: 750;
      }
      .chip button { border: 0; background: transparent; color: inherit; padding: 0; font-weight: 900; }
      .secondary, .ghost, .danger, .primary {
        min-height: 38px;
        border-radius: 7px;
        padding: 0 14px;
        font-size: 12px;
        font-weight: 800;
      }
      .primary { border: 0; background: linear-gradient(135deg, var(--teal), #006b78); color: #fff; min-width: 170px; }
      .secondary { border: 1px solid var(--line); background: #fff; color: #253246; }
      .ghost { border: 1px solid transparent; background: transparent; color: #40506a; }
      .danger { border: 1px solid #efb8b2; background: #fff; color: var(--red); }
      .button-row { display: flex; gap: 9px; align-items: center; margin-top: 20px; }

      .menu {
        position: absolute;
        z-index: 5;
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 7px;
        box-shadow: var(--shadow);
        padding: 6px;
      }
      .menu button { display: block; width: 190px; border: 0; background: #fff; text-align: left; padding: 9px; border-radius: 6px; }
      .menu button:hover { background: var(--teal-soft); }

      details {
        margin-top: 22px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fff;
      }
      summary { padding: 13px; font-weight: 850; cursor: pointer; }
      pre {
        overflow: auto;
        white-space: pre-wrap;
        margin: 0;
        border-top: 1px solid var(--soft-line);
        background: #102033;
        color: #e7edf5;
        padding: 13px;
        font-size: 12px;
        line-height: 1.5;
      }
      .copy-line { display: flex; justify-content: space-between; align-items: center; padding: 10px 13px; border-top: 1px solid var(--soft-line); }

      .readiness-panel {
        margin-top: 18px;
        padding: 13px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fbfdff;
      }
      .readiness-panel h3 { margin-bottom: 10px; }
      .readiness-item {
        display: grid;
        grid-template-columns: 14px minmax(0, 1fr) auto;
        gap: 8px;
        align-items: start;
        padding: 8px 0;
        border-top: 1px solid var(--soft-line);
        color: #40506a;
        font-size: 12px;
      }
      .readiness-item:first-of-type { border-top: 0; }
      .readiness-item strong { display: block; color: #24334a; }
      .readiness-item span { overflow-wrap: anywhere; }
      .readiness-dot {
        width: 9px;
        height: 9px;
        margin-top: 4px;
        border-radius: 50%;
        background: var(--line);
      }
      .readiness-item.ready .readiness-dot { background: var(--green); }
      .readiness-item.warn .readiness-dot { background: var(--amber); }
      .readiness-state {
        border-radius: 999px;
        padding: 2px 8px;
        background: #eef3f8;
        color: #40506a;
        font-size: 10px;
        font-weight: 850;
        white-space: nowrap;
      }
      .readiness-item.ready .readiness-state { background: var(--green-soft); color: var(--green); }
      .readiness-item.warn .readiness-state { background: var(--amber-soft); color: var(--amber); }

      .status-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
      .badge {
        display: inline-flex;
        align-items: center;
        min-height: 25px;
        border-radius: 999px;
        padding: 0 10px;
        font-size: 12px;
        font-weight: 850;
      }
      .badge.running { background: #e7f0ff; color: var(--blue); }
      .badge.complete { background: var(--green-soft); color: var(--green); }
      .badge.failed, .badge.cancelled { background: var(--red-soft); color: var(--red); }
      .badge.queued { background: var(--amber-soft); color: var(--amber); }

      .ready-box {
        min-height: 520px;
        display: grid;
        place-items: center;
        text-align: center;
      }
      .compass {
        width: 96px;
        height: 96px;
        display: grid;
        place-items: center;
        margin: 0 auto 14px;
        border-radius: 50%;
        border: 1px solid var(--line);
        background: radial-gradient(circle, var(--teal-soft), #fff);
        color: var(--teal);
        font-size: 36px;
      }

      .active-run-banner {
        display: none;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 14px;
        border: 1px solid #b8e4c7;
        background: var(--green-soft);
        color: #0c5e40;
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 12px;
        font-weight: 800;
      }
      .active-run-banner.visible { display: flex; }
      .live-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.75fr);
        gap: 14px;
        align-items: stretch;
      }
      .live-side {
        display: grid;
        gap: 14px;
        align-content: start;
      }
      .timeline { list-style: none; padding: 0; margin: 0; }
      .timeline li {
        position: relative;
        margin: 0 0 16px 18px;
        padding-left: 14px;
        color: #334158;
        font-size: 12px;
      }
      .timeline li:before {
        content: "";
        position: absolute;
        left: -18px;
        top: 2px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--line);
      }
      .timeline li.success:before { background: var(--green); }
      .timeline li.error:before { background: var(--red); }
      .timeline li.warning:before { background: var(--amber); }
      .timeline strong { display: block; text-transform: capitalize; }
      .browser-frame {
        min-height: calc(100vh - 235px);
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        background: #fff;
      }
      .browser-bar { display: flex; gap: 8px; align-items: center; padding: 8px; border-bottom: 1px solid var(--soft-line); }
      .browser-url { flex: 1; border: 1px solid var(--line); border-radius: 6px; padding: 7px 9px; color: #40506a; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .workbench-toolbar {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        padding: 8px;
        border-bottom: 1px solid var(--soft-line);
        background: #f8fbff;
      }
      .workbench-toolbar button {
        min-height: 30px;
        border: 1px solid var(--line);
        border-radius: 6px;
        background: #fff;
        color: #40506a;
        font-size: 11px;
        font-weight: 800;
      }
      .workbench-toolbar button:disabled { opacity: 0.55; cursor: not-allowed; }
      .browser-shot {
        min-height: calc(100vh - 330px);
        padding: 22px;
        background: linear-gradient(180deg, #ffffff, #f4f8fc);
        overflow: auto;
      }
      .browser-shot img {
        width: 100%;
        max-height: calc(100vh - 360px);
        object-fit: contain;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: #fff;
      }
      .site-preview { border: 1px solid var(--line); border-radius: 8px; background: #fff; padding: 18px; }
      .product-preview-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 18px; }
      .fake-product { min-height: 138px; border: 1px solid var(--soft-line); background: #f2f5f8; display: grid; place-items: center; color: #7b8799; }
      .event-log { max-height: 320px; overflow: auto; }
      .event-log div { border: 1px solid var(--soft-line); border-radius: 7px; padding: 9px; margin-bottom: 8px; font-size: 12px; }

      .metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 14px 0; }
      .metric { border: 1px solid var(--line); border-radius: 8px; background: #fff; padding: 12px; }
      .metric span { display: block; color: #40506a; font-size: 10px; font-weight: 850; letter-spacing: 0.05em; text-transform: uppercase; }
      .metric strong { display: block; margin-top: 8px; font-size: 22px; color: var(--teal); }
      .workspace-tabs { margin-bottom: 14px; border-width: 0 0 1px; border-radius: 0; background: transparent; overflow: visible; }
      .workspace-tabs button { border: 0; border-bottom: 2px solid transparent; background: transparent; color: #314057; }
      .workspace-tabs button.active { background: transparent; color: var(--teal); border-bottom-color: var(--teal); }

      table { width: 100%; border-collapse: collapse; font-size: 12px; }
      th, td { border-bottom: 1px solid var(--soft-line); padding: 10px; text-align: left; vertical-align: top; }
      th { background: #f8fbff; color: #29384d; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }
      tr[data-record-index] { cursor: pointer; }
      tr[data-record-index]:hover { background: var(--teal-soft); }
      .source-badge { display: inline-flex; padding: 3px 8px; border-radius: 999px; background: var(--green-soft); color: var(--green); font-weight: 850; font-size: 11px; }
      .warn-box, .ok-box {
        border-radius: 8px;
        padding: 12px;
        margin-top: 12px;
        font-size: 12px;
      }
      .warn-box { border: 1px solid #f4c39d; background: var(--amber-soft); color: #7d4108; }
      .ok-box { border: 1px solid #b8e4c7; background: var(--green-soft); color: #0c5e40; }
      .warn-box, .ok-box, .browser-shot p { overflow-wrap: anywhere; }
      .browser-truth {
        border: 1px solid #bfd3ea;
        background: #eef6ff;
        color: #21496f;
        border-radius: 8px;
        padding: 10px;
        margin-top: 12px;
        font-size: 12px;
        overflow-wrap: anywhere;
      }

      .drawer.closed { display: none; }
      .drawer .selected-image {
        width: 90px;
        height: 120px;
        border: 1px solid var(--line);
        border-radius: 8px;
        object-fit: cover;
        background: #f4f7fa;
      }
      .kv { display: grid; grid-template-columns: 110px 1fr; gap: 8px; margin-top: 10px; font-size: 12px; }
      .kv strong { color: #506177; }
      .tab-panel.hidden { display: none; }
      .utility-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
      .utility-card { border: 1px solid var(--line); border-radius: 8px; background: #fff; padding: 14px; }
      .utility-card h3 { margin-bottom: 8px; }
      .toolbar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin: 12px 0; }
      #toast {
        position: fixed;
        right: 22px;
        bottom: 22px;
        z-index: 20;
        min-width: 180px;
        border-radius: 8px;
        background: var(--ink);
        color: #fff;
        padding: 12px 14px;
        box-shadow: var(--shadow);
      }
    </style>
  </head>
  <body>
    <header class="topbar">
      <div class="brand"><div class="logo">S</div><div><strong>SCOUT</strong><span>Intelligence Platform</span></div></div>
      <nav class="topnav">
        <button class="active" type="button" data-top-section="runs">Runs</button>
        <button type="button" data-top-section="projects">Projects</button>
        <button type="button" data-top-section="settings">Settings</button>
        <a href="/docs" data-top-section="docs">Docs</a>
      </nav>
      <div class="user-pill"><span>•</span><div class="avatar">A</div></div>
    </header>

    <div class="app-shell" id="appShell">
      <aside class="rail">
        <button class="active" data-rail-section="run"><span>□</span>Run</button>
        <button data-rail-section="history"><span>↻</span>History</button>
        <button data-rail-section="browser"><span>⊞</span>Browser</button>
        <button data-rail-section="presets"><span>▤</span>Presets</button>
        <button data-rail-section="targets"><span>⌖</span>Targets</button>
        <button data-rail-section="data"><span>▥</span>Data</button>
        <button data-rail-section="integrations"><span>⌬</span>Integrations</button>
        <button data-rail-section="settings"><span>⚙</span>Settings</button>
        <button data-rail-section="help"><span>?</span>Help</button>
      </aside>

      <section class="setup-pane">
        <div class="card card-pad">
          <div class="section-title"><div><h1>Run Setup</h1><p class="subtle">Configure your run and click Start Execution.</p></div></div>

          <label class="label" for="useCase">Use Case</label>
          <select id="useCase">
            <option value="products">Product Intelligence - E-commerce</option>
            <option value="prism">PRISM Company Intelligence</option>
            <option value="company">Company Intelligence</option>
            <option value="investor">Investor Intelligence</option>
            <option value="careers">Careers and Hiring</option>
            <option value="jobs">Jobs</option>
            <option value="news">News and Blogs</option>
            <option value="research">Research</option>
            <option value="docs">Documentation</option>
            <option value="social">Social Profiles</option>
            <option value="locations">Locations</option>
            <option value="website-quality">Website Quality</option>
          </select>
          <p id="useCaseHelp" class="subtle" style="margin-top:8px;"></p>
          <div id="expectedOutputs" class="ok-box"></div>

          <label class="label" id="targetLabel" for="targetUrl">Target URL</label>
          <div class="input-row">
            <input id="targetUrl" placeholder="https://www.example.com" />
            <button id="clearStartUrl" class="secondary" type="button">×</button>
          </div>
          <p class="subtle" id="targetExample">Example: https://www.example.com</p>

          <label class="label">Execution Mode</label>
          <div class="mode-tabs" id="modeTabs">
            <button type="button" class="active" data-mode="auto">Auto</button>
            <button type="button" data-mode="crawl4ai">Crawler</button>
            <button type="button" data-mode="webfetch">WebFetch</button>
            <button type="button" data-mode="websearch">WebSearch</button>
            <button type="button" data-mode="scout-browser">Scout Browser</button>
            <button type="button" data-mode="user-browser">User Browser</button>
            <button type="button" data-mode="saved">Saved</button>
            <button type="button" data-mode="api">API</button>
          </div>
          <p id="modeHelp" class="subtle" style="margin-top:8px;">Auto starts with crawler and Scout Browser capture. User Browser is a manual escalation only after those paths fail or need human interaction.</p>

          <label class="label">Crawl Settings</label>
          <p class="subtle">Tune how Scout collects pages. Defaults are safe for most runs.</p>
          <div class="settings-row" id="crawlChips"></div>
          <div style="position:relative;">
            <button id="addOption" class="secondary" type="button">+ Add option</button>
            <div id="addOptionMenu" class="menu hidden"></div>
          </div>

          <label class="label" for="workdir">Working Directory</label>
          <div class="input-row">
            <input id="workdir" value="/Users/arijitchowdhury/AI-Development/Scout/tests" />
            <button id="pickDir" class="secondary" type="button">Browse</button>
          </div>
          <p class="subtle">All outputs, logs, and artifacts will be saved here.</p>

          <div class="readiness-panel" id="readinessPanel">
            <h3>Run Readiness</h3>
            <div class="readiness-item" data-ready-item="target">
              <div class="readiness-dot"></div>
              <span><strong>Target</strong><span data-ready-text="target">Pending URL</span></span>
              <span class="readiness-state" data-ready-state="target">Required</span>
            </div>
            <div class="readiness-item" data-ready-item="mode">
              <div class="readiness-dot"></div>
              <span><strong>Mode</strong><span data-ready-text="mode">Auto selected by default</span></span>
              <span class="readiness-state" data-ready-state="mode">Default</span>
            </div>
            <div class="readiness-item" data-ready-item="output">
              <div class="readiness-dot"></div>
              <span><strong>Output folder</strong><span data-ready-text="output">Pending folder</span></span>
              <span class="readiness-state" data-ready-state="output">Required</span>
            </div>
            <div class="readiness-item warn" data-ready-item="capture">
              <div class="readiness-dot"></div>
              <span><strong>Browser reality</strong><span data-ready-text="capture">Scout Browser is a separate capture session. Hard sites may still block it.</span></span>
              <span class="readiness-state" data-ready-state="capture">Known limit</span>
            </div>
            <div class="readiness-item" data-ready-item="start">
              <div class="readiness-dot"></div>
              <span><strong>Start state</strong><span data-ready-text="start">Waiting for required inputs</span></span>
              <span class="readiness-state" data-ready-state="start">Not ready</span>
            </div>
          </div>

          <div class="button-row">
            <button id="startExecution" class="primary" type="button">▶ Start Execution</button>
            <button id="clearRun" class="secondary" type="button">Clear Run</button>
          </div>
          <p id="runStatus" class="subtle" style="margin-top:8px;">Ready. The app will show run status immediately after Start Execution.</p>

          <details id="developerDetails">
            <summary>Developer Details (CLI / API)</summary>
            <div class="copy-line"><strong>CLI command</strong><button class="secondary" type="button" data-copy-target="commandPreview">Copy</button></div>
            <pre id="commandPreview"></pre>
            <div class="copy-line"><strong>API request</strong><button class="secondary" type="button" data-copy-target="httpPreview">Copy</button></div>
            <pre id="httpPreview"></pre>
          </details>
        </div>
      </section>

      <main class="workspace">
        <div id="activeRunBanner" class="active-run-banner">
          <span id="activeRunBannerText">Active run</span>
          <button id="returnToActiveRun" class="secondary" type="button">Return to Run</button>
        </div>
        <section id="readyPanel" class="card card-pad ready-box">
          <div>
            <div class="compass">⌖</div>
            <h2>Ready to run</h2>
            <p>Configure a target and click Start Execution. Scout will switch into live execution with status, logs, and browser evidence.</p>
          </div>
        </section>

        <section id="livePanel" class="hidden">
          <div class="card card-pad">
            <div class="status-header">
              <div>
                <div class="badge running" id="runStateBadge">queued</div>
                <h2 style="margin-top:8px;">Live Execution</h2>
                <p class="subtle">Run ID: <span id="activeRunId">none</span></p>
              </div>
              <div class="button-row" style="margin:0;">
                <button id="cancelRun" class="danger" type="button">Cancel Run</button>
                <button class="secondary" type="button" data-clear-action>Clear Run</button>
              </div>
            </div>
            <div class="live-grid">
              <div>
                  <h3>Capture Workbench</h3>
                <div id="browserEvidence" class="browser-frame"></div>
              </div>
              <div class="live-side">
                <div>
                  <h3>Progress Timeline</h3>
                  <ul id="timeline" class="timeline"></ul>
                </div>
                <div>
                  <h3>Live Event Log</h3>
                  <div id="eventLog" class="event-log"></div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="resultsPanel" class="hidden" style="margin-top:14px;">
          <div class="card card-pad">
            <div class="status-header">
              <div><h2>Results Review</h2><p class="subtle">Merged records, sources, blocked evidence, artifacts, and logs.</p></div>
              <span id="completedAt" class="subtle"></span>
            </div>
            <div class="metrics">
              <div class="metric"><span>Pages Processed</span><strong id="metricPages">0</strong></div>
              <div class="metric"><span>Product Records</span><strong id="metricRecords">0</strong></div>
              <div class="metric"><span>Unique Sources</span><strong id="metricSources">0</strong></div>
              <div class="metric"><span>Blocked Pages</span><strong id="metricBlocked">0</strong></div>
              <div class="metric"><span>Warnings</span><strong id="metricWarnings">0</strong></div>
            </div>
            <div class="tabs workspace-tabs" id="resultTabs">
              <button class="active" data-panel="overviewPanel" type="button">Overview</button>
              <button data-panel="browserPanel" type="button">Browser</button>
              <button data-panel="recordsPanel" type="button">Records</button>
              <button data-panel="sourcesPanel" type="button">Sources</button>
              <button data-panel="blockedPanel" type="button">Blocked</button>
              <button data-panel="artifactsPanel" type="button">Artifacts</button>
              <button data-panel="logsPanel" type="button">Logs</button>
            </div>
            <div id="overviewPanel" class="tab-panel"></div>
            <div id="browserPanel" class="tab-panel hidden"></div>
            <div id="recordsPanel" class="tab-panel hidden">
              <table id="recordsTable"><thead id="recordsTableHead"><tr><th>#</th><th>Product Name</th><th>Brand</th><th>Price</th><th>SKU</th><th>Source</th></tr></thead><tbody></tbody></table>
            </div>
            <div id="sourcesPanel" class="tab-panel hidden"></div>
            <div id="blockedPanel" class="tab-panel hidden"></div>
            <div id="artifactsPanel" class="tab-panel hidden"></div>
            <div id="logsPanel" class="tab-panel hidden"></div>
          </div>
        </section>

        <section id="utilityScreen" class="hidden">
          <div class="card card-pad">
            <div class="status-header">
              <div>
                <h2 id="screenTitle">Projects</h2>
                <p id="screenDescription" class="subtle"></p>
              </div>
              <button id="returnToRun" class="secondary" type="button">Back to Run</button>
            </div>
            <div id="screenContent"></div>
          </div>
        </section>
      </main>

      <aside class="drawer closed" id="detailDrawer">
        <div class="status-header">
          <h2>Selected Record</h2>
          <button id="closeDrawer" class="ghost" type="button">×</button>
        </div>
        <div id="drawerContent"><p class="subtle">Select a record or source to inspect evidence.</p></div>
      </aside>
    </div>

    <div id="toast" class="hidden"></div>

    <script>
      let API_KEY = "dev-key";
      fetch("/api/config").then(r => r.json()).then(c => { API_KEY = c.api_key; }).catch(() => {});
      const state = {
        mode: "auto",
        runId: null,
        poller: null,
        screen: "run",
        history: [],
        records: [],
        sources: [],
        blocked: [],
        events: [],
        artifacts: {},
        browserEvidence: {},
        browserSession: {},
        options: { max_depth: 3, respect_robots_txt: true, delay_seconds: 1.0 }
      };
      const optionDefaults = { max_depth: 3, respect_robots_txt: true, delay_seconds: 1.0 };
      const optionLabels = {
        max_depth: "Max Depth",
        respect_robots_txt: "Respect robots.txt",
        delay_seconds: "Delay"
      };
      const useCaseContracts = {
        products: {
          label: "Product/category URL",
          placeholder: "https://www.example.com",
          example: "Example: https://www.example.com",
          help: "Extract product/category data and prepare downstream-ready product records.",
          outputs: "Outputs: product records, listing/detail sources, blocked detail pages, exports, Algolia prep."
        },
        prism: {
          label: "Company name, domain, or PRISM target URL",
          placeholder: "Nike or https://www.nike.com",
          example: "Example: Adobe, Nike, https://www.algolia.com",
          help: "Build a PRISM prospect bundle across company, executives, investor, careers, and news evidence.",
          outputs: "Outputs: company, executive, social, investor, career, and news records."
        },
        company: {
          label: "Company name, domain, or about URL",
          placeholder: "https://www.adobe.com/about-adobe.html",
          example: "Example: https://www.adobe.com/about-adobe.html",
          help: "Extract company overview, key URLs, leadership, and social evidence.",
          outputs: "Outputs: company.v1, executive.v1, company_social.v1."
        },
        investor: {
          label: "Investor relations URL or company domain",
          placeholder: "https://www.adobe.com/investor-relations.html",
          example: "Example: https://ir.homedepot.com",
          help: "Collect investor pages, reports, presentations, filings, and events.",
          outputs: "Outputs: investor_asset.v1 records and filing/report citations."
        },
        careers: {
          label: "Careers URL or company domain",
          placeholder: "https://www.algolia.com/careers/",
          example: "Example: https://www.adobe.com/careers.html",
          help: "Find careers pages, ATS hints, departments, and hiring signals.",
          outputs: "Outputs: career_site.v1 records and hiring evidence."
        },
        jobs: {
          label: "Company domain or job URL",
          placeholder: "https://job-boards.greenhouse.io/eve/jobs/4245857009",
          example: "Example: Greenhouse, Ashby, Workday, or native job URL.",
          help: "Extract and score job postings against a profile or target role criteria.",
          outputs: "Outputs: job_posting.v1 records, match scores, reject reasons, ATS evidence."
        },
        news: {
          label: "Newsroom, blog URL, or company domain",
          placeholder: "https://www.constructor.io/blog/",
          example: "Example: https://blog.algolia.com or https://newsroom.homedepot.com",
          help: "Collect recent company news, blogs, announcements, and dated source links.",
          outputs: "Outputs: news_signal.v1 records with dates, URLs, and citations."
        },
        research: {
          label: "URL, domain, or research prompt",
          placeholder: "companies with weak ecommerce search UX",
          example: "Example: British Airways website quality research",
          help: "Normalize broad web research evidence into reusable records.",
          outputs: "Outputs: research_record.v1 records, source evidence, summaries, citations."
        },
        docs: {
          label: "Documentation URL or sitemap URL",
          placeholder: "https://www.algolia.com/doc/",
          example: "Example: https://www.algolia.com/doc/",
          help: "Collect documentation pages, sections, markdown, and source URLs.",
          outputs: "Outputs: documentation records, source pages, markdown/DOM evidence."
        },
        social: {
          label: "Company domain or social profile source URL",
          placeholder: "https://www.algolia.com/",
          example: "Example: https://www.algolia.com/",
          help: "Find public company social profile links and preserve where they were found.",
          outputs: "Outputs: company_social.v1 records with platform, URL, and citations."
        },
        locations: {
          label: "Locations/store finder URL or company domain",
          placeholder: "https://www.homedepot.com/l/",
          example: "Example: https://www.homedepot.com/l/",
          help: "Extract public location/store evidence when available, or blocked/unsupported evidence when not.",
          outputs: "Outputs: location records or explicit blocked/unsupported evidence."
        },
        "website-quality": {
          label: "Website URL",
          placeholder: "https://www.britishairways.com/",
          example: "Example: https://www.britishairways.com/",
          help: "Assess website quality, UX/content gaps, and competitor improvement opportunities.",
          outputs: "Outputs: website-quality findings, evidence snippets, source citations."
        }
      };
      const utilityScreens = {
        history: { title: "Run History", description: "Review app runs from this session and reopen results." },
        presets: { title: "Presets", description: "Apply repeatable run templates for common Scout workflows." },
        targets: { title: "Target Catalog", description: "Use the balanced Scout test target matrix directly in the app." },
        data: { title: "Data Browser", description: "Inspect records, sources, blocked pages, artifacts, and reports for the active run." },
        integrations: { title: "Integrations", description: "Prepare records for Algolia and future downstream ingestion." },
        settings: { title: "Settings", description: "Inspect local workdir, API key status, live-test flag, and runtime information." },
        help: { title: "How to Use Scout", description: "Learn Scout workflows, execution modes, artifacts, and citation evidence." },
        projects: { title: "Projects", description: "Organize run outputs by project and open artifact locations." },
        browser: { title: "Live Browser", description: "Browse sites in a managed browser, capture and harvest structured records from any page." }
      };
      const targetCatalog = [
        ["Algolia", "Private B2B SaaS", "https://www.algolia.com/", "PRISM, company, careers, blogs, docs"],
        ["Constructor", "Private B2B SaaS", "https://constructor.com/", "PRISM, competitor intel, company, careers, blogs"],
        ["L.L.Bean", "Private retail commerce", "https://www.llbean.com/", "Products, careers, company"],
        ["Patagonia", "Private retail commerce", "https://www.patagonia.com/", "Products, company, sustainability/blog"],
        ["Adobe", "Public company", "https://www.adobe.com/", "Company, investor, careers, blogs/news"],
        ["Home Depot", "Public retail", "https://www.homedepot.com/", "Investor, careers, product catalog, news"],
        ["Estée Lauder", "Hard-site retail", "https://www.esteelauder.com/", "Hard-site product/category fallback"],
        ["British Airways", "Travel", "https://www.britishairways.com/", "Travel company intel, careers, website quality"]
      ];
      const presets = [
        ["L.L.Bean outdoor products", "products", "https://www.llbean.com/"],
        ["Nike company intelligence", "company", "https://www.nike.com/"],
        ["Adobe investor intelligence", "investor", "https://www.adobe.com/investor-relations.html"],
        ["Algolia careers", "careers", "https://www.algolia.com/careers/"],
        ["Constructor news/blogs", "news", "https://constructor.com/blog/"],
        ["British Airways website quality", "website-quality", "https://www.britishairways.com/"]
      ];

      const el = (id) => document.getElementById(id);
      const qs = (selector, root = document) => root.querySelector(selector);
      const qsa = (selector, root = document) => Array.from(root.querySelectorAll(selector));

      function toast(message) {
        const node = el("toast");
        node.textContent = message;
        node.classList.remove("hidden");
        window.setTimeout(() => node.classList.add("hidden"), 1800);
      }

      function modeLabel() {
        return state.mode;
      }

      function modeSessionLabel(mode = state.mode) {
        if (mode === "scout-browser" || mode === "browser") return "Scout browser session";
        if (mode === "user-browser") return "User browser session";
        return "Crawler session";
      }

      function modeHelpFor(mode, label) {
        const helpByMode = {
          "auto": "Auto selected. Scout will not open User Browser unless you explicitly switch modes after a block.",
          "user-browser": "User Browser selected manually. Scout will open Chrome/CDP and wait for you to capture the active tab.",
          "scout-browser": "Scout Browser selected. Scout will use a scout browser session.",
          "crawl4ai": "Crawler selected. Scout will use a Crawl4AI crawler session.",
          "webfetch": "WebFetch selected. Scout will fetch pages over plain HTTP without a browser.",
          "websearch": "WebSearch selected. Scout will gather evidence from web search results.",
          "saved": "Saved selected. Scout will load evidence from a saved snapshot instead of the live web.",
          "api": "API selected. Scout will use structured API providers where available."
        };
        return helpByMode[mode] || `${label} selected. Scout will use a ${modeSessionLabel(mode).toLowerCase()}.`;
      }

      function useCaseLabel() {
        return el("useCase").value;
      }

      function activePayload() {
        return {
          use_case: useCaseLabel(),
          mode: modeLabel(),
          url: el("targetUrl").value.trim(),
          query: el("targetUrl").value.trim(),
          output_dir: el("workdir").value.trim(),
          browser_fallback: true,
          ...state.options
        };
      }

      function currentUseCaseContract() {
        return useCaseContracts[useCaseLabel()] || useCaseContracts.products;
      }

      function updateUseCaseContract() {
        const contract = currentUseCaseContract();
        el("targetLabel").textContent = contract.label;
        el("targetUrl").placeholder = contract.placeholder;
        el("targetExample").textContent = contract.example;
        el("useCaseHelp").textContent = contract.help;
        el("expectedOutputs").textContent = contract.outputs;
        renderMetrics();
        updateDeveloperDetails();
      }

      function showRunWorkspace() {
        state.screen = "run";
        el("appShell").classList.remove("utility-mode");
        el("utilityScreen").classList.add("hidden");
        if (state.runId) {
          el("readyPanel").classList.add("hidden");
          el("livePanel").classList.remove("hidden");
          el("activeRunBanner").classList.add("visible");
        } else {
          el("readyPanel").classList.remove("hidden");
          el("activeRunBanner").classList.remove("visible");
        }
        qsa("[data-rail-section]").forEach((button) => button.classList.toggle("active", button.dataset.railSection === "run"));
        qsa("[data-top-section]").forEach((button) => button.classList.toggle("active", button.dataset.topSection === "runs"));
      }

      function showUtilityScreen(screen) {
        const meta = utilityScreens[screen] || utilityScreens.history;
        state.screen = screen;
        el("appShell").classList.add("utility-mode");
        if (state.runId) el("activeRunBanner").classList.add("visible");
        el("readyPanel").classList.add("hidden");
        el("livePanel").classList.add("hidden");
        el("resultsPanel").classList.add("hidden");
        el("utilityScreen").classList.remove("hidden");
        el("detailDrawer").classList.add("closed");
        el("screenTitle").textContent = meta.title;
        el("screenDescription").textContent = meta.description;
        qsa("[data-rail-section]").forEach((button) => button.classList.toggle("active", button.dataset.railSection === screen));
        qsa("[data-top-section]").forEach((button) => button.classList.toggle("active", button.dataset.topSection === screen || (screen === "projects" && button.dataset.topSection === "projects")));
        renderUtilityScreen(screen);
      }

      function applyPreset(useCase, url) {
        el("useCase").value = useCase;
        el("targetUrl").value = url;
        updateUseCaseContract();
        showRunWorkspace();
        toast("Preset applied");
      }

      function renderUtilityScreen(screen) {
        const content = el("screenContent");
        if (screen === "history") {
          content.innerHTML = state.history.length
            ? `<table><thead><tr><th>Run ID</th><th>Use Case</th><th>Status</th><th>Records</th><th>Action</th></tr></thead><tbody>${state.history.map((run) => `<tr><td>${escapeHtml(run.run_id)}</td><td>${escapeHtml(run.use_case)}</td><td>${escapeHtml(run.status)}</td><td>${(run.records || []).length}</td><td><button class="secondary" type="button" data-open-history="${escapeAttr(run.run_id)}">Reopen</button></td></tr>`).join("")}</tbody></table>`
            : `<div class="warn-box">No app runs in this browser session yet. Start a run to populate history.</div>`;
          return;
        }
        if (screen === "presets") {
          content.innerHTML = `<div class="utility-grid">${presets.map(([name, useCase, url]) => `<div class="utility-card"><h3>${escapeHtml(name)}</h3><p class="subtle">${escapeHtml(url)}</p><button class="secondary" type="button" data-preset-use-case="${escapeAttr(useCase)}" data-preset-url="${escapeAttr(url)}">Use Preset</button></div>`).join("")}</div>`;
          return;
        }
        if (screen === "targets") {
          content.innerHTML = `<table><thead><tr><th>Company</th><th>Segment</th><th>Primary Use</th><th>Action</th></tr></thead><tbody>${targetCatalog.map(([name, segment, url, use]) => `<tr><td>${escapeHtml(name)}</td><td>${escapeHtml(segment)}</td><td>${escapeHtml(use)}</td><td><button class="secondary" type="button" data-target-url="${escapeAttr(url)}">Use Target</button></td></tr>`).join("")}</tbody></table>`;
          return;
        }
        if (screen === "data" || screen === "projects") {
          content.innerHTML = `<div class="toolbar"><button class="secondary" type="button" data-panel="recordsPanel">Records</button><button class="secondary" type="button" data-panel="sourcesPanel">Sources</button><button class="secondary" type="button" data-panel="artifactsPanel">Artifacts</button><button class="secondary" type="button" data-download-records ${state.records.length ? "" : "disabled"} title="${state.records.length ? "Download records as JSON" : "No records to download yet."}">Download Records</button></div>${Object.keys(state.artifacts).length ? el("artifactsPanel").innerHTML : "<div class='warn-box'>No active run artifacts yet.</div>"}`;
          return;
        }
        if (screen === "integrations") {
          content.innerHTML = `<div class="utility-grid"><div class="utility-card"><h3>Algolia Preparation</h3><label class="label">App ID</label><input id="algoliaAppId" placeholder="Your Algolia app ID"><label class="label">API Key</label><input id="algoliaApiKey" type="password" placeholder="Session only"><label class="label">Index Name</label><input id="algoliaIndexName" placeholder="products_dev"><button class="secondary" type="button" data-preview-algolia>Preview Readiness</button></div><div class="utility-card"><h3>Preview</h3><div id="algoliaPreview">No preview yet.</div></div><div class="utility-card"><h3>Security</h3><p class="subtle">Credentials stay in this browser session and are not written to artifacts.</p></div></div>`;
          return;
        }
        if (screen === "settings") {
          content.innerHTML = `<div class="utility-grid"><div class="utility-card"><h3>Working Directory</h3><p>${escapeHtml(el("workdir").value)}</p></div><div class="utility-card"><h3>API Key</h3><p>Configured for local app requests.</p></div><div class="utility-card"><h3>Live Tests</h3><p>${escapeHtml(String(Boolean(window.SCOUT_LIVE_TESTS)))}</p></div></div>`;
          return;
        }
        if (screen === "browser") {
          const port = window.location.port ? ":" + window.location.port : "";
          const liveBrowserUrl = window.location.protocol + "//" + window.location.hostname + port + "/app/live-browser";
          content.innerHTML = `<div style="display:flex;flex-direction:column;gap:12px;height:calc(100vh - 200px);">` +
            `<div style="display:flex;gap:8px;align-items:center;">` +
            `<a href="${liveBrowserUrl}" target="_blank" class="secondary" style="text-decoration:none;padding:6px 14px;border:1px solid var(--line);border-radius:5px;font-size:12px;">Open in New Tab ↗</a>` +
            `<span class="subtle" style="font-size:11px;">Browse sites, solve CAPTCHAs, then capture structured records.</span>` +
            `</div>` +
            `<iframe src="${liveBrowserUrl}" style="flex:1;border:1px solid var(--line);border-radius:6px;width:100%;min-height:400px;" allow="clipboard-write"></iframe>` +
            `</div>`;
          return;
        }
        if (screen === "help") {
          content.innerHTML = `<div class="utility-grid"><div class="utility-card"><h3>1. Configure</h3><p class="subtle">Choose a use case, target, mode, crawl settings, and working directory.</p></div><div class="utility-card"><h3>2. Execute</h3><p class="subtle">Start a run and watch the run ID, timeline, browser evidence, and logs.</p></div><div class="utility-card"><h3>3. Review</h3><p class="subtle">Inspect records, sources, blocked pages, artifacts, logs, and citations.</p></div></div>`;
        }
      }

      function setReadinessItem(key, status, text, stateLabel) {
        const item = qs(`[data-ready-item="${key}"]`);
        const textNode = qs(`[data-ready-text="${key}"]`);
        const stateNode = qs(`[data-ready-state="${key}"]`);
        if (!item || !textNode || !stateNode) return;
        item.classList.remove("ready", "warn");
        if (status) item.classList.add(status);
        textNode.textContent = text;
        stateNode.textContent = stateLabel;
      }

      function updateReadinessPanel(runData = null) {
        const target = el("targetUrl").value.trim();
        const workdir = el("workdir").value.trim();
        const mode = modeLabel();
        const hasTarget = Boolean(target);
        const hasWorkdir = Boolean(workdir);
        setReadinessItem(
          "target",
          hasTarget ? "ready" : "",
          hasTarget ? target : "Pending URL",
          hasTarget ? "Ready" : "Required"
        );
        setReadinessItem(
          "mode",
          mode === "auto" ? "warn" : "ready",
          `${mode} selected`,
          mode === "auto" ? "Default" : "Selected"
        );
        setReadinessItem(
          "output",
          hasWorkdir ? "ready" : "",
          hasWorkdir ? workdir : "Pending folder",
          hasWorkdir ? "Ready" : "Required"
        );
        const captureText = mode === "user-browser"
          ? "Manual escalation: opens Scout-managed Chrome only when you intentionally choose User Browser for a blocked/human-gated page."
          : mode === "scout-browser" || mode === "browser"
          ? "Scout Browser is the automated embedded Playwright capture path. Use it before escalating to User Browser."
          : "Crawler modes do not open your real browser. User Browser is not invoked automatically.";
        setReadinessItem("capture", "warn", captureText, "Known limit");
        if (runData) {
          const records = (runData.records || []).length;
          const blocked = (runData.blocked_pages || []).length;
          const status = runData.status || "queued";
          setReadinessItem(
            "start",
            status === "complete" && records ? "ready" : status === "failed" || blocked ? "warn" : "",
            `Last run ${status}: ${records} records, ${blocked} blocked pages`,
            status
          );
          return;
        }
        setReadinessItem(
          "start",
          hasTarget && hasWorkdir ? "ready" : "",
          hasTarget && hasWorkdir ? "Ready to start" : "Waiting for required inputs",
          hasTarget && hasWorkdir ? "Ready" : "Not ready"
        );
      }

      function updateDeveloperDetails() {
        const payload = activePayload();
        const optionFlags = Object.entries(state.options).map(([key, value]) => {
          if (key === "max_depth") return `  --max-depth ${value}`;
          if (key === "respect_robots_txt") return `  --respect-robots-txt ${value}`;
          if (key === "delay_seconds") return `  --delay ${value}`;
          return "";
        }).filter(Boolean).join(" \\\\\\n");
        el("commandPreview").textContent = `scout run ${payload.use_case} \\\\\\n  --mode ${payload.mode} \\\\\\n  --url "${payload.url}" \\\\\\n  --output "${payload.output_dir}"${optionFlags ? " \\\\\\n" + optionFlags : ""}`;
        el("httpPreview").textContent = `POST /app/runs\\nX-API-Key: ${API_KEY}\\nContent-Type: application/json\\n\\n${JSON.stringify(payload, null, 2)}`;
        updateReadinessPanel();
      }

      function optionValueText(key, value) {
        if (key === "respect_robots_txt") return value ? "On" : "Off";
        if (key === "delay_seconds") return `${value}s`;
        return String(value);
      }

      function renderOptionChips() {
        const wrap = el("crawlChips");
        wrap.innerHTML = "";
        Object.entries(state.options).forEach(([key, value]) => {
          const chip = document.createElement("span");
          chip.className = "chip";
          chip.dataset.optionChip = key;
          chip.innerHTML = `${optionLabels[key]}: ${optionValueText(key, value)} <button type="button" aria-label="Remove ${optionLabels[key]}" data-remove-option="${key}">×</button>`;
          wrap.appendChild(chip);
        });
        updateDeveloperDetails();
      }

      function renderAddOptionMenu() {
        const menu = el("addOptionMenu");
        const missing = Object.keys(optionDefaults).filter((key) => !(key in state.options));
        menu.innerHTML = "";
        if (!missing.length) {
          const message = document.createElement("div");
          message.style.padding = "9px";
          message.textContent = "All crawl settings are already active.";
          menu.appendChild(message);
          return;
        }
        missing.forEach((key) => {
          const button = document.createElement("button");
          button.type = "button";
          button.dataset.addOption = key;
          button.textContent = `Restore ${optionLabels[key]}`;
          menu.appendChild(button);
        });
      }

      function setRunState(status) {
        const badge = el("runStateBadge");
        badge.textContent = status || "queued";
        badge.className = `badge ${status || "queued"}`;
      }

      function renderBrowserEvidence(evidence) {
        const url = evidence.url || el("targetUrl").value.trim() || "No URL loaded";
        const title = evidence.title || "Scout browser evidence";
        const session = evidence.session_type || modeSessionLabel(evidence.provider || state.mode);
        const status = evidence.status || "waiting";
        const note = evidence.note || "Waiting for captured browser evidence.";
        const blocked = /access denied|blocked|permission/i.test(`${title} ${note} ${evidence.text_preview || ""}`);
        const truth = evidence.provider === "user-browser"
          ? "User Browser capture uses evidence posted from your real browser session."
          : "Scout Browser is not a live embedded browser. It is a separate automated capture session, so hard sites can still block it.";
        const screenshot = evidence.screenshot_data_url
          ? `<img src="${escapeAttr(evidence.screenshot_data_url)}" alt="Captured browser evidence for ${escapeAttr(title)}">`
          : `<div class="site-preview"><h2>${escapeHtml(title)}</h2><p>${escapeHtml(note)}</p><div class="product-preview-grid"><div class="fake-product">Screenshot pending</div><div class="fake-product">DOM / Markdown pending</div></div></div>`;
        const textPreview = evidence.text_preview
          ? `<div class="ok-box"><strong>Extracted text preview</strong><br>${escapeHtml(String(evidence.text_preview).slice(0, 700))}</div>`
          : "";
        const failures = (evidence.network_failures || []).length
          ? `<div class="warn-box">Network failures captured: ${escapeHtml(String((evidence.network_failures || []).length))}</div>`
          : "";
        const sessionDetails = evidence.provider === "user-browser"
          ? `<div class="browser-truth"><strong>Chrome CDP</strong><br>Status: ${escapeHtml(evidence.status || "waiting_for_user_capture")}<br>Port: ${escapeHtml(evidence.debugging_port || "not connected")}<br>Profile: ${escapeHtml(evidence.profile_dir || "Scout-managed profile pending")}</div>`
          : "";
        const blockedGuidance = blocked
          ? `<div class="warn-box"><strong>User Browser bridge needed</strong><br>This target blocked Scout's separate browser context. To make this work for hard sites, Scout needs a Chrome/CDP or extension bridge that captures the page from your real browser session and posts DOM evidence to <code>/app/runs/{run_id}/user-browser-capture</code>.</div>`
          : "";
        const canCapture = state.runId && evidence.provider === "user-browser" && ["opened", "captured", "waiting"].includes(String(evidence.status || "opened"));
        el("browserEvidence").innerHTML = `
          <div class="browser-bar"><span>●</span><div class="browser-url">${escapeHtml(url)}</div></div>
          <div class="workbench-toolbar">
            <button type="button" data-open-current-url title="Open this target in your normal browser session.">Open in User Browser</button>
            <button type="button" disabled title="A live embedded browser is not available in this web app.">Back</button>
            <button type="button" disabled title="A live embedded browser is not available in this web app.">Forward</button>
            <button type="button" disabled title="Use Start Execution to refresh Scout's separate capture session.">Refresh Capture</button>
            <button type="button" data-capture-active-tab ${canCapture ? "" : "disabled"} title="Capture Active Tab through the Scout-managed Chrome CDP session.">Capture Active Tab</button>
            <button type="button" disabled title="Evidence is saved automatically to the selected working directory.">Save Evidence</button>
          </div>
          <div class="browser-shot">
            <h2>${escapeHtml(title)}</h2>
            <p class="subtle">${escapeHtml(session)} · ${escapeHtml(status)} · Provider: ${escapeHtml(evidence.provider || state.mode)} · Viewport: ${escapeHtml(evidence.viewport || "not captured")}</p>
            <div class="browser-truth">${escapeHtml(truth)}</div>
            ${sessionDetails}
            ${screenshot}
            ${textPreview}
            ${failures}
            ${blockedGuidance}
          </div>`;
      }

      function renderTimeline(events) {
        el("timeline").innerHTML = events.map((event) => `<li class="${escapeHtml(event.level || "info")}"><strong>${escapeHtml(event.stage)}</strong>${escapeHtml(event.message || "")}</li>`).join("");
        el("eventLog").innerHTML = events.map((event) => `<div><strong>${escapeHtml(event.stage)}</strong><br>${escapeHtml(event.message || "")}<br><span class="subtle">${escapeHtml(event.timestamp || "")}</span></div>`).join("");
      }

      function renderMetrics() {
        el("metricPages").textContent = state.sources.length;
        el("metricRecords").textContent = state.records.length;
        el("metricSources").textContent = state.sources.length;
        el("metricBlocked").textContent = state.blocked.length;
        el("metricWarnings").textContent = state.events.filter((event) => event.level === "warning").length;
      }

      function isProductRun() {
        return (state.runUseCase || useCaseLabel()) === "products";
      }

      function recordsTableHeaders() {
        return isProductRun()
          ? "<tr><th>#</th><th>Product Name</th><th>Brand</th><th>Price</th><th>SKU</th><th>Source</th></tr>"
          : "<tr><th>#</th><th>Record Name</th><th>Type</th><th>Confidence</th><th>Source</th></tr>";
      }

      function renderRecords() {
        const tbody = qs("#recordsTable tbody");
        el("recordsTableHead").innerHTML = recordsTableHeaders();
        const columns = isProductRun() ? 6 : 5;
        if (!state.records.length) {
          tbody.innerHTML = `<tr><td colspan="${columns}">No records yet. Start a run or inspect blocked/fallback evidence.</td></tr>`;
          return;
        }
        tbody.innerHTML = state.records.map((record, index) => {
          const source = record._source || record.source || {};
          const sourceType = record.source_type || (source.extractor === "listing_card" ? "Listing" : "Detail");
          if (!isProductRun()) {
            return `<tr data-record-index="${index}">
              <td>${index + 1}</td>
              <td>${escapeHtml(record.name || record.title || "")}</td>
              <td>${escapeHtml(record.record_type || "")}</td>
              <td>${escapeHtml(record.confidence == null ? "" : String(record.confidence))}</td>
              <td><span class="source-badge">${escapeHtml(sourceType)}</span></td>
            </tr>`;
          }
          const price = record.price == null ? "" : `$${record.price}`;
          return `<tr data-record-index="${index}">
            <td>${index + 1}</td>
            <td>${escapeHtml(record.name || "")}</td>
            <td>${escapeHtml(record.brand || "")}</td>
            <td>${escapeHtml(price)}</td>
            <td>${escapeHtml(record.sku || "")}</td>
            <td><span class="source-badge">${escapeHtml(sourceType)}</span></td>
          </tr>`;
        }).join("");
      }

      function renderResultPanels() {
        const listingCount = state.records.filter((record) => {
          const source = record._source || record.source || {};
          return record.source_type === "Listing" || source.extractor === "listing_card";
        }).length;
        el("overviewPanel").innerHTML = `
          <div class="${state.records.length ? "ok-box" : "warn-box"}">${state.records.length ? `${listingCount || state.records.length} listing records found.` : "No records found yet."}</div>
          <div id="blockedSummary" class="${state.blocked.length ? "warn-box" : "ok-box"}">${state.blocked.length ? `Detail pages blocked: ${state.blocked.length}. Blocked enrichment is reported separately from listing records.` : "No blocked pages reported."}</div>`;
        el("browserPanel").innerHTML = el("browserEvidence").innerHTML;
        el("sourcesPanel").innerHTML = state.sources.length
          ? `<table><thead><tr><th>URL</th><th>Provider</th><th>Status</th><th>Confidence</th></tr></thead><tbody>${state.sources.map((source) => `<tr><td>${escapeHtml(source.source_url || source.url || "")}</td><td>${escapeHtml(source.provider || "")}</td><td>${escapeHtml(source.status || source.status_code || "")}</td><td>${escapeHtml(String(source.confidence ?? ""))}</td></tr>`).join("")}</tbody></table>`
          : `<p class="subtle">No sources loaded.</p>`;
        el("blockedPanel").innerHTML = state.blocked.length
          ? `<table><thead><tr><th>URL</th><th>Reason</th><th>Fallback</th></tr></thead><tbody>${state.blocked.map((item) => `<tr><td>${escapeHtml(item.url || "")}</td><td>${escapeHtml(item.reason || "")}</td><td>${item.fallback_attempted ? "Attempted" : "Not attempted"}</td></tr>`).join("")}</tbody></table>`
          : `<p class="subtle">No blocked pages.</p>`;
        el("artifactsPanel").innerHTML = Object.keys(state.artifacts).length
          ? `<table><thead><tr><th>Artifact</th><th>Path</th></tr></thead><tbody>${Object.entries(state.artifacts).map(([key, value]) => `<tr><td>${escapeHtml(key)}</td><td>${escapeHtml(String(value || ""))}</td></tr>`).join("")}</tbody></table>`
          : `<p class="subtle">No artifacts loaded.</p>`;
        el("logsPanel").innerHTML = el("eventLog").innerHTML;
        renderRecords();
        qsa("#resultTabs button").forEach((button) => button.classList.remove("active"));
        qs('[data-panel="recordsPanel"]').classList.add("active");
        qsa(".tab-panel").forEach((panel) => panel.classList.add("hidden"));
        el("recordsPanel").classList.remove("hidden");
      }

      function renderRun(data) {
        state.runId = data.run_id || state.runId;
        state.runUseCase = data.use_case || state.runUseCase;
        state.records = data.records || [];
        state.sources = data.sources || [];
        state.blocked = data.blocked_pages || [];
        state.events = data.events || [];
        state.artifacts = data.artifacts || {};
        state.browserEvidence = data.browser_evidence || {};
        el("appShell").classList.add("running-mode");
        el("activeRunBanner").classList.add("visible");
        el("activeRunBannerText").textContent = `Active run ${state.runId || ""} · ${data.status || "queued"} · ${data.use_case || useCaseLabel()} · ${(state.records || []).length} records`;
        el("readyPanel").classList.add("hidden");
        el("livePanel").classList.remove("hidden");
        el("activeRunId").textContent = state.runId || "none";
        el("runStatus").textContent = `Run ${state.runId || ""}: ${data.status || "queued"} · ${state.events.length} events · ${state.records.length} records`;
        setRunState(data.status || "queued");
        renderTimeline(state.events);
        renderBrowserEvidence(state.browserEvidence);
        updateReadinessPanel(data);
        if (["complete", "failed", "cancelled"].includes(data.status)) {
          el("appShell").classList.remove("running-mode");
          el("startExecution").disabled = false;
          el("startExecution").textContent = "▶ Start Execution";
          el("resultsPanel").classList.remove("hidden");
          el("completedAt").textContent = data.updated_at || "";
          renderMetrics();
          renderResultPanels();
          const existing = state.history.findIndex((run) => run.run_id === data.run_id);
          if (existing >= 0) state.history[existing] = data;
          else state.history.unshift(data);
          stopPolling();
        }
      }

      function stopPolling() {
        if (state.poller) {
          window.clearInterval(state.poller);
          state.poller = null;
        }
      }

      async function fetchJson(url, options = {}) {
        const response = await fetch(url, {
          ...options,
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
            ...(options.headers || {})
          }
        });
        if (!response.ok) {
          const text = await response.text();
          throw new Error(`${response.status} ${text}`);
        }
        return await response.json();
      }

      async function startRun() {
        const payload = activePayload();
        if (!payload.url) {
          el("runStatus").textContent = "Enter a Target / Start URL before starting execution.";
          el("targetUrl").focus();
          toast("Enter a target URL before starting.");
          return;
        }
        el("startExecution").disabled = true;
        el("startExecution").textContent = "Running...";
        el("runStatus").textContent = "Run created. Loading live execution...";
        try {
          const data = await fetchJson("/app/runs", { method: "POST", body: JSON.stringify(payload) });
          renderRun(data);
          stopPolling();
          state.poller = window.setInterval(async () => {
            try {
              const next = await fetchJson(`/app/runs/${state.runId}`);
              renderRun(next);
            } catch (error) {
              stopPolling();
              toast(error.message);
            }
          }, 700);
        } catch (error) {
          el("startExecution").disabled = false;
          el("startExecution").textContent = "▶ Start Execution";
          el("runStatus").textContent = `Run failed to start: ${error.message}`;
          toast("Run failed to start");
        }
      }

      async function cancelRun() {
        if (!state.runId) return;
        const data = await fetchJson(`/app/runs/${state.runId}/cancel`, { method: "POST" });
        renderRun(data);
      }

      async function captureActiveTab() {
        if (!state.runId) {
          toast("Start a User Browser run first");
          return;
        }
        el("runStatus").textContent = "Capturing active Chrome tab...";
        try {
          const data = await fetchJson(`/app/runs/${state.runId}/capture-active-tab`, { method: "POST" });
          renderRun(data);
          toast(data.status === "complete" ? "Active tab captured" : "Capture finished with warnings");
        } catch (error) {
          el("runStatus").textContent = `Capture failed: ${error.message}`;
          toast("Capture failed");
        }
      }

      async function refreshBrowserStatus() {
        try {
          state.browserSession = await fetchJson("/app/browser/status");
        } catch (error) {
          state.browserSession = { connected: false, status: "unavailable", error: error.message };
        }
      }

      async function openNativeDirectoryPicker() {
        el("pickDir").disabled = true;
        try {
          const result = await fetchJson("/workdir/pick-native", {
            method: "POST",
            body: JSON.stringify({ current_path: el("workdir").value.trim() || "~" })
          });
          if (result.picked && result.path) {
            el("workdir").value = result.path;
            updateDeveloperDetails();
            toast("Working directory selected");
          } else if (result.cancelled) {
            toast("Folder selection cancelled");
          } else {
            toast("Native folder picker unavailable. Edit the path directly.");
          }
        } catch (error) {
          toast(`Folder picker failed: ${error.message}`);
        } finally {
          el("pickDir").disabled = false;
        }
      }

      function clearRun() {
        stopPolling();
        state.runId = null;
        state.runUseCase = null;
        state.records = [];
        state.sources = [];
        state.blocked = [];
        state.events = [];
        state.artifacts = {};
        state.browserEvidence = {};
        el("appShell").classList.remove("running-mode", "utility-mode");
        el("activeRunBanner").classList.remove("visible");
        el("readyPanel").classList.remove("hidden");
        el("livePanel").classList.add("hidden");
        el("resultsPanel").classList.add("hidden");
        el("detailDrawer").classList.add("closed");
        el("startExecution").disabled = false;
        el("startExecution").textContent = "▶ Start Execution";
        el("runStatus").textContent = "Ready. The app will show run status immediately after Start Execution.";
        updateReadinessPanel();
        renderMetrics();
      }

      function openRecordDrawer(index) {
        const record = state.records[index];
        if (!record) return;
        const source = record._source || record.source || {};
        el("detailDrawer").classList.remove("closed");
        el("drawerContent").innerHTML = `
          ${record.image ? `<img class="selected-image" src="${escapeAttr(record.image)}" alt="">` : ""}
          <h3 style="margin-top:12px;">${escapeHtml(record.name || "Record")}</h3>
          <div class="kv"><strong>Brand</strong><span>${escapeHtml(record.brand || "")}</span></div>
          <div class="kv"><strong>Price</strong><span>${escapeHtml(record.price == null ? "" : `$${record.price}`)}</span></div>
          <div class="kv"><strong>URL</strong><span>${escapeHtml(record.url || "")}</span></div>
          <div class="kv"><strong>Evidence Source</strong><span>${escapeHtml(source.category_url || source.url || record.url || "")}</span></div>
          <div class="kv"><strong>Citations</strong><span>${(record.citations || []).length}</span></div>
          <div class="ok-box">Selecting a record keeps the evidence and citation context in the same workspace.</div>`;
      }

      function escapeHtml(value) {
        return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
      }
      function escapeAttr(value) { return escapeHtml(value).replace(/"/g, "&quot;"); }

      document.addEventListener("click", async (event) => {
        const target = event.target;
        const railButton = target.closest("[data-rail-section]");
        if (railButton) {
          const section = railButton.dataset.railSection;
          if (section === "run") showRunWorkspace();
          else showUtilityScreen(section);
        }

        const topButton = target.closest("[data-top-section]");
        if (topButton && topButton.tagName !== "A") {
          const section = topButton.dataset.topSection;
          if (section === "runs") showRunWorkspace();
          else showUtilityScreen(section);
        }

        const presetButton = target.closest("[data-preset-use-case]");
        if (presetButton) {
          applyPreset(presetButton.dataset.presetUseCase, presetButton.dataset.presetUrl);
        }

        const targetButton = target.closest("[data-target-url]");
        if (targetButton) {
          el("targetUrl").value = targetButton.dataset.targetUrl;
          updateDeveloperDetails();
          showRunWorkspace();
          toast("Target applied");
        }

        const historyButton = target.closest("[data-open-history]");
        if (historyButton) {
          const run = state.history.find((item) => item.run_id === historyButton.dataset.openHistory);
          if (run) {
            showRunWorkspace();
            renderRun(run);
          }
        }

        const downloadButton = target.closest("[data-download-records]");
        if (downloadButton) {
          if (!state.records.length) {
            toast("No records to download yet.");
            return;
          }
          const blob = new Blob([JSON.stringify(state.records, null, 2)], { type: "application/json" });
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          link.download = `${state.runId || "scout"}-records.json`;
          link.click();
          URL.revokeObjectURL(url);
          toast("Records download prepared");
        }

        const algoliaButton = target.closest("[data-preview-algolia]");
        if (algoliaButton) {
          const missing = [];
          if (!el("algoliaIndexName").value.trim()) missing.push("index name");
          if (!state.records.length) missing.push("records");
          el("algoliaPreview").textContent = missing.length
            ? `Not ready: missing ${missing.join(", ")}.`
            : `Ready: ${state.records.length} records can be prepared for ${el("algoliaIndexName").value.trim()}.`;
        }

        const modeButton = target.closest("[data-mode]");
        if (modeButton) {
          qsa("[data-mode]").forEach((button) => button.classList.remove("active"));
          modeButton.classList.add("active");
          state.mode = modeButton.dataset.mode;
          el("modeHelp").textContent = modeHelpFor(state.mode, modeButton.textContent);
          updateDeveloperDetails();
        }

        const removeOption = target.closest("[data-remove-option]");
        if (removeOption) {
          delete state.options[removeOption.dataset.removeOption];
          renderOptionChips();
        }

        if (target.closest("#addOption")) {
          renderAddOptionMenu();
          el("addOptionMenu").classList.toggle("hidden");
        }

        const addOption = target.closest("[data-add-option]");
        if (addOption) {
          state.options[addOption.dataset.addOption] = optionDefaults[addOption.dataset.addOption];
          el("addOptionMenu").classList.add("hidden");
          renderOptionChips();
        }

        const copyButton = target.closest("[data-copy-target]");
        if (copyButton) {
          const source = el(copyButton.dataset.copyTarget);
          await navigator.clipboard.writeText(source.textContent);
          toast("Copied");
        }

        const openCurrentUrl = target.closest("[data-open-current-url]");
        if (openCurrentUrl) {
          const url = (state.browserEvidence && state.browserEvidence.url) || el("targetUrl").value.trim();
          if (url) window.open(url, "_blank", "noopener,noreferrer");
        }

        const captureActive = target.closest("[data-capture-active-tab]");
        if (captureActive) {
          await captureActiveTab();
        }

        const tab = target.closest("[data-panel]");
        if (tab) {
          if (state.screen !== "run") showRunWorkspace();
          if (state.runId || state.records.length || state.sources.length || state.blocked.length) {
            el("readyPanel").classList.add("hidden");
            el("resultsPanel").classList.remove("hidden");
          }
          qsa("#resultTabs button").forEach((button) => button.classList.remove("active"));
          tab.classList.add("active");
          qsa(".tab-panel").forEach((panel) => panel.classList.add("hidden"));
          el(tab.dataset.panel).classList.remove("hidden");
        }

        const row = target.closest("[data-record-index]");
        if (row) openRecordDrawer(Number(row.dataset.recordIndex));
      });

      el("targetUrl").addEventListener("input", updateDeveloperDetails);
      el("workdir").addEventListener("input", updateDeveloperDetails);
      el("useCase").addEventListener("change", updateUseCaseContract);
      el("clearStartUrl").addEventListener("click", () => { el("targetUrl").value = ""; updateDeveloperDetails(); });
      el("pickDir").addEventListener("click", openNativeDirectoryPicker);
      el("startExecution").addEventListener("click", startRun);
      el("cancelRun").addEventListener("click", cancelRun);
      el("clearRun").addEventListener("click", clearRun);
      qsa("[data-clear-action]").forEach((button) => button.addEventListener("click", clearRun));
      el("closeDrawer").addEventListener("click", () => el("detailDrawer").classList.add("closed"));
      el("returnToActiveRun").addEventListener("click", showRunWorkspace);

      renderOptionChips();
      updateUseCaseContract();
      renderBrowserEvidence({});
      renderRecords();
      renderMetrics();
      updateReadinessPanel();
    </script>
  </body>
</html>"""
