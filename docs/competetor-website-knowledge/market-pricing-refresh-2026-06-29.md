# Market Pricing Refresh

Date: 2026-06-29

Status: Current public pricing refresh for Scout hosted economics.

Pricing pages change often. Re-check source pages before publishing final public
pricing claims.

## Executive Takeaway

The market still supports Scout's current hosted pricing posture:

- Local Scout should stay free for adoption and trust.
- The `$22` hosted beta pass must remain finite credits, not unlimited access.
- Browser work must be a separate and smaller credit bucket than simple fetches.
- Public hosted plans should not launch until real private-beta usage data
  proves cost-per-run and support load.
- A future recurring hosted plan is more defensible than a permanent one-time
  hosted plan, but only after Stripe, support, limits, and security gates close.

## 2026-06-29 Live Refresh Addendum

The follow-up source refresh did not change the core recommendation. It made the
risk clearer:

- **Hosted crawler APIs sell metered operations.** Firecrawl, Tavily, Exa,
  ScrapingBee, ScraperAPI, Apify, and Zyte all communicate usage in credits,
  requests, plan allowances, compute units, or endpoint-specific prices.
- **Browser infrastructure is explicitly metered.** Browserbase and Zyte-style
  pricing make browser/rendered work a separate cost center. Scout should keep
  `browser_credits` separate from simple scrape/crawl credits.
- **Free tiers are acquisition tools, not unlimited infrastructure.** Competitors
  use free credits/trials to start developers, then route real usage into paid
  plans, enterprise, or pay-as-you-go.
- **A one-time hosted pass is safe only as beta packaging.** The `$22` hosted
  beta pass should buy a fixed credit allotment and a support relationship, not
  lifetime hosted execution.

Decision implication:

```text
Approve $22 as a private-beta finite-credit pass.
Do not approve $22 as a public, unlimited, or lifetime hosted plan.
Do not launch public hosted pricing until usage telemetry proves real cost per
standard page, browser page, screenshot, extraction run, artifact write, and
support incident.
```

## Current Competitor Signals

| Vendor | Current public signal | Scout implication |
|---|---|---|
| Firecrawl | Scrape, crawl, map, and monitor are priced as credits per page; search and browser interaction have separate credit rates. | Keep Scout hosted metered by action. Do not sell unlimited hosted crawling. |
| Browserbase | Free, Developer, Startup, and custom plans; browser hours, fetch/search calls, proxy bandwidth, and retention are visible meters. | Browser execution is infrastructure, not a free add-on. Keep Scout browser credits separate. |
| Apify | Free/Starter/Scale/Business plans combine monthly prepaid usage with compute-unit pricing and pay-as-you-go. | Hosted Scout needs plan credits plus overage/subscription thinking before public scale. |
| Tavily | Credit-based API model: free monthly credits, pay-as-you-go, monthly plans, enterprise. | For agent-facing APIs, a credit model is normal and understandable. |
| Exa | Free requests plus endpoint-specific prices for search, contents, deep search, monitors, and agent runs. | Different acquisition/intelligence operations should not share one flat cost. |
| ScrapingBee | Free starter credits; plans provide monthly API credits; request options can consume multiple credits. | Scout should make multipliers explicit when rendering, browser, proxy, or extraction features are used. |
| ScraperAPI | Credits are plan-bound; pay-as-you-go can continue past limits on higher plans; unused credits reset on renewal. | Avoid hidden surprises; if credits expire or reset, say so plainly. |
| Zyte | Prices vary by website difficulty and whether browser rendering is required; offers pay-as-you-go and monthly commitments. | Hard-site and browser-rendered work must be priced as materially more expensive than simple HTTP pages. |

## Source Notes

### Firecrawl

Source: https://www.firecrawl.dev/pricing

Observed public pricing model:

- Scrape, crawl, map, and monitor cost credits per page.
- Search and browser interaction have separate rates.
- Advanced features can cost additional credits.

Scout lesson:

- Keep the hosted unit model simple but action-aware.
- The website should say "finite hosted credits" rather than "hosted access."

### Browserbase

Source: https://www.browserbase.com/pricing

Observed public pricing model:

- Free plan exists for prototyping.
- Developer plan is listed at `$20/mo`.
- Startup plan is listed at `$99/mo`.
- Plans expose browser hours, concurrent browsers, search/fetch calls, proxy
  bandwidth, overage rates, and retention.

Scout lesson:

- Browser capacity is its own product cost.
- Scout's `browser_credits` bucket is directionally correct.
- A hosted browser feature should never be bundled into a tiny one-time payment
  without a hard cap.

### Apify

Source: https://apify.com/pricing

Observed public pricing model:

- Free plan includes small monthly spend.
- Starter, Scale, and Business plans combine monthly payment with prepaid usage.
- Compute units remain a central consumption metric.

Scout lesson:

- If Scout becomes a hosted platform, usage must survive beyond a one-time
  checkout through either finite credit packs or subscription plans.

### Tavily

Source: https://docs.tavily.com/documentation/api-credits

Observed public pricing model:

- Free monthly API credits.
- Pay-as-you-go per credit.
- Monthly plans with lower per-credit rates.
- Enterprise custom pricing.

Scout lesson:

- A credit model is accepted for AI-agent retrieval APIs.
- Scout should expose clear credit cost per action in docs and `/v1/hosted/me`.

### Exa

Source: https://exa.ai/pricing

Observed public pricing model:

- Free monthly request allowance.
- Search, contents, deep search, monitors, and agent runs are priced
  differently.
- Agent costs vary by compute/tool effort.

Scout lesson:

- Avoid pretending all "web intelligence" calls cost the same.
- Future Scout intelligence runs may need higher or separate pricing than basic
  `/scrape`.

### ScrapingBee

Sources:

- https://www.scrapingbee.com/pricing/
- https://www.scrapingbee.com/faq/
- https://help.scrapingbee.com/en/article/available-plans-explained-kbinm/

Observed public pricing model:

- Free credits are used for trial.
- Paid plans provide monthly API credit pools.
- Request options can cost multiple credits.

Scout lesson:

- Feature multipliers need to be visible before users run expensive actions.
- Browser/render/proxy-like features should show estimated cost before run
  start.

### ScraperAPI

Sources:

- https://www.scraperapi.com/pricing/
- https://docs.scraperapi.com/getting-started/quick-start/credits-and-requests-costs
- https://docs.scraperapi.com/resources/faq/plans-and-billing

Observed public pricing model:

- Plan credits drive usage.
- Pay-as-you-go can extend usage on higher plans.
- Unused credits may reset at renewal.

Scout lesson:

- Credit expiration/retention language must be explicit.
- If Scout adds recurring plans later, credit rollover/reset needs a deliberate
  policy.

### Zyte

Sources:

- https://www.zyte.com/zyte-api/
- https://www.zyte.com/pricing/
- https://docs.zyte.com/zyte-api/pricing.html

Observed public pricing model:

- Website difficulty affects price.
- Browser-rendered responses cost more than basic HTTP responses.
- Pay-as-you-go and minimum-commitment options exist.

Scout lesson:

- Hard-site pricing cannot be flat without losing money.
- The current private beta can use simple buckets, but public plans should
  eventually price by action/difficulty or route browser work to a separate
  add-on.

## Recommendation For Scout

Keep the current private-beta offer:

```text
Local Scout: free.
Hosted beta pass: $22 one-time, finite credits.
Standard credits: 2,000.
Browser credits: 100.
Artifact retention: 7 days.
Max pages per run: 100.
Max concurrent hosted runs: 1.
```

Do not approve public pricing yet.

Before public hosted launch, choose one of:

1. **Credit-pack model:** one-time credit packs that expire or have retention
   limits.
2. **Starter subscription:** monthly plan with included standard/browser
   credits and overage disabled until billing maturity improves.
3. **Hybrid:** free local + `$22` beta pass + later monthly hosted plans once
   beta usage is measured.

Recommended next step:

- Keep `$22` as a private beta pass only.
- Collect real hosted run cost/usage data.
- Do not market a permanent one-time hosted plan.
- Do not add subscription copy until Stripe test-mode checkout/webhook and
  support operations are verified.
