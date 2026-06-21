# SESSION — 2026-06-21

## Status

Scout = **standalone universal acquisition engine** (`scout.core` library + HTTP/MCP service), consumed by PRISM and others. The unblock ladder is built and PROVEN against a real behavioral wall. Branch `codex/scout-platform-foundation`, clean, **269 unit tests green**, through commit `27f296d`.

> NOTE: This file was stale (frozen at Jun 12, said "Phase B next"). That was wrong — Phase B and most of Phase C's hardest slice already shipped. The authoritative arc lives in memory `scout-phased-rebuild-plan.md`. This refresh (Jun 21) reflects true state.

---

## Resume Action (next session, in order)

1. Read this file fully, then memory `scout-phased-rebuild-plan.md` for the full arc + all locked decisions.
2. **Surface the structuring engine in the UI:** the `/app/live-browser` console "Native grab" still renders the raw blob — wire its results panel to show `markdown` + `records` from `/app/browser/capture` (the endpoint already returns them).
3. **Per-listing detail from the cleared native session** (browse-and-harvest: human navigates, Scout structures each cleared page; note the Jun 17 finding that crawl-from-here AUTO-nav re-challenges on PerimeterX).
4. Expose `unblock`/`harvest`/structure as **API endpoints for PRISM**; wire the embedded pane into the main `/app`.

## DONE 2026-06-21 — structured-record extraction (commit `7ce395b`)

**Problem:** the native-grab fallback returned a ~1.2M-char raw-text blob, not structured records.

**Root cause (verified in code):** the native-grab path bypassed Crawl4AI — `capture_active_tab` ([user_browser.py:181](scout/api/user_browser.py:181)) did `page.content()` + `body.inner_text()` via Playwright and returned raw text, never routing it through Scout's own engine. It was a *bypassed-engine* problem, not a missing extractor. See memory `blob-means-bypassed-engine.md`.

**Fix (shipped):** `scout/core/capture_extract.py::structure_capture()` feeds the held HTML back through `AsyncWebCrawler` via the **`raw://` scheme** (crawl4ai 0.7.7 async_crawler_strategy.py:485 — strips prefix, processes bytes, status 200, **no network fetch** → no wall re-trigger). Returns `CaptureExtraction` = clean markdown (default/free) + typed `records` when a CSS or LLM schema is supplied. `/app/browser/capture` now returns `markdown`/`records`/`record_count` for a cleared page and **skips structuring while still blocked**. Tests: 6 unit + 2 integration (real Crawl4AI, `.invalid` host proves no fetch) + 2 API contract. 277 unit green, pyright 0, ruff clean.

## Locked architecture (do not relitigate)

- **Scope boundary** (ADR 2026-06-12): Scout = acquire + extract (verbatim/structured/cited, target-agnostic). PRISM/skills = interpret. Scout never has an opinion.
- **Universal acquisition engine** (ADR 2026-06-14): consumers import Scout; `scout.core` never imports a consumer. Intelligence verticals are CONSUMER specs, not Scout features.
- **Human-assisted rung is the priority** for behavioral walls; unattended crawling of Zillow/LinkedIn-class sites is not achievable by anyone. Confirmed acceptable.
- **Embedded canvas cannot clear behavioral walls** (Jun 18, live): forwarded press-and-hold on the CDP canvas gets the tick but PerimeterX rejects it (CDP input lacks real-OS fidelity). So: embedded pane = viewing + normal/easy sites; **native-window solve REQUIRED for PerimeterX/DataDome press-and-hold**. Native fallback is shipped + reachable.
- **Block detector matches the CHALLENGE, not the vendor SDK** (fix c7c8fbb) — cleared PerimeterX pages still carry `_px`; matching the SDK looped detection forever.

## Proven end-to-end (evidence)

- **Zillow / PerimeterX, Arijit's Mac, 2026-06-17:** `scout unblock` opened real Chrome → Arijit solved press-and-hold → Scout detected cleared + captured **615 real Roswell rentals** (names+prices+beds). First live proof the human-assisted rung beats a real anti-bot wall.
- **Embedded browser, 2026-06-18:** example.com streamed onto the canvas inside the Scout page; Zillow → auto block-banner (vendor=perimeterx); Native solve + Native grab reachable. (`docs/audit/2026-06-14-unblock/embedded-browser-live.png`.)
- **Crawl-from-here live finding (Zillow):** mechanism works, but all 5 detail pages RE-CHALLENGED — PerimeterX scores behavior per-page, so an automated `page.goto` fails even with the cleared cookie. Implication: for PX/DataDome detail pages the HUMAN must navigate (per-page human-assist or browse-and-harvest), not just solve one gate.

## What's built

- `scout/core/blocking.py` (block detection, P1) · `scout/core/acquisition.py` (escalation spine) · T1 stealth wired into `scrape()` (proxy/UA/override_navigator/delay) · `scout/core/human_assisted.py` + `scout unblock` CLI · `scout/core/crawl_from_here.py` · `scout/core/live_browser.py` (CDP screencast engine) · `scout/api/routers/live_browser.py` (WS bridge `/app/live`) · `scout/api/live_browser_page.py` (console `/app/live-browser`) · `scout/api/routers/app_browser.py` (native open/capture).

## What has NOT been done (do not claim otherwise)

- Native grab now returns structured markdown + records from the API, but the `/app/live-browser` console UI still renders the old raw blob — NOT yet wired to show records.
- Embedded pane not yet wired into the main `/app` (lives at `/app/live-browser`).
- NO `unblock`/`harvest` API endpoints for PRISM yet.
- Harvest / crawl-from-cleared-native-session not built.
- Branch NOT pushed; nothing merged to main.
- Known quality bugs deferred: checkout-interstitial junk product records ("Hang Tight!"), duplicate variants, empty brand; API key embedded in `/app` HTML (single-user acceptable); default workdir = repo `tests/`.

## Genuine blockers (need Arijit)

Residential proxy budget · his machine + logged-in sessions for hardest-rung (LinkedIn/Zillow-logged-in) validation · legal/ToS sign-off on LinkedIn capture + job auto-apply.

## How to run

```bash
python3 -m scout.cli serve --port 8421      # app at http://localhost:8421/app ; live browser at /app/live-browser
python3 -m pytest tests/unit -q             # 269 tests
python3 -m pytest tests/e2e -q              # Playwright (starts own server)
python3 -m pyright scout/ && ruff check scout/ tests/
```

## Reference

| Path | Purpose |
|---|---|
| memory `scout-phased-rebuild-plan.md` | Full arc + every locked decision |
| `scout/core/modes/extract.py` | The Crawl4AI extraction machinery the native-grab path should reuse |
| `scout/api/routers/app_browser.py` | Native open/capture endpoints (where the blob is returned) |
| `scout/api/user_browser.py` | `capture_active_tab` — raw HTML/text capture (the bypass) |
| `docs/decisions/` | Scope-boundary, ICP, universal-engine ADRs |
