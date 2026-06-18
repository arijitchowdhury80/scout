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
  header { display: flex; gap: 8px; align-items: center; padding: 10px 14px; border-bottom: 1px solid rgba(255,255,255,.1); }
  header .brand { font-weight: 700; letter-spacing: .04em; }
  input#url { flex: 1; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.2); color: #fafafa; border-radius: 8px; padding: 8px 12px; font-family: ui-monospace, monospace; }
  button { background: #0C5CAB; color: #fff; border: 0; border-radius: 8px; padding: 8px 14px; font-weight: 600; cursor: pointer; }
  button.secondary { background: rgba(255,255,255,.08); }
  .status { padding: 6px 14px; font-size: 12px; color: #9ca3af; border-bottom: 1px solid rgba(255,255,255,.06); }
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
  </header>
  <div class="status" id="status">Idle. Enter a URL and click Open.</div>
  <div class="stage"><canvas id="screen" width="1280" height="800" tabindex="0"></canvas></div>
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

    function connect(url) {
      stop();
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
  </script>
</body>
</html>
"""
