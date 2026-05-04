# Scout Core — Pre-Mortem

Assume Scout ships Phase 1 and fails. What went wrong?

---

## Tigers (Real Risks — Evidence-Based)

### 🔴 T1: Crawl4AI API surface doesn't match implementation (LAUNCH-BLOCKING)
**What**: `fit_markdown`, `arun_many()` iteration pattern, `CrawlerRunConfig` field names — all were written against documentation without running against the installed package. At least one will be wrong.
**Evidence**: The implementation uses `getattr(result, "fit_markdown", None)` — a defensive fallback that signals uncertainty at write time. `async for result in await crawler.arun_many(...)` is an unusual double-await pattern.
**Impact**: All modes silently return empty content or throw at runtime. Docker smoke test fails immediately.
**Classification**: Launch-Blocking
**Mitigation**: Before building the API layer, run a smoke test against a real URL with the installed Crawl4AI package. Verify exact attribute paths and async patterns.
**Owner**: Builder
**Decision Date**: Before Task #12 (API) begins

---

### 🔴 T2: Missing test layers — integration + contract tests absent (LAUNCH-BLOCKING)
**What**: TestingSOPs require 3 layers (unit, integration, contract). Only unit tests exist. "Module not done until all three layers present."
**Evidence**: `tests/integration/` directory exists but is empty. No contract tests anywhere.
**Impact**: Code passes unit tests but fails against real Crawl4AI at runtime. Silent regressions when Crawl4AI upgrades.
**Classification**: Launch-Blocking (per TestingSOPs Definition of Done)
**Mitigation**: Build integration tests for all 5 modes + API layer. Build contract tests verifying Pydantic model shapes.
**Owner**: Builder
**Decision Date**: Must be done before Phase 1 is declared complete

---

### 🟡 T3: Docker Playwright startup fails (FAST-FOLLOW)
**What**: Playwright in headless Docker requires `--shm-size=1g` and potentially `--cap-add=SYS_ADMIN` for sandboxing. Standard Docker config won't have this.
**Evidence**: This is a known Playwright-in-Docker issue. Crawl4AI's own Docker setup docs mention it.
**Impact**: `docker compose up` starts, health check passes, but any crawl with `use_js=True` (the default) throws a browser crash.
**Classification**: Fast-Follow (affects Docker delivery, not core library)
**Mitigation**: Research Crawl4AI's own Dockerfile — copy their exact browser configuration. Test `docker compose up && curl /scrape` as part of AC-11.
**Owner**: Builder
**Decision Date**: During Task #13 (Docker)

---

### 🟡 T4: SOP violations in existing code require non-trivial refactoring (FAST-FOLLOW)
**What**: CodingSOPs require: (a) docstring on every public function, (b) try/catch with specific exception types first, (c) `pyright --strict` clean. Current code has module-level docstrings but no function-level docstrings, catches bare `Exception` as first catch, and pyright hasn't been run.
**Evidence**: Reviewed scrape.py, crawl.py, extract.py — all catch `except Exception as exc` as the primary (and only) handler. No function docstrings. `import logging` SOP vs `import structlog` in implementation.
**Impact**: Code review fails. PR blocked at merge gate.
**Classification**: Fast-Follow (doesn't block functionality; blocks standards compliance)
**Mitigation**: SOP validation pass (Task #20) catches and fixes all violations before continuing.
**Owner**: Builder
**Decision Date**: Task #20 (SOP validation) runs before Task #12 begins

---

### 🟡 T5: `ScoutCrawler` not injectable / testable at API layer (FAST-FOLLOW)
**What**: The API layer needs to inject `ScoutCrawler` as a dependency (so tests can mock it). If it's constructed inside each route handler, it can't be overridden in tests.
**Evidence**: FastAPI dependency injection pattern requires the crawler to be a lifespan-managed singleton, not constructed per-request.
**Impact**: API layer unit tests can't mock the crawler → forced to use real Crawl4AI in API tests → slow, fragile, requires real network.
**Classification**: Fast-Follow (design issue in API layer — not yet built)
**Mitigation**: Task #12 (API) must use FastAPI lifespan + `Depends()` injection pattern from the start. Write the API tests first to validate the DI contract.
**Owner**: Builder
**Decision Date**: Task #12 design

---

## Paper Tigers (Sounds Scary, Won't Happen)

### PT1: Crawl4AI is abandoned / goes AGPL
**Why overblown**: 65k GitHub stars, actively maintained, MIT license hardcoded in pyproject.toml. Even if they change license, our vendored version is already MIT. Version pin isolates us from upstream changes.

### PT2: Scout can't handle JS-heavy sites
**Why overblown**: Crawl4AI uses stealth Playwright for JS rendering. `use_js=True` enables full browser. Not perfect (Cloudflare will still block), but better than anything else we'd self-host.

### PT3: Pydantic v2 model contracts will break between versions
**Why overblown**: Pydantic v2 is stable. `model_config = {"frozen": True}` on ScoutMetadata prevents mutation bugs. If we upgrade Pydantic, tests catch regressions.

---

## Elephants (Nobody's Discussing This)

### E1: Token estimate quality
**What**: `len(text) // 4` is a rough estimate. For Asian-language content or code-heavy pages, this can be off by 3x. PRISM modules may make LLM call budgeting decisions based on this number.
**Investigation needed**: Check whether PRISM intel modules use `token_estimate` for anything beyond display. If they use it to decide whether to truncate before an LLM call, we need a better estimate (tiktoken is already in pyproject.toml).

### E2: Multi-domain crawl scope
**What**: `include_external=False` in CrawlRequest means BFS won't follow links that leave the start domain. But some company sites redirect to subdomains (e.g., `careers.nike.com` from `nike.com/careers`). These would be treated as external and dropped.
**Investigation needed**: Test intel_hiring's typical career page URLs. If `careers.subdomain.com` patterns are common, the default `include_external=False` silently misses them.

### E3: LLM extraction cost at scale
**What**: `/extract` calls Gemini Flash for every request. At PRISM's scale (hundreds of companies), this could add up. No cost tracking, no caching, no deduplication.
**Investigation needed**: Before PRISM Phase 4 integration, estimate how many `/extract` calls intel_company would make per enrichment run. Add result caching if needed.

---

## Launch-Blocker Summary

| # | Risk | Mitigation | Owner | Gate |
|---|---|---|---|---|
| T1 | Crawl4AI API mismatch | Smoke test before API build | Builder | Before Task #12 |
| T2 | Missing integration + contract tests | Build both layers | Builder | Before Phase 1 "done" |
