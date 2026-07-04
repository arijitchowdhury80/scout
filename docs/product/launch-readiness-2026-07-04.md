# Scout Beta Launch Readiness — 2026-07-04
Consolidated status + the actions only Arijit can take (secrets / accounts). Verified via live SSH
to the VPS and the local test suite. Nothing here is claimed done without evidence.

## Hardware verdict (VPS 72.61.72.147, verified live 2026-07-04 00:25 EDT)
| Resource | Actual | Verdict |
|---|---|---|
| CPU | 2 vCPU (AMD EPYC 9354P) | Tight for browser work; OK for scrapes given the 8-active throttle |
| RAM | 7.8 GiB (5.9 GiB available at check) | Adequate **only** because concurrency is capped at 8 |
| Swap | **0 B (none)** | ⚠️ Risk — an OOM under a browser burst hard-kills processes |
| Disk | 96 GB, **79% used, 21 GB free** | ⚠️ Watch — artifacts can fill it |
| Neighbors | Shared with PRISM (:8000) + Hermes | A Scout spike can starve them |
| Runtime | Scout in Docker → `127.0.0.1:8421`, fronted by Caddy (:443) | Healthy, up 2h at check |
| Load | 0.02 (idle) | Plenty of headroom at rest |

**Bottom line:** the box can host the beta **as designed** — Scout throttles to 8 active requests
with a 250-deep queue, so it never attempts 250 true-simultaneous heavy crawls; it serializes them.
It is **not** sized for 250 concurrent browser renders, and the app does not try to be. For the
average beta load (~0.1 ops/sec, see economics doc) there is ample headroom; the stress point is
**concurrent browser work** (100 browser credits/tester now enabled).

### Recommended before launch (low-risk, high-value)
1. **Add 4 GB swap** — cheapest insurance against OOM under browser bursts on a swapless 8 GB box.
   `fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile` + fstab.
2. **Cap the Scout container** so a spike can't starve PRISM/Hermes: `--cpus=1.5 --memory=5g`
   (or compose `deploy.resources.limits`). Protects neighbors on the shared box.
3. **Disk headroom** — 21 GB free with beta artifact retention at 7 days should hold, but add a
   cron prune of `scout-runs/` older than retention and alert at 90% disk.
- If browser load proves too heavy in the first days, upgrade to the next tier (4 vCPU / 16 GB).

## ⛔ Blockers that need Arijit (secrets / external accounts) — code is ready, config is not
These are **not set in the live prod container** (verified via SSH — env keys empty):
1. **Email delivery (Resend) — REQUIRED for the beta to function.** Without it, `POST
   /v1/hosted/beta-key` provisions the account but the key email never sends (falls to "pending").
   Set on the container:
   - `HOSTED_KEY_DELIVERY_SMTP_HOST=smtp.resend.com`
   - `HOSTED_KEY_DELIVERY_SMTP_PORT=587`
   - `HOSTED_KEY_DELIVERY_SMTP_USERNAME=resend`
   - `HOSTED_KEY_DELIVERY_SMTP_PASSWORD=<Resend API key>`
   - `HOSTED_KEY_DELIVERY_SMTP_FROM_EMAIL=<you@your-verified-domain>`
   - `HOSTED_KEY_DELIVERY_SMTP_USE_TLS=true`
   Requires: a Resend account + a verified sending domain (SPF/DKIM). No code change — the SMTP
   sender is Resend-compatible as-is.
2. **Stripe (test mode) — REQUIRED for card-backed $0 beta signup.** `STRIPE_SECRET_KEY` empty in
   prod. Provide Stripe **test** keys + price IDs (see the Stripe go-live checklist doc). Card is
   captured via `setup` mode, never charged.

## ✅ Verified DONE tonight (with evidence)
- **LLM cost audit — $0 exposure, confirmed in the live prod container** (LLM_API_KEY empty,
  hosted-only=true, llm-mode=disabled). See `llm-cost-audit-2026-07-04.md`.
- **Credit metering race fixed** — atomic conditional debit (both fixed- and variable-cost paths);
  concurrency test proves 100 parallel debits on a 20-credit balance cap at 20, never negative.
- **Beta grant set to 1,000 std + 100 browser, 30 days** (your call) — single source of truth in
  `plan_limits`; email copy derives from it.
- **Credit economics finalized** — `credit-economics-2026-07-04.md` (also in vault). ~88% margin on
  paid; beta trial breaks even trivially (marginal cost ≈ $0, self-hosted, no LLM).
- **Prod config discrepancy resolved** — the running container has correct safety flags; the stale
  committed `secrets/scout-production.env` was just incomplete.

## In progress / remaining
- Website beta-credit copy alignment to the new grant (running).
- Local 250-concurrent load-test evidence (running).
- Distribution e2e validation (HTTP / skill / Docker / CLI / pip) — your call was "keep all, make
  them work e2e."
- Live Stripe test-mode smoke + full 250-user load run against prod — both gated on the secrets above
  and your go-ahead to hammer the shared prod box.
