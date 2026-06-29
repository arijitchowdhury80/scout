# Scout Website Decision Map

Date: 2026-06-29

Status: competitor-research-to-website decision map

This map is derived from the competitor research folder. It explains how the
research shaped the current Scout website, which files implement each decision,
and which claims remain blocked.

## Source Research Used

- `competitor-matrix.md`
- `website-patterns.md`
- `market-pricing-snapshot-2026-06-28.md`
- `market-pricing-refresh-2026-06-29.md`
- `pricing-and-payment-recommendation.md`
- `production-readiness-and-distribution.md`
- `scout-differentiation.md`
- `scout-website-plan.md`

Competitor patterns referenced here include Firecrawl, Browserbase, Apify,
Tavily, Exa, ScrapingBee, ScraperAPI, Zyte, Diffbot, Jina Reader, and Crawl4AI.

## Website sections now backed by research

| Website decision | Research signal | Current implementation |
|---|---|---|
| Lead with "citable, downstream-ready records" instead of generic crawling | Firecrawl owns the clean hosted scrape/crawl/message lane; Scout needs the evidence + typed-record wedge. | `website/index.html`, `docs/product/differentiation.md` |
| Use split CTAs: `Install locally` and `Join hosted beta` | Competitors use get-started/API-key CTAs, but Scout's safe beta posture is local-first with optional hosted convenience. | `website/index.html`, `website/quickstart.html`, `website/beta.html` |
| Show artifact/evidence model early | Competitor sites often show markdown/API output; Scout differentiates through source pages, blocked pages, citations, validation, and reports. | `website/index.html`, `website/status.html` |
| Keep pricing finite and metered | Firecrawl, Browserbase, Apify, Tavily, Zyte, and similar products meter hosted work through credits, browser hours, compute, or plan allowances. | `website/pricing.html`, `docs/product/hosted-economics-and-usage-limits.md` |
| Separate browser/rendered work from standard fetches | Browserbase and Zyte make browser/rendered acquisition visibly expensive. | `website/pricing.html`, hosted plan credit buckets |
| Avoid marketplace/platform claims | Apify validates the platform/marketplace model, but Scout does not have marketplace maturity. | website copy avoids actor marketplace claims |
| Keep docs/API path visible | Firecrawl, Tavily, Exa, and Browserbase all use docs as a primary developer conversion path. | `/docs`, `website/quickstart.html`, README |
| State launch boundaries visibly | Beta trust depends on not overstating hard-site, security, hosted-scale, or public-launch readiness. | `website/status.html`, `website/legal.html`, `website/beta.html` |

## Design System Decision

The website uses the Supadesign IndustrialGray direction rather than a generic
soft SaaS gradient style.

Why:

- Scout should feel like infrastructure: precise, inspectable, and technical.
- The product story depends on terminal readouts, artifact folders, source
  evidence, and status panels.
- The warm industrial grid supports a local-first utility rather than a glossy
  no-code app promise.

Current files:

- `website/assets/warm-industrial-design-system/warm-industrial.css`
- `website/styles.css`
- `website/index.html`
- `website/pricing.html`
- `website/status.html`
- `website/beta.html`

## Claims To Keep Out

Do not add these to the website, README, or beta materials:

- Better than Firecrawl.
- Firecrawl killer.
- No unlimited hosted crawling.
- No guaranteed hard-site bypass.
- Production-ready multi-tenant SaaS.
- Clean dependency/security posture before the audit gate closes.
- Certified app UI.
- Public self-serve hosted launch.

The legacy `/app` UI is not the product for launch. The launch product surface
is CLI, HTTP API, Docker-from-source, skill usage, hosted beta API for approved
testers, artifacts, and the static website.

## Public-launch copy still blocked

The current website can support controlled private beta only. Public-launch copy
still depends on:

- license decision,
- final license expression and `LICENSE`,
- registry publishing policy,
- Docker image publishing policy,
- real Stripe test-mode smoke,
- dependency audit/risk decision,
- final terms/privacy,
- release artifact smoke.

## Next Website Decisions

Before public launch:

1. Re-check competitor pricing pages and update the pricing refresh.
2. Decide whether the public hosted offer is subscription, credit pack, or both.
3. Replace beta legal placeholders with approved legal copy.
4. Add a short examples/docs path only for workflows with certification evidence.
5. Keep local install and artifact evidence as the primary differentiation.
