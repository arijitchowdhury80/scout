# Firecrawl Teardown — captured with Scout (dogfood), 2026-07-06

Scout mapped + scraped firecrawl.dev to learn its structure. This is the evidence base for the
design-language verdict and the site rebuild. Raw artifacts: `urls-*.txt`, `pages/*.md`,
`shots/*.png`, `_scrape-index.json`.

## Method (Scout dogfood)
- `map_urls` (sitemap-first) on both domains → full URL inventory.
- `scrape` on a curated 20-page representative set → clean markdown + word counts.
- `scrape` with screenshot on 5 key pages → full-page PNGs.
- Two marketing pages (`/crawl`, `/agent`) timed out on the local http-first fetch (net::ERR_TIMED_OUT).
  Not a Scout defect — transient; the JS-screenshot pass captured them fine. Noted, not hidden.

## Information architecture (what they publish)
| Domain | URLs | Biggest sections |
|---|---|---|
| www.firecrawl.dev | 540 | **blog 276**, **glossary 207**, alternatives 20, use-cases 13, tools 5 |
| docs.firecrawl.dev | 900 (capped read at 800) | i18n ×5 (es/fr/ja/pt-BR/zh ~147 each), **api-reference 49**, **quickstarts 45**, **developer-guides 26**, features 11, use-cases 12 |

**Takeaways:**
1. **Marketing is an SEO content engine.** 276 blog + 207 glossary + 20 programmatic "vs-competitor"
   pages + 13 use-case landers. This is a deliberate inbound machine, not a brochure.
2. **Every capability has its own landing page:** `/scrape`, `/crawl`, `/monitor`, `/interact`,
   `/agent`, plus `/playground`, `/pricing`, `/about`, `/changelog`, `/brand`, `/careers`.
3. **Docs are deep and fully internationalized** into 5 languages. English core alone: 49 API-reference
   endpoints, 45 quickstarts, 26 developer guides (LLM SDKs, MCP setups, common-sites, cookbooks).
4. **They publish `/llms.txt`** — an AI-agent-readable index of all docs. On-brand for an agent tool.

## Content depth (words per page, Scout-measured)
| Page | Words |
|---|---|
| /changelog | 7,452 |
| / (home) | 2,669 |
| /alternatives/firecrawl-vs-apify | 2,188 |
| /use-cases/competitive-intelligence | 1,079 |
| /pricing | 940 |
| docs / (intro) | 894 |
| docs /features/ask | 828 |
| /use-cases (hub) | 799 |
| /scrape (product) | 694 |
| docs quickstart / dev-guide | 200–545 |
Median scraped page ≈ **694 words**; marketing landers run **1,000–2,700**. Scout's pages are a
fraction of this — the content gap is real and quantified.

## Docs + playground patterns worth stealing
- **Docs run on Mintlify** (category-standard dev-docs platform): global search (⌘K), per-page
  "Copy page", left nav tree grouped Get-Started / Core-Endpoints / Quickstarts / Developer-Guides /
  Webhooks / Use-Cases, code blocks with language tabs (Python/Node/cURL/CLI), callout boxes,
  version switcher, i18n, and the `llms.txt` index. Instant credibility; nothing hand-rolled.
- **Docs intro leads with two cards:** "Get your API key" + "Try it in the Playground" — the exact
  two actions a new dev needs.
- **Playground is a real tool:** tabs Search/Scrape/Parse/Map/Crawl, URL input, Format dropdown,
  "Get code" (copy the API call), "Start scraping". "API, Docs and Playground — all in one place."

## Design language (visual)
Warm + calm + trustworthy. Near-white surface, **single orange accent**, humanist sans (Geist),
**sentence-case** headers (not shouting), generous whitespace, subtle ASCII-map motif. The **product
demo widget is the hero** (a working scrape box), immediately followed by social proof: GitHub stars
(145.8K), "Trusted by 150,000+ companies" + logos (Shopify, Lovable, Canva, Zapier), "Backed by Y
Combinator", "SOC II Type 2". Every page reads "adopt me in production today."

## What to borrow vs where Scout should differ
**Borrow:** demo-as-hero, social proof scaffolding, per-capability landing pages, Mintlify docs,
`/llms.txt`, deep content engine, calm trustworthy skin, "Get key + Try playground" dual CTA.
**Keep as Scout's edge:** the *evidence-grade / citable records* positioning is a genuine
differentiator — Firecrawl returns markdown; Scout preserves proof, citations, blocked-page notes,
typed records. Don't dilute that; just dress it in a more trustworthy skin. Scout's amber/gold accent
is a clean visual differentiator vs Firecrawl orange — worth keeping.
