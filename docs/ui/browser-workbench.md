# Scout Browser Workbench Recovery Slice

Date: 2026-05-21

## Decision

Scout's app surface now treats browser evidence as the primary workspace during product runs, not as a small placeholder card. The UI distinguishes three browser/session concepts:

- **Crawler session**: the default Crawl4AI-backed acquisition path.
- **Scout browser session**: a Playwright-controlled browser launched by Scout to capture screenshot, DOM, rendered text, links, console errors, and network failures.
- **User browser session**: a future CDP or browser-extension bridge for pages that are visible in the user's own browser but blocked in Scout's isolated session.

## What Changed

- `scout-browser` mode launches Playwright, navigates to the target URL, and writes browser evidence under the selected output directory.
- If the Scout Browser capture sees an access-denied or blocked page, the run is marked failed with explicit blocked/fallback evidence instead of silently succeeding.
- The app shell keeps active runs persistent through navigation and shows an Active Run banner with a return action.
- The left rail is wider so labels such as `Integrations` do not clip.
- Live execution uses a larger Browser Workbench area with screenshot-capable evidence rendering, run timeline, and event log.

## Current Product Behavior

For Estée Lauder hard-site testing, Scout Browser can capture evidence but receives an access-denied page from the isolated Scout browser session. This is now represented as:

- a blocked page entry,
- a blocked source entry,
- a browser screenshot artifact,
- DOM/text/link artifacts,
- a visible failed run status with evidence preserved.

This does not yet solve product extraction from Estée Lauder when bot protection blocks Scout's own browser session. The next step for that exact case is User Browser mode through Chrome CDP or a browser-extension bridge.

## Deferred Work

- Interactive browser controls (`Back`, `Forward`, `Refresh`, `Capture`, `Extract`, `Save Evidence`) are visible but intentionally disabled with explanatory tooltips until the browser session control API is added.
- DOM-to-product extraction from Scout Browser evidence is not complete yet.
- User Browser mode is represented honestly as bridge-required; it does not yet connect to Chrome/CDP or an extension.
