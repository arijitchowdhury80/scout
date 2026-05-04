# Scout Core — Value Proposition

## 6-Part JTBD Template

**1. Who**
Two consumers:
- **PRISM intel modules** (intel_hiring, intel_company, and future modules) — Python async code that needs to fetch and structure web content
- **Claude** (via Claude Code skill in Phase 2, MCP server in Phase 3) — needs to browse the web for research tasks

**2. Why — The Job It's Hired For**
*"When I need to fetch a web page and get structured, clean content back in Python — I want a consistent, reliable tool I own, so I can stop depending on external SaaS billing, rate limits, and TypeScript adapters."*

The problem isn't crawling per se (Crawl4AI does that). The problem is:
- No consistent response schema — Crawl4AI returns raw `CrawlResult` objects, not validated Pydantic models
- No version isolation — Crawl4AI updates break callsites throughout PRISM
- No self-hosted API — Claude and external tools can't call Crawl4AI directly
- Apify dependency is SaaS rent + TypeScript FFI pain + data passing through an external vendor

**3. What Before (without Scout)**
- PRISM intel modules call Apify actors via HTTP → TypeScript adapter layer → per-crawl billing → data returned as unvalidated JSON
- intel_company and intel_hiring each have bespoke crawling logic, copy-pasted and diverging
- Claude has no reliable way to browse the web — ad-hoc workarounds
- Any new module that needs web data must re-implement crawling from scratch

**4. How — Key Capabilities**
- `POST /scrape` — single URL → clean markdown + optional screenshot + metadata
- `POST /crawl` — BFS recursive multi-page crawl → list of CrawlPage objects
- `POST /extract` — LLM-structured extraction using Pydantic schema + instruction
- `POST /map` — fast URL discovery (site map) without content extraction
- `POST /screenshot` — visual capture only (viewport-configurable base64 PNG)
- `GET /health` — version, uptime, readiness probe
- `ScoutCrawler` class — Python import for zero-HTTP-overhead use in PRISM
- All responses: typed Pydantic v2 models with consistent shape

**5. What After (with Scout)**
- PRISM intel modules `from scout.core import ScoutCrawler` — one import, consistent Pydantic responses
- No Apify dependency, no per-crawl billing
- Claude can `scout_scrape`, `scout_crawl`, `scout_extract` via skill — reliable and documented
- New PRISM modules get web crawling for free by calling Scout
- Crawl4AI upgrades: one file change (`core/version.py`) + tests — nothing else breaks

**6. Alternatives Considered**
| Alternative | Why rejected |
|---|---|
| Self-hosted Firecrawl | AGPL-3.0 (commercial distribution requires open-sourcing), loses Fire-engine on self-host, TypeScript/Node.js stack |
| Apify (keep current) | SaaS billing, TypeScript FFI, vendor data access, no Python integration |
| Crawl4AI direct (no wrapper) | No version isolation, no consistent schema, no self-hosted API, bespoke logic per module |
| Scrapy | No LLM extraction, no async, no stealth browser, complex setup |
| Jina.ai | SaaS, per-call billing, vendor dependency |

**Value Proposition Statement**

Scout is a self-hosted Python web crawler (built on Crawl4AI) that gives PRISM and Claude a consistent, schema-validated interface to the web — eliminating Apify dependency, enforcing Pydantic response contracts at every boundary, and serving as the permanent data acquisition infrastructure for all current and future PRISM modules.
