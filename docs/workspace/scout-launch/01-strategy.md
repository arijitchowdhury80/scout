# Scout Product Strategy Canvas

Date: 2026-06-27
Mode: Full strategy canvas

## 1. Vision

Scout should become the owned acquisition workbench for AI, demo, and
intelligence workflows: a system that turns messy web pages into trustworthy,
citable, downstream-ready records.

Values:

- truth over fake success,
- evidence on every record,
- owned workflows over rented black boxes,
- browser/session handoff where generic crawlers fail,
- practical downstream outputs, not raw scrape theater.

## 2. Market Segments

Primary segment for private beta:

- technical users who need website data transformed into usable records:
  solutions engineers, AI-agent builders, competitive intelligence researchers,
  and data/product operators.

Why first:

- they understand local tools,
- they can tolerate beta roughness,
- they can evaluate output quality,
- they have immediate website-to-record pain.

## 3. Relative Costs

Scout should not compete on hosted scale price first. Its cost advantage is:

- no per-crawl SaaS fee for local/self-hosted runs,
- less manual research time,
- reusable artifacts,
- fewer one-off scripts.

It should compete on unique value more than low cost.

## 4. Value Propositions

### AI Builders

Before: Agents need web data, but generic fetches are brittle and unaudited.

How: Scout gives agents a local acquisition engine with scrape/crawl/map,
browser capture, structured records, and artifacts.

After: Agents can request evidence-backed records, not just page blobs.

Alternatives: Firecrawl, browser-use scripts, Playwright scripts, manual fetch.

### Solutions Engineers

Before: Building a demo index from a prospect site is manual and slow.

How: Scout extracts product records and can push/preview Algolia records.

After: Demo data becomes repeatable and inspectable.

Alternatives: manual copy/paste, one-off scrapers, Apify actors, Firecrawl plus
custom normalization.

### Competitive Intelligence Teams

Before: Site monitoring needs repeatable acquisition and quality checks.

How: Scout provides acquisition metadata, structured artifacts, and collector
recommendations.

After: CI knows what was fetched, how good it is, and when to fall back.

Alternatives: direct HTTP, hosted crawlers, manual browser review.

## 5. Trade-Offs

Scout will not:

- claim universal unblock,
- compete first as a massive hosted crawling API,
- support every website perfectly,
- own every consumer's source strategy,
- auto-bypass legal/ToS restrictions,
- make privacy the only value proposition.

These trade-offs keep Scout focused on acquisition quality, evidence, browser
handoff, records, and downstream artifacts.

## 6. Key Metrics

North Star:

- Successful evidence-backed records produced per run.

One metric for the next quarter:

- Private beta activation: percentage of testers who complete one real workflow
  and can locate usable artifacts.

Supporting metrics:

- record count,
- citation/source coverage,
- blocked evidence coverage,
- time to first successful run,
- direct HTTP vs Scout benchmark win rate,
- user-reported "would use again" score.

## 7. Growth

Initial growth should be founder-led and design-partner led.

Channels:

- GitHub,
- personal network,
- Algolia/SE demo community,
- AI-agent builders,
- technical blog posts,
- private beta website.

Scaling later requires:

- MCP server,
- Docker packaging,
- better docs,
- hosted option decision,
- examples and demo videos.

## 8. Capabilities

Must-have capabilities:

- reliable scrape/crawl/map/screenshot,
- browser/user-session capture,
- structured extraction,
- product records,
- artifact and citation model,
- run persistence and UI,
- packaging and install docs,
- legal/compliance posture.

Build vs buy:

- Build Scout's orchestration, evidence, records, and workflows.
- Use Crawl4AI for crawling/rendering/extraction substrate.
- Use Playwright/CDP for browser capture.
- Use Algolia client for indexing.

## 9. Defensibility

Scout's defensibility is not a secret crawler trick. It is workflow depth:

- domain-specific record production,
- browser/user-session handoff,
- artifacts and evidence,
- integrations into PRISM/CI/Algolia/agents,
- local-first operator experience,
- accumulated benchmark/confidence maps by site type.

## Weakest Point

Scout is not yet clearly superior to Firecrawl for generic crawling. The
positioning must avoid that fight and focus on evidence-backed acquisition to
records, browser handoff, and downstream workflows.

## Critical Hypotheses

1. Users value artifacts/evidence enough to choose Scout over generic scrape
   APIs. Confidence: medium. Test: private beta interviews.
2. Browser/user-session capture is a meaningful differentiator. Confidence:
   medium-high. Test: hard-site workflows with real users.
3. Product-to-record workflows are valuable outside Algolia. Confidence:
   medium. Test: export records to JSON/CSV/Search UI, not only Algolia.
4. Local install friction is acceptable for private beta. Confidence: medium.
   Test: observe install sessions.
5. Scout can maintain quality across varied sites. Confidence: medium-low.
   Test: benchmark harness and live E2E matrix.
