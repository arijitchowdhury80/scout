# ADR: Embedded Live Browser via CDP screencast

- **Date:** 2026-06-12
- **Status:** Accepted (Phase B design decision; implementation is Phase C slice C0.6)

## Context

Scout's Capture Workbench shows a static screenshot of an automated capture; its Back/Forward/Refresh controls are disabled placeholders. Blocked or interactive sites (cookie walls, logins, CAPTCHAs, hard WAFs) force an escalation jump straight to the user's real Chrome (User Browser mode). Arijit's requirement (2026-06-12): a browser *inside* Scout — open a site inline, navigate it, crawl it, and screenshot it without leaving the app.

Framing target sites in an iframe is not viable: `X-Frame-Options`/`frame-ancestors` block most commercial sites, and cross-origin iframes expose no DOM or screenshot access anyway.

## Decision

Make Scout's existing server-side Playwright **Chromium session visible and steerable in the UI** via the Chrome DevTools Protocol:

- **Outbound (view):** `Page.startScreencast` emits JPEG frames; a FastAPI WebSocket endpoint (`/app/browser/live/{session_id}`) relays them to a `<canvas>` in the Capture Workbench.
- **Inbound (control):** mouse/keyboard/scroll events on the canvas are forwarded back through the same WebSocket and dispatched via `Input.dispatchMouseEvent` / `Input.dispatchKeyEvent`. URL bar, Back, Forward, Refresh become real controls (`Page.navigate`, history).
- **Session model:** one persistent Playwright context per run (or per workbench session), with a persistent profile directory so cookies/logins survive across runs.
- **Crawl from this session:** a workbench action hands the live, authenticated `BrowserContext` to the products/use-case extractors, so extraction sees exactly what the user unblocked. Screenshots and DOM captures come from the same session and land in the run's evidence artifacts.

This is the pattern used by Browserless and Steel for their embedded browser views.

## Position in the escalation ladder

`crawler → scout-browser (headless capture) → embedded live browser (interactive, this ADR) → user browser (real Chrome via CDP bridge)`

**Honest limitation:** the embedded browser is still automated Chromium. Hardened WAFs (Akamai-class) fingerprint automation regardless of a human at the controls; interaction and a persistent profile improve pass rates but do not guarantee them. The user's real Chrome remains the final escape hatch. The UI must keep saying so.

## Consequences

- Requires WebSocket support in the API layer (auth: same X-API-Key at connect time) — built after C0.3 since it shares streaming infrastructure with SSE run events.
- Frame relay is bandwidth-tolerant at one operator (JPEG quality/fps tunable; pause screencast when the pane is hidden).
- The Capture Workbench mockup (Phase B) is designed around this pane as its centerpiece.
- Future option (explicitly out of scope now): hosting the interactive search-audit testing flow in this pane.

## Rejected alternatives

- **iframe embedding**: blocked by frame-ancestors; no capture access.
- **noVNC + headful browser in a virtual display**: heavier moving parts (Xvfb/VNC server), worse latency, no structural advantage over CDP screencast.
- **Electron/native shell**: changes the product from a self-hosted web service to a desktop app; breaks the `scout serve` deployment story.
