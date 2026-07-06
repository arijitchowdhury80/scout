# 01 — Intake · $12/mo "Unlimited" Subscription

**Date:** 2026-07-06 · **Requestor:** Arijit · **Run:** run-2026-07-06-001

## Scope classification → **FULL PATH**
Reasoning (technical surface, not team size):
- **External surface:** new Stripe recurring price + `mode=subscription` checkout + new webhook events (`invoice.paid`, `customer.subscription.deleted`).
- **New data flow:** subscription lifecycle + monthly credit reset — net-new state machine over the existing debit-only metering.
- **Security-sensitive:** money/billing. A reset bug = free unlimited credits or wrongful revocation.
→ Any one of these forces FULL. All three present. Not downgradable.

## 8-dimension intake (spec is pre-locked by Arijit)
1. **Problem/goal:** Recurring revenue tier. $12/mo for 50,000 credits/month, fair-use "unlimited". Serves builders/agencies that blow past one-time packs.
2. **Users:** Hosted Scout API subscribers (self-serve via /pricing + Stripe Checkout).
3. **Success criteria:** A subscriber checks out ($12/mo test-mode), gets 50k credits; on each monthly renewal credits **reset to 50k** (no rollover); hard-stop 402 at cap until next cycle; cancel → revoke. `/pricing` shows the plan.
4. **Constraints:** TDD; unit+integration+contract; pyright clean; ruff clean; Pydantic on boundaries; no hardcoded secrets (Stripe via env); Stripe stays **TEST mode**; show-before-prod.
5. **Compliance:** No PCI scope on our side (Stripe hosts checkout + stores cards). No new PII beyond existing tenant email. Separate axis from scope gate.
6. **Rollback:** Feature is additive + env-gated (`STRIPE_UNLIMITED_PRICE_ID` empty ⇒ plan not offered, exactly like the existing price-id gating). Rollback = unset the env var + redeploy previous image snapshot (`docker-scout:<prev-stamp>`), or `git revert` + `scout-deploy.sh`. No schema migration that can't be reversed (credit balances are per-tenant rows).
7. **Dependencies:** Stripe API (already integrated). No new library — reuse existing `stripe_checkout.py` HTTP client.
8. **Effort/risk:** Medium. Highest-risk piece = the monthly reset webhook (idempotency + correct cycle handling).

## Locked spec (from Arijit)
- $12/mo Stripe **recurring** price (test mode), created via Stripe API on the VPS.
- New plan tier `HOSTED_UNLIMITED` (or similar) → 50,000 standard credits.
- Checkout: `mode=subscription`.
- **invoice.paid** → set tenant standard credits to 50,000 (reset, not add). Idempotent per invoice.
- **customer.subscription.deleted** → revoke (downgrade plan, zero the recurring grant).
- Env: `STRIPE_UNLIMITED_PRICE_ID`.
- Website `/pricing`: add the plan card with the "50 dossiers / 5 sites / 10k products" story.

## Open question for the build (surface at Spec)
- **Reset semantics on invoice.paid:** hard SET to 50,000 (drop any leftover, no rollover) — matches "no rollover". Confirm this is a SET, not an ADD, so a mid-cycle top-up purchase isn't wiped. Decision: recurring reset SETs the *subscription grant* to 50k; any separately-purchased one-time credits are tracked/added on top (or documented as not-stackable for v1). **Flag at Spec.**
