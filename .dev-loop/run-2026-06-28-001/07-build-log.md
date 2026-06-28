# Build Log - Scout Product Launch Checkpoint

Date: 2026-06-28
Status: Checkpoint verified, not product-launch complete

## Scope Built

- Competitor website research baseline under `docs/competetor-website-knowledge/`.
- Scout private-beta website foundation under `website/`, using the
  Supadesign IndustrialGray design system.
- Generic product export adapters for JSON, JSONL, CSV, and SQLite.
- CLI command `scout product-export`.
- Hosted-readiness primitives:
  - API key generation, hashing, masking, and usability checks.
  - Hosted plan and credit policy definitions.
  - Hosted URL safety / SSRF validation helpers.
- Workspace planning docs for hosted readiness, launch website, and product
  export adapters.

## Verification Run

Commands run from `/Users/arijitchowdhury/Dropbox/AI-Development/Scout`.

```bash
python3 -m pytest tests/unit/core/platform tests/unit/core/products tests/unit/cli/test_run_commands.py -q
```

Result: `116 passed, 8 warnings`.

```bash
python3 -m pytest tests/unit/ -q
```

Result: `428 passed, 8 warnings`.

```bash
python3 -m pyright scout/
```

Result: `0 errors, 0 warnings, 0 informations`.

```bash
ruff check scout/ tests/
ruff format --check scout/ tests/
```

Result: `All checks passed!` and `180 files already formatted`.

```bash
python3 -m http.server 8766 --directory website
```

Then a Python Playwright Chromium check validated:

- desktop viewport `1440x1000`
- mobile viewport `390x844`
- hero heading visible
- `#why`, `#evidence`, `#pricing`, `#quickstart`, and `#beta` sections present
- 14 links present
- no browser console messages

Screenshots were written to ignored local output:

- `validation-output/website-scout-launch/desktop.png`
- `validation-output/website-scout-launch/mobile.png`

## Not Complete Yet

This checkpoint does not finish the full launch objective. Remaining work:

- Hosted multi-tenant persistence and API-key management endpoints.
- Hosted quota middleware, Stripe checkout, and webhook handling.
- Deployment architecture and infrastructure.
- Local distribution package validation across install paths.
- Full product website beyond one static landing page.
- Current competitor/pricing research refresh before public launch.
- Legal/license review for Crawl4AI attribution and distribution posture.
- Broader live feature certification before making public product claims.

## Follow-Up Checkpoint - Hosted Account Service

Date: 2026-06-28

Built:

- `scout.core.platform.account_service`
- `HostedTenantRecord`
- `HostedAccountStatus`
- `HostedProvisioningResult`
- `HostedAccountDecision`
- `InMemoryHostedAccountStore`
- `HostedAccountService`

Behavior:

- provisions hosted tenants for hosted-enabled plans only,
- generates one-time raw API keys while storing only hashes,
- seeds standard and browser credits from the selected hosted plan,
- authenticates keys by hash and required scope,
- rejects revoked keys,
- debits standard and browser credit buckets separately,
- denies insufficient-credit actions without mutating balances.

TDD:

- RED: `python3 -m pytest tests/unit/core/platform/test_account_service.py -q`
  failed with missing `scout.core.platform.account_service`.
- GREEN: same command passed with `6 passed`.

Verification:

- `python3 -m pytest tests/unit/core/platform -q` -> `59 passed`.
- `python3 -m pytest tests/unit/ -q` -> `434 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/` -> `All checks passed!`.
- `ruff format --check scout/ tests/` -> `182 files already formatted`.

## Follow-Up Checkpoint - Hosted Admission Service

Date: 2026-06-28

Built:

- `scout.core.platform.hosted_admission`
- `HostedAdmissionDecision`
- `HostedAdmissionService`

Behavior:

- authenticates API key and scope before URL safety checks,
- rejects unknown/wrong-scope keys without leaking URL safety details,
- validates hosted URLs and resolved IPs before any credit debit,
- denies unsafe URLs without mutating balances,
- debits credits only after auth and URL safety pass,
- preserves URL safety and usage decisions for future API error responses.

TDD:

- RED: `python3 -m pytest tests/unit/core/platform/test_hosted_admission.py -q`
  failed with missing `scout.core.platform.hosted_admission`.
- GREEN: same command passed with `6 passed`.

Verification:

- `python3 -m pytest tests/unit/ -q` -> `440 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/` -> `All checks passed!`.
- `ruff format --check scout/ tests/` -> `184 files already formatted`.

## Follow-Up Checkpoint - Hosted Account Persistence

Date: 2026-06-28

Built:

- `scout.core.platform.account_sqlite_store`
- `SQLiteHostedAccountStore`

Behavior:

- persists hosted tenants,
- persists API-key metadata and scopes without storing raw API keys,
- persists standard and browser credit balances,
- supports lookup by key hash,
- supports persisted key revocation,
- preserves credit debits across fresh service instances.

TDD:

- RED: `python3 -m pytest tests/unit/core/platform/test_account_sqlite_store.py -q`
  failed with missing `scout.core.platform.account_sqlite_store`.
- GREEN: same command passed with `3 passed`.

Verification:

- `python3 -m pytest tests/unit/core/platform -q` -> `68 passed`.
- `python3 -m pytest tests/unit/ -q` -> `443 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/` -> `All checks passed!`.
- `ruff format --check scout/ tests/` -> `186 files already formatted`.

## Follow-Up Checkpoint - Hosted HTTP Boundary

Date: 2026-06-28

Built:

- `/v1/hosted/scrape`
- hosted Bearer auth extraction,
- hosted account service dependency,
- hosted account SQLite service binding on FastAPI startup,
- static local auth middleware pass-through for `/v1/hosted/*`,
- `HostedAccountStore` protocol so account services can use in-memory or
  SQLite stores cleanly.

Behavior:

- hosted endpoint does not require local `X-API-Key`,
- missing Bearer token returns 401,
- unsafe URL returns 403 and does not call crawler,
- valid hosted key with `runs:create` scope calls crawler once,
- admitted request debits one standard credit,
- response includes tenant/key IDs and credit charge but never echoes the raw
  API key.

TDD:

- RED: `python3 -m pytest tests/unit/api/test_hosted_scrape.py tests/unit/api/test_auth.py -q`
  failed because `get_hosted_account_service` did not exist.
- GREEN: same command passed with `9 passed`.

Verification:

- `python3 -m pytest tests/unit/api -q` -> `110 passed`.
- `python3 -m pytest tests/unit/ -q` -> `447 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/` -> `All checks passed!`.
- `ruff format --check scout/ tests/` -> `188 files already formatted`.

## Follow-Up Checkpoint - Hosted Beta Provisioning CLI

Date: 2026-06-28

Built:

- `scout hosted-provision`
- `_hosted_account_db_path(...)`

Behavior:

- provisions a hosted tenant by email,
- defaults to `hosted_beta_pass`,
- defaults to `runs:create` scope,
- accepts repeated `--scope` values,
- writes tenant/key/balance records to hosted account SQLite DB,
- prints raw `scout_live_...` key once,
- does not store the raw key in SQLite,
- rejects non-hosted plans such as `local_free`.

TDD:

- RED: `python3 -m pytest tests/unit/cli/test_run_commands.py -q -k "hosted_provision"`
  failed because the command did not exist.
- GREEN: same command passed with `2 passed`.

Verification:

- `python3 -m pytest tests/unit/cli/test_run_commands.py -q` -> `15 passed`.
- `python3 -m pytest tests/unit/ -q` -> `449 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/` -> `All checks passed!`.
- `ruff format --check scout/ tests/` -> `188 files already formatted`.
# Hosted Payment Provisioning Checkpoint

Date: 2026-06-28

Built:

- `scout.core.platform.payment_provisioning`
- `HostedCheckoutProvisioningRequest`
- `HostedCheckoutProvisioningResult`
- `HostedCheckoutProvisioningRecord`
- `HostedPaymentProvisioningService`
- `SQLiteHostedPaymentStore`

Behavior:

- paid `$22` hosted beta checkout provisions one hosted tenant/key,
- duplicate provider/session processing is idempotent,
- retries return existing tenant/key metadata without a raw API key,
- unpaid checkout is rejected before provisioning,
- wrong amount/currency is rejected before provisioning,
- raw API keys are not stored in SQLite.

Verification:

- RED: `python3 -m pytest tests/unit/core/platform/test_payment_provisioning.py -q`
  failed with missing `payment_provisioning` module.
- GREEN: `python3 -m pytest tests/unit/core/platform/test_payment_provisioning.py -q`
  passed: 6 tests.
- Platform checkpoint: `python3 -m pytest tests/unit/core/platform -q`
  passed: 74 tests.

Still pending:

- email or portal key delivery,
- production transactional Postgres store,
- Customer Portal/subscription handling.

# Hosted Stripe Webhook Checkpoint

Date: 2026-06-28

Built:

- `scout.api.routers.billing`
- `POST /v1/billing/stripe/webhook`
- `SCOUT_STRIPE_WEBHOOK_SECRET` / `stripe_webhook_secret` setting
- `get_hosted_payment_provisioning_service`
- `get_stripe_webhook_secret`

Behavior:

- verifies Stripe `Stripe-Signature` HMAC without adding a Stripe SDK
  dependency,
- rejects missing or invalid signatures before provisioning,
- ignores irrelevant Stripe event types,
- provisions hosted beta access for valid paid
  `checkout.session.completed` events,
- handles duplicate checkout sessions through existing idempotent payment
  provisioning,
- never returns raw `scout_live_...` API keys in webhook responses.

Verification:

- RED: `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py -q`
  failed because payment provisioning dependency did not exist.
- GREEN: `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  passed: 12 tests.
- Focused pyright on billing/deps/main/test files passed with 0 errors.
- Focused Ruff check and format passed.

Full verification:

- `python3 -m pytest tests/unit/api -q` -> `116 passed`.
- `python3 -m pytest tests/unit/ -q` -> `461 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/ && ruff format --check scout/ tests/` -> passed,
  `192 files already formatted`.

Still pending:

- secure customer key delivery after webhook provisioning,
- live Stripe CLI/sandbox smoke test,
- production transactional Postgres store,
- Customer Portal/subscription handling.

# Hosted Key Delivery Gate Checkpoint

Date: 2026-06-28

Built:

- `scout.core.platform.key_delivery`
- `HostedApiKeyDeliveryService` protocol
- `DisabledHostedApiKeyDeliveryService`
- Stripe webhook delivery gate

Behavior:

- refuses to create a new hosted key when no delivery channel is configured,
- returns `503` before provisioning in disabled-delivery state,
- sends the raw key to an enabled delivery adapter exactly once,
- does not include raw `scout_live_...` keys in webhook responses,
- does not redeliver keys on idempotent webhook replay.

Verification:

- RED: `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py -q`
  failed with missing `key_delivery` module.
- GREEN: `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  passed: 13 tests.
- Focused pyright on key delivery, billing, deps, main, and webhook tests
  passed with 0 errors.
- Focused Ruff check and format passed.

Full verification:

- `python3 -m pytest tests/unit/api -q` -> `117 passed`.
- `python3 -m pytest tests/unit/ -q` -> `462 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/ && ruff format --check scout/ tests/` -> passed,
  `193 files already formatted`.

Still pending:

- real email/portal/one-time handoff delivery provider,
- live Stripe CLI/sandbox smoke test.

# Hosted SMTP Key Delivery Checkpoint

Date: 2026-06-28

Built:

- `SmtpHostedApiKeyDeliveryConfig`
- `SmtpHostedApiKeyDeliveryService`
- SMTP startup config under `HOSTED_KEY_DELIVERY_SMTP_*`

Behavior:

- SMTP delivery is enabled only when SMTP host and from-email are configured,
- sends the one-time raw hosted API key to the checkout customer,
- includes tenant/key metadata in the email body,
- returns structured failure status when SMTP send fails,
- API startup defaults to SMTP delivery service with empty config, which means
  delivery remains disabled until launch credentials are configured.

Verification:

- RED: `python3 -m pytest tests/unit/core/platform/test_key_delivery.py -q`
  failed because SMTP delivery classes did not exist.
- GREEN: `python3 -m pytest tests/unit/core/platform/test_key_delivery.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  passed: 17 tests.
- Focused pyright on SMTP delivery, config, main, billing, and tests passed with
  0 errors.
- Focused Ruff check and format passed.

Full verification:

- `python3 -m pytest tests/unit/api -q` -> `117 passed`.
- `python3 -m pytest tests/unit/ -q` -> `466 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/ && ruff format --check scout/ tests/` -> passed,
  `194 files already formatted`.

Still pending:

- real SMTP smoke test with test credentials,
- Stripe sandbox webhook smoke with SMTP configured.

# Hosted Stripe Checkout Session Checkpoint

Date: 2026-06-28

Built:

- `scout.core.platform.stripe_checkout`
- `StripeCheckoutConfig`
- `StripeCheckoutService`
- `UrllibStripeCheckoutTransport`
- `POST /v1/billing/stripe/checkout-session`
- startup config for `STRIPE_SECRET_KEY`, `STRIPE_BETA_PRICE_ID`,
  `STRIPE_SUCCESS_URL`, and `STRIPE_CANCEL_URL`

Behavior:

- creates one-time Stripe Checkout Sessions for the hosted beta pass,
- sends Stripe a form-encoded `mode=payment` request with one beta price line
  item,
- passes optional `customer_email`,
- returns only checkout URL, checkout session id, success, and reason,
- fails with `503` when Stripe Checkout is not configured,
- does not provision hosted accounts before webhook-confirmed payment,
- does not return Stripe secret keys or raw Scout API keys.

Verification:

- RED:
  `python3 -m pytest tests/unit/core/platform/test_stripe_checkout.py tests/unit/api/test_billing_stripe_checkout.py -q`
  failed with missing `scout.core.platform.stripe_checkout` and missing
  `get_stripe_checkout_service`.
- GREEN:
  `python3 -m pytest tests/unit/core/platform/test_stripe_checkout.py tests/unit/api/test_billing_stripe_checkout.py -q`
  passed: 4 tests.
- Billing checkpoint:
  `python3 -m pytest tests/unit/api/test_billing_stripe_checkout.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  passed: 15 tests.
- Full API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 119 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 470 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 197 files already
  formatted.

Still pending:

- live Stripe test-mode Checkout Session smoke,
- website CTA wiring to call checkout route and redirect to Stripe,
- hosted Customer Portal.

# Scout Website Hosted Beta Checkout Checkpoint

Date: 2026-06-28

Built:

- hosted beta checkout form in `website/index.html`,
- email input for key-delivery address,
- browser-side POST to `/v1/billing/stripe/checkout-session`,
- redirect to returned `checkout_url`,
- visible loading, success, and error states,
- matching IndustrialGray form styling in `website/styles.css`,
- static website regression test in `tests/unit/website/test_launch_website.py`.

Behavior:

- the website no longer has a static hosted-beta CTA only,
- hosted beta checkout stays honest: `$22` beta pass, limited hosted credits,
  not unlimited crawling,
- the website contains no Stripe secret keys,
- if Stripe Checkout is not configured, the user sees a clear error state.

Verification:

- RED:
  `python3 -m pytest tests/unit/website/test_launch_website.py -q` failed
  because `hostedBetaCheckout` did not exist.
- GREEN:
  `python3 -m pytest tests/unit/website/test_launch_website.py tests/unit/api/test_billing_stripe_checkout.py -q`
  passed: 3 tests.
- Playwright static smoke against
  `python3 -m http.server 8767 --directory website` passed:
  - desktop viewport: checkout form visible, email input visible, no console errors,
  - mobile viewport: checkout form visible, email input visible, no console errors.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 198 files already
  formatted.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 471 tests.

Still pending:

- live Stripe test-mode smoke from website click through Checkout redirect,
- deploy/proxy decision for serving the static site and API from the same origin,
- public docs links after docs are organized.

# Scout Website Same-Origin Serving Checkpoint

Date: 2026-06-28

Built:

- `scout.api.launch_site`
- API root `/` now serves `website/index.html`
- public `/styles.css`
- public `/assets/warm-industrial-design-system/warm-industrial.css`
- auth middleware bypass for launch-site assets

Behavior:

- `scout serve` now opens the real Scout launch website at `/`, not a tiny
  placeholder page,
- hosted beta checkout posts to the same API origin,
- `/app` remains available separately for the internal Scout app surface,
- protected API routes still require `X-API-Key` or hosted Bearer auth.

Verification:

- RED:
  `python3 -m pytest tests/unit/website/test_launch_website.py -q` failed
  because `/` still served the placeholder and `/styles.css` returned 403.
- GREEN:
  `python3 -m pytest tests/unit/website/test_launch_website.py tests/unit/api/test_auth.py -q`
  passed: 10 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 199 files already
  formatted.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 473 tests.

Still pending:

- live browser smoke against `scout serve`,
- production hosting/deployment target decision,
- live Stripe test-mode Checkout redirect.

# Scout Serve Launch Website Browser Smoke

Date: 2026-06-28

Verified:

- started `python3 -m scout.cli serve --host 127.0.0.1 --port 8768`,
- `/health` returned 200 with Scout `0.1.0` and Crawl4AI `0.7.7`,
- desktop browser smoke at `1440x1000` loaded `/`, showed the launch website
  hero, showed the hosted beta checkout form, and had no console errors,
- mobile browser smoke at `390x844` loaded `/`, showed the launch website hero,
  showed the hosted beta checkout form, and had no console errors,
- missing-config checkout submit showed `Stripe Checkout is not configured.`,
  re-enabled the submit button, and returned the expected server-side `503`.

Evidence screenshots:

- `validation-output/website-scout-launch/desktop-scout-serve-root.png`
- `validation-output/website-scout-launch/mobile-scout-serve-root.png`
- `validation-output/website-scout-launch/checkout-error-scout-serve-root.png`

Note:

- Chromium logs a failed-resource console message for the intentional `503`
  missing-config checkout path. This is expected until real Stripe test-mode
  config is supplied and the happy-path redirect is exercised.

Still pending:

- live Stripe test-mode Checkout redirect,
- webhook smoke with Stripe CLI or Stripe test webhook,
- production deployment/hosting target decision.

# Stripe Billing Readiness Checkpoint

Date: 2026-06-28

Built:

- `GET /v1/billing/stripe/status`
- non-secret readiness flags for checkout, webhook, key delivery, and
  paid-key-delivery readiness
- website startup fetch of `/v1/billing/stripe/status`
- disabled hosted-beta checkout button when Stripe checkout is not configured
- clear website copy directing users to local install when hosted payment is
  unavailable

Behavior:

- the readiness endpoint returns booleans only,
- no Stripe keys, webhook secrets, SMTP secrets, or Scout API keys are exposed,
- the website no longer waits for a failed submit to explain hosted beta status,
- when checkout is configured but key delivery is not, the website can warn that
  delivery is still being finalized.

Verification:

- RED:
  `python3 -m pytest tests/unit/api/test_billing_stripe_checkout.py tests/unit/website/test_launch_website.py -q`
  failed because `/v1/billing/stripe/status` returned 404 and the website did
  not fetch readiness.
- GREEN:
  `python3 -m pytest tests/unit/api/test_billing_stripe_checkout.py tests/unit/website/test_launch_website.py -q`
  passed: 7 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 121 tests.
- Browser smoke:
  `python3 -m scout.cli serve --host 127.0.0.1 --port 8769`; Playwright
  confirmed the page requested `/v1/billing/stripe/status`, disabled the
  checkout button when config was absent, showed hosted-beta-not-configured
  copy, and emitted no console errors.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 199 files already
  formatted.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 475 tests.

Still pending:

- live Stripe test-mode Checkout redirect,
- webhook smoke with Stripe CLI or Stripe test webhook,
- SMTP/test email smoke for key delivery.

# Hosted Launch Environment Example Checkpoint

Date: 2026-06-28

Built:

- `.env.example` now documents every `scout.api.config.Settings` field,
- grouped local-only, persistence, Stripe Checkout, Stripe webhook, SMTP key
  delivery, and server bind settings,
- regression test `tests/unit/api/test_env_example.py` keeps the example aligned
  with future settings changes,
- `docs/distribution.md` now documents paid hosted beta env requirements and the
  non-secret Stripe readiness endpoint.

Behavior:

- local users can still ignore Stripe/SMTP settings,
- hosted beta operators can see the exact env var names required for checkout,
  webhook confirmation, and key delivery,
- missing future settings will fail the env-example regression test.

Verification:

- RED:
  `python3 -m pytest tests/unit/api/test_env_example.py -q` failed because
  `DB_PATH` and other settings were missing from `.env.example`.
- GREEN:
  `python3 -m pytest tests/unit/api/test_env_example.py -q` passed: 1 test.
- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_env_example.py tests/unit/api/test_billing_stripe_checkout.py tests/unit/website/test_launch_website.py -q`
  passed: 8 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 122 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 200 files already
  formatted.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 476 tests.

Still pending:

- live Stripe test-mode values,
- SMTP smoke values,
- deploy environment/secrets manager decision.

# Hosted Account Balance Endpoint Checkpoint

Date: 2026-06-28

Built:

- `GET /v1/hosted/me`
- `HostedAccountSummaryResponse`
- `HostedAccountService.get_tenant`

Behavior:

- hosted beta users can inspect their plan, account status, plan limits, and
  remaining standard/browser credits with their Bearer key,
- the endpoint requires hosted Bearer auth,
- response includes tenant/key IDs for support diagnostics but never returns the
  raw `scout_live_...` API key,
- `/v1/hosted/scrape` remains the only hosted work endpoint in this slice and
  continues to debit standard credits.

Verification:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_scrape.py -q` failed because
  `/v1/hosted/me` returned 404.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_scrape.py tests/unit/core/platform/test_account_service.py tests/unit/core/platform/test_hosted_policy.py -q`
  passed: 17 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 124 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 478 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 200 files already
  formatted.

Still pending:

- global request rate-limit middleware,
- hosted products/run endpoints,
- hosted usage dashboard.

# Hosted Per-Key Rate-Limit Checkpoint

Date: 2026-06-28

Built:

- `scout.core.platform.hosted_rate_limit`
- `HostedRateLimitConfig`
- `HostedRateLimitDecision`
- `HostedRateLimiter`
- `get_hosted_rate_limiter`
- FastAPI startup binding for `app.state.hosted_rate_limiter`
- rate-limit enforcement on `/v1/hosted/me`
- rate-limit enforcement on `/v1/hosted/scrape`

Behavior:

- hosted API keys are throttled by a configurable sliding window,
- over-limit calls return `429` with `Retry-After`,
- `/v1/hosted/scrape` authenticates the key and checks URL safety before
  rate-limit admission,
- over-limit scrapes do not call the crawler and do not spend hosted credits,
- the limiter is process-local and appropriate only for single-node/private-beta
  use.

TDD:

- RED:
  `python3 -m pytest tests/unit/core/platform/test_hosted_rate_limit.py tests/unit/api/test_hosted_scrape.py -q`
  failed because `scout.core.platform.hosted_rate_limit` and
  `get_hosted_rate_limiter` did not exist.
- GREEN:
  `python3 -m pytest tests/unit/core/platform/test_hosted_rate_limit.py tests/unit/api/test_hosted_scrape.py -q`
  passed: 9 tests.

Verification:

- Focused checkpoint:
  `python3 -m pytest tests/unit/core/platform/test_hosted_rate_limit.py tests/unit/api/test_hosted_scrape.py tests/unit/api/test_env_example.py -q`
  passed: 10 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 125 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 482 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 202 files already
  formatted.

Still pending:

- distributed/shared throttling for multi-instance hosted production,
- gateway/WAF abuse policy,
- hosted products/run endpoints,
- hosted usage dashboard.

# Hosted Crawl Endpoint Checkpoint

Date: 2026-06-28

Built:

- `POST /v1/hosted/crawl`
- `HostedCrawlResponse`
- hosted crawl plan-page limit enforcement
- hosted crawl standard-credit preflight
- hosted crawl returned-page debit

Behavior:

- hosted crawl requires a Bearer `scout_live_...` key with `runs:create`,
- unsafe URLs are rejected before crawler execution,
- requested `max_pages` must be at least 1 and no greater than the hosted plan
  `max_pages_per_run`,
- the account must have enough standard credits for requested `max_pages` before
  the crawl starts,
- returned crawls charge one standard credit per returned page, capped by the
  requested `max_pages`,
- hosted crawl shares the per-key rate limiter and returns `429` without a
  second debit or crawler call when the key is over limit.

TDD:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_crawl.py -q` failed because
  `/v1/hosted/crawl` returned 404.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_crawl.py -q` passed: 5 tests.

Verification:

- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_hosted_crawl.py tests/unit/api/test_hosted_scrape.py -q`
  passed: 11 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 130 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 487 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 203 files already
  formatted.

Still pending:

- async hosted crawl jobs,
- persisted crawl artifact storage for hosted users,
- high-level hosted `run` endpoints,
- distributed/shared throttling for multi-instance production.

# Hosted Products Endpoint Checkpoint

Date: 2026-06-28

Built:

- `POST /v1/hosted/products`
- `HostedProductsResponse`
- hosted product target URL safety check
- hosted product plan limit enforcement
- hosted product standard-credit preflight
- hosted product returned-record debit

Behavior:

- hosted products requires a Bearer `scout_live_...` key with `runs:create`,
- requests must provide `site` or `start_url`,
- unsafe target URLs are rejected before product extraction,
- requested `max_products` must be at least 1 and no greater than the hosted
  plan `max_pages_per_run`,
- the account must have enough standard credits for requested `max_products`
  before product extraction starts,
- returned product runs charge one standard credit per returned product record,
  capped by requested `max_products`,
- hosted products shares the per-key rate limiter and returns `429` without a
  second debit or product crawler call when the key is over limit.

TDD:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_products.py -q` failed because
  `/v1/hosted/products` returned 404.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_products.py -q` passed: 5 tests.

Verification:

- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_hosted_products.py tests/unit/api/test_hosted_crawl.py tests/unit/api/test_hosted_scrape.py -q`
  passed: 16 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 135 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 492 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 204 files already
  formatted.

Still pending:

- async hosted product jobs,
- persisted product artifacts for hosted users,
- dashboard access to hosted run artifacts,
- distributed/shared throttling for multi-instance production.

# Hosted High-Level Run Endpoint Checkpoint

Date: 2026-06-28

Built:

- `POST /v1/hosted/run/{use_case}`
- `HostedRunResponse`
- hosted run record-limit enforcement
- hosted run standard-credit preflight
- hosted run returned-record debit
- tenant-labeled server-derived output directories

Behavior:

- hosted high-level runs require a Bearer `scout_live_...` key with
  `runs:create`,
- request `url` is checked through hosted URL safety when supplied,
- caller-provided `output_dir` is ignored for hosted safety,
- Scout derives output under server `SCOUT_WORKDIR` with a tenant-labeled run
  folder,
- requested `max_records` must be at least 1 and no greater than the hosted plan
  `max_pages_per_run`,
- the account must have enough standard credits for requested `max_records`
  before the run starts,
- returned runs charge one standard credit per returned record, capped by
  requested `max_records`,
- hosted run shares the per-key rate limiter and returns `429` without a second
  debit when the key is over limit.

TDD:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_run.py -q` failed because
  `/v1/hosted/run/company` returned 404.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_run.py -q` passed: 5 tests.

Verification:

- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_hosted_run.py tests/unit/api/test_hosted_products.py tests/unit/api/test_hosted_crawl.py tests/unit/api/test_hosted_scrape.py -q`
  passed: 21 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 140 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 497 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 205 files already
  formatted.

Still pending:

- async hosted run jobs,
- hosted run artifact dashboard UI,
- distributed/shared throttling for multi-instance production.

# Hosted Run Retrieval Checkpoint

Date: 2026-06-28

Built:

- `GET /v1/hosted/runs/{run_id}`
- `GET /v1/hosted/runs/{run_id}/records`
- `GET /v1/hosted/runs/{run_id}/artifacts`
- hosted owner-key retrieval guard

Behavior:

- hosted retrieval requires a Bearer `scout_live_...` key with `runs:create`,
- owner keys can retrieve run summary metadata,
- owner keys can retrieve `records.json` content,
- owner keys can retrieve artifact path metadata,
- another hosted tenant receives `404` for a run it does not own,
- raw hosted API keys are not returned in retrieval responses,
- private-beta ownership is enforced through tenant-labeled run output
  directories until run persistence has explicit tenant columns.

TDD:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q` failed
  because `/v1/hosted/runs/{run_id}` returned 404.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q` passed:
  3 tests.

Verification:

- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py tests/unit/api/test_hosted_run.py -q`
  passed: 8 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 143 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 500 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 206 files already
  formatted.

Still pending:

- hosted artifact dashboard UI,
- object storage and signed artifact URLs for multi-instance hosting.

## Hosted Run Ownership Persistence Checkpoint

Date: 2026-06-28

Built:

- `RunRow.tenant_id`
- `RunRow.key_id`
- SQLite `runs.tenant_id`
- SQLite `runs.key_id`
- SQLite migration helper for missing run columns on `init_db`
- `remember_run(..., tenant_id, key_id)`
- hosted run retrieval guard based on persisted tenant ownership

Behavior:

- hosted runs persist non-secret tenant and key IDs with the run,
- hosted retrieval uses the persisted `tenant_id`, not output-directory path
  parsing,
- local/non-hosted runs keep empty tenant/key IDs,
- existing SQLite databases add missing ownership columns during `init_db`,
- raw hosted API keys are not returned by retrieval endpoints.

TDD:

- RED:
  `python3 -m pytest tests/unit/api/test_db.py tests/unit/api/test_hosted_run_retrieval.py -q`
  failed because the `runs` table, `RunRow`, and hosted summary response lacked
  persisted ownership fields.
- GREEN:
  `python3 -m pytest tests/unit/api/test_db.py tests/unit/api/test_hosted_run_retrieval.py -q`
  passed: 14 tests.

Verification:

- Focused checkpoint:
  `python3 -m pytest tests/unit/api/test_db.py tests/unit/api/test_hosted_run_retrieval.py tests/unit/api/test_hosted_run.py -q`
  passed: 19 tests.
- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 144 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 501 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 206 files already
  formatted.

Still pending:

- hosted artifact dashboard UI,
- object storage and signed artifact URLs for multi-instance hosting,
- production user/account model beyond hosted API keys.

## Hosted Artifact Download Checkpoint

Date: 2026-06-28

Built:

- `GET /v1/hosted/runs/{run_id}/artifacts/{artifact_name}/download`
- `download_urls` in `GET /v1/hosted/runs/{run_id}/artifacts`
- known-artifact allowlist for hosted downloads
- run-output-directory confinement before serving artifact files

Behavior:

- hosted artifact downloads require the same Bearer key ownership check as run
  summary, records, and artifact metadata,
- another tenant receives `404` for an owned run's artifact download route,
- unknown artifact names return `404`,
- artifact files are only served when the resolved file lives under the
  persisted run output directory,
- the private-beta route is local filesystem backed; production object storage
  and signed URLs remain future work.

TDD:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q` failed
  because `/artifacts` had no `download_urls` and artifact download routes
  returned the framework `404`.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q` passed:
  5 tests.

Still pending:

- hosted artifact dashboard UI,
- object storage and signed artifact URLs for multi-instance hosting,
- async hosted jobs for long-running artifact-producing workflows.

## Hosted Run List Checkpoint

Date: 2026-06-28

Built:

- `GET /v1/hosted/runs`
- tenant-scoped run listing in `scout.api.run_store`
- SQLite `RunDB.list_runs(..., tenant_id=...)`
- dashboard-safe hosted run list items with summary, records, and artifact URLs

Behavior:

- hosted users can list runs created by their own Bearer key tenant,
- runs from other tenants are omitted,
- list responses do not expose server `output_dir` paths,
- list responses do not echo raw hosted API keys,
- persisted SQLite run ownership supports listing after restart.

TDD:

- RED:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py -q` failed
  because `/v1/hosted/runs` returned `404`.
- GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_run_retrieval.py tests/unit/api/test_db.py -q`
  passed: 18 tests.

Verification:

- API checkpoint:
  `python3 -m pytest tests/unit/api -q` passed: 148 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 508 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 206 files already
  formatted.

Still pending:

- hosted dashboard UI,
- object storage and signed artifact URLs for multi-instance hosting,
- async hosted jobs for long-running workflows.

## Local Package Metadata And Wheel Smoke Checkpoint

Date: 2026-06-28

Built:

- distribution package name changed to `scout-web`,
- installed CLI command remains `scout`,
- `pyproject.toml` now includes README, authors, keywords, URLs, and package
  classifiers,
- runtime dependency metadata includes `email-validator` for Pydantic
  `EmailStr` models,
- Hatch wheel build explicitly ships the `scout` module even though the
  distribution name is `scout-web`,
- README and distribution docs now show `pip install scout-web` as the primary
  local install path.

TDD and packaging evidence:

- RED:
  `python3 -m pytest tests/unit/test_package_metadata.py -q` failed because
  package name was still `scout` and classifiers were missing.
- GREEN:
  metadata tests passed after updating `pyproject.toml`.
- BUILD RED:
  `python3 -m build` failed because Hatch could not infer package files for
  distribution name `scout-web`.
- GREEN:
  explicit Hatch wheel package config made `python3 -m build` produce
  `scout_web-0.1.0.tar.gz` and `scout_web-0.1.0-py3-none-any.whl`.
- SMOKE RED:
  clean wheel install exposed missing `email-validator` runtime dependency.
- SMOKE GREEN:
  clean virtualenv install from `dist/scout_web-0.1.0-py3-none-any.whl` passed
  `import scout` and `scout --help`.

Still pending:

- final Scout license decision and license expression,
- public package publish workflow,
- fresh Mac/Linux install verification,
- Docker publish verification.

## Docker Distribution Smoke Checkpoint

Date: 2026-06-28

Built:

- Dockerfile now copies `README.md` and `website/` before `pip install .`,
- `.dockerignore` keeps `README.md` available while still excluding other
  Markdown docs from the Docker context,
- wheel packaging force-includes `website/` so `scout serve` can serve `/`
  after clean wheel install,
- Docker runtime now uses `DB_PATH=/data/scout.db`, matching Scout settings,
- Docker compose now uses `DB_PATH=/data/scout.db`.

TDD and distribution evidence:

- RED:
  `python3 -m pytest tests/unit/test_docker_distribution.py -q` failed because
  Docker did not copy `README.md` and used `SCOUT_DB_PATH`.
- GREEN:
  Docker config tests passed after copying package metadata and using `DB_PATH`.
- BUILD RED:
  `docker build -f docker/Dockerfile -t scout:launch-smoke .` failed because
  `.dockerignore` excluded `README.md`.
- ROOT RED:
  first container smoke returned `/health` 200 but `/` 500 because
  `/app/website/index.html` was missing.
- GREEN:
  `python3 -m build` produced `scout_web-0.1.0` artifacts with launch website
  files inside the wheel.
- GREEN:
  clean wheel install started `scout serve`; `/health` and `/` passed.
- GREEN:
  `docker build -f docker/Dockerfile -t scout:launch-smoke .` passed.
- GREEN:
  built container smoke passed `/health`, `/`, and `/styles.css` on port
  `18421`.

Still pending:

- Docker publish workflow and registry decision,
- Linux CI Docker smoke with the exact release image,
- final public release checklist.

## CI Release Gate Checkpoint

Date: 2026-06-28

Built:

- GitHub CI `package-build` job,
- CI wheel/sdist build gate,
- CI clean virtualenv install from `dist/scout_web-0.1.0-py3-none-any.whl`,
- CI installed package import smoke,
- CI installed `scout --help` smoke,
- Docker CI runtime smoke after image build:
  - `/health`,
  - `/`,
  - `/styles.css`.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_ci_workflow.py -q` failed because the
  workflow had no `package-build` job and no Docker runtime smoke.
- GREEN:
  `python3 -m pytest tests/unit/test_ci_workflow.py -q` passed after adding
  package and Docker smoke gates.

Still pending:

- publish workflow and registry decision,
- release-tag artifact upload/publish automation,
- CI smoke against the final published package/image rather than the local
  checkout build.

## Product Export Generalization Checkpoint

Date: 2026-06-28

Built:

- `ProductExportFormat.GOOGLE_SHEETS`
- Google Sheets import bundle writer:
  - `products.google-sheets.csv`
  - `products.google-sheets-import.md`
- SQLite table-name validation before SQL interpolation
- CLI help/docs for `scout product-export --format google_sheets`
- launch docs clarifying Algolia is one adapter, not the core product model

Behavior:

- product records can export to JSON, JSONL, CSV, SQLite, and Google Sheets
  import bundles,
- direct Google Sheets API push remains intentionally out of scope until there
  is an explicit credential and security model,
- unsafe SQLite table names fail before reaching SQLite.

TDD:

- RED:
  `python3 -m pytest tests/unit/core/products/test_exports.py -q` failed
  because `ProductExportFormat.GOOGLE_SHEETS` did not exist and unsafe SQLite
  table names reached SQLite.
- GREEN:
  `python3 -m pytest tests/unit/core/products/test_exports.py -q` passed:
  8 tests.

Verification:

- Focused checkpoint:
  `python3 -m pytest tests/unit/core/products/test_exports.py tests/unit/cli/test_run_commands.py -q -k "product_export or export_product_records"`
  passed: 12 tests.
- Product exporter checkpoint:
  `python3 -m pytest tests/unit/core/products -q` passed: 52 tests.
- CLI checkpoint:
  `python3 -m pytest tests/unit/cli/test_run_commands.py -q` passed: 16 tests.
- Full unit checkpoint:
  `python3 -m pytest tests/unit/ -q` passed: 504 tests.
- Static/lint checkpoint:
  `python3 -m pyright scout/` passed with 0 errors; `ruff check scout/ tests/`
  and `ruff format --check scout/ tests/` passed with 206 files already
  formatted.

## Release Artifact Workflow Checkpoint

Date: 2026-06-28

Built:

- `.github/workflows/release.yml`,
- `v*` tag trigger,
- release wheel/sdist build,
- release clean virtualenv wheel install smoke,
- release installed package `import scout` smoke,
- release installed `scout --help` smoke,
- release Docker image build and runtime smoke:
  - `/health`,
  - `/`,
  - `/styles.css`,
- workflow artifact upload for `dist/*`,
- GitHub Release attachment for `dist/*`.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_release_workflow.py -q` failed because
  `.github/workflows/release.yml` did not exist.
- GREEN:
  `python3 -m pytest tests/unit/test_release_workflow.py -q` passed after
  adding the tag-driven release artifact workflow.

Boundary:

- This workflow does not publish to PyPI, GHCR, Docker Hub, or another package
  registry yet.
- Registry publishing remains blocked on license and distribution-policy
  decisions.

Verification:

- Focused release/package/Docker gate:
  `python3 -m pytest tests/unit/test_release_workflow.py tests/unit/test_ci_workflow.py tests/unit/test_docker_distribution.py tests/unit/test_package_metadata.py -q`
  passed: 11 tests.
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 519 tests, 8 warnings.
- Type check:
  `python3 -m pyright scout/` passed: 0 errors, 0 warnings, 0 informations.
- Lint/format:
  `ruff check scout/ tests/ && ruff format --check scout/ tests/` passed:
  all checks passed, 210 files already formatted.
