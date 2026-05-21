# Scout UI Full Validation - 2026-05-21

## Summary

This report supersedes the earlier `scout-ui-live-validation-2026-05-21.md`.
The earlier report overstated coverage. This report separates what is actually
verified from what remains product capability work.

## Fresh Verification Results

| Check | Command | Result |
|---|---|---|
| Focused app-run + E2E | `python3 -m pytest tests/unit/api/test_app_runs.py tests/e2e/test_app_ui_exhaustive.py -q` | 15 passed |
| Live UI target matrix | `SCOUT_LIVE_TESTS=1 python3 -m pytest tests/live/test_app_live_targets.py -v` | 39 passed in 364.53s |
| Full E2E | `python3 -m pytest tests/e2e/test_app_ui_exhaustive.py -v` | 11 passed |
| Unit suite | `python3 -m pytest tests/unit/ -v` | 195 passed |
| Full suite | `python3 -m pytest tests/ -v` | 212 passed, 41 skipped |
| Pyright | `python3 -m pyright scout/` | 0 errors, 0 warnings |
| Ruff check | `ruff check scout/ tests/` | All checks passed |
| Ruff format check | `ruff format --check scout/ tests/` | 113 files already formatted |

## Deterministic UI Coverage

The E2E suite now validates the app shell and core interactions through `/app`:

- Run Setup, Live Execution, and Results Review surfaces.
- Start Execution creates a visible run immediately.
- Cancel Run and Clear Run update UI state.
- Target URL clear button clears the field and command preview.
- Native directory picker endpoint updates one workdir field.
- Cancelled folder selection does not open a secondary dialog.
- Crawl Settings chips are removable/restorable.
- Developer Details is collapsed by default and copyable.
- Top nav and left rail utility screens switch to visible screens.
- Use-case dropdown changes labels, helper copy, expected outputs, and payload.
- Result tabs switch visible panels.
- Visible enabled controls are inventoried and must be classified.

The generated control manifest is produced by
`test_visible_enabled_controls_are_classified` in the pytest temp output. It is
not committed as a permanent artifact because it is runtime evidence.

## Live Target Results

| Use Case | Target | Mode | Status | Records | Sources | Citations | Blocked | Artifacts | Run ID |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| products | Estée Lauder | auto | success | 0 | 1 | 0 | 1 | 1 | app_run_bce69c26218f |
| products | Lacoste | auto | success | 10 | 1 | 10 | 1 | 1 | app_run_bdc00627234b |
| products | Nike | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_83e88ba82b53 |
| products | L.L.Bean | auto | success | 10 | 1 | 10 | 1 | 1 | app_run_d0731b2857e9 |
| products | Patagonia | auto | success | 0 | 1 | 0 | 1 | 1 | app_run_c93d61844c86 |
| products | Home Depot | auto | success | 0 | 1 | 0 | 1 | 1 | app_run_40f139a2f08a |
| company | Algolia | auto | success | 3 | 1 | 3 | 1 | 1 | app_run_b14603caa723 |
| company | Constructor | auto | success | 3 | 1 | 3 | 1 | 1 | app_run_c094ede34346 |
| company | Adobe | auto | success | 3 | 1 | 3 | 1 | 1 | app_run_73c17dd51443 |
| company | Home Depot | auto | success | 3 | 1 | 3 | 1 | 1 | app_run_1713cbb2d05b |
| company | Nike | auto | success | 3 | 1 | 3 | 1 | 1 | app_run_5e44e989cba7 |
| company | British Airways | auto | success | 3 | 1 | 3 | 1 | 1 | app_run_07dac7befcda |
| company | Estée Lauder | auto | success | 3 | 1 | 3 | 1 | 1 | app_run_f68ff7520a82 |
| prism | Algolia | auto | success | 6 | 1 | 6 | 1 | 1 | app_run_dbaeb28b2317 |
| prism | Constructor | auto | success | 6 | 1 | 6 | 1 | 1 | app_run_c3f43d92ecb6 |
| prism | Adobe | auto | success | 6 | 1 | 6 | 1 | 1 | app_run_8a8911a3321b |
| prism | Home Depot | auto | success | 6 | 1 | 6 | 1 | 1 | app_run_57b486f88e28 |
| prism | Nike | auto | success | 6 | 1 | 6 | 1 | 1 | app_run_10bbcd3ac898 |
| prism | British Airways | auto | success | 6 | 1 | 6 | 1 | 1 | app_run_8d3dcd68cb18 |
| prism | Estée Lauder | auto | success | 6 | 1 | 6 | 1 | 1 | app_run_ecdcf009a6e5 |
| careers | Algolia | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_0f4168f10517 |
| careers | Constructor | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_677f196b4b43 |
| careers | Adobe | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_6fc8319ec11c |
| careers | Home Depot | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_5c21958be69a |
| careers | Nike | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_fd3e7ae1b10e |
| careers | British Airways | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_f950e5dc6bad |
| careers | Estée Lauder | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_aafe27eac0c7 |
| news | Algolia | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_269c46211547 |
| news | Constructor | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_9f875716cb2e |
| news | Adobe | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_67b694a82451 |
| news | Home Depot | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_286cc8d09c2f |
| news | Nike | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_c4136ca08b90 |
| news | British Airways | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_8a5ad914ba9e |
| news | Estée Lauder | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_f329fbd739c7 |
| investor | Adobe | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_f5c71a7c5287 |
| investor | Home Depot | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_5a43d66ba020 |
| investor | Estée Lauder | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_7d195bb4cee3 |
| investor | British Airways | auto | success | 1 | 1 | 1 | 1 | 1 | app_run_cb40cdf66fef |
| products hard-site | Estée Lauder | auto | success | 0 | 1 | 0 | 1 | 1 | app_run_7414b5c7548e |
| products hard-site | Estée Lauder | crawl4ai | success | 0 | 1 | 0 | 1 | 1 | app_run_f05d9903e4fb |
| products hard-site | Estée Lauder | browser | blocked_with_evidence | 0 | 1 | 0 | 1 | 1 | app_run_4c2f279031a3 |

## What Passed

- The live UI matrix ran through `/app`, not direct backend-only calls.
- Every live run produced a run ID.
- Every live run exposed artifact visibility in the UI.
- Product runs either produced product records or blocked/fallback evidence.
- Estée Lauder browser mode no longer launches unmanaged pop-up browser windows;
  it records explicit blocked/fallback evidence and artifacts.

## Known Gaps

- The live tests prove workflow mechanics, artifacts, source/citation presence,
  and blocked evidence. They do not prove deep semantic quality for every field.
- Product extraction for Estée Lauder, Patagonia, and Home Depot currently passed
  via blocked/fallback evidence rather than product records.
- Workflow-specific high-fidelity visual mockup images have not been generated
  for every use case. The workflow spec pages and approved base mockup now define
  the contract for the next UI build pass.

## Browser Workbench Recovery Addendum

Added after the app recovery pass on 2026-05-21:

- Backend `scout-browser` mode now launches a Playwright-controlled browser and captures screenshot, DOM, rendered text, links, console errors, and network failures.
- The Browser Workbench now occupies the primary live-execution workspace instead of a small placeholder card.
- Active runs survive navigation through the global Active Run banner and `Return to Run` action.
- Rail labels are widened and verified not to clip.
- User Browser mode is represented as a future Chrome CDP / browser-extension bridge and does not pretend to access the user's browser session yet.

Fresh verification performed for this addendum:

| Check | Result |
|---|---|
| `python3 -m pytest tests/e2e/test_app_ui_exhaustive.py -q` | 14 passed |
| `python3 -m pytest tests/unit/api/test_app_runs.py tests/unit/api/test_app_frontend.py -q` | 12 passed |
| `SCOUT_LIVE_TESTS=1 python3 -m pytest tests/live/test_app_live_targets.py -q` | 39 passed |
| `python3 -m pytest tests/ -q` | 216 passed, 41 skipped |
| `python3 -m pyright scout/api/routers/app_runs.py` | 0 errors |
| `ruff check scout/api/routers/app_runs.py scout/api/frontend.py tests/unit/api/test_app_runs.py tests/unit/api/test_app_frontend.py tests/e2e/test_app_ui_exhaustive.py` | passed |
| Estée Lauder `scout-browser` smoke via `/app/runs` | failed with explicit blocked evidence, screenshot, DOM/text/link artifacts |

Estée Lauder hard-site evidence from the smoke run:

- Status: `failed`
- Reason: `scout_browser_access_denied`
- Browser evidence: screenshot captured
- Artifacts written: `manifest.json`, `records.json`, `source_pages.json`, `blocked_pages.json`, `extraction_report.md`, `browser/screenshot.png`, `browser/dom.html`, `browser/text.txt`, `browser/links.json`

## Screenshots And Visual Evidence

- `docs/design/scout-app-first-ux-approved-mockup-2026-05-21.png`
- `docs/validation/screenshots/scout-ui-desktop-2026-05-21.png`
- `docs/validation/screenshots/scout-ui-laptop-2026-05-21.png`
- `docs/validation/screenshots/scout-ui-tablet-2026-05-21.png`
- `docs/validation/screenshots/scout-ui-mobile-2026-05-21.png`
- `docs/validation/screenshots/scout-ui-run-complete-2026-05-21.png`

## Vault Updates

The Scout vault was updated under `Projects/Scout/`:

- `index.md` normalized as the canonical project map.
- `wiki/ux/workflows/` populated with workflow specs.
- `wiki/decisions/2026-05-21-app-first-validation-gate.md` added.
- `wiki/dev-log.md` and `log.md` updated.
- Loose legacy design/spec files moved to `wiki/sources/legacy/`.
- Approved mockup saved to `raw/assets/`.
