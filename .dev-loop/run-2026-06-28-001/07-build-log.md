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

## Follow-Up Checkpoint - Launch Website Examples Page

Date: 2026-06-29

Built:

- `website/examples.html`
- public `/examples` and `/examples.html` launch-site routes
- public auth allowlist entries for the new examples routes
- launch-site navigation links to Examples
- website README route entry and task checklist update
- frontend-builder workspace notes for the examples page

Behavior:

- Provides beta-safe workflows for page-to-markdown, product category records,
  company intelligence packets, and saved/captured HTML extraction.
- Documents the artifact contract: `records.json`, `source_pages.json`,
  `blocked_pages.json`, and `extraction_report.md`.
- States current launch boundaries: no guaranteed hard-site bypass and no
  certified legacy `/app` UI claim.

TDD:

- RED: targeted website test failed because `website/examples.html` did not
  exist and `/examples` returned `403`.
- GREEN: targeted website test passed after adding the page, route, and auth
  allowlist.

Verification:

- `python3 -m pytest tests/unit/website/test_launch_website.py::test_launch_website_has_beta_onboarding_pages tests/unit/website/test_launch_website.py::test_api_serves_launch_website_beta_onboarding_pages_without_auth -q` -> `2 passed, 2 warnings`.
- `python3 -m pytest tests/unit/website/test_launch_website.py -q` -> `11 passed, 2 warnings`.
- `python3 -m pytest tests/unit/ -q` -> `642 passed, 8 warnings`.
- `python3 -m pyright scout/` -> `0 errors, 0 warnings, 0 informations`.
- `ruff check scout/ tests/ && ruff format --check scout/ tests/` -> `All checks passed!`, `227 files already formatted`.
- Launch-readiness smoke -> private beta `ready_with_limits`, public launch
  `blocked`, Codex-actionable now `0`.

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

## Launch Governance Checkpoint

Date: 2026-06-28

Built:

- `SECURITY.md` private beta security policy,
- GitHub private beta bug issue template,
- GitHub private beta feature request template,
- `docs/product/release-checklist.md`,
- unit contract tests for launch governance artifacts.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_launch_governance_docs.py -q` failed
  because `SECURITY.md`, beta issue templates, and the release checklist did
  not exist.
- GREEN:
  `python3 -m pytest tests/unit/test_launch_governance_docs.py -q` passed
  after adding the launch governance files.

Boundary:

- No license was selected in this checkpoint.
- No PyPI, GHCR, Docker Hub, or other registry publish was enabled.
- Public launch remains blocked until the release checklist gates are closed.

Verification:

- Focused governance/release gate:
  `python3 -m pytest tests/unit/test_launch_governance_docs.py tests/unit/test_release_workflow.py tests/unit/test_ci_workflow.py -q`
  passed: 7 tests.
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 522 tests, 8 warnings.
- Type check:
  `python3 -m pyright scout/` passed: 0 errors, 0 warnings, 0 informations.
- Lint/format:
  `ruff check scout/ tests/ && ruff format --check scout/ tests/` passed:
  all checks passed, 211 files already formatted.

## Security Scan Evidence Checkpoint

Date: 2026-06-28

Built:

- `docs/security/security-audit-2026-06-28.md`,
- security audit documentation tests,
- release checklist links to recorded dependency and secret scan evidence.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_security_audit_docs.py -q` failed
  because the security audit report did not exist and the release checklist
  did not mark scans as recorded.

Dependency CVE scan:

- Command:
  `rm -rf /tmp/scout-security-audit-venv && python3 -m venv /tmp/scout-security-audit-venv && /tmp/scout-security-audit-venv/bin/python -m pip install --upgrade pip && /tmp/scout-security-audit-venv/bin/python -m pip install . && /tmp/scout-security-audit-venv/bin/python -m pip install pip-audit && /tmp/scout-security-audit-venv/bin/python -m pip_audit --local`
- Result:
  failed with 2 vulnerability rows for `lxml 5.4.0` / `PYSEC-2026-87`;
  fixed version is `6.1.0`.
- Root constraint:
  current Crawl4AI releases tested require `lxml~=5.3`.
- Attempted fix:
  adding `lxml>=6.1.0` to Scout made package installation fail because it
  conflicts with Crawl4AI's current constraint. The attempted dependency floor
  was reverted to keep Scout installable.

Secret scan:

- Command:
  targeted `git grep` over tracked files for common OpenAI, Slack, Google,
  AWS, private-key, and Stripe token patterns.
- Result:
  zero matches.

Boundary:

- The dependency scan is recorded but not clean.
- Public launch remains blocked until the `lxml` CVE is resolved upstream,
  patched, or explicitly risk-accepted.
- The secret scan was targeted and tracked-file-only; an entropy-aware scan is
  still needed before public launch.

Verification:

- Focused security/doc/package gate:
  `python3 -m pytest tests/unit/test_security_audit_docs.py tests/unit/test_launch_governance_docs.py tests/unit/test_package_metadata.py -q`
  passed: 9 tests.
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 524 tests, 8 warnings.
- Type check:
  `python3 -m pyright scout/` passed: 0 errors, 0 warnings, 0 informations.
- Lint/format:
  `ruff check scout/ tests/ && ruff format --check scout/ tests/` passed:
  all checks passed, 212 files already formatted.

## Entropy-Aware Secret Scan Checkpoint

Date: 2026-06-28

Built:

- security audit report section for entropy-aware `detect-secrets` evidence,
- release checklist gate for recorded entropy-aware secret scan,
- unit contract coverage for that evidence.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_security_audit_docs.py -q` failed
  because the audit report did not include `Entropy-Aware Secret Scan` evidence
  and the release checklist did not mark it as recorded.

Scan command:

- `/tmp/scout-detect-secrets-venv/bin/detect-secrets scan --no-verify --exclude-files '(^dist/|^validation-output/|^scout-runs/|^\\.pytest_cache/|^\\.ruff_cache/)' > /tmp/scout-detect-secrets.json`

Scan result:

- files with findings: 18,
- total candidate findings: 26,
- no candidate secret values were printed into docs,
- masked review indicates likely placeholders/examples/test fixtures, but each
  candidate still needs explicit audit or allowlisting before public launch.

Boundary:

- This improves security evidence but does not make the repo secret-scan clean.
- Public launch remains blocked until candidate findings are audited and either
  removed or explicitly allowlisted.

Verification:

- Focused security audit doc gate:
  `python3 -m pytest tests/unit/test_security_audit_docs.py -q` passed:
  2 tests.
- Focused governance/security gate:
  `python3 -m pytest tests/unit/test_security_audit_docs.py tests/unit/test_launch_governance_docs.py -q`
  passed: 5 tests.
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 524 tests, 8 warnings.
- Type check:
  `python3 -m pyright scout/` passed: 0 errors, 0 warnings, 0 informations.
- Lint/format:
  `ruff check scout/ tests/ && ruff format --check scout/ tests/` passed:
  all checks passed, 212 files already formatted.

## Detect-Secrets Baseline Checkpoint

Date: 2026-06-28

Built:

- `.secrets.baseline` with 26 current candidates audited as non-secrets,
- `docs/security/detect-secrets-audit-2026-06-28.md`,
- unit tests verifying every baseline finding is audited,
- unit tests verifying the candidate audit report is present.

Scan gate:

- `/tmp/scout-detect-secrets-venv/bin/detect-secrets-hook --baseline .secrets.baseline --no-verify --exclude-files '(^dist/|^validation-output/|^scout-runs/|^\\.pytest_cache/|^\\.ruff_cache/)' $(git ls-files)`
- Result: passed with the committed baseline.

Verification:

- Focused baseline/security gate:
  `python3 -m pytest tests/unit/test_secret_baseline.py tests/unit/test_security_audit_docs.py -q`
  passed: 4 tests.
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 526 tests, 8 warnings.
- Type check:
  `python3 -m pyright scout/` passed: 0 errors, 0 warnings, 0 informations.
- Lint/format:
  `ruff check scout/ tests/ && ruff format --check scout/ tests/` passed:
  all checks passed, 213 files already formatted.

Boundary:

- This creates a repeatable secret-scan gate for tracked files.
- It does not resolve the Crawl4AI/lxml dependency CVE.
- Public launch still requires the baseline hook to pass on the final release
  commit.

## CI Secret Scan Gate Checkpoint

Date: 2026-06-28

Built:

- GitHub CI `secret-scan` job,
- CI install step for `detect-secrets`,
- blocking CI command:
  `detect-secrets-hook --baseline .secrets.baseline --no-verify --exclude-files '(^dist/|^validation-output/|^scout-runs/|^\\.pytest_cache/|^\\.ruff_cache/)' $(git ls-files)`,
- CI workflow contract test for the secret-scan job.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_ci_workflow.py -q` failed because
  `.github/workflows/ci.yml` had no `secret-scan` job.
- GREEN:
  `python3 -m pytest tests/unit/test_ci_workflow.py -q` passed after adding
  the CI secret-scan job.

Verification:

- Local hook:
  `/tmp/scout-detect-secrets-venv/bin/detect-secrets-hook --baseline .secrets.baseline --no-verify --exclude-files '(^dist/|^validation-output/|^scout-runs/|^\\.pytest_cache/|^\\.ruff_cache/)' $(git ls-files)`
  passed.
- Focused CI/security gate:
  `python3 -m pytest tests/unit/test_ci_workflow.py tests/unit/test_secret_baseline.py tests/unit/test_security_audit_docs.py -q`
  passed: 7 tests.
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 527 tests, 8 warnings.
- Type check:
  `python3 -m pyright scout/` passed: 0 errors, 0 warnings, 0 informations.
- Lint/format:
  `ruff check scout/ tests/ && ruff format --check scout/ tests/` passed:
  all checks passed, 213 files already formatted.

Boundary:

- This enforces the audited tracked-file secret baseline in CI.
- It does not perform a dependency CVE audit in CI because the current
  Crawl4AI/lxml CVE would fail; that remains an explicit public-launch blocker.

## CI Dependency Audit Visibility Checkpoint

Date: 2026-06-28

Built:

- GitHub CI `dependency-audit` job,
- CI install step for the current package and dev extras,
- CI install step for `pip-audit`,
- CI command `python -m pip_audit --local`,
- `continue-on-error: true` while the known Crawl4AI/lxml dependency blocker
  remains open,
- CI workflow contract test for dependency-audit visibility.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_ci_workflow.py -q` failed because
  `.github/workflows/ci.yml` had no `dependency-audit` job.
- GREEN:
  `python3 -m pytest tests/unit/test_ci_workflow.py -q` passed after adding
  the non-blocking dependency audit job.

Boundary:

- This gives CI visibility into dependency CVEs.
- The job is intentionally non-blocking because the current audit fails on
  `lxml 5.4.0` / `PYSEC-2026-87` via Crawl4AI's `lxml~=5.3` constraint.
- Public launch remains blocked until the audit is clean or a documented risk
  decision is made.

Verification:

- Focused CI/security gate:
  `python3 -m pytest tests/unit/test_ci_workflow.py tests/unit/test_security_audit_docs.py tests/unit/test_secret_baseline.py -q`
  passed: 8 tests.
- Local secret hook:
  `/tmp/scout-detect-secrets-venv/bin/detect-secrets-hook --baseline .secrets.baseline --no-verify --exclude-files '(^dist/|^validation-output/|^scout-runs/|^\\.pytest_cache/|^\\.ruff_cache/)' $(git ls-files)`
  passed.
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 528 tests, 8 warnings.
- Type check:
  `python3 -m pyright scout/` passed: 0 errors, 0 warnings, 0 informations.
- Lint/format:
  `ruff check scout/ tests/ && ruff format --check scout/ tests/` passed:
  all checks passed, 213 files already formatted.

## Crawl4AI/lxml Risk Decision Checkpoint

Date: 2026-06-28

Built:

- `docs/security/crawl4ai-lxml-risk-decision-2026-06-28.md`,
- release checklist gate for maintainer approval,
- launch status link to the decision record,
- unit tests requiring the risk decision artifact and public-launch blocker.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_lxml_risk_decision_docs.py -q` failed
  because the risk decision document and release checklist gate were missing.
- GREEN:
  `python3 -m pytest tests/unit/test_lxml_risk_decision_docs.py -q` passed
  after adding the decision-required artifact.

Boundary:

- The risk is not approved by this checkpoint.
- Public launch remains blocked.
- The recommended path is limited private beta only, with explicit maintainer
  acceptance and no clean-audit claim.

Verification:

- Focused launch/security gate:
  `python3 -m pytest tests/unit/test_lxml_risk_decision_docs.py tests/unit/test_ci_workflow.py tests/unit/test_security_audit_docs.py tests/unit/test_secret_baseline.py -q`
  passed: 10 tests.
- Local secret hook:
  `/tmp/scout-detect-secrets-venv/bin/detect-secrets-hook --baseline .secrets.baseline --no-verify --exclude-files '(^dist/|^validation-output/|^scout-runs/|^\\.pytest_cache/|^\\.ruff_cache/)' $(git ls-files)`
  passed.
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 530 tests, 8 warnings.
- Type check:
  `python3 -m pyright scout/` passed: 0 errors, 0 warnings, 0 informations.
- Lint/format:
  `ruff check scout/ tests/ && ruff format --check scout/ tests/` passed:
  all checks passed, 214 files already formatted.

## Founder Decision Draft Packet And Launch Evidence Checkpoint

Date: 2026-06-29

Built:

- generated founder decision draft packet under
  `docs/product/founder-decision-drafts/`,
- `docs/product/founder-decision-drafts/index.md`,
- launch action packet references to the generated draft packet,
- launch evidence index row for the founder decision draft packet,
- governance tests that prevent draft packets from being treated as launch
  approvals.

Boundary:

- Drafts are review aids only.
- No founder decision records are approved.
- Private beta remains `ready_with_limits`.
- Public launch remains `blocked`.
- The latest readiness check reports 14 public-launch blockers with 14 stable,
  unique blocker IDs.

Verification:

- Focused launch governance docs:
  `python3 -m pytest tests/unit/test_launch_governance_docs.py -q` passed:
  25 tests.
- Touched test file lint/format:
  `ruff check tests/unit/test_launch_governance_docs.py && ruff format --check tests/unit/test_launch_governance_docs.py`
  passed.
- Launch readiness smoke:
  `python3 scripts/launch_readiness_check.py --json` summarized as
  `ready_with_limits blocked 14 14`.
- Founder decision record check:
  `python3 -m scout.cli launch-decision-check --root . --check-existing`
  passed with `PASS: 0 founder decision records found.`
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 635 tests, 8 warnings.

Next gate:

- Arijit reviews and approves or changes the six generated decision drafts.
- Codex must not add a final license expression, `LICENSE` file, release tag,
  public registry publishing, or blocking dependency-audit policy until the
  relevant decision record is approved.

## Founder Decision Draft Safety Checkpoint

Date: 2026-06-29

Built:

- `scout launch-decision-check --check-drafts`
- script support:
  `python3 scripts/founder_decision_record_check.py --check-drafts`
- shared draft safety validator in `scout.launch_decision_record`
- docs and website references to the new draft-safety command.

Behavior:

- validates generated founder decision drafts under
  `docs/product/founder-decision-drafts/`,
- requires draft files to remain `Status: Deferred`,
- requires `Public launch allowed by this decision? No`,
- requires founder-review placeholders to remain present,
- fails if a draft starts to look like an approval before it has been copied
  into the completed decision-record naming pattern.

Verification:

- RED:
  `python3 -m pytest tests/unit/test_founder_decision_record_check.py tests/unit/cli/test_run_commands.py::test_launch_decision_check_command_scans_existing_drafts -q`
  failed because `--check-drafts` was not implemented.
- GREEN focused suite:
  `python3 -m pytest tests/unit/test_founder_decision_record_check.py tests/unit/cli/test_run_commands.py::test_launch_decision_check_command_scans_existing_drafts tests/unit/test_launch_governance_docs.py tests/unit/website/test_launch_website.py -q`
  passed: 44 tests, 2 warnings.
- Type check:
  `python3 -m pyright scout/` passed: 0 errors.
- Lint/format:
  `ruff check ... && ruff format --check ...` passed for touched Python files.
- Launch readiness smoke:
  `python3 scripts/launch_readiness_check.py --json` summarized as
  `ready_with_limits blocked 14 14`.
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 638 tests, 8 warnings.
- Real script smoke:
  `python3 scripts/founder_decision_record_check.py --root . --check-existing --check-drafts`
  passed with 0 completed records and 6 safe deferred drafts.

## README Launch Readiness Workflow Checkpoint

Date: 2026-06-29

Built:

- Added a README launch-readiness section that exposes the current launch gate
  truth at the repo entry point.
- Documented the verification commands:
  - `scout launch-readiness`
  - `scout launch-readiness --json`
  - `scout launch-readiness --require-public`
  - `scout launch-decision-check --check-existing --check-drafts`
- Linked the founder decision draft packet and clarified that drafts are review
  aids only, not approvals or release evidence.

TDD:

- RED: `python3 -m pytest tests/unit/test_launch_governance_docs.py -q`
  failed because README did not include the launch readiness workflow section.
- GREEN: same command passed with `26 passed`.

Verification:

- `python3 -m pytest tests/unit/test_launch_governance_docs.py -q` -> `26 passed`.
- `python3 -m scout.cli launch-readiness --root . --json` confirmed:
  - private beta: `ready_with_limits`
  - public launch: `blocked`
  - Codex-actionable now: `0`
- `python3 -m scout.cli launch-decision-check --root . --check-existing --check-drafts`
  -> `PASS: 0 founder decision records found`; `PASS: 6 founder decision drafts are safe for review`.
- `python3 -m pytest tests/unit/ -q` -> `639 passed, 8 warnings`.

## Private Beta Tester Handoff Checkpoint

Date: 2026-06-29

Built:

- Added `docs/product/private-beta-tester-handoff.md`, a sendable packet for
  approved private beta testers.
- Linked the handoff from README and `/beta`.
- Registered the handoff in the release checklist and launch evidence index.

Behavior:

- Gives testers a 30-minute first-run path.
- Separates local-first, Docker, hosted convenience, and skill/agent paths.
- States current launch truth: private beta `ready_with_limits`, public launch
  `blocked`.
- Repeats hosted beta finite-credit limits and no-unlimited/no-hard-site-bypass
  boundaries.
- Points feedback to private beta issue templates and warns testers not to
  share secrets.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_launch_governance_docs.py::test_private_beta_tester_handoff_packet_is_sendable_and_boundary_safe -q`
  failed because the handoff packet did not exist.
- RED:
  `python3 -m pytest tests/unit/website/test_launch_website.py::test_launch_website_has_beta_onboarding_pages -q`
  failed because `/beta` did not link the handoff.
- GREEN:
  both focused tests passed after adding the packet and website link.

Verification:

- `python3 -m pytest tests/unit/test_launch_governance_docs.py tests/unit/website/test_launch_website.py -q`
  -> `38 passed, 2 warnings`.
- `ruff check tests/unit/test_launch_governance_docs.py tests/unit/website/test_launch_website.py`
  -> `All checks passed!`.
- `ruff format --check tests/unit/test_launch_governance_docs.py tests/unit/website/test_launch_website.py`
  -> `2 files already formatted`.
- `python3 -m pytest tests/unit/ -q` -> `640 passed, 8 warnings`.
- `python3 -m scout.cli launch-readiness --root . --json` confirmed:
  - private beta: `ready_with_limits`
  - public launch: `blocked`
  - Codex-actionable now: `0`

## Private Beta Invitation Packet Checkpoint

Date: 2026-06-29

Built:

- Added `docs/product/private-beta-invitation-packet.md`.
- Registered the packet in the private beta launch plan and launch evidence
  index.

Behavior:

- Defines the recommended 5-10 tester cohort profiles.
- Names users not to invite during private beta.
- Provides operator preflight commands before sending invitations.
- Includes invite and follow-up email copy.
- Defines manual success metrics for activation, artifact discovery, feedback,
  value clarity, and boundary clarity.
- Keeps tester names, emails, API keys, and private feedback out of the public
  repository.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_launch_governance_docs.py::test_private_beta_invitation_packet_defines_recruiting_and_preflight -q`
  failed because the invite packet did not exist.
- GREEN:
  same focused test passed after adding the packet and references.

Verification:

- `python3 -m pytest tests/unit/test_launch_governance_docs.py -q` -> `28 passed`.
- `ruff check tests/unit/test_launch_governance_docs.py` -> `All checks passed!`.
- `ruff format --check tests/unit/test_launch_governance_docs.py` -> `1 file already formatted`.
- `python3 -m pytest tests/unit/ -q` -> `641 passed, 8 warnings`.
- `python3 -m scout.cli launch-readiness --root . --json` confirmed:
  - private beta: `ready_with_limits`
  - public launch: `blocked`
  - Codex-actionable now: `0`

## Competitor Website Decision Map Checkpoint

Date: 2026-06-29

Built:

- Added `docs/competetor-website-knowledge/website-decision-map.md`.
- Registered the map in `docs/competetor-website-knowledge/source-index.md`.
- Updated launch evidence to reference the decision map as the bridge between
  competitor research and implemented website sections.

Behavior:

- Maps Firecrawl, Browserbase, Apify, Tavily, and adjacent competitor patterns
  to Scout website decisions.
- Records why the site leads with local install, hosted beta, artifacts,
  evidence, finite credits, and launch status.
- Preserves blocked claims: no unlimited hosted crawling, no guaranteed
  hard-site bypass, no certified legacy `/app` UI, and no public self-serve
  hosted launch.
- Names the Supadesign IndustrialGray design decision and the current website
  files it influences.

TDD:

- RED:
  `python3 -m pytest tests/unit/test_launch_governance_docs.py::test_competitor_website_decision_map_ties_research_to_current_site -q`
  failed because the decision map did not exist.
- GREEN:
  the focused test passed after adding the map and references.

Verification:

- `python3 -m pytest tests/unit/test_launch_governance_docs.py -q` -> `29 passed`.
- `ruff check tests/unit/test_launch_governance_docs.py` -> `All checks passed!`.
- `ruff format --check tests/unit/test_launch_governance_docs.py` -> `1 file already formatted`.
- `python3 -m pytest tests/unit/ -q` -> `642 passed, 8 warnings`.

## Launch Readiness Actionable Summary Checkpoint

Date: 2026-06-29

Built:

- `public_launch.actionable_summary.codex_actionable_now` in the readiness JSON,
- `Codex actionable now: 0` in the readiness text output,
- matching copy in the launch dashboard, gate burndown, and status website.

Why:

- The readiness report already assigned Codex eight public-launch blockers, but
  every Codex-owned item depends on a founder/risk/publishing decision, release
  artifact, or Stripe test-mode setup. The new summary prevents handoffs from
  misreading assigned work as immediately executable work.

Verification:

- RED:
  `python3 -m pytest tests/unit/test_launch_readiness_check.py -q` failed
  because `actionable_summary` and `Codex actionable now: 0` did not exist.
- Focused suite:
  `python3 -m pytest tests/unit/test_launch_readiness_check.py tests/unit/website/test_launch_website.py tests/unit/test_launch_governance_docs.py -q`
  passed: 43 tests, 2 warnings.
- Readiness text smoke:
  `python3 scripts/launch_readiness_check.py --root .` printed
  `Codex actionable now: 0`.
- Readiness JSON smoke:
  `python3 scripts/launch_readiness_check.py --json` summarized as
  `ready_with_limits blocked 0` for private beta, public launch, and Codex
  actionable-now count.
- Type check:
  `python3 -m pyright scout/` passed: 0 errors.
- Lint/format:
  `ruff check ... && ruff format --check ...` passed for touched Python files.
- Full unit suite:
  `python3 -m pytest tests/unit/ -q` passed: 638 tests, 8 warnings.
