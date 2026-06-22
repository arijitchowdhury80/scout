"""The embedded-browser console page.

A self-contained page that renders a live Chromium session *inside* the Scout UI
via the /app/live WebSocket: frames are painted to a canvas and the user's
mouse/keyboard on the canvas are forwarded back. This is the "embedded browser,
not a popup" surface. The API key is injected server-side (same pattern as /app).
"""

from __future__ import annotations


def live_browser_page_html(api_key: str) -> str:
    """Return the embedded-browser console HTML with the API key injected."""
    return _PAGE.replace("__SCOUT_API_KEY__", api_key)


_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Scout — Embedded Browser</title>
<style>
  :root { color-scheme: dark; }
  body { margin: 0; background: #09090b; color: #fafafa; font: 14px/1.5 system-ui, sans-serif; }
  header { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,.1); }
  header .brand { font-weight: 700; letter-spacing: .04em; }
  input#url { flex: 1 1 240px; min-width: 0; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.2); color: #fafafa; border-radius: 8px; padding: 8px 12px; font-family: ui-monospace, monospace; }
  button { background: #0C5CAB; color: #fff; border: 0; border-radius: 8px; padding: 8px 14px; font-weight: 600; cursor: pointer; white-space: nowrap; }
  button.secondary { background: rgba(255,255,255,.08); }
  button.native { background: #b45309; }
  .status { padding: 6px 14px; font-size: 12px; color: #9ca3af; border-bottom: 1px solid rgba(255,255,255,.06); }
  #blockbar { display: none; align-items: center; gap: 10px; padding: 10px 14px; background: rgba(245,158,11,.14); border-bottom: 1px solid rgba(245,158,11,.4); color: #fde68a; font-size: 13px; }
  #blockbar button { background: #b45309; }
  #capturedbar { display: none; align-items: center; gap: 10px; padding: 10px 14px; background: rgba(16,185,129,.15); border-bottom: 1px solid rgba(16,185,129,.4); color: #6ee7b7; font-size: 13px; }
  #capturedbar button { background: #047857; }
  .stage { position: relative; }
  #capturedOverlay { display: none; position: absolute; inset: 12px; background: rgba(4,120,87,.92); border-radius: 8px; color: #ecfdf5; align-items: center; justify-content: center; flex-direction: column; gap: 8px; text-align: center; padding: 24px; }
  #capturedOverlay h2 { margin: 0; font-size: 18px; }
  .stage { display: grid; place-items: center; padding: 12px; }
  canvas { background: #101522; border: 1px solid rgba(255,255,255,.12); border-radius: 8px; max-width: 100%; cursor: crosshair; }
  .hint { padding: 8px 14px; font-size: 12px; color: #fcd34d; background: rgba(245,158,11,.08); border-top: 1px solid rgba(245,158,11,.2); }
  pre#out { margin: 0; padding: 10px 14px; font-size: 11px; color: #9ca3af; white-space: pre-wrap; }
</style>
</head>
<body>
  <header>
    <span class="brand">SCOUT</span>
    <input id="url" value="https://example.com" spellcheck="false" />
    <button id="go">Open</button>
    <button id="snap" class="secondary">Capture</button>
    <button id="stop" class="secondary">Stop</button>
    <button id="nativeOpen" class="native" title="Open in your real browser to solve a press &amp; hold">Native&nbsp;solve</button>
    <button id="nativeGrab" class="native" title="Capture the cleared page from your real browser">Native&nbsp;grab</button>
  </header>
  <div class="status" id="status">Idle. Type a URL and press Enter (or click Open).</div>
  <div id="blockbar">
    <span>⚠ This site is blocking automated access (<span id="blockvendor">bot wall</span>). Forwarded clicks won't clear a press &amp; hold — solve it in your real browser.</span>
    <button id="bannerNative">Solve in real browser →</button>
    <button id="bannerGrab" class="secondary">Then grab the page</button>
  </div>
  <div id="capturedbar">
    <span>✓ Captured <b id="capturedtitle"></b> — <span id="capturedrecords" style="display:none"><b id="recordcount">0</b> records, </span><span id="capturedchars">0</span> chars of markdown from your real browser.</span>
    <button id="downloadCapture">Download .md</button>
    <button id="downloadRecords" class="secondary" style="display:none">Download records .json</button>
    <button id="previewCapture" class="secondary">Preview</button>
  </div>
  <div class="stage">
    <canvas id="screen" width="1280" height="800" tabindex="0"></canvas>
    <div id="capturedOverlay">
      <h2>✓ Captured &amp; structured via Crawl4AI</h2>
      <div id="capturedOverlayText"></div>
      <div style="font-size:12px;opacity:.8">(The canvas behind is the separate embedded session — ignore it.)</div>
    </div>
  </div>
  <div class="hint">This browser runs inside Scout. If a site shows a "press &amp; hold" challenge, solve it right here on the canvas. (Hardest behavioral walls may still need the native-window fallback.)</div>
  <pre id="out"></pre>

  <script>
    const KEY = "__SCOUT_API_KEY__";
    const canvas = document.getElementById("screen");
    const ctx = canvas.getContext("2d");
    const statusEl = document.getElementById("status");
    const out = document.getElementById("out");
    let ws = null, frameW = 1280, frameH = 800;

    function setStatus(t) { statusEl.textContent = t; }
    function log(o) { out.textContent = (typeof o === "string" ? o : JSON.stringify(o, null, 2)) + "\\n" + out.textContent; }

    function normalizeUrl(u) {
      u = (u || "").trim();
      if (!u) return "";
      return /^(https?:|about:|data:|file:)/.test(u) ? u : "https://" + u;
    }

    function connect(rawUrl) {
      stop();
      const url = normalizeUrl(rawUrl);
      if (!url) { setStatus("Enter a URL first."); return; }
      document.getElementById("url").value = url;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const proto = location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${location.host}/app/live?key=${encodeURIComponent(KEY)}&url=${encodeURIComponent(url)}`);
      setStatus("Connecting to " + url + " …");
      ws.onopen = () => setStatus("Live: " + url + " (interact on the canvas)");
      ws.onclose = () => setStatus("Disconnected.");
      ws.onerror = () => setStatus("WebSocket error.");
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.kind === "frame") {
          const img = new Image();
          img.onload = () => {
            frameW = img.naturalWidth; frameH = img.naturalHeight;
            if (canvas.width !== frameW) canvas.width = frameW;
            if (canvas.height !== frameH) canvas.height = frameH;
            ctx.drawImage(img, 0, 0);
          };
          img.src = "data:image/jpeg;base64," + msg.data;
        } else if (msg.kind === "blocked") {
          document.getElementById("blockvendor").textContent = msg.vendor || "bot wall";
          document.getElementById("blockbar").style.display = "flex";
        } else if (msg.kind === "cleared") {
          document.getElementById("blockbar").style.display = "none";
        } else if (msg.kind === "error") {
          setStatus("Error: " + msg.message);
        } else {
          log(msg);
        }
      };
    }

    function stop() { if (ws) { try { ws.close(); } catch (e) {} ws = null; } }

    function send(o) { if (ws && ws.readyState === 1) ws.send(JSON.stringify(o)); }

    function coords(e) {
      const r = canvas.getBoundingClientRect();
      return { x: Math.round((e.clientX - r.left) / r.width * frameW),
               y: Math.round((e.clientY - r.top) / r.height * frameH) };
    }

    canvas.addEventListener("mousemove", (e) => { const c = coords(e); send({ kind: "input", event: { type: "mousemove", x: c.x, y: c.y } }); });
    canvas.addEventListener("mousedown", (e) => { const c = coords(e); send({ kind: "input", event: { type: "mousedown", x: c.x, y: c.y, button: "left" } }); canvas.focus(); });
    canvas.addEventListener("mouseup", (e) => { const c = coords(e); send({ kind: "input", event: { type: "mouseup", x: c.x, y: c.y, button: "left" } }); });
    canvas.addEventListener("wheel", (e) => { const c = coords(e); send({ kind: "input", event: { type: "wheel", x: c.x, y: c.y, deltaX: e.deltaX, deltaY: e.deltaY } }); e.preventDefault(); }, { passive: false });
    canvas.addEventListener("keydown", (e) => { send({ kind: "input", event: { type: "keydown", key: e.key, text: e.key.length === 1 ? e.key : "" } }); e.preventDefault(); });
    canvas.addEventListener("keyup", (e) => { send({ kind: "input", event: { type: "keyup", key: e.key } }); });

    document.getElementById("go").onclick = () => connect(document.getElementById("url").value.trim());
    document.getElementById("snap").onclick = () => send({ kind: "snapshot" });
    document.getElementById("stop").onclick = stop;

    // Enter in the URL bar opens (was: had to click Open).
    document.getElementById("url").addEventListener("keydown", (e) => {
      if (e.key === "Enter") connect(document.getElementById("url").value.trim());
    });

    // Native-window fallback for behavioral walls (PerimeterX press & hold)
    // that forwarded canvas input can't clear.
    async function api(path, body) {
      const r = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": KEY },
        body: JSON.stringify(body),
      });
      return r.json();
    }
    async function nativeOpen() {
      const url = normalizeUrl(document.getElementById("url").value);
      setStatus("Opening " + url + " in your REAL browser — solve the press & hold there, then click grab.");
      await api("/app/browser/open", { url });
    }
    let lastCapture = null;
    async function nativeGrab() {
      const url = normalizeUrl(document.getElementById("url").value);
      setStatus("Capturing from your real browser…");
      const res = await api("/app/browser/capture", { url });
      if (res.error) { setStatus("Native capture error: " + res.error); return; }
      if (res.blocked) { setStatus("Still blocked (" + res.vendor + ") — finish the press & hold, then grab again."); return; }
      lastCapture = res;
      document.getElementById("blockbar").style.display = "none";
      document.getElementById("capturedtitle").textContent = res.title || url;
      const mdLen = (res.markdown || "").length;
      document.getElementById("capturedchars").textContent = mdLen;
      if (res.record_count > 0) {
        document.getElementById("recordcount").textContent = res.record_count;
        document.getElementById("capturedrecords").style.display = "inline";
        document.getElementById("downloadRecords").style.display = "inline-block";
      } else {
        document.getElementById("capturedrecords").style.display = "none";
        document.getElementById("downloadRecords").style.display = "none";
      }
      document.getElementById("capturedbar").style.display = "flex";
      const summary = res.record_count > 0
        ? (res.title || url) + " — " + res.record_count + " records, " + mdLen + " chars"
        : (res.title || url) + " — " + mdLen + " chars of markdown";
      document.getElementById("capturedOverlayText").textContent = summary;
      document.getElementById("capturedOverlay").style.display = "flex";
      setStatus("Captured: " + (res.title || url) + (res.record_count > 0 ? " (" + res.record_count + " records)" : " (" + mdLen + " chars)") + " from your real browser.");
    }
    function downloadBlob(content, filename, mime) {
      const blob = new Blob([content], { type: mime });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    }
    document.getElementById("downloadCapture").onclick = () => {
      if (!lastCapture) return;
      downloadBlob(lastCapture.markdown || "", "scout-capture.md", "text/markdown");
    };
    document.getElementById("downloadRecords").onclick = () => {
      if (!lastCapture || !lastCapture.records || !lastCapture.records.length) return;
      downloadBlob(JSON.stringify(lastCapture.records, null, 2), "scout-records.json", "application/json");
    };
    document.getElementById("previewCapture").onclick = () => {
      if (!lastCapture) return;
      const md = lastCapture.markdown || "";
      log(md.slice(0, 8000));
      if (lastCapture.records && lastCapture.records.length) {
        log("--- Records (" + lastCapture.records.length + ") ---");
        log(JSON.stringify(lastCapture.records.slice(0, 20), null, 2));
      }
    };
    document.getElementById("nativeOpen").onclick = nativeOpen;
    document.getElementById("nativeGrab").onclick = nativeGrab;
    document.getElementById("bannerNative").onclick = nativeOpen;
    document.getElementById("bannerGrab").onclick = nativeGrab;
  </script>
</body>
</html>
"""
