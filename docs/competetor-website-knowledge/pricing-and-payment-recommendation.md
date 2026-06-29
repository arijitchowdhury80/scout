# Pricing And Payment Recommendation

Date: 2026-06-28
Updated: 2026-06-29

## 2026-06-29 Pricing Update

The earlier `$22` hosted beta pass and `$9/month` starter concepts are no
longer recommended prices. Arijit rejected them as arbitrary. They remain in
this document only as historical examples of finite-credit thinking, not as
approved pricing.

The active plan is now:

- free local beta;
- invite-only hosted free allowance for validation;
- pay-as-you-go or prepaid hosted credits as the first paid model;
- subscriptions only after usage telemetry supports predictable recurring
  value;
- pricing derived from the unit-economics model in
  `docs/product/unit-economics-and-pricing-model-2026-06-29.md`.

## Market Pattern

Competitors generally do not sell unlimited hosted crawling for a small one-time
fee. They use:

- free trials,
- monthly subscriptions,
- credits/request quotas,
- browser-session metering,
- team plans,
- enterprise/sales-assisted pricing.

This is rational because crawling and browser automation have variable cost.
See `market-pricing-snapshot-2026-06-28.md` for the current official-site
evidence snapshot.

## Scout Pricing Principles

1. **Local should be free or very low friction.**
   Local users bring their own compute and storage, so Scout's marginal cost is
   near zero.

2. **Hosted must be metered.**
   Hosted fetches, browser minutes, screenshots, LLM calls, storage, and retries
   cost money.

3. **One-time payment is not the default recommendation.**
   If used at all, a one-time beta pack must be finite, capped, and justified by
   measured costs.

4. **Do not sell "unlimited hard-site scraping."**
   That is operationally and legally risky.

## Historical Pricing Sketch For Private Beta

This section is superseded by the 2026-06-29 update above. Do not use these
numbers on the public website or checkout flow without a new founder approval.

### Local

**Free**

- CLI/API/local service.
- User stores artifacts locally.
- User brings optional provider keys.
- Community support / best-effort docs.

CTA: `Install locally`

### Hosted Beta Pass

**$22 one-time beta pass**

Use this only as a limited, early-access product:

- 1 hosted API key.
- Fixed credit allotment, for example 2,000 standard page credits.
- Browser/session credits separate and small, for example 100 browser credits.
- 7-day artifact retention.
- No guaranteed unblock.
- No unlimited usage.

CTA: `Get hosted beta access`

This should be copy-framed as:

```text
One-time beta access. Includes finite hosted credits. Local Scout remains free.
```

Do not frame it as lifetime hosted access.

### Hosted Starter

**$9/month**

- Monthly credits.
- Reasonable rate limits.
- Hosted artifact retention.
- No heavy browser usage beyond included credits.

### Hosted Pro

**$29/month**

- Higher credits.
- More browser/session credits.
- Longer retention.
- Team-ready usage logs.

### Enterprise / Self-Hosted

Custom:

- dedicated deployment,
- private worker pool,
- custom retention,
- compliance/security review,
- support.

## Credit Model Sketch

Start simple:

| Action | Suggested Credit Cost |
|---|---:|
| Direct fetch/scrape | 1 |
| Crawl discovered page | 1 |
| Screenshot | 3 |
| Scout browser page render | 5 |
| Browser minute | 10 |
| LLM extraction call | pass-through or separate |
| Stored artifact bundle over retention | storage metered |

Hard limits:

- max pages per run,
- max run duration,
- max concurrent runs,
- max browser minutes/day,
- max artifact retention.

## Why Not Unlimited $22

Bad scenario:

- 1,000 users pay $22 = $22,000 gross.
- A small fraction run millions of pages or browser minutes.
- Hosted costs outpace revenue quickly.
- Abuse and support burden rise.

The one-time offer should buy **credits/access**, not unlimited hosted
infrastructure.

## Superseded Recommendation After Market Refresh

The prior recommendation was:

1. **Local free** as the main distribution path.
2. **$22 hosted beta pass** as finite credits for early adopters.
3. **No lifetime/unlimited hosted promise.**
4. **Subscriptions only after usage data is measured**, likely:
   - Starter: `$9/month` for light hosted use,
   - Pro: `$29/month` for heavier records/browser use,
   - Enterprise/self-host: custom.
5. **Separate browser credits** because browser rendering costs materially more
   than simple HTTP acquisition.

Updated recommendation: replace step 2 and the `$9/month` examples with a
unit-economics-driven pay-as-you-go/prepaid credit model.

## Decision Boundary For Launch

The launch site can show the private-beta offer, but it should not imply that
hosted Scout is generally self-serve or unlimited.

Previous beta-safe copy, now superseded:

```text
Hosted beta pass: finite hosted credits for approved testers.
Local Scout remains free.
Browser-heavy workflows use separate, smaller credits.
```

Unsafe copy:

```text
Pay $22 and use hosted Scout forever.
Unlimited hosted crawling.
Unlimited browser extraction.
Public self-serve API access.
```

Rationale: competitor pricing pages consistently separate free/local adoption
from hosted infrastructure cost. Scout should follow the market economics while
keeping its local-first differentiation.

## Payment Stack Recommendation

Hosted beta:

- Stripe Checkout for one-time beta pass and subscriptions.
- Stripe Customer Portal for subscription management.
- Webhook to provision credits/API key.
- Internal `usage_events` table.
- API middleware checks active plan and remaining credits.

Tables needed:

- `users`
- `api_keys`
- `plans`
- `subscriptions`
- `credit_balances`
- `usage_events`
- `runs`
- `artifacts`

Implementation seed now exists in code:

- `HostedPlan`
- `HostedAction`
- `HostedPlanLimits`
- `HostedUsageBalance`
- `HostedUsageDecision`
- `plan_limits(...)`
- `check_hosted_usage(...)`
- `HostedPaymentProvisioningService`
- `SQLiteHostedPaymentStore`

This is not a full Stripe integration yet. It is the policy and provisioning
core that a Stripe webhook should call after signature verification. The
current payment provisioning layer records processed checkout sessions so
webhook retries do not create duplicate keys and the raw API key is only
returned on first processing.

## Public Website Pricing Copy

Use plain language:

```text
Local Scout is free. Run it on your machine and keep your artifacts where you
want them.

Hosted Scout is for convenience. It includes managed API keys, hosted workers,
and usage credits. Browser automation is metered because it costs real compute.
```
