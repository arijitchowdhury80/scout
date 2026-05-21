# AGENTS.md — Scout Project

## What This Is

Scout is a self-hosted web intelligence platform built on Crawl4AI. It replaces Apify in PRISM's intel modules and serves as a general-purpose crawler for Codex and other tools.

## Resume Context

- **SESSION.md** — current task, exact resume action, all decisions, remaining work
- **Memory** — `~/.Codex/projects/-Users-arijitchowdhury-AI-Development-PIP/memory/`
- **Workspace** — `docs/workspace/scout-core/` — PRD (with acceptance criteria), pre-mortem, strategy

## Hard Constraints

1. **workflow-build-module skill FIRST** — never build before Phase 1 thinking docs exist
2. **TDD always** — tests before implementation, RED before GREEN
3. **Three test layers required** — unit + integration + contract before component is "done"
4. **No raw dicts crossing boundaries** — Pydantic on every response
5. **pyright must be clean** — run `python3 -m pyright scout/` before committing
6. **structlog** — approved structured logger; stdout only (no file logging Phase 1)
7. **FastAPI DI** — ScoutCrawler is lifespan singleton injected via `Depends(get_crawler)` in `deps.py`
8. **Smoke test before PRISM integration** — HTTP stack must pass AC-1 through AC-8 first

## Verification

```bash
python3 -m pytest tests/unit/ -v          # 70 tests, fast
python3 -m pytest tests/ -v               # +6 integration (needs network)
python3 -m pyright scout/                 # 0 errors required
ruff check scout/ && ruff format --check scout/
```

## Phase Status

- Phase 1 core library: **COMPLETE**
- Phase 1 API layer: **COMPLETE**
- Phase 1 Docker: **COMPLETE**
- Phase 2 Codex skill file: **COMPLETE** (not yet registered)
- Platform execution modes: **FOUNDATION COMPLETE**
- Multi-use-case run surface: **FOUNDATION COMPLETE** for CLI + HTTP + skill docs
- **Smoke test: PENDING** ← do this next
- **PRISM Phase 4 integration: PENDING** ← main goal, after smoke test

## Current Platform Direction

Scout is not only a product scraper or job hunter. Treat it as a reusable web
intelligence platform with vertical processors for company, PRISM, investor,
careers, jobs, products, news, and generic research. All high-level runs must
preserve the standard artifact contract:

```text
manifest.json
records.json
records.jsonl
source_pages.json
blocked_pages.json
validation.json
extraction_report.md
```

Supported execution modes are `auto`, `crawl4ai`, `webfetch`, `websearch`,
`browser`, `saved`, and `api`. Browser fallback is secondary and should only be
used when regular acquisition is blocked, sparse, JS-heavy, or explicitly being
verified.

Private job profiles, resume-derived preferences, API tokens, and personal
research profiles stay in vault-backed or ignored local files. Public examples
must use sanitized fixtures.

## Reference Artifacts

| Path | Purpose |
|---|---|
| `docs/workspace/scout-core/04-prd.md` | Acceptance criteria AC-1 through AC-12 |
| `docs/workspace/scout-core/05-pre-mortem.md` | Risks — T3 Docker, T5 FastAPI DI |
| `scout/core/types.py` | All Pydantic contracts — change here first |
| `scout/api/deps.py` | `get_crawler()` dependency — import this for test overrides |
| `scout/skill/scout.md` | Codex skill definition |


<claude-mem-context>
# Memory Context

# [Scout] recent context, 2026-05-22 12:00am EDT

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (14,852t read) | 248,157t work | 94% savings

### May 13, 2026
S381 Get up to speed on Scout skill, evaluate its codebase, fix installation instructions and directory structure issues, enhance it to scrape products for Algolia indexing, and refactor it to be a pure scraper without unnecessary bloat. Work includes brainstorming, planning, documentation, and GitHub updates. (May 13 at 5:05 PM)
S380 Verify if a new scout repository needs to be created on GitHub, and plan migration strategy for Scout standalone package (May 13 at 5:05 PM)
### May 14, 2026
S382 Get up to speed on Scout skill, evaluate its codebase, fix installation instructions and directory structure issues, enhance it to scrape products for Algolia indexing, and refactor it to be a pure scraper without unnecessary bloat. (May 14 at 2:13 AM)
S386 Validate Scout's architectural fit for multiple intelligence-gathering use cases: company research, investor analysis, job applications, prospect research, and social platforms. Confirm appropriate scope and positioning. (May 14 at 2:13 AM)
S389 Comprehensive system testing via internal browser: validate every route, click, and journey through the Scout Intelligence Platform application (May 14 at 7:56 PM)
### May 20, 2026
S390 User needs thorough and exhaustive end-to-end testing to validate all buttons, tabs, and features for two companies (Estee Lauder and Nike) - this is the 5th request for this testing (May 20 at 3:12 PM)
S391 Evaluate Scout skill and plan enhancements to make it a pure web scraper for Algolia product indexing and general intelligence gathering; get up to speed on codebase, identify issues, and prepare fixes (May 20 at 4:44 PM)
### May 21, 2026
2470 2:05a 🔴 Scout Estée Lauder test now passes after assertion correction
2490 2:16a 🔵 Estée Lauder product page crawl fails with Playwright timeout
2491 " 🔴 Add timeout handling for product extraction with graceful failure recording
2493 " ✅ Update test expectations to recognize timeout as blocked_with_evidence status
2495 2:17a 🔵 Unit and E2E tests pass after timeout handling implementation
2505 2:19a 🔵 Estée Lauder product crawl test now passes with timeout handling
2531 2:29a 🔵 Scout timeout failure on Estée Lauder hard site product scraping
2532 2:30a 🟣 Scout app-run watchdog timeout mechanism
2541 2:40a 🔵 Scout test suite has Playwright timeout on Estée Lauder product scraping
2542 2:41a 🔴 Scout adds explicit browser mode timeout handling in product scraping
2543 2:43a 🔄 Scout frontend redesigned to app-first composite layout
2544 " 🟣 Scout API adds app_runs and workdir routers for UI workflow support
2545 " ✅ Scout products mode tracks empty product evidence instead of silent success
2546 " ✅ Scout project metadata and agents documentation updated
2547 " ✅ Scout test suite expanded with e2e, live, and app-runs unit tests
2548 " ✅ Scout documentation expanded with UI validation, design, and internal browser validation
2549 " ✅ Scout middleware and main app configuration updated for app platform
2550 2:44a 🟣 Scout auth middleware expanded with public path whitelist for app UI
2551 " 🟣 Scout implements app_runs router for UI-driven run session lifecycle
2552 " 🟣 Scout implements workdir router for directory browsing and native folder picker
2553 " 🟣 Scout implements comprehensive E2E tests for app-first UI controls
2554 " 🟣 Scout implements live website UI tests covering 39 real targets
2555 " ⚖️ Scout adopts app-first UI as primary product surface
2556 " 🔵 Scout validation shows 188 unit tests, 2 E2E, 39 live tests passing with clean type checks
2557 2:50a ✅ Scout UI workflow specifications documented for all 10 use cases and utility screens
2574 3:53a 🔵 No test execution evidence in validation workflow
2575 3:56a 🔵 Frontend execution flow examined but not invoked
2576 " ✅ Frontend UX improvement for missing URL validation
2577 " 🟣 Added e2e test for missing URL validation behavior
2578 3:57a ✅ Scout server restarted with updated frontend code
2579 " 🔵 Modified validation code confirmed in served frontend
2580 " 🔵 E2E tests execute successfully; inline validation verified
2581 " 🔵 End-to-end app-first Scout execution validated; complete run with extracted records
2582 3:58a 🔵 Second end-to-end validation run confirms stability
2583 " ✅ Session changes summarized in git diff
2584 " 🔵 Complete e2e test suite passes; all 8 UI validation tests successful
2585 " 🔵 Code quality checks pass; modified files meet style standards
2586 " 🔵 Expanded test suite passes; 12 total tests validated
2587 " ✅ Frontend validation improvement committed and pushed
2588 " ✅ Changes successfully pushed to GitHub repository
2589 4:03a 🔵 Working Directory Browse Default Path Configuration
2590 " ✅ Working Directory Default Path Updated
2591 " 🔵 Test File Structure Mismatch for Workdir Assertion
2592 " ✅ Test Assertion Added for Workdir Default Path
2593 4:04a 🔵 Workdir Default Path Changes Pass Test Suite
2594 " ✅ Scout Server Started with Updated Workdir Default
2595 " 🔵 Live Server Verification: Workdir Default Path Active
2596 " 🔵 Browser-Based Verification: Workdir Default Value in DOM
2597 4:05a ✅ Workdir Default Path Changes Committed and Deployed
2598 " 🔵 Changes Successfully Pushed to Remote Repository
S392 Change the app's default working directory from /tmp/scout-runs/app to /Users/arijitchowdhury/AI-Development/Scout/tests (May 21 at 4:07 AM)
**Investigated**: Examined workdir browsing implementation across scout/api/routers/workdir.py, scout/api/frontend.py, and related test files to understand how the default path is set and used in the frontend UI

**Learned**: The workdir input field (#workdir) in the frontend has a hardcoded default value attribute. The backend endpoint /workdir/browse defaults to home directory (~), but the frontend HTML renders the input element with its own default. Changing the HTML input value attribute directly updates what users see when the app loads

**Completed**: Modified scout/api/frontend.py to change the workdir input default value to /Users/arijitchowdhury/AI-Development/Scout/tests; added test assertion in tests/unit/api/test_app_frontend.py to verify the new default is rendered; verified all tests pass (8 passed), ruff checks pass, and code formatting is correct; started Scout server on http://127.0.0.1:8421; verified via HTTP and Playwright that the workdir field displays the new default; committed and pushed changes to branch codex/scout-platform-foundation (commit 72461c4)

**Next Steps**: Session work is complete. The server is currently running on port 8421 with the updated frontend. AGENTS.md remains locally modified from session context but was not committed as it was not part of the requested change

S393 Build Scout Browser Workbench recovery slice and update vault with latest project status (May 22 at 12:00 AM)
**Investigated**: Reviewed the app-first UI regressions around tiny browser evidence, stale live status, active run loss during navigation, clipped rail labels, and Estée Lauder hard-site behavior. Checked `scout/api/frontend.py`, `scout/api/routers/app_runs.py`, E2E tests, live UI tests, and the Scout vault structure under `Projects/scout`.

**Learned**: A normal web app cannot literally embed a native browser process, but Scout can run a Playwright-controlled browser and render captured screenshot/DOM/text/network evidence in the app. Estée Lauder still blocks Scout's isolated browser session with Access Denied, even though a user's normal browser may view the page. That requires a future User Browser bridge through Chrome CDP or a browser extension.

**Completed**: Implemented `scout-browser` mode with Playwright screenshot, DOM, text, links, console error, network failure, status-code, and metadata capture. Updated app UI so Browser Workbench is the primary live-execution area, added Active Run banner persistence through navigation, widened the rail, and renamed browser session concepts to Crawler session / Scout browser session / User browser session. Access-denied browser captures now produce failed blocked evidence with artifacts instead of silent success. Updated tests and validation docs. Verification passed: E2E 14/14, live UI matrix 39/39, unit 196/196, full suite 216 passed with 41 skipped, Pyright 0 errors, Ruff check/format passed. Committed and pushed `e585042` to `codex/scout-platform-foundation`.

**Vault Updated**: Added Scout vault ADR `wiki/decisions/2026-05-22-browser-workbench-session-modes.md`, UX note `wiki/ux/browser-workbench-recovery-2026-05-22.md`, status synthesis `wiki/syntheses/current-status-2026-05-22.md`, and updated `index.md`, `log.md`, `wiki/dev-log.md`, and `wiki/open-questions.md`.

**Next Steps**: Build User Browser Capture V1: Chrome CDP or extension bridge, explicit consent/security state, active-tab screenshot/DOM/text capture, app endpoints, and then browser-DOM product parsing into `product.v1` records.


Access 248k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>
