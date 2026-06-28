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
