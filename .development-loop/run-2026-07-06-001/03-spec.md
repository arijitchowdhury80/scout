# 03 — Spec · $12/mo Unlimited Subscription

## Contracts (change-here-first)
### pricing.py
- `HostedCreditPackage`: add `is_subscription: bool = False`.
- New package `unlimited_monthly`: amount_cents=1200, standard_credits=50000, browser_credits=0,
  trial_days=0, requires_payment_method=True, is_public_purchase=True, is_subscription=True,
  hosted_plan=HOSTED_UNLIMITED. customer_summary = the "25k pages + 10k products + 50 dossiers" story.

### hosted.py
- New `HostedPlan.HOSTED_UNLIMITED = "hosted_unlimited"`.
- plan_limits(HOSTED_UNLIMITED): hosted_enabled=True, standard_credits=50000, browser_credits=0,
  artifact_retention_days=30, max_pages_per_run=250, max_concurrent_runs=2.
- Update `_higher_plan` rank so UNLIMITED sits above STARTER (and where you place it vs PRO).

### config.py
- `stripe_unlimited_price_id: str = ""`.

### stripe_checkout.py
- Config carries the unlimited price id; `price_id_for_package("unlimited_monthly")` returns it.
- `create_checkout_session`: if `package.is_subscription` → `mode=subscription`,
  `line_items[0][price]=<recurring price id>`, quantity 1, metadata[package_id]=unlimited_monthly,
  metadata[plan]=hosted_unlimited. (Not mode=payment.)

### payment_provisioning.py
- `process_checkout` (checkout.session.completed, mode=subscription): provision or UPGRADE the tenant
  to HOSTED_UNLIMITED, SET standard credits to 50000, store the stripe subscription id + customer id.
  Idempotent by checkout_session_id (existing pattern).
- NEW `process_invoice_paid(invoice)`: find tenant by stripe customer/subscription id → **SET** standard
  credits to 50000 (reset, no rollover, no add). Idempotent by invoice id (store processed invoice ids).
- NEW `process_subscription_deleted(subscription)`: find tenant → downgrade plan off UNLIMITED, zero the
  subscription grant (set standard credits to 0 or LOCAL_FREE limits). Idempotent.

### billing.py webhook (`/v1/billing/stripe/webhook`)
- Extend the event switch: currently only `checkout.session.completed`. Add:
  - `invoice.paid` → payment_provisioning.process_invoice_paid
  - `customer.subscription.deleted` → payment_provisioning.process_subscription_deleted
  - keep signature verification for all.

### website/pricing.html
- Add the $12/mo Unlimited plan card with the 25k pages + 10k products + 50 dossiers copy.

## v1 decisions (documented)
- Reset **SETs** standard credits to 50,000 each cycle (not add). No rollover.
- Subscribers do **not** stack one-time packs in v1 (single standard-credit bucket).
- Hard-stop at 0 until next invoice.paid (existing atomic debit returns insufficient → 402).

## Rollback
Env-gated: `STRIPE_UNLIMITED_PRICE_ID` empty ⇒ checkout returns "price not configured", plan hidden.
Rollback = unset env + `scout-deploy.sh`, or `git revert` + redeploy previous image snapshot.

## Feature flag
The empty-price-id gate IS the flag. Plan only offered when env set (prod), off by default (tests, local).

## Test layers (TDD, RED first)
- unit: pricing package fields; plan_limits(UNLIMITED); checkout builds mode=subscription payload;
  process_invoice_paid SETs to 50k (not add); idempotency (same invoice twice = one reset);
  process_subscription_deleted downgrades; hard-stop after exhaustion.
- integration: webhook routes invoice.paid + subscription.deleted to the right handler w/ sig check.
- contract: Pydantic response models unchanged; StripeCheckoutResult for subscription.
