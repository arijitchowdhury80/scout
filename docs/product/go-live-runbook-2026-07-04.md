# Scout Beta — Go-Live Runbook (Arijit's morning checklist)
**Date:** 2026-07-04 · Everything code-side is done and verified. This is the exact sequence to flip
the two remaining config blockers (email + Stripe) and launch. ~30–45 min.

Prod env lives in **`/opt/prism/scout/.env`** on the VPS (perms 600). After editing it, apply with:
```bash
cd /opt/prism/scout/docker && sudo docker compose up -d      # recreates the scout container with new env
sudo docker inspect scout --format '{{.State.Health.Status}}' # expect: healthy
```
All admin commands below run from the Mac: `scripts/scout-hosted-admin <command>` (needs SSH + the
admin `SCOUT_API_KEY`).

---

## BLOCKER 1 — Email delivery via Resend (REQUIRED — without it, no tester gets their key)

1. **Create/verify the sending domain in Resend** (https://resend.com):
   - Add your domain (e.g. `chowmes.com` or a subdomain like `mail.chowmes.com`).
   - Add the DNS records Resend shows: **SPF** (TXT), **DKIM** (CNAME/TXT), and a **DMARC** TXT record.
     Wait for Resend to show the domain **Verified** (usually minutes; can take longer for DNS).
   - Create an **API key** (Sending access).

2. **Set these in `/opt/prism/scout/.env`** (no code change — the SMTP sender is Resend-compatible):
   ```env
   HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.resend.com
   HOSTED_KEY_DELIVERY_SMTP_PORT=587
   HOSTED_KEY_DELIVERY_SMTP_USERNAME=resend
   HOSTED_KEY_DELIVERY_SMTP_PASSWORD=<your Resend API key>
   HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=Arijit Chowdhury <arijit@your-verified-domain>
   HOSTED_KEY_DELIVERY_SMTP_USE_TLS=true
   ```
   The `FROM_EMAIL` local part/domain must be on the **verified** domain, or Resend rejects the send.

3. **Apply** (recreate container, above), then **smoke test**:
   ```bash
   scripts/scout-hosted-admin send-test-email --to <your-personal-email>
   ```
   Confirm the email arrives (check spam on first send). The body is already signed by you and derives
   its credit figures from the live plan limits (1,000 std + 100 browser, 30 days).

4. **Drain the queue** — any signups that happened while SMTP was off are stored as *pending*; deliver
   them now:
   ```bash
   scripts/scout-hosted-admin process-pending-signups
   scripts/scout-hosted-admin retry-failed-signups     # if any earlier attempts hard-failed
   ```

---

## BLOCKER 2 — Stripe (TEST mode for launch — no real charges)

1. **Create a Stripe account**, stay in **Test mode** (toggle top-right). Get the **test** keys
   (`sk_test_…`) from Developers → API keys.

2. **Create the products/prices** (Test mode) and copy each **Price ID** (`price_…`):
   | Package | Price | Type |
   |---|---|---|
   | Standard 1,000 credits | $10.00 one-time | `STRIPE_STANDARD_1000_PRICE_ID` |
   | Standard 3,000 credits | $25.00 one-time | `STRIPE_STANDARD_3000_PRICE_ID` |
   | Standard 15,000 credits | $100.00 one-time | `STRIPE_STANDARD_15000_PRICE_ID` |
   | Browser 100 credits | $20.00 one-time | `STRIPE_BROWSER_100_PRICE_ID` |
   The **$0 beta** uses Stripe Checkout `setup` mode (card captured, never charged) — **no price ID
   needed** for it.

3. **Create a webhook** (Developers → Webhooks) → endpoint
   `https://scout.chowmes.com/v1/billing/stripe/webhook`, event `checkout.session.completed`. Copy the
   **signing secret** (`whsec_…`).

4. **Set in `/opt/prism/scout/.env`:**
   ```env
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_STANDARD_1000_PRICE_ID=price_...
   STRIPE_STANDARD_3000_PRICE_ID=price_...
   STRIPE_STANDARD_15000_PRICE_ID=price_...
   STRIPE_BROWSER_100_PRICE_ID=price_...
   STRIPE_SUCCESS_URL=https://scout.chowmes.com/account?checkout=success
   STRIPE_CANCEL_URL=https://scout.chowmes.com/pricing?checkout=cancel
   STRIPE_BETA_SUCCESS_URL=https://scout.chowmes.com/account?beta=success
   STRIPE_BETA_CANCEL_URL=https://scout.chowmes.com/beta?beta=cancel
   STRIPE_PORTAL_RETURN_URL=https://scout.chowmes.com/account
   ```

5. **Apply**, then **smoke test the pipeline** end to end:
   ```bash
   scripts/scout-hosted-admin readiness          # checks packages, checkout, blockers
   scripts/scout-hosted-admin production-smoke    # full gate with exact next steps
   ```
   Then do a manual **$0 beta signup** on https://scout.chowmes.com/beta with a Stripe **test card**
   (`4242 4242 4242 4242`, any future expiry/CVC) → confirm: card captured, **$0 charged**, key emailed.

### Post-launch — flipping Stripe to LIVE (do NOT do at launch)
Swap `sk_test_…`→`sk_live_…`, recreate the Test-mode products/prices/webhook in **Live** mode, update
the four price IDs + webhook secret, re-run `readiness` + `production-smoke`. Only after that does real
money move.

---

## Pre-launch cleanup (recommended)
- **Spam/test tenants:** the prod account DB has ~4,264 tenants pre-launch (public signup + only
  IP-rate-limiting). Review and disable non-real ones:
  ```bash
  scripts/scout-hosted-admin list-accounts        # inspect
  scripts/scout-hosted-admin disable-access --email <spam@…>   # per offender
  ```
  Consider adding email-verification/captcha to the public signup before broad promotion.
- **PRISM postgres `restart: no`** — set it to `unless-stopped` so your other product's DB survives a
  reboot.

## Final go/no-go
```bash
scripts/scout-hosted-admin production-smoke     # must be green
scripts/scout-hosted-admin overview             # live readiness + metrics for all testers
```
When both email and Stripe smokes pass and `production-smoke` is green → **launch.**
Watch testers live during the beta with `scripts/scout-hosted-admin overview` / `metrics`.
