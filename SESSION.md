# SESSION — 2026-07-06 (Scout SaaS prod-readiness + launch + subscription)

## Status
**Scout is LAUNCH-READY for Monday (email-only + $0 card-backed beta both live & verified in prod).**
Two feature builds IN PROGRESS via background subagents at persist time:
1. `$12/mo unlimited subscription` (50k credits/mo, monthly reset) — TDD build.
2. `/beta` register UX redesign (3 redundant forms → one dual-action card + demoted reissue).

## Resume action (do FIRST next session)
1. Read this file, then `.development-loop/run-2026-07-06-001/` (01-intake.md, 03-spec.md, state.json).
2. Check both subagents' final state: `git status` — feature code is UNCOMMITTED in the working tree (subscription in scout/core/platform/*, scout/api/routers/billing.py, config.py, website/pricing.html; redesign in website/beta.html + website/assets/hosted-keygen.js).
3. **Reconcile `tests/unit/website/test_launch_website.py`** — the /beta redesign changed beta-form assertions; update them for the new single `hostedRegisterForm` (buttons hostedRegCardBtn/hostedRegEmailBtn, status hostedRegStatus, compact reissue) + the new $12 pricing card.
4. Run FULL verification yourself (Zero-Trust — subagent self-reports are NOT evidence):
   `python3 -m pytest tests/unit/ -q` (all green), `python3 -m pyright scout/` (0 errors), `ruff check scout/ tests/ && ruff format --check`.
5. Show Arijit the tested diff (subscription + redesign) BEFORE any prod deploy.
6. Then: create the $12/mo Stripe RECURRING price on the VPS (test mode, script like setup-stripe.sh using sk_ in /opt/prism/scout/.env), set `STRIPE_UNLIMITED_PRICE_ID` in .env, deploy (`git push` → VPS `git pull` → `sudo /opt/prism/scout/docker/scout-deploy.sh`), verify /v1/billing/stripe/status + a subscription checkout smoke.

## What is LIVE in production now (verified — do not redo)
- scout.chowmes.com (Caddy TLS → Docker container `scout` on 127.0.0.1:8421, VPS 72.61.72.147).
- **Email register→key** via Resend (domain verified; DKIM/SPF/MX in Hostinger DNS). SMTP wired (smtp.resend.com). Delivery verified (`delivery_status: delivered`).
- **Stripe test-mode** $0 card-backed beta + 3 one-time price packs + webhook — `ready_for_beta_checkout: true`, $0 checkout returns a real Stripe session. (Sandbox "Medium"-managed AC-Medium acct — fine for test; swap to a dedicated real Scout Stripe acct before real charges.)
- Beta grant: **1,000 standard + 100 browser credits, 30-day trial** (plan_limits(HOSTED_BETA_PASS) = source of truth).
- Metering: **atomic credit debit** (try_debit_action) — the TOCTOU race is FIXED.
- Prod hardened: Scout DB nightly backup (backup.sh → prism-data git repo), container limits (5g/1.5cpu/512pids), 4GB swap, Caddy security headers, versioned deploy wrapper (scout-deploy.sh keeps last-2 images), weekly docker-cache-prune cron.
- Config: Settings `extra="ignore"` (stray env vars can't crash Scout).
- Latest deployed commit: `326ff97`. Local artifacts commit: `5403014`.

## Decisions locked this session
- **$12/mo subscription = 50,000 standard credits/mo**, monthly reset (SET to 50k, no rollover), hard-stop at cap, fair-use "unlimited". Marketing: "25k page ops + 10k products + 50 company dossiers/month". v1: no one-time-pack stacking for subscribers (single standard bucket).
- Credit model: 1 credit ≈ 1 page/scrape/record; screenshot=3; browser render=5 / min=10.
- Launch = email-only + $0 card-backed (Stripe TEST mode); real Stripe acct + LIVE mode post-launch.
- Distributions = HTTP API + self-host skill only; Docker/CLI/pip = INTERNAL (Docker IS the prod runtime).
- LLM audit: **$0 exposure** (no LLM key, ollama-local default, hosted-only gating) — prod-verified.

## What has NOT been done (prevent false completion claims)
- Subscription + /beta redesign: code written by subagents but NOT verified-by-main, NOT committed, NOT deployed.
- $12/mo Stripe RECURRING price NOT created; STRIPE_UNLIMITED_PRICE_ID NOT set.
- Housekeeping deferred: signup abuse protection (4,264 bot/test tenants pre-launch, public signup only IP-rate-limited); 3 smoke-test tenants (arijit+scoutsmoke/scoutsmoke2/stripesmoke) still in prod DB; scout-home.png/scout-beta-live.png accidentally committed to repo (gitignore+rm); exposed Resend key `re_CdbetMSM_…` (Arijit: leave for now, rotate later); the `scout-smtp` Resend key is Full-access not Sending-access (UI slip).

## Reference files
- `.development-loop/run-2026-07-06-001/{01-intake.md,03-spec.md,state.json}` — subscription spec + gates.
- `docs/product/{llm-cost-audit,credit-economics,prod-architecture-security-review,launch-readiness,go-live-runbook}-2026-07-04.md`.
- Deploy: `git push origin codex/scout-saas-prod-ready` → VPS `cd /opt/prism/scout && git pull` → `sudo docker/scout-deploy.sh`. SSH: `ssh -i ~/.ssh/chowmes_ed25519 chowmesadmin@72.61.72.147`.
- VPS scripts (not in repo): backup.sh (Scout section), scout-deploy.sh, setup-stripe.sh, set-resend-smtp.sh.

## Files changed this session
- Committed (326ff97 + earlier): scout/core/platform/{account_service,account_sqlite_store,hosted,pricing,key_delivery}.py, scout/api/{config.py,routers/hosted.py}, website/{beta.html,pricing.html}, tests, docs/product/*, .development-loop/* (5403014).
- UNCOMMITTED at persist (in-flight subagents): subscription code + /beta redesign — see Resume action #2.
- Prod-only (SSH): backup.sh patch, swap, docker limits, Caddy headers, scout-deploy.sh, setup-stripe.sh, set-resend-smtp.sh, weekly cron.
