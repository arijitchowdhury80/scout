# Website Copy Review Against Competitor Research

Date: 2026-06-28
Status: Reviewed for private-beta launch positioning

## Scope

This review checks the current Scout static launch website against the
competitor research in `docs/competetor-website-knowledge/`.

Reviewed Scout pages:

- `website/index.html`
- `website/quickstart.html`
- `website/pricing.html`
- `website/beta.html`
- `website/legal.html`
- `website/terms.html`
- `website/privacy.html`
- `website/README.md`

Research inputs:

- `docs/competetor-website-knowledge/competitor-matrix.md`
- `docs/competetor-website-knowledge/website-patterns.md`
- `docs/competetor-website-knowledge/market-pricing-snapshot-2026-06-28.md`
- `docs/competetor-website-knowledge/pricing-and-payment-recommendation.md`
- `docs/competetor-website-knowledge/scout-differentiation.md`

## Verdict

The current website copy is aligned with the competitor research for private
beta. It should not be treated as final public-launch marketing, but it is safe
enough for controlled beta because it:

- leads with a clear outcome, not vague AI language;
- separates local install from hosted beta access;
- avoids "unlimited hosted crawling";
- avoids "guaranteed hard-site bypass";
- explains evidence, citations, blocked pages, and artifact folders;
- exposes pricing and checkout paths without embedding secrets;
- preserves `/docs` as API documentation instead of replacing it with marketing;
- states current launch blockers and legal/security limits.

## Competitor Pattern Coverage

| Competitor pattern | Scout implementation | Assessment |
|---|---|---|
| Hero with one-sentence outcome | Homepage: "Turn messy web pages into citable, downstream-ready records." | Pass. This is sharper than generic "crawler API" copy. |
| Split CTA | Homepage: "Install locally" and "Join hosted beta" | Pass. Matches local-first plus hosted convenience strategy. |
| Code sample / quickstart | Homepage and `/quickstart` include local install commands and `scout serve` path | Pass for private beta. Future public launch should add a short GIF/video. |
| Product primitives | Homepage shows scrape, crawl, map, browser capture, records, artifacts, citations | Pass. Does not overstuff the hero. |
| Use cases | Product catalogs, competitive intelligence, agent tools | Pass. Honest and current. |
| Docs path | Navigation keeps `/docs` as FastAPI/Swagger API docs and adds `/quickstart` | Pass. Developer-friendly. |
| Pricing | `/pricing` explains free local and finite hosted beta pass | Pass. Matches competitor credit/subscription economics. |
| Payment/free trial flow | `/beta` uses name/email API-key registration through `/v1/hosted/beta-key`; `/pricing` uses `/v1/billing/stripe/checkout-session` for paid hosted-credit packages. | Pass for current private-beta posture; SMTP key-delivery smoke and Stripe paid-checkout smoke remain pending. |
| FAQ/legal boundaries | `/legal`, `/terms`, and `/privacy` cover beta placeholders and third-party notices | Pass for private beta; lawyer-reviewed docs still required for broad commercial launch. |
| Trust/social proof | Not present | Acceptable for private beta. Do not fake logos or testimonials. |
| Enterprise security claims | Not present | Correct. Current security posture does not support enterprise claims. |

## Differentiation Review

The website does not try to out-position Firecrawl as a faster hosted markdown
API. That is the right call. Firecrawl, ScrapingBee, ScraperAPI, Apify,
Browserbase, Tavily, Exa, Zyte, and Diffbot all make stronger hosted-scale
claims than Scout can honestly support today.

Scout's site focuses on the differentiated wedge:

- local-first acquisition;
- source evidence;
- blocked-page evidence;
- citations;
- typed records;
- artifact folders;
- downstream exports;
- optional hosted convenience.

That is the correct private-beta story.

## Claims That Are Intentionally Avoided

The current website correctly avoids:

- "unlimited hosted scraping";
- "Firecrawl killer";
- "guaranteed unblock";
- "production-ready multi-tenant SaaS";
- "enterprise compliant";
- "lifetime API access";
- fake customer logos or testimonials;
- claims that Scout owns Crawl4AI.

These omissions are product discipline, not weakness.

## Copy Risks And Follow-Ups

| Risk | Impact | Follow-up |
|---|---|---|
| The site is honest but not yet emotionally polished | Beta users may understand Scout but not feel urgency | Add demo GIF/video showing URL -> records -> artifacts once flows are certified. |
| No social proof | Public visitors may not trust it yet | Use real beta quotes only after beta users provide them. |
| Pricing is beta-safe but not final | Public launch cannot proceed on draft pricing | Keep "Public launch pricing and hosted usage limits approved" unchecked. |
| Legal pages are placeholders | Commercial launch blocked | Replace with lawyer-reviewed terms/privacy before broad hosted launch. |
| `/docs` is Swagger, not a polished docs site | Developer onboarding is functional but plain | Build docs site only after API/CLI surface stabilizes. |

## Release Checklist Impact

This review satisfies:

```text
Website copy reviewed against competitor research.
```

It does **not** satisfy:

```text
Public launch pricing and hosted usage limits approved.
Stripe checkout and webhook tested in Stripe test mode.
Skill usage docs tested from current package.
Local install instructions tested on a fresh machine or clean container.
Docker install instructions tested from docs only.
```
