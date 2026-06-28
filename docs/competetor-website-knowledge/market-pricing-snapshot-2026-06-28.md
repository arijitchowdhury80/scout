# Market Pricing Snapshot

Date: 2026-06-28
Status: Current official-site snapshot

This page records current public pricing signals from adjacent crawler, browser,
search, and extraction products. The purpose is not to copy competitor pricing.
It is to prevent Scout from launching an economically unsafe hosted offer.

## Summary

The market pattern is clear:

- hosted crawling is sold with monthly credits, request quotas, or overage;
- hosted browser automation is metered by browser hours, sessions, concurrency,
  proxy usage, or fetch calls;
- extraction/knowledge APIs use monthly credit allotments and rate limits;
- free tiers exist, but they are capped;
- enterprise plans are custom and include security/support commitments;
- no serious competitor sells unlimited hosted crawling/browser usage for a
  small one-time fee.

## Current Pricing Signals

| Product | Public model observed | Launch implication for Scout |
|---|---|---|
| Firecrawl | Free monthly credits, paid monthly plans, scale/enterprise, endpoint-based credit costs. Scrape/crawl/map/monitor are page-credit based; browser interaction is per browser minute. | Scout hosted should meter pages and browser minutes separately. Do not offer unlimited hosted usage. |
| Apify | Free tier, monthly prepaid platform usage, pay-as-you-go overage, compute units, proxy charges, storage/data-transfer charges. | If Scout hosts worker infrastructure, storage and proxy/browser costs need hard limits and visible usage. |
| Browserbase | Free, developer, startup, and custom plans. Browser hours, concurrency, search calls, fetch calls, proxy GB, retention, and token allowances are explicit. | Browser workbench/hosted browser mode must be its own metered bucket, not hidden inside page credits. |
| ScrapingBee | Credit-based plans beginning at paid monthly tiers, with free trial credits and feature gating around JS rendering, proxies, screenshots, and extraction. | Anti-blocking/rendering features cost more and should be visibly metered. |
| ScraperAPI | Monthly plans with API credits, concurrency, geotargeting, JS rendering, parsing APIs, crawler access, pay-as-you-go, and enterprise. | Hosted usage tiers should expose concurrency and monthly quotas early. |
| Tavily | Free monthly API credits, pay-as-you-go per credit, adjustable project plan, enterprise. | API-oriented users expect both free trial and pay-as-you-go/subscription options. |
| Exa | Free request allowance, endpoint-specific pricing for search, contents, deep search, monitors, and agent runs; enterprise with zero data retention and custom limits. | Scout should separate primitive costs: scrape, crawl, browser, extraction/LLM, storage. |
| Zyte | Per-website pricing with HTTP and browser-rendered response tiers, monthly commitments, and pricing based on site complexity. | Hard-site/browser-rendered pages are meaningfully more expensive than simple HTTP fetches. |
| Diffbot | Free tier plus monthly credit allotments, rate limits, overage on paid plans, extraction/crawl/knowledge graph feature gating. | Structured-record value can command more than raw crawling, but it still needs quotas and overage rules. |

## Evidence Highlights

- Firecrawl publicly presents free and paid monthly plans and states that API
  credits vary by endpoint/feature. Its pricing page lists scrape/crawl/map as
  one credit per page and browser interaction as credits per browser minute.
- Apify presents subscription plans with prepaid platform usage and pay-as-you-go
  overage. It itemizes compute units, proxy, storage, data transfer, and
  concurrency.
- Browserbase explicitly prices browser hours, concurrent browsers, fetch/search
  calls, proxy GB, and retention.
- ScrapingBee and ScraperAPI both frame scraping as API-credit plans with
  concurrency and feature gates.
- Exa and Tavily are AI-search adjacent, not crawler-only, but they reinforce
  the same pattern: API usage is metered by credits or endpoint requests.
- Zyte and Diffbot show the enterprise side of the market: site complexity,
  structured extraction, rate limits, support, and overages all matter.

## Recommendation

For Scout:

1. Keep local Scout free for private beta and developer adoption.
2. Offer hosted only as a capped beta pass or subscription.
3. Treat `$22 one-time` as a **finite beta credit pack**, not unlimited access.
4. Split credits into at least:
   - standard page credits,
   - browser/render credits,
   - optional LLM/extraction credits,
   - artifact retention/storage limits.
5. Require hard caps:
   - max pages per run,
   - max products per run,
   - max records per run,
   - max browser minutes/day,
   - max concurrent runs,
   - retention window.
6. Launch copy must say "metered hosted beta" instead of "unlimited hosted
   crawler."

## Source Index

- Firecrawl homepage: https://www.firecrawl.dev/
- Firecrawl pricing: https://www.firecrawl.dev/pricing
- Firecrawl docs: https://docs.firecrawl.dev/
- Apify pricing: https://apify.com/pricing
- Browserbase pricing: https://www.browserbase.com/pricing
- ScrapingBee pricing: https://www.scrapingbee.com/pricing/
- ScraperAPI pricing: https://www.scraperapi.com/pricing/
- Tavily pricing: https://www.tavily.com/pricing
- Exa pricing: https://exa.ai/pricing
- Zyte pricing: https://www.zyte.com/pricing/
- Diffbot pricing: https://www.diffbot.com/pricing/
