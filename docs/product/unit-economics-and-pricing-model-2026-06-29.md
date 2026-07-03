# Scout Unit Economics And Pricing Model

Date: 2026-06-29
Status: Launch candidate model defined; final paid launch still requires founder approval and Stripe verification

## Recommended Launch Candidate As Of 2026-07-03

Recommended launch candidate as of 2026-07-03:

- Local Scout remains free.
- Beta trial: 30 days, 100 standard credits, $0 charge, payment method required through Stripe setup-mode once hosted billing is configured.
- First pay-as-you-go package: $10 for 1,000 standard credits.
- Browser-heavy work is not included in the first public pay-as-you-go package.
- Browser credits remain private/controlled until browser-worker cost is measured.
- Subscriptions remain deferred until usage telemetry proves recurring demand.

What the first $10 package gives the customer:

| Unit | Customer meaning |
|---|---|
| 1 scrape | 1 scrape = 1 standard credit |
| 1 returned crawl page | 1 returned crawl page = 1 standard credit |
| 1 product/intelligence record | 1 record = 1 standard credit |
| 1 screenshot | 1 screenshot = 3 standard credits |
| 1 browser render | 1 browser render = 5 browser credits |
| 1 browser minute | 1 browser minute = 10 browser credits |

Default unit-economics calculation for the $10 / 1,000 standard-credit package:

Estimated cost for 1,000 standard credits: $2.59. Estimated gross margin: 74.1%. Break-even: 17 packs/month.

| Line item | Value |
|---|---:|
| Revenue | $10.00 |
| Variable hosted cost | $1.50 |
| Payment processing | $0.59 |
| Allocated support | $0.50 |
| Estimated cost for 1,000 standard credits | $2.59 |
| Gross profit | $7.41 |
| Estimated gross margin | 74.1% |
| Fixed monthly cost assumption | $120 |
| Break-even | 17 packs/month |

This model is implemented in `scout.core.platform.pricing`, returned by
`GET /v1/billing/packages`, and rendered on the pricing page from the live
billing model. The response includes both the package economics and the
assumptions behind them: fixed monthly cost, standard-credit cost,
browser-credit cost, allocated support cost, payment percent fee, payment fixed
fee, and target gross margin. It is a launch candidate, not an irrevocable
public price. If hosting, LLM, browser, firewall, storage, support, or payment
costs change, change the package before enabling paid checkout.

## Decision Update

The previous `$22` one-time hosted beta pass and `$9/month` hosted starter ideas
are **not approved pricing**. They were placeholders for a finite-credit beta
model, but Arijit rejected them as arbitrary. Scout pricing now has to be
derived from unit economics before the website, checkout, or launch plan can
claim a specific hosted price.

The current recommended direction is:

- local Scout remains free for users who bring their own compute, browser,
  storage, and keys;
- hosted Scout starts with a small free allowance or invite-only test credits;
- paid hosted Scout should be pay-as-you-go or prepaid credits first;
- subscriptions should come later only if usage telemetry proves predictable
  recurring value;
- browser/rendered/LLM-heavy work must be priced separately from simple page
  fetches.

## Why This Matters

Scout has real hosted costs. A flat price is dangerous unless we know:

- fixed monthly operating cost;
- variable cost per run, page, browser minute, screenshot, artifact bundle, and
  LLM extraction;
- payment processor fees;
- support/security/maintenance cost per active customer;
- target gross margin;
- break-even volume.

If Scout underprices hosted work, a small number of heavy users can consume more
compute, browser time, storage, LLM calls, and support than they paid for. If
Scout overprices before proving value, private beta adoption will stall.

## Cost Buckets

### Fixed Monthly Costs

| Cost bucket | Examples | Owner |
|---|---|---|
| Hosting base | Hostinger/VPS/container host, database, backups | Scout |
| Security edge | firewall/WAF, rate limiting, abuse controls, secret scanning | Scout |
| Monitoring | logs, uptime, metrics, alerting | Scout |
| Support tooling | support inbox, docs site, issue triage, customer messages | Scout |
| Maintenance | patching, dependency audits, release work, incident response | Scout |
| Payment operations | Stripe setup, bookkeeping, tax/accounting overhead | Scout |

### Variable Usage Costs

| Unit | Cost drivers |
|---|---|
| Direct scrape | HTTP request, retries, bandwidth, parser CPU |
| Crawl page | fetch, link discovery, dedupe, artifact writes |
| Rendered page | browser CPU/RAM, page load time, screenshots, network diagnostics |
| Browser minute | Playwright/Puppeteer worker time, proxy if configured, screenshots |
| Screenshot | browser render plus image storage and transfer |
| LLM extraction | prompt tokens, output tokens, retries, structured extraction validation |
| Artifact storage | raw HTML, markdown, screenshots, records, reports, retention period |
| Support event | human/debug time when a run fails, blocks, or needs explanation |

## Pricing Formula

Use this model before approving any public hosted number:

```text
fixed_monthly_cost =
  hosting_base
  + security_edge
  + monitoring
  + support_tooling
  + maintenance_allocation
  + payment_operations

variable_run_cost =
  direct_pages * cost_per_direct_page
  + rendered_pages * cost_per_rendered_page
  + browser_minutes * cost_per_browser_minute
  + screenshots * cost_per_screenshot
  + llm_calls * cost_per_llm_call
  + artifact_mb_days * cost_per_artifact_mb_day
  + expected_support_minutes * cost_per_support_minute

loaded_cost_per_paid_unit =
  variable_run_cost
  + payment_fee_per_unit
  + allocated_fixed_cost_per_unit

minimum_price =
  loaded_cost_per_paid_unit / (1 - target_gross_margin)

break_even_paid_units =
  fixed_monthly_cost / gross_profit_per_paid_unit
```

Target margin should be explicit. For a hosted developer API, a reasonable early
target is usually 60-80 percent gross margin after variable infrastructure and
payment fees, with a separate allowance for support and maintenance.

## First Pricing Hypothesis

This is the pricing structure to test, not final pricing:

| Tier | Purpose | Pricing posture | Guardrails |
|---|---|---|---|
| Local Free | adoption, skill/CLI/API testing, private artifacts | free | user brings compute/storage/keys |
| Hosted Free | proof of value | small monthly or invite credits | hard caps, short retention, no heavy browser allowance |
| Pay As You Go | honest hosted economics | prepaid credits or wallet top-up | credits expire or retain capped artifacts; browser/LLM costs visible |
| Team/Pro | only after telemetry | monthly commitment plus credits | higher limits, longer retention, support SLA if justified |
| Enterprise/Self-hosted | controlled deployments | custom | dedicated workers, security review, custom retention |

## Credit Design

Credits should map to cost, not marketing fantasy:

| Action | Suggested credit class | Pricing note |
|---|---|---|
| Direct scrape | standard | cheap, high-volume unit |
| Crawl page | standard | cheap unless retries explode |
| Screenshot | render | more expensive than scrape |
| Scout browser page render | browser | separate pool or higher multiplier |
| Browser minute | browser | metered tightly |
| LLM extraction | AI | pass-through plus margin or separate AI credits |
| Artifact retention beyond default | storage | retention is a product decision and cost center |

## Required Inputs Before Final Pricing

- Current Hostinger or hosting plan cost.
- Current LLM model pricing for any hosted extraction defaults.
- Current WAF/firewall/security service cost.
- Current support tooling cost.
- Expected maintenance hours per month and internal hourly cost.
- Expected payment processor fees for US and international cards.
- Expected private-beta average usage:
  - pages per run,
  - rendered pages per run,
  - browser minutes per run,
  - LLM calls per run,
  - artifact MB per run,
  - support tickets per active user.
- Target gross margin and minimum monthly profit goal.

## Website Copy Rule

Until this model is filled with real costs and founder-approved pricing, the
public website must not show `$22`, `$9/month`, or any other arbitrary hosted
price. It can say:

```text
Local Scout is free during beta. Hosted Scout is metered and invite-only while
we validate unit economics. Pricing will be based on actual compute, browser,
LLM, storage, security, and support costs.
```

## Launch Checklist Impact

The public pricing gate remains open. Closure requires:

1. cost inputs populated;
2. usage assumptions documented;
3. break-even table generated;
4. founder approval recorded;
5. website pricing page updated to the approved structure;
6. checkout configuration aligned with the approved structure;
7. verification that no stale `$22` or `$9` pricing claims remain in public
   website copy.
