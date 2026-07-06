# Scout Pricing Model — LOCKED 2026-07-06 (supersedes earlier)

Decided with Arijit this session. Supersedes the "50 dossiers / $12 unlimited" framing in
[[scout-saas-launch-state]] memory.

## Tiers
| Tier | Price | Credits | Notes |
|---|---|---|---|
| **Free (GA)** | $0 | **5,000** one-time | Public free tier. Acquisition hook (PLG). |
| **Beta** | $0 | 10,000 / 30 days | Existing beta cohort — unchanged, already shipped. Separate from GA free. |
| **Monthly** | **$12/mo** | **50,000 / month** | Hero plan (MRR). Resets each cycle, hard-stop at cap. **NOT called "unlimited."** |
| Pay-go (demoted) | $10 / $25 / $100 | 10k / 30k / 150k | One-time packs, never expire. Secondary. |
| Heavy (future) | $49 / $99 (TBD) | 250k / 1M (TBD) | Penciled for expansion revenue. Not at launch. |

## Naming rule (brand integrity)
Never say "unlimited" for a capped plan — it contradicts Scout's honesty brand. Say the number:
"50,000 credits / month."

## Credit → capability (dossier standardized at ~200 credits)
- 1 credit = 1 scrape / crawled page / product / record
- 3 = screenshot · 5 = browser render · 10 = browser minute
- **1 company dossier ≈ 200 credits** (representative company crawl; varies by site size)
- Monthly 50k mix (marketed): **20,000 pages + 10,000 products + 100 dossiers** (= 20k+10k+20k = 50k) ✓
- Free 5k ≈ 5,000 pages · or 25 dossiers · or 2 product catalogs

## Per-credit ladder (now coherent — no arbitrage)
Pay-go $10/10k=0.10¢ → $25/30k=0.083¢ → $100/150k=0.067¢ (volume discount) · Monthly $12/50k=0.024¢
(cheapest, recurring). Pay-go = no-commit premium; Monthly = commitment discount. Gap ~4×, not the
old broken ~40×.

## Unit economics
- **Marginal cost per credit ≈ $0** (self-hosted, no LLM, own VPS ~$80/yr). Credit generosity is
  nearly free on the cost side.
- **$12/mo ≈ $11.35 net** after Stripe (~2.9% + $0.30) → ~95% gross margin per subscriber.
- **Binding constraint = hardware capacity, not $.** If many subs maxed 50k/mo the shared box (with
  PRISM/Hermes) couldn't serve it. Managed by rate limits (8-active cap) + the documented GA scaling
  (Redis/shared-state + workers + bigger VPS, funded by MRR). 50k is a deliberate, affordable
  land-grab bet that most users won't max.

## Market focus
Market the **Monthly subscription** hardest (MRR = the durable business). Free = acquisition hook;
pay-go = fallback for non-committers. $12 caps revenue/customer → add the heavy tier for expansion.
