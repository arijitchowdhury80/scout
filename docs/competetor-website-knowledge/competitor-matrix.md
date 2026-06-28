# Competitor Matrix

Date: 2026-06-28
Status: Research baseline

## Executive Summary

The market clusters into five groups:

1. **Crawler APIs** - Firecrawl, ScrapingBee, ScraperAPI, Zyte.
2. **AI search/research APIs** - Exa, Tavily, Jina Reader.
3. **Browser automation infrastructure** - Browserbase.
4. **Scraping marketplaces/platforms** - Apify.
5. **Extraction/knowledge graph platforms** - Diffbot.

Scout should not mimic all of them. The strongest website direction is to
position Scout as a **local-first acquisition layer for AI workflows** with
optional hosted convenience.

## Competitor Notes

### Firecrawl

**Positioning:** Developer-first web data API for turning websites into
LLM-ready markdown, search/crawl/map/extract workflows, and agent consumption.

**Website Pattern:**

- Strong hero with plain developer value proposition.
- Quick code sample near the top.
- Product primitives: scrape, crawl, map, search, extract.
- Docs-first navigation.
- Pricing and free-trial CTA are visible early.
- Trust/social proof, examples, and enterprise messaging.

**Pricing/Onboarding Pattern:**

- Free/developer entry point.
- Usage/credit-based paid plans.
- Team/business/enterprise escalation.
- Hosted API is the default experience; self-host/open-source appears as a
  trust and developer adoption path.

**Scout Takeaway:**

Do not try to out-Firecrawl Firecrawl. Scout needs sharper language around
evidence, local control, browser handoff, artifact folders, and typed records.

### Exa

**Positioning:** Search API built for AI applications, with content retrieval and
neural/web search workflows.

**Website Pattern:**

- AI-native framing.
- API docs and use-case examples.
- Emphasis on search quality and AI relevance.
- Pricing shaped around API calls/usage.

**Scout Takeaway:**

Scout should avoid claiming to be a web-scale AI search index. If Scout includes
web search or discovery, it should frame that as acquisition support, not the
core product.

### Tavily

**Positioning:** Search/extract/crawl API for AI agents and research agents.

**Website Pattern:**

- Agent-oriented language.
- Simple developer API examples.
- Clear docs path.
- Pricing and API key flow.

**Scout Takeaway:**

Scout can borrow the agent-oriented framing, but Scout's wedge is not just API
search. It is owned acquisition plus evidence and artifacts.

### Apify

**Positioning:** Large web scraping and automation platform with actors,
marketplace, storage, proxies, scheduling, and many ready-made scrapers.

**Website Pattern:**

- Marketplace and catalog are central.
- Lots of use cases and prebuilt actors.
- Platform, integrations, enterprise, and docs navigation.
- Monetization through subscriptions, platform usage, and enterprise contracts.

**Scout Takeaway:**

Apify is a platform. Scout should not launch with a marketplace promise. A
future "recipes/presets" gallery could be useful, but v1 should stay focused.

### Browserbase

**Positioning:** Hosted browser infrastructure for AI agents and automation.

**Website Pattern:**

- Browser/session primitives.
- Developer API and SDK examples.
- Reliability/scale/security language.
- Pricing tied to browser sessions, concurrency, and managed infrastructure.

**Scout Takeaway:**

Browserbase validates that browser execution has real infrastructure cost.
Scout's hosted version must meter browser/session usage carefully. A one-time
unlimited fee is economically unsafe.

### ScrapingBee

**Positioning:** Web scraping API handling proxies, JavaScript rendering,
rotating IPs, and anti-blocking complexity.

**Website Pattern:**

- Direct pain statement: avoid proxies and blocks.
- Code snippets.
- Feature blocks for JS rendering, proxy rotation, screenshots/search snippets.
- Pricing based on credits/requests.

**Scout Takeaway:**

Anti-blocking alone is a commodity promise and risky to overclaim. Scout should
say it escalates and records evidence honestly rather than promising unblock
magic.

### ScraperAPI

**Positioning:** Hosted scraping API with proxy rotation, CAPTCHA handling,
browser rendering, and structured endpoints.

**Website Pattern:**

- Simple URL-to-API framing.
- Pricing table with request credits.
- Developer examples.
- Enterprise/scaled scraping path.

**Scout Takeaway:**

Hosted scraping economics are request/credit-based for a reason. Scout hosted
must have quotas.

### Zyte

**Positioning:** Enterprise-grade web data extraction infrastructure with
managed browser/proxy/extraction capabilities.

**Website Pattern:**

- Enterprise trust.
- Managed API/infrastructure language.
- Use-case and compliance emphasis.
- Sales-assisted enterprise motion.

**Scout Takeaway:**

If Scout ever sells to teams, security, compliance, rate limits, logs,
observability, and support policies become part of the product, not side notes.

### Diffbot

**Positioning:** Structured web data and knowledge graph extraction.

**Website Pattern:**

- Entity/data graph framing.
- Enterprise/API positioning.
- Less "crawler utility," more "web knowledge layer."

**Scout Takeaway:**

Scout's typed-record story should be concrete and practical: product records,
company records, news records, investor assets, etc. Avoid overclaiming a
general knowledge graph.

### Jina Reader

**Positioning:** URL/content reader for LLM-ready extraction and simple
developer consumption.

**Website Pattern:**

- Extremely simple "turn URL into readable content" flow.
- Developer-friendly endpoint patterns.
- Low-friction trial.

**Scout Takeaway:**

Scout needs a very simple first demo. Even if the backend is rich, the first
website experience should be "URL -> evidence -> records" in under a minute.

### Crawl4AI

**Positioning:** Open-source crawler/scraper toolkit for AI workflows.

**Legal/Dependency Note:**

Crawl4AI is an upstream dependency. The license file currently uses the Apache
License 2.0. Apache 2.0 generally permits commercial use, modification, and
distribution with attribution/license-notice obligations. This is not legal
advice; keep a third-party notices file and verify dependency licenses before
commercial distribution.

**Scout Takeaway:**

Scout should be clear: it uses Crawl4AI internally for parts of acquisition.
Scout's product value sits above Crawl4AI: orchestration, records, citations,
artifact contract, browser/user-session capture, workflows, and distribution.

## Positioning Comparison

| Product | Primary User | Primary Interface | Main Promise | Scout Should Borrow | Scout Should Avoid |
|---|---|---|---|---|---|
| Firecrawl | Developers/AI builders | Hosted API + docs | LLM-ready web data | Clean primitive names and docs-first CTA | Generic crawler positioning |
| Exa | AI app builders | Search API | AI-native web search | Agent/search use-case language | Search-engine claims |
| Tavily | Agent builders | API | Search/extract/crawl for agents | Research-agent examples | Becoming a search vendor |
| Apify | Scrapers/automation teams | Platform + marketplace | Actors and scraping platform | Presets/recipes idea | Marketplace promise at launch |
| Browserbase | AI automation teams | Browser API | Managed browsers at scale | Browser-session value framing | Underpricing hosted browser costs |
| ScrapingBee | Developers | Hosted API | Proxies/JS/blocking handled | Simple pain-led copy | "We beat blocks" overclaim |
| ScraperAPI | Developers/data teams | Hosted API | Scaled scraping API | Credit-based pricing | Unlimited one-time hosted plan |
| Zyte | Enterprises | Managed API/sales | Enterprise web data | Security/compliance emphasis | Enterprise claims before readiness |
| Diffbot | Data teams | API/knowledge graph | Structured web knowledge | Typed-record story | Generic knowledge graph claims |
| Jina Reader | AI builders | URL/API | Readable content for LLMs | Frictionless demo | Over-simple if evidence is hidden |
| Crawl4AI | Developers | Library | Open-source crawling | Open-source trust | Pretending Scout built everything from scratch |

