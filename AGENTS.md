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

# [Scout] recent context, 2026-05-21 2:48am EDT

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (17,024t read) | 256,170t work | 93% savings

### May 13, 2026
S381 Get up to speed on Scout skill, evaluate its codebase, fix installation instructions and directory structure issues, enhance it to scrape products for Algolia indexing, and refactor it to be a pure scraper without unnecessary bloat. Work includes brainstorming, planning, documentation, and GitHub updates. (May 13 at 5:05 PM)
S380 Verify if a new scout repository needs to be created on GitHub, and plan migration strategy for Scout standalone package (May 13 at 5:05 PM)
### May 14, 2026
S382 Get up to speed on Scout skill, evaluate its codebase, fix installation instructions and directory structure issues, enhance it to scrape products for Algolia indexing, and refactor it to be a pure scraper without unnecessary bloat. (May 14 at 2:13 AM)
S386 Validate Scout's architectural fit for multiple intelligence-gathering use cases: company research, investor analysis, job applications, prospect research, and social platforms. Confirm appropriate scope and positioning. (May 14 at 2:13 AM)
S389 Comprehensive system testing via internal browser: validate every route, click, and journey through the Scout Intelligence Platform application (May 14 at 7:56 PM)
### May 20, 2026
S390 User needs thorough and exhaustive end-to-end testing to validate all buttons, tabs, and features for two companies (Estee Lauder and Nike) - this is the 5th request for this testing (May 20 at 3:12 PM)
### May 21, 2026
2422 1:36a 🔵 Directory picker implementation uses native HTML5 file input with webkitdirectory
2423 " 🔄 Directory picker refactored from file input to native API call
2425 1:37a ✅ Tests updated to verify API-based directory picker instead of file input
2429 " ✅ Unit test assertions updated to verify API endpoint presence and file input removal
2431 " 🔵 All directory picker tests pass after refactoring to API-based implementation
2432 1:38a 🔵 Live application verification confirms directory picker refactoring is complete
2433 " 🔵 Code quality checks pass but formatting needs to be applied to test file
2437 " 🔵 Directory picker refactoring passes complete quality and test verification
2441 1:43a ⚖️ Scout UI scope: Build all planned screens and use-case-specific form contracts
2442 1:44a 🔵 New UI scope tests fail; navigation controls remain disabled and use-case labels not yet implemented
2443 " ✅ Frontend HTML and CSS updated to enable navigation and add use-case-specific form labels
2444 1:45a ✅ Added utility screen section and dynamic target example element to frontend
2445 " ✅ Added comprehensive use-case contracts, utility screen definitions, and preset/target data to frontend
2446 1:46a ✅ Implemented utility screen navigation and use-case-specific form contracts in JavaScript
2447 " ✅ Wired navigation, utility screen, and utility feature event handlers; completed "All screens now" UI implementation
2448 1:47a 🔵 "All screens now" UI implementation complete: all 9 e2e tests pass
2449 " ✅ Live target tests updated to match refactored frontend DOM and element IDs
2450 1:48a 🔵 Complete implementation verification: all 25 tests pass, zero type/lint/format issues
2451 " 🔵 Test files need ruff formatting after recent edits
2452 1:49a 🔵 Final verification complete: all systems pass, project in clean state
2453 " 🔵 Complete unit test suite passes: 194 tests
2454 1:50a 🔵 Complete test suite passes: 209 tests, 41 skipped (live tests)
2465 2:00a 🔵 Scout UI execution hangs during product crawl workflow test
2466 2:01a 🔴 Scout UI test fixed to handle execution button state transitions
2467 2:02a 🔵 Scout crawl execution completes but returns zero product records for Estée Lauder
2468 2:03a ✅ Scout test assertion simplified to remove redundant status_text check
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
S391 Evaluate Scout skill and plan enhancements to make it a pure web scraper for Algolia product indexing and general intelligence gathering; get up to speed on codebase, identify issues, and prepare fixes (May 21 at 2:44 AM)
**Investigated**: Explored Scout codebase structure and recent changes. Examined:
- Browser mode timeout issue in product scraping (test_estee_lauder_hard_site_modes_from_ui failing with 180s timeout)
- Frontend HTML redesign (app-first UI with topbar, rail, setup pane, workspace, drawer)
- New app_runs router for UI-driven run sessions with event tracking and state management
- New workdir router for directory browsing and macOS native folder picker
- Auth middleware expansion to whitelist public paths for browser-facing UI
- Test suite expansion: E2E tests for UI controls, live tests for 39 real websites
- Documentation: app-first UI design decision, validation results, responsive screenshots
- Project metadata (AGENTS.md) reflecting platform foundation status

**Learned**: Scout has undergone significant architectural transformation from self-educating interface to app-first platform:
- Three-state UX model: Run Setup (configure target/mode/output) → Live Execution (timeline/cancellation) → Results Review (records/sources/evidence)
- Browser mode timeout problem addressed by recording blocked/fallback evidence instead of hanging
- App-runs router manages in-memory run registry with async task execution and 150s watchdog timeout
- Empty product extraction now explicitly tracked as blocked evidence (reason: "no_product_records") instead of silent success
- Frontend uses composite four-column layout: rail (62px) + setup-pane + workspace + drawer for responsive design
- Separation of concerns: new /app/runs API separate from legacy /run and /products endpoints
- Comprehensive test coverage validates UI controls, real websites, and type safety

**Completed**: Scout platform foundation refactored to app-first model with:
- Frontend redesigned: color palette modernized (blue-teal primary), layout changed to four-column grid, all typography/spacing/shadows updated
- App_runs router implemented: AppRunState, AppRunRequest, event streaming, timeout protection, product-specific execution
- Workdir router implemented: directory browsing (/workdir/browse), macOS native picker (/workdir/pick-native)
- Auth middleware expanded: public_paths set now includes /app, /docs, /openapi.json, /favicon.ico, /redoc
- Products mode enhanced: empty extraction now recorded as blocked evidence with reason "no_product_records"
- E2E test suite: 2 comprehensive browser-based UI control tests covering layout, execution, cancellation, record/source/blocked panels
- Live test suite: 39 real-website tests covering 6 product targets (Nike, Estée Lauder, Home Depot, etc.) and 33 intelligence targets (company, PRISM, careers, news, investor)
- Validation documentation: test results (188 unit + 2 E2E + 39 live all passing), type checking clean (Pyright 0 errors), responsive screenshots (desktop, laptop, tablet, mobile)
- AGENTS.md updated: Phase status shows platform execution modes and multi-use-case run surface at FOUNDATION COMPLETE

**Next Steps**: Primary session appears to be in review/documentation phase after major refactor. Likely next steps:
- Prepare GitHub push with all changes (branch: codex/scout-platform-foundation)
- Address original user requests about Scout being too "fat" and needing pure scraper focus
- Evaluate what extra functionality should be removed/simplified
- Prepare product readiness for Algolia indexing workflow
- Plan PRISM integration smoke test


Access 256k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>
