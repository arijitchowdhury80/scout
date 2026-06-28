# Pricing And Payment Recommendation

Date: 2026-06-28

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

## Scout Pricing Principles

1. **Local should be free or very low friction.**
   Local users bring their own compute and storage, so Scout's marginal cost is
   near zero.

2. **Hosted must be metered.**
   Hosted fetches, browser minutes, screenshots, LLM calls, storage, and retries
   cost money.

3. **One-time payment can be a beta offer, not unlimited service.**
   A $22 one-time plan can work only with hard limits.

4. **Do not sell "unlimited hard-site scraping."**
   That is operationally and legally risky.

## Recommended Pricing For Private Beta

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

This is not Stripe integration yet. It is the policy layer that Stripe
provisioning, API-key middleware, and run admission control should use.

## Public Website Pricing Copy

Use plain language:

```text
Local Scout is free. Run it on your machine and keep your artifacts where you
want them.

Hosted Scout is for convenience. It includes managed API keys, hosted workers,
and usage credits. Browser automation is metered because it costs real compute.
```
