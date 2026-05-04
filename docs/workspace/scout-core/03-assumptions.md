# Scout Core — Assumptions

## Value Assumptions

| Assumption | Confidence | If Wrong |
|---|---|---|
| PRISM intel modules will produce equivalent or better data quality using Scout vs. Apify | Medium | PRISM Phase 4 integration fails; we need to keep Apify as fallback for specific actors |
| Clean markdown from Crawl4AI is sufficient for LLM-based intel extraction | Medium | Token noise in fit_markdown degrades extraction quality; need additional filtering |
| Claude will use Scout skill for research tasks when available | High | Low risk — Claude uses available tools |
| The Pydantic response schema covers all fields PRISM modules need | Medium | PRISM modules need fields not in ScoutMetadata (e.g., structured author info); requires schema extension |

## Feasibility Assumptions

| Assumption | Confidence | If Wrong |
|---|---|---|
| Crawl4AI v0.8.x BFSDeepCrawlStrategy works reliably for multi-page crawls | Medium | Some site structures break BFS traversal; need fallback strategies |
| Crawl4AI LLMExtractionStrategy works with Gemini Flash as default provider | Medium | Gemini Flash extraction quality is poor for complex schemas; need provider fallback |
| PruningContentFilter threshold=0.4 produces good signal/noise ratio across diverse sites | Low-Medium | Threshold needs per-domain tuning; one-size-fits-all value too aggressive/conservative |
| Crawl4AI's stealth Playwright handles most modern anti-bot measures | Medium | Heavy Cloudflare/Akamai sites block even stealth Playwright; ScrapingBee fallback needed sooner than planned |
| Docker + Playwright headless works in standard container without special config | Medium | Browser sandbox issues require additional Docker privileges (--cap-add, --shm-size) |

## Viability Assumptions

| Assumption | Confidence | If Wrong |
|---|---|---|
| Phase 1 (core + API + Docker) can be completed in ~3 days of engineering | High | Scope creep or Crawl4AI API surface complexity adds time |
| Crawl4AI is actively maintained and v0.8.x is stable enough for production | High | Crawl4AI breaks in minor version; version.py isolation contains the blast radius |
| Running Playwright in Docker doesn't blow out memory/CPU for typical PRISM workloads | Medium | Resource usage too high for co-hosting with PRISM; needs dedicated container/VM |
| ScrapingBee API key already available in PRISM environment | High | Already confirmed — PRISM has ScrapingBee key |

## Integration Assumptions

| Assumption | Confidence | If Wrong |
|---|---|---|
| PRISM modules can `from scout.core import ScoutCrawler` without circular dependency | High | Scout must be a separate installed package, not a submodule of PRISM |
| FastAPI async is compatible with Crawl4AI's async internals | High | Crawl4AI uses asyncio — same event loop as FastAPI |
| `CrawlerRunConfig` and `BrowserConfig` API from Crawl4AI v0.8.x matches what was used in implementation | Medium | Previous session built against docs; need to verify against actual installed package |
| The `fit_markdown` attribute exists on CrawlResult in v0.8.x | Medium-Low | **HIGH RISK** — this attribute name is assumed from docs; may be `markdown.fit_markdown` or different |
| `arun_many()` returns an async generator (used in crawl + map modes) | Medium | May be a coroutine returning a list; iteration pattern would fail at runtime |

---

## Top 3 Riskiest Assumptions

### 🔴 Risk 1: `fit_markdown` attribute path on CrawlResult (Feasibility)
**Assumption**: `result.fit_markdown` is the correct attribute access on a Crawl4AI `CrawlResult` object.
**Evidence against**: Crawl4AI docs show `result.markdown` for raw markdown and `result.markdown.fit_markdown` (nested) in some versions. The implementation uses `getattr(result, "fit_markdown", None) or result.markdown` — the `getattr` fallback suggests this was already uncertain.
**Impact**: Every mode silently falls back to unfiltered `result.markdown` if the attribute is wrong. Content quality degrades. No error thrown.
**Mitigation needed**: Verify against installed package before PRISM integration.

### 🔴 Risk 2: `arun_many()` async iteration pattern (Feasibility)
**Assumption**: `await crawler.arun_many([url])` returns an async generator that can be iterated with `async for result in await ...`.
**Evidence against**: The pattern `async for result in await crawler.arun_many(...)` is unusual — typically either `async for result in crawler.arun_many(...)` or `results = await crawler.arun_many(...)`. The double await + async for may not work.
**Impact**: crawl and map modes silently return empty results or throw a TypeError at runtime.
**Mitigation needed**: Smoke test against real URL before building API layer.

### 🟡 Risk 3: PruningContentFilter threshold too aggressive (Value)
**Assumption**: threshold=0.4 produces good output across diverse site types.
**Evidence against**: No empirical testing done. Career pages with sparse content (e.g., "We're hiring! Check back soon.") may be pruned too aggressively. News pages with heavy boilerplate may still have too much noise.
**Impact**: Downstream LLM extraction quality varies unpredictably. PRISM intel modules produce inconsistent results.
**Mitigation needed**: Test against 3-5 real target URLs before PRISM integration.
