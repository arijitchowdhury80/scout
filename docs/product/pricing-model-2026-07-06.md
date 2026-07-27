# Scout Pricing Model — LOCKED 2026-07-06, simplified 2026-07-27 (supersedes earlier)

Decided with Arijit this session. Supersedes the "50 dossiers / $12 unlimited" framing in
[[scout-saas-launch-state]] memory.

**2026-07-27 update (founder decision):** simplified to exactly two paid tiers. The $25/30k
and $100/150k pay-go packs are retired entirely (not merely hidden). Monthly repriced from
50,000 to 20,000 credits/month; the $10 one-time pack repriced from 10,000 to 15,000 credits.

## Tiers
| Tier | Price | Credits | Notes |
|---|---|---|---|
| **Free (GA)** | $0 | **5,000** one-time | Public free tier. Acquisition hook (PLG). |
| **Beta** | $0 | 5,000 / 30 days | Beta cohort. Matches the deployed HOSTED_BETA_PASS (5,000 standard + 100 browser credits). Separate from GA free. |
| **Monthly** | **$12/mo** | **20,000 / month** | Hero plan (MRR). Resets each cycle, hard-stop at cap. **NOT called "unlimited."** |
| Pay-go (demoted) | $10 | 15k | One one-time pack, never expires. Secondary. |
| Heavy (future) | $49 / $99 (TBD) | 250k / 1M (TBD) | Penciled for expansion revenue. Not at launch. |

## Naming rule (brand integrity)
Never say "unlimited" for a capped plan — it contradicts Scout's honesty brand. Say the number:
"20,000 credits / month."

## Credit → capability (dossier standardized at ~200 credits)
- 1 credit = 1 scrape / crawled page / product / record
- 3 = screenshot · 5 = browser render · 10 = browser minute
- **1 company dossier ≈ 200 credits** (representative company crawl; varies by site size)
- Monthly 20k mix (marketed): **8,000 pages + 4,000 products + 40 dossiers** (= 8k+4k+8k = 20k) ✓
- Pay-go $10/15k mix (marketed): **15,000 pages, or 75 dossiers**
- Free 5k ≈ 5,000 pages · or 25 dossiers · or 2 product catalogs

## Per-credit ladder
Pay-go $10/15k = 0.067¢/credit · Monthly $12/20k = 0.06¢/credit (cheapest, recurring). Pay-go =
no-commit premium; Monthly = commitment discount. The gap is intentionally tight now — two
tiers, priced close, so the decision is "commit or not," not "which volume discount."

## Unit economics
- **Marginal cost per credit ≈ $0** (self-hosted, no LLM, own VPS ~$80/yr). Credit generosity is
  nearly free on the cost side.
- **$12/mo ≈ $11.35 net** after Stripe (~2.9% + $0.30) → ~95% gross margin per subscriber.
- **Binding constraint = hardware capacity, not $.** If many subs maxed 20k/mo the shared box (with
  PRISM/Hermes) couldn't serve it. Managed by rate limits (8-active cap) + the documented GA scaling
  (Redis/shared-state + workers + bigger VPS, funded by MRR). 20k is a deliberate, affordable
  land-grab bet that most users won't max.

## Market focus
Market the **Monthly subscription** hardest (MRR = the durable business). Free = acquisition hook;
pay-go = fallback for non-committers. $12 caps revenue/customer → add the heavy tier for expansion.
