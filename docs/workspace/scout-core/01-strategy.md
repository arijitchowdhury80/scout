# Scout Core — Strategy

## 1. Does this fit the product vision?

Scout is the data acquisition layer for PRISM. PRISM's value is structured intelligence about prospects — but that intelligence comes from raw web data. Today, PRISM's intel modules depend on Apify (SaaS, per-usage billing, TypeScript, outside our control) for web crawling. Scout replaces that dependency with a Python-native, MIT-licensed, self-hosted crawler we fully own.

Fit: **High.** PRISM can't produce intelligence without web data. Scout closes the infrastructure gap at the bottom of the stack. Without Scout, every PRISM intel module is either blocked, paying SaaS rent, or hacking around limitations.

Scout also has a secondary product dimension: it is useful beyond PRISM. As a standalone FastAPI service, it can serve any future tool we build — Claude skills, N8N automations, ad-hoc research — without re-implementing crawling each time.

## 2. Who is the target segment?

Internal system, two consumers:

**Primary: PRISM intel modules** — specifically intel_hiring and intel_company in Phase 4. These modules need to fetch company career pages, leadership pages, investor pages, and news. They need structured output (markdown, extracted JSON), not raw HTML. They run in Python async workflows.

**Secondary: Claude (via skill/MCP)** — Claude needs to browse the web when researching prospects. Today this is ad-hoc. Scout gives Claude a reliable, documented, self-hosted tool with consistent output.

There is no external end-user in Phase 1. This is pure infrastructure.

## 3. What's the trade-off?

By building Scout we are choosing NOT to:
- Continue paying Apify per-crawl fees (good — eliminates ongoing cost)
- Self-host Firecrawl (rejected: AGPL-3.0 licensing risk, loses Fire-engine on self-host, TypeScript/Node stack)
- Use Crawl4AI directly inside PRISM modules without an abstraction layer (bad: version lock, no consistent response schema, no self-hosted API surface)

The cost of building Scout: ~2-3 days of engineering to Phase 1 complete. The benefit: permanent elimination of Apify dependency, consistent crawling interface for all future modules.

**What we're NOT building in Phase 1:**
- /search endpoint (Crawl4AI doesn't do web search — Perplexity handles this in PRISM)
- /interact endpoint (action chains: click, fill, scroll — Phase 2+)
- CLI tool (Phase 3)
- MCP server (Phase 3 — skill ships in Phase 2)
- Redis job queue for async /crawl (simplified to synchronous in Phase 1)

## 4. What's the key metric?

**PRISM intel_hiring and intel_company migrate to Scout with no regression in data quality.**

Operationally: the acceptance test is running `pytest prism_platform/v2/modules/intel_hiring/tests/ -v` after PRISM Phase 4 integration and seeing all tests green, with no Apify calls in the execution path.

Secondary metric: Scout scrapes a real career page (e.g., `https://nike.com/careers`) and returns non-empty markdown with a populated metadata block within 15 seconds.

## 5. What's the defensibility?

Scout is not a product differentiation play — it is infrastructure. The defensibility is:

- **Ownership**: MIT license, no vendor dependency, no AGPL exposure. We can modify anything.
- **Python-native**: Same stack as PRISM. Direct import with zero HTTP overhead for PRISM.
- **Version isolation**: `core/version.py` pins Crawl4AI version. Upgrading = one file change + tests.
- **Anti-bot**: Crawl4AI's 3-tier detection (httpx → stealth Playwright → ScrapingBee proxy) is better than what we get from Apify on their free/starter tier.

The moat is small but real: replacing this later would require re-engineering the entire data acquisition layer of PRISM.
