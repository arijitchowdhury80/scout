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
- **Smoke test: PENDING** ← do this next
- **PRISM Phase 4 integration: PENDING** ← main goal, after smoke test

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

# [Scout] recent context, 2026-05-14 10:11am EDT

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (20,400t read) | 185,979t work | 89% savings

### May 13, 2026
S381 Get up to speed on Scout skill, evaluate its codebase, fix installation instructions and directory structure issues, enhance it to scrape products for Algolia indexing, and refactor it to be a pure scraper without unnecessary bloat. Work includes brainstorming, planning, documentation, and GitHub updates. (May 13 at 5:05 PM)
S380 Verify if a new scout repository needs to be created on GitHub, and plan migration strategy for Scout standalone package (May 13 at 5:05 PM)
1351 6:56p ✅ Artifacts module updated: blocked_pages.json writing and report enrichment complete
1353 6:57p ✅ REFACTOR complete: deduplication bug fixed, all 5 core tests passing
1354 " 🔵 Complete test suite passes: 36/36 tests green for fallback ladder implementation
1355 " ✅ Documentation updated: fallback ladder strategy and Estee Lauder hard-site example
1356 " 🔵 Verification suite results: 106/106 tests pass, ruff clean, pyright reports 2 type errors
1357 " 🔴 Type safety: added None guard in listing parser before accessing optional attributes
1358 6:58p 🔵 All verification gates pass: 106 tests, pyright strict, ruff clean, format complete
1359 " 🔵 FINAL VERIFICATION: All gates pass—product blocked-page fallback feature complete and production-ready
### May 14, 2026
1360 12:30a 🔵 Scout live crawl reveals extraction gaps for product data
1361 " 🔵 Scout URL tracking captures only category pages, not explored sub-pages
1362 " 🔵 Scout map command finds zero product URLs despite 22 sitemap URLs available
1363 " 🔄 Scout test suite updated to reject product-catalog category links as non-products
1364 12:31a 🔵 Scout extraction logic does not yet filter product-catalog navigation links
1365 " 🔴 Scout extraction logic now filters product-catalog CTA links and validates product cards
1366 " 🔴 Scout product extraction tests now pass with CTA and product-catalog filtering
1367 " 🔵 Scout live crawl shows improved extraction quality after product-catalog filtering fix
1368 " 🟣 Scout extraction tests enhanced with context-aware product card filtering
1369 12:32a 🔵 Scout extraction does not yet implement context-aware product link filtering
1370 " 🟣 Scout implements context-aware HTML filtering for product link extraction
1371 " 🔴 Scout context-aware extraction passes all product listing tests
1372 " 🔵 Scout context-aware filtering validates without regression on esteelauder.com
1373 " 🟣 Scout adds dual-context filtering with nav-context detection
1374 12:33a 🔵 Scout nav-context filtering patch application failed
1375 " 🟣 Scout nav-context filtering successfully implemented with dual-stack approach
1376 " 🔴 Scout dual-stack nav-context filtering passes all test cases
1377 " 🔵 Scout nav-context filtering over-rejects product extraction on live site
1378 " 🔵 Unit test infrastructure issue: AsyncMock not JSON serializable in artifact writing
1380 " 🔴 All unit tests passing after test fixture update
1381 12:34a 🔵 Scout product extraction delivers high-quality records on Lacoste.com
1382 " 🟣 Scout product feature types and contracts fully defined and tested
1383 12:35a 🟣 Scout product extraction feature implementation complete with comprehensive testing and validation
S382 Get up to speed on Scout skill, evaluate its codebase, fix installation instructions and directory structure issues, enhance it to scrape products for Algolia indexing, and refactor it to be a pure scraper without unnecessary bloat. (May 14 at 2:13 AM)
1384 2:14a 🟣 Scout products scraping feature implementation and documentation overhaul
1385 " ✅ New documentation and configuration files created
1386 " 🟣 Product-focused test suite added for live retail site validation
1387 2:22a 🟣 Browser fallback testing implemented as secondary channel after regular scrape blocking
1388 " 🔵 Test failures reveal missing type model fields for browser fallback feature
1389 " 🟣 Browser fallback implementation completed in type models and products mode
1390 " 🟣 Browser fallback feature validated: all tests passing
1391 2:23a ✅ CLI and documentation updated for browser fallback feature
1392 " 🔵 Ruff format check identifies test file formatting needed
1393 " 🔵 Test suite: 1 failed due to browser fallback mock exhaustion
1394 " 🔴 Test fixed: disabled browser fallback for existing blocked-page test
1395 " 🔵 Syntax error: indentation mismatch in test_products.py after browser_fallback patch
1396 " 🔴 Indentation corrected in test_products_skips_blocked_product_pages
1397 " 🔵 Indentation error persists: resp = await products still misaligned
1398 2:24a 🔵 Ruff format cannot repair indentation: file has unparseable syntax
1399 " 🔵 Code quality checks now passing: syntax and format validated
1400 " 🟣 Browser fallback feature complete and fully validated
1401 10:08a 🔵 Uncommitted Changes and Untracked Files in Scout Repository
1402 " 🔵 Untracked Documentation and Feature Files Require Git Integration

Access 186k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>