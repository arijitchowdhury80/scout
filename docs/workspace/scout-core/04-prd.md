# Scout Core — PRD

## 1. Summary

Scout is a self-hosted web intelligence platform built on Crawl4AI that replaces Apify in PRISM's intel modules. It exposes a FastAPI REST service (5 endpoints) and a Python library (`ScoutCrawler`) that PRISM modules import directly. Phase 1 ships core library + API + Docker; Claude integration (skill) ships in Phase 2.

## 2. Background

PRISM's intel_hiring and intel_company modules currently use Apify SaaS for web crawling. This creates: per-crawl billing, a TypeScript FFI layer, data passing through a vendor, and no shared schema. Crawl4AI (MIT, Python, 65k+ GitHub stars) eliminates all of these. Scout is the thin abstraction layer that makes Crawl4AI production-ready for PRISM.

Decision record: Self-hosted Firecrawl was evaluated and rejected (AGPL-3.0, loses Fire-engine on self-host, TypeScript stack). See `docs/workspace/scout-core/02-value-prop.md`.

## 3. Objective

**Goal**: Eliminate PRISM's Apify dependency by building a self-hosted, Python-native web crawler that PRISM modules can use directly.

**Key Results (Phase 1 done when all pass)**:
1. `docker compose up -d && curl -X POST http://localhost:8000/scrape -d '{"url": "https://nike.com"}' -H "Content-Type: application/json"` returns `{"success": true, "markdown": "...", ...}` within 30 seconds
2. All 5 endpoints respond with typed Pydantic responses matching `scout/core/types.py` contracts
3. `pytest tests/ -v` passes with unit + integration test layers for all 5 modes + API routes
4. PRISM intel_hiring tests pass with Scout replacing Apify (Phase 4 acceptance gate — not Phase 1)

## 4. Solution

### 4.1 Architecture

```
scout/
  core/           ← Python library (PRISM imports directly)
    crawler.py    ← ScoutCrawler: unified entry point
    modes/        ← 5 mode functions (scrape, crawl, extract, map, screenshot)
    types.py      ← All Pydantic request/response models
    version.py    ← Crawl4AI version pin
  api/            ← FastAPI service
    main.py       ← App + lifespan (ScoutCrawler singleton)
    routers/      ← 5 endpoint routers + health
    middleware/   ← API key auth
    config.py     ← Settings (API key, LLM key, timeouts)
  docker/
    Dockerfile
    docker-compose.yml
```

**Key design principle**: `ScoutCrawler` is instantiated once at API startup (lifespan) and injected via FastAPI dependency. All 5 mode functions are stateless async functions that `ScoutCrawler` delegates to.

### 4.2 API Contracts (Pydantic — source of truth: `scout/core/types.py`)

All request bodies and response envelopes are defined in `types.py`. No raw dicts cross any boundary.

**POST /scrape**
- Request: `ScrapeRequest(url, formats=[markdown], use_js=False, wait_for="", timeout_ms=30000)`
- Response: `ScrapeResponse(success, url, markdown, raw_html, screenshot_base64, links, metadata, error, duration_ms)`

**POST /crawl**
- Request: `CrawlRequest(url, max_depth=2, max_pages=10, url_pattern="", include_external=False, use_js=False, timeout_ms=60000)`
- Response: `CrawlResponse(success, start_url, pages=[CrawlPage], total_pages, error, duration_ms)`

**POST /extract**
- Request: `ExtractRequest(url, schema={}, instruction, llm_provider="gemini/gemini-2.0-flash", use_js=False, timeout_ms=45000)`
- Note: `schema` field — JSON Schema dict. In Pydantic model uses `Field(alias="schema")` to avoid shadowing.
- Response: `ExtractResponse(success, url, data={}, markdown, metadata, error, duration_ms)`

**POST /map**
- Request: `MapRequest(url, max_pages=100, url_pattern="", include_external=False)`
- Response: `MapResponse(success, start_url, urls=[], total, error, duration_ms)`

**POST /screenshot**
- Request: `ScreenshotRequest(url, full_page=True, viewport_width=1280, viewport_height=800, wait_for="", use_js=True)`
- Response: `ScreenshotResponse(success, url, screenshot_base64, width, height, error, duration_ms)`

**GET /health**
- Response: `{"status": "ok", "crawl4ai_version": "0.8.x", "scout_version": "0.1.0", "uptime_seconds": N}`

### 4.3 Authentication

API key via `X-API-Key` header. Key configured in environment variable `SCOUT_API_KEY`. Requests without valid key → 403. Health endpoint is unauthenticated.

### 4.4 Dependencies

- `crawl4ai>=0.8.0` — crawler engine
- `fastapi>=0.115.0` + `uvicorn[standard]` — API layer
- `pydantic>=2.0.0` — type contracts
- `structlog>=24.0.0` — structured logging
- Python ≥ 3.11

### 4.5 Dropped from Phase 1

- `/search` — Crawl4AI doesn't do web search. Perplexity handles this in PRISM.
- `/interact` — action chains (click, fill, scroll). Phase 2+.
- Redis job queue — /crawl and /map are synchronous in Phase 1 (no async job IDs).
- CLI tool — Phase 3.
- MCP server — Phase 3 (skill ships Phase 2).

## 5. Assumptions (from 03-assumptions.md)

Top risks:
- `fit_markdown` attribute path on CrawlResult may be wrong (silent fallback to unfiltered markdown)
- `arun_many()` async iteration pattern may not work as implemented
- PruningContentFilter threshold=0.4 untested against real target URLs

## 6. Acceptance Criteria

### AC-1: /scrape returns clean markdown
- Given a live URL, `POST /scrape {"url": "https://example.com"}` returns `success=true`, non-empty `markdown`, populated `metadata.title` and `metadata.word_count > 0`
- `duration_ms` is populated and > 0

### AC-2: /scrape returns screenshot when requested
- `POST /scrape {"url": "https://example.com", "formats": ["markdown", "screenshot"]}` returns non-empty `screenshot_base64`

### AC-3: /crawl returns multiple pages
- `POST /crawl {"url": "https://example.com", "max_pages": 3}` returns `total_pages >= 1` with at least one page having non-empty `markdown`

### AC-4: /extract returns structured data
- `POST /extract {"url": "...", "schema": {...}, "instruction": "..."}` returns `data` dict with keys matching schema

### AC-5: /map returns URL list
- `POST /map {"url": "https://example.com"}` returns `urls` list with at least 1 URL and `total >= 1`

### AC-6: /screenshot returns base64 PNG
- `POST /screenshot {"url": "https://example.com"}` returns non-empty `screenshot_base64` and correct `width`/`height`

### AC-7: /health returns version info
- `GET /health` returns `{"status": "ok", "crawl4ai_version": "...", "scout_version": "..."}`

### AC-8: Auth blocks unauthenticated requests
- Any endpoint except /health without `X-API-Key` header returns 403

### AC-9: All unit tests pass
- `pytest tests/unit/ -v` — all pass

### AC-10: All integration tests pass
- `pytest tests/integration/ -v` — all pass (against real URLs)

### AC-11: Docker compose starts cleanly
- `docker compose up -d` brings up Scout on port 8000; `curl http://localhost:8000/health` returns 200

### AC-12: pyright --strict clean on all Scout code
- `pyright scout/ --strict` reports zero errors

## 7. Release Plan

**Phase 1 (current)**: Core library + FastAPI + Docker. No external dependencies beyond Crawl4AI + FastAPI. Standalone. Smoke-testable via docker compose.

**Phase 2**: Claude Code skill (`scout/skill/scout.md`). 30 minutes. Claude can scrape/crawl via the running API.

**Phase 3**: CLI (`scout scrape <url>`), MCP server.

**Phase 4**: PRISM integration — intel_hiring + intel_company migrate to `from scout.core import ScoutCrawler`.

## 8. Open Questions

1. **fit_markdown vs markdown.fit_markdown**: Which attribute path is correct in Crawl4AI v0.8.x? Must verify against installed package. (Risk #1 from assumptions doc)
2. **arun_many() iteration**: Is `async for result in await crawler.arun_many(...)` correct? (Risk #2)
3. **Docker Playwright resource requirements**: Does Playwright run cleanly in standard Alpine/Debian container? Or do we need `--shm-size` and `--cap-add`?
4. **ScrapingBee integration**: Is the fallback to ScrapingBee built into Crawl4AI's browser config, or does it require a separate adapter in Scout? (Plan says 3-tier: httpx → Playwright → ScrapingBee — but Crawl4AI may not support this natively)
5. **Pydantic `version` field**: CodingSOPs say every model needs a `version` field for forward-compat. Should Scout models have this? Decision needed before API layer is built.
