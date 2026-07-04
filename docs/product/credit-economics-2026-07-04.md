# Scout Credit Economics & Business Model — Beta Launch
**Date:** 2026-07-04 · **Status:** Beta grant APPROVED by Arijit (1,000 std + 100 browser, 30 days).
Paid-tier margins below are for reference; live pricing stays a "launch candidate, not a forever price."

## The one insight that reframes everything
Scout is **self-hosted on a fixed-cost VPS, uses no LLM, and makes no per-call cloud API calls.**
So the **marginal cost of one scrape ≈ $0.** There is no OpenAI/Anthropic bill, no per-request
metered infra. The only real money is: (1) the fixed VPS you already pay for, (2) Stripe's fee on
*paid* purchases, (3) email (Resend, free tier). This makes the committed placeholder cost
(`0.15¢/credit` = $1.50/1,000) roughly 10× too pessimistic for a self-hosted box.

## What a credit buys the user
1 standard credit = 1 scrape, OR 1 returned crawl page, OR 1 product/intelligence record.
3 standard credits = 1 screenshot. Browser work is separately metered (5 browser credits/render,
10/browser-minute). So **1,000 standard credits ≈ 1,000 scrapes / 1,000 crawl pages / 333
screenshots / 1,000 intel records.**

## What 1,000 credits actually COST Arijit
| Cost component | Amount per 1,000 credits | Basis |
|---|---|---|
| Infra (fully allocated) | ~$0.14 | $14/mo VPS ÷ ~100k sustainable ops/mo × 1,000. Marginal cost is ~$0; this is the generous fully-loaded share. |
| Stripe fee (paid sales only) | ~$0.59 | 2.9% + $0.30 on a $10 charge. **$0 for invited beta (no charge).** |
| Support/ops allocation | ~$0.50 | Judgment reserve. |
| **Loaded cost (paid $10 pack)** | **~$1.23** | Infra + Stripe + support. |
| **Margin at $10 / 1,000** | **~88%** | ($10 − $1.23) / $10. Better than the placeholder's 74%. |

VPS = Hostinger KVM (2 vCPU AMD EPYC 9354P, 7.8 GiB RAM, 96 GB disk), **shared with PRISM +
Hermes**, so attributing the whole ~$14/mo to Scout is conservative.

## Beta trial cost exposure (250 testers) — APPROVED
- **Grant:** 1,000 standard + 100 browser credits per tester, 30-day trial. Charged **$0** (invited;
  card captured via Stripe `setup` mode, never billed).
- **Total granted:** 250 × 1,000 = **250,000 standard** + 25,000 browser credits.
- **Real 30-day cost to Arijit:** fixed VPS (~$14, already sunk) + Resend (free tier, 3,000
  emails/mo covers 250 signups) + Stripe ($0, no charges) = **~$14, effectively $0 incremental.**
- **Break-even:** trivially met — there is no marginal cost per credit and no charges. The trial
  cannot lose money; worst case is opportunity cost of VPS capacity.
- **Capacity sanity check:** 250k standard ops over 30 days = **~8,333 ops/day** = ~0.1 ops/sec
  average. The box throttles to 8 active requests (queue 250); theoretical ceiling is ~3 ops/sec
  sustained → the beta uses a low single-digit % of capacity on average. Bursts are absorbed by
  the queue. ✅ Comfortable for scrapes; browser-heavy bursts are the real stress point (see
  hardware note — recommend adding swap before heavy concurrent browser use).

## Why the generous grant is the right call
The beta's purpose is for 250 people to *hammer every feature*. Since marginal cost ≈ $0, a stingy
100-credit grant would just cause testers to hit the wall mid-session and stop testing — pure
downside. 1,000 std + 100 browser lets them exercise the full surface without gating, at ~$0 cost.

## Paid packages (reference, unchanged)
| Package | Price | Credits | Loaded cost | Margin |
|---|---|---|---|---|
| standard_1000 | $10 | 1,000 std | ~$1.23 | ~88% |
| standard_3000 | $25 | 3,000 std | ~$2.6 | ~90% |
| standard_15000 | $100 | 15,000 std | ~$9 | ~91% |
| browser_100 | $20 | 100 browser | (private until browser costs validated) | — |

## Where this is hardcoded (single source of truth)
- Actual granted balance: `plan_limits(HOSTED_BETA_PASS)` in `scout/core/platform/hosted.py`
  (1,000 std / 100 browser). Provisioning reads this.
- Display/Stripe package: `beta_trial` in `scout/core/platform/pricing.py`.
- Email copy derives its numbers from `plan_limits` (no drift) — `scout/api/routers/hosted.py`.
- Trial length: `_BETA_TRIAL_DAYS = 30` in `scout/api/routers/hosted.py`.

## Open items for go-live (business, not code)
- Confirm the real Hostinger monthly bill to replace the ~$14 estimate above (Arijit's invoice).
- Set Stripe test keys + price IDs to activate paid purchase (item 6).
- Set Resend SMTP creds so beta keys actually deliver (item 2 — currently unset in prod).
