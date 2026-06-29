# Hosted Economics And Usage Limits

Date: 2026-06-28
Status: Recommendation documented; final commercial approval still pending

## Decision Summary

Scout should launch with this commercial posture:

- **Local Scout stays free for private beta.**
- **Hosted Scout is paid convenience, not the primary value wedge.**
- **The `$22` one-time hosted beta pass must be finite credits, not unlimited
  lifetime hosted crawling.**
- **Browser/rendered work must be metered separately from ordinary page
  acquisition.**
- **Subscriptions can follow after private-beta usage data is measured.**

This keeps Scout's strongest promise intact: users can run acquisition locally
when privacy, artifact ownership, cost control, or user-browser capture matters.
Hosted exists for convenience, demos, and users who do not want to run local
workers.

## Why Unlimited Hosted Access Is Unsafe

Hosted crawling has variable cost:

- outbound fetches and retries,
- browser rendering and screenshots,
- worker CPU and memory,
- network egress,
- artifact storage and retention,
- support burden,
- abuse handling,
- optional LLM extraction/enrichment.

Competitor pricing reinforces this: crawler, browser, search, and extraction
products generally use credits, subscriptions, quotas, pay-as-you-go, or
enterprise plans. None of the reviewed mature competitors position a low
one-time payment as unlimited hosted crawling.

Reviewed market references:

- Firecrawl: `https://www.firecrawl.dev/pricing`
- Apify: `https://apify.com/pricing`
- Browserbase: `https://www.browserbase.com/pricing`
- ScrapingBee: `https://www.scrapingbee.com/pricing/`
- ScraperAPI: `https://www.scraperapi.com/pricing/`
- Tavily: `https://www.tavily.com/pricing`
- Exa: `https://exa.ai/pricing`
- Zyte: `https://www.zyte.com/pricing/`
- Diffbot: `https://www.diffbot.com/pricing/`

Detailed market notes live in:

- `docs/competetor-website-knowledge/market-pricing-snapshot-2026-06-28.md`
- `docs/competetor-website-knowledge/market-pricing-refresh-2026-06-29.md`
- `docs/competetor-website-knowledge/pricing-and-payment-recommendation.md`

The 2026-06-29 refresh checked current public pricing signals for Firecrawl,
Browserbase, Apify, Tavily, Exa, ScrapingBee, ScraperAPI, and Zyte. The same
conclusion held: mature crawler, browser, search, and extraction products meter
usage through credits, subscriptions, overage, or enterprise plans. None of the
reviewed vendors support the idea that `$22` should buy unlimited hosted
crawling.

## Private Beta Hosted Pass

Recommended offer:

```text
$22 one-time hosted beta pass.
Includes finite hosted credits.
Local Scout remains free.
No unlimited hosted crawling.
```

Current code-aligned beta pass limits:

| Limit | Current value |
|---|---:|
| Standard credits | 2,000 |
| Browser credits | 100 |
| Artifact retention | 7 days |
| Max pages per run | 100 |
| Max concurrent hosted runs | 1 |

Current action costs:

| Hosted action | Credit bucket | Cost |
|---|---|---:|
| Scrape | standard | 1 |
| Crawl page | standard | 1 |
| Screenshot | standard | 3 |
| Browser render | browser | 5 |
| Browser minute | browser | 10 |

These values are implemented in `scout.core.platform.hosted` and covered by
unit tests. They are beta policy defaults, not final public pricing.

## Hosted Product Boundary

Hosted Scout should be described as:

- a managed API key,
- hosted workers,
- finite usage credits,
- limited artifact retention,
- safer onboarding for users who do not want local setup.

Hosted Scout should **not** be described as:

- unlimited scraping,
- guaranteed hard-site bypass,
- production multi-tenant SaaS readiness,
- a replacement for legal review or website permission,
- the only way to use Scout.

## Subscription Direction

After private beta, use observed usage to decide whether subscriptions are
worth launching. A plausible future structure:

| Plan | Purpose | Guardrail |
|---|---|---|
| Local Free | local CLI/API/Docker adoption | user brings compute and storage |
| Hosted Beta Pass | early hosted validation | finite one-time credit pack |
| Hosted Starter | lightweight recurring hosted API | monthly credits and rate limits |
| Hosted Pro | heavier hosted records/browser use | higher credits, retention, logs |
| Enterprise/Self-hosted | dedicated/private deployment | custom support and security terms |

Do not launch a subscription until:

- Stripe test-mode checkout and webhook have been smoke-tested,
- hosted usage logs can support billing analysis,
- support process is defined,
- public terms/privacy are lawyer-reviewed,
- dependency and security launch blockers are closed or accepted.

## Website Copy Guidance

Good:

```text
Run Scout locally for free. Use hosted Scout when you want managed workers and
a hosted API key. Hosted beta includes finite credits; browser work is metered
because it uses real compute.
```

Bad:

```text
Pay once and scrape unlimited pages forever.
```

## Release Checklist Impact

This document satisfies the documentation portion of:

```text
Hosted economics and usage limits documented against the `$22` beta pass and
any subscription alternative.
```

It does **not** approve final public launch pricing. That remains a separate
business decision.
