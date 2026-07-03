# Scout Public Hosted Launch Readiness Plan

Date: 2026-07-03
Repo: `/Users/arijitchowdhury/Dropbox/AI-Development/Scout`
Branch: `codex/scout-saas-prod-ready`

## Executive Verdict

Scout is not ready to present as a broad, self-serve hosted SaaS for 200 public testers yet.

Scout is closer to ready for a controlled demo/private beta if the launch surface is framed honestly:

- The public website and anonymous playground can demonstrate Scout concepts.
- The local package can be downloaded and smoke-tested.
- Hosted API access exists for provisioned keys. Self-serve hosted onboarding is
  implemented as name/email API-key registration, but production still needs SMTP
  delivery configuration before it can complete end to end.
- The legacy app UI is not the public launch surface.

The critical blockers for tomorrow are not core scraping mechanics. They are hosted access, spend safety, account/key issuance, quotas, and clear product framing.

## Current Evidence

### Verified Locally

- `python3 -m pytest tests/unit/ -q`
  - Result: `659 passed, 8 warnings`.
- `python3 -m pyright scout/`
  - Result: `0 errors, 0 warnings, 0 informations`.
- `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: all checks passed; 226 files already formatted.
- `SCOUT_LIVE_TESTS=1 python3 -m pytest tests/live/test_playground_live_workflows.py -q`
  - Result: `1 passed in 162.09s`.
- `python3 scripts/release_artifact_smoke.py --dist-dir dist --serve --port 18425`
  - Result: wheel and sdist smoke passed.
  - Artifacts:
    - `dist/scout_web-0.1.0-py3-none-any.whl`
    - `dist/scout_web-0.1.0.tar.gz`

### Verified In Production

Production domain: `https://scout.chowmes.com/`

- `/` returns `200`.
- `/docs` returns `200`.
- `/v1/playground/capabilities` returns `200`.
- `/health` returns `200`.
- `/v1/hosted/me` correctly returns `401` without a Bearer key.
- `/app` returns `403`, consistent with hosted-only production guard.
- `/api/docs` returns `403`, consistent with hosted-only production guard.
- `/assets/hosted-keygen.js` is part of the public beta website for status and
  replacement-key support.
- `/beta` exposes the public name/email beta registration form and posts to
  `POST /v1/hosted/beta-key`. SMTP key delivery is required before the path can
  send API keys end to end. If SMTP is missing, Scout records
  `pending_delivery` signups without creating accounts, keys, or credits.
- `/pricing` exposes paid credit package information; the Stripe path requires
  Stripe price IDs, checkout URLs, webhook secret, and SMTP delivery before
  paid checkout is live-ready.

Production playground workflow smoke via `curl`:

- 17 workflows exercised against production `/v1/playground/run`.
- 16 returned HTTP `200` and `success=true`.
- `social` returned HTTP `200` and `success=false` against `example.com`; this is expected for that target because it contains no social profile evidence.
- No production 5xx or 429 was observed in that run.

### Production Environment Safety Evidence

Inside the production container, these LLM-related environment variables are unset:

- `LLM_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `GOOGLE_API_KEY`
- `LITELLM_API_KEY`

That means the current production container should not be able to call OpenAI, Anthropic, Gemini, or similar API-backed LLMs through environment keys.

This is good, but not sufficient. The code should still enforce a hosted-production LLM policy so a future environment variable cannot quietly turn into a large bill.

## Current Hosted Surface

### What Exists

- Hosted API Bearer-key authentication.
- SQLite-backed hosted tenants, API-key hashes, and credit balances.
- Per-key in-memory request rate limiting.
- Hosted routes:
  - `/v1/hosted/me`
  - `/v1/hosted/scrape`
  - `/v1/hosted/crawl`
  - `/v1/hosted/products`
  - `/v1/hosted/run/{use_case}`
  - hosted run listing, records, artifacts, and artifact download.
- URL safety checks for hosted fetches.
- Plan primitives with standard/browser credits and max pages per run.

### What Is Not Ready

- Self-serve hosted key generation is implemented, but not live-operational
  until SMTP delivery is configured.
- No deployed login/account portal.
- No user-owned API key management UI.
- No distributed rate limit. The current limiter is in-memory per process.
- No production-grade database for hosted account state.
- No object storage or signed artifact URLs.
- No durable async worker queue.
- No enforced hosted concurrent-run limiter despite the plan model having `max_concurrent_runs`.
- No global cost circuit breaker.
- No abuse dashboard, suspension UI, or emergency kill switch.
- No hosted-production LLM provider allowlist/denylist.
- No load test proving 200 attendees can hit the hosted surface safely.

## LLM Spend Policy

Hard rule: hosted production must not use frontier hosted LLMs by accident.

For tomorrow:

- Keep all external LLM API keys unset in production.
- Do not configure `LLM_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, or `LITELLM_API_KEY`.
- Do not expose any hosted endpoint that accepts arbitrary `llm_provider` and can activate paid LLM calls.
- Playground extract should remain CSS-schema based, not LLM based.
- Hosted extraction should reject or ignore LLM-backed extraction unless a cheap allowlisted provider is explicitly enabled.

Required code hardening before public hosted beta:

- Add `SCOUT_HOSTED_LLM_MODE=disabled|allowlist`.
- Default hosted production to `disabled`.
- Add `SCOUT_HOSTED_LLM_PROVIDER_ALLOWLIST`, empty by default.
- Reject provider strings containing frontier/API-backed providers unless explicitly allowlisted.
- Add tests proving hosted requests cannot select OpenAI, Anthropic, Gemini, or other paid frontier providers by request body.
- Add startup logs that print the hosted LLM policy without printing secrets.

If an LLM is needed later, prefer a cheap self-hosted/open-source path:

- Ollama/vLLM/local model endpoint behind Scout infrastructure.
- Small model only.
- Strict max tokens.
- Per-key monthly budget.
- Global daily spend ceiling.
- Fast circuit breaker if queue/runtime cost spikes.

## Throttling And Cost Controls

The current hosted limits are not safe enough for 200 public testers.

Current risks:

- `HOSTED_BETA_PASS` now grants 100 standard credits and 0 browser credits per account.
- 250 testers at 100 credits each creates a 25,000 standard-credit exposure before considering concurrency or abuse.
- The hosted rate limiter is in-memory and per-process, not Redis/distributed.
- Credit debit is not atomic under concurrency.
- `max_concurrent_runs` exists in plan limits but is not enforced.
- The anonymous playground allows 20 requests/hour/IP, which is okay for demo friction but still needs a global kill switch.

Tomorrow-safe limits:

- Reduce beta key standard credits to 50-100.
- Set browser credits to 0 for public beta unless the browser feature is explicitly part of the demo.
- Reduce hosted per-key rate to 5-10 requests/minute.
- Add per-IP throttling to beta key generation.
- Keep beta signup behind `HOSTED_BETA_SIGNUP_ENABLED` and disable it immediately if abuse appears.
- Add global in-process emergency caps for single-VPS demo:
  - max active hosted runs
  - max hosted runs/minute
  - max playground runs/minute
- Add a config kill switch:
  - `SCOUT_HOSTED_SIGNUP_ENABLED=false`
  - `SCOUT_PLAYGROUND_ENABLED=false`
  - `SCOUT_HOSTED_RUNS_ENABLED=false`
- Log every hosted key generation and hosted run admission.

Production-grade limits:

- Move rate limits to Redis.
- Move credits and account state to Postgres with atomic debits.
- Enforce per-key, per-tenant, per-IP, and global limits.
- Enforce `max_concurrent_runs`.
- Add queue admission before crawler work starts.
- Add retention cleanup for artifacts.
- Add alerts for request spikes, high failure rates, and nonzero LLM usage.

## Hosted Login And API Key Flow

The launch requirement says most users will run hosted, log in, create their own API key, and test Scout.

Current reality:

- Full login/account UI is not implemented.
- The public `/beta` page exposes direct name/email registration through
  `POST /v1/hosted/beta-key`.
- Raw hosted API keys are never returned in the browser. They are emailed once
  when SMTP key delivery is configured.
- `/v1/billing/stripe/checkout-session` remains the paid hosted-credit checkout
  path and a future/secondary card-backed beta verification path, not the
  current public beta CTA.
- `/beta` registration is live-ready only when hosted beta signup is enabled
  and SMTP delivery is configured and smoke-tested.

Tomorrow options:

1. Controlled hosted beta, fastest:
   - Configure SMTP delivery and keep beta credits low.
   - Send testers to `/beta`.
   - Users enter name/email and receive one API key by email after Scout records
     the hosted account.
   - This is not real login. It is email-captured key issuance.

2. Payment-method-backed beta:
   - Configure Stripe test/live keys, package price IDs, webhook secret, checkout
     success/cancel URLs, and SMTP delivery.
   - Send testers to `/pricing` and select `$0 beta trial`.
   - Users complete Stripe setup-mode checkout and receive one API key after the
     signed webhook provisions access.

3. Manual key provisioning, safest:
   - Pre-create a small pool of API keys.
   - Give keys only to selected testers.
   - Keep anonymous playground public for everyone else.
   - Avoids last-minute signup abuse but creates demo friction.

4. True login, not tomorrow-safe:
   - Add Clerk/Auth.js or equivalent.
   - Add account portal.
   - Add key create/revoke/list.
   - Add tenant dashboard.
   - Add email verification and abuse controls.

Recommendation for tomorrow: direct `/beta` registration only after SMTP is
configured and verified. Do not use an on-screen raw-key fallback. Use Stripe
only after a full test-mode checkout/webhook/email/key verification pass.

## Release Plan For Tomorrow

### Phase 0: Decide Launch Framing

Decision to make before any deploy:

- Do not call this a public SaaS launch.
- Call it a hosted beta/playground demo.
- State that protected sites may block automated access.
- State that outputs are evidence/artifact demos, not guaranteed complete intelligence.

### Phase 1: Cost-Safe Hosted Beta Patch

Implement:

- Configure hosted SMTP delivery and smoke-test beta API-key email delivery.
- Lower hosted beta credits.
- Set browser credits to 0 for public beta.
- Add hosted LLM disabled policy.
- Add provider rejection tests.
- Keep direct keygen email-only with no browser raw-key fallback.
- Add global hosted run emergency cap.
- Add config kill switches.
- Make launch-readiness distinguish:
  - local/private beta readiness
  - public playground readiness
  - hosted self-serve readiness

Verification:

- Unit tests for checkout, throttles, LLM denylist, and credit limits.
- `python3 -m pytest tests/unit/ -q`
- `python3 -m pyright scout/`
- `ruff check scout/ tests/ && ruff format --check scout/ tests/`
- Production `curl` confirms:
  - `/beta#beta-key` is the public beta access path
  - `/v1/hosted/beta-key` records beta registration by name/email
  - `/v1/billing/stripe/checkout-session` remains reserved for paid packages
    and future/secondary card-backed beta verification
  - generated key can call `/v1/hosted/me`
  - generated key can run one capped hosted workflow
  - credits decrement
  - exhausted credits reject work

### Phase 2: Deploy And Smoke Production

Deploy:

- Commit the hosted beta patch.
- Push to GitHub.
- Pull/rebuild on VPS.
- Restart container/service.
- Confirm container image changed and health is green.

Production smoke:

- Home page.
- Docs page.
- Playground capabilities.
- All 17 playground workflows, with realistic targets.
- Beta key generation flow.
- Hosted `/me`.
- Hosted scrape/crawl/products with low caps.
- Rate limit behavior.
- Credit exhaustion behavior.
- LLM env remains unset.
- Hosted LLM policy reports disabled.

### Phase 3: Demo Operating Plan

Before the talk:

- Prepare a short demo script.
- Prepare 3-5 known-good playground examples.
- Prepare a fallback static artifact set in case target sites block.
- Keep the VPS dashboard/log shell open.
- Keep kill-switch env vars ready.
- Watch 5xx, 429, CPU, memory, and disk.

During the talk:

- Drive most attendees to the playground first.
- Enable signup only when ready.
- Keep per-user credits low.
- Pause keygen if abuse or load spikes.

After the talk:

- Disable signup if abuse or load spikes.
- Disable signup if needed.
- Export usage logs.
- Review blocked/error pages.
- Decide whether to build true login/account portal.

## Production-Grade Plan After Demo

To make Scout a real public hosted system:

- Add auth/account portal.
- Add API key create/list/revoke.
- Move account data to Postgres.
- Move rate limits to Redis.
- Add async job queue and worker pool.
- Add object storage for artifacts.
- Add signed downloads.
- Add artifact retention/deletion jobs.
- Add billing integration and Stripe test-mode smoke.
- Add model policy enforcement and cost dashboards.
- Add admin abuse/suspension controls.
- Add load testing for expected attendee and bot traffic.
- Add terms/privacy/fair-use copy.
- Add uptime/error/cost alerts.

## Go/No-Go Checklist

Go for controlled demo if:

- Production website and docs load.
- Anonymous playground passes representative workflow smoke.
- Hosted key issuance is either disabled/manual or deployed with throttles.
- Hosted beta credits are low.
- Browser credits are zero unless explicitly needed.
- External LLM API keys are unset.
- Hosted LLM mode is disabled or denylisted.
- Generated hosted keys can run one workflow and show credit decrement.
- Rate limiting and credit exhaustion are visibly enforced.
- Kill switches are tested.

No-go for public hosted self-serve if any of these remain true:

- Users cannot obtain their own hosted key.
- Keygen has no brute-force protection.
- Hosted credits remain high.
- Frontier LLMs can be invoked by config or request body.
- There is no global kill switch.
- Credit debit remains race-prone under concurrent hosted requests.
- The team has not run production hosted smoke with a real generated key.

## Bottom Line

Scout can be demoed tomorrow as a constrained hosted playground plus controlled beta.

Scout should not be launched tomorrow as a public self-serve hosted SaaS until cost controls, LLM guardrails, signup/key issuance, and production hosted verification are deployed and tested.
