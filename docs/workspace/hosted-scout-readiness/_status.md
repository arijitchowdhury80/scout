# Hosted Scout Readiness Status

Date: 2026-06-28
Status: In progress

## Checklist

- [x] Existing auth/settings/run persistence inspected.
- [x] Production architecture written.
- [x] Security and scale audit written.
- [x] Failing hosted policy tests written.
- [x] Minimal hosted policy module implemented.
- [x] Focused verification passed.
- [x] API-key lifecycle tests written.
- [x] API-key lifecycle module implemented.
- [x] API-key focused verification passed.
- [x] URL safety/SSRF tests written.
- [x] URL safety/SSRF module implemented.
- [x] URL safety focused verification passed.
- [x] Hosted account service tests written.
- [x] Hosted account service implemented.
- [x] Hosted account service verification passed.
- [x] Hosted admission service tests written.
- [x] Hosted admission service implemented.
- [x] Hosted admission service verification passed.
- [x] SQLite hosted account persistence tests written.
- [x] SQLite hosted account store implemented.
- [x] SQLite hosted account persistence verification passed.
- [x] Hosted HTTP scrape boundary tests written.
- [x] Hosted HTTP scrape boundary implemented.
- [x] Hosted HTTP scrape boundary verification passed.
- [x] Hosted beta provisioning CLI tests written.
- [x] Hosted beta provisioning CLI implemented.
- [x] Hosted beta provisioning CLI verification passed.
- [x] Hosted payment provisioning tests written.
- [x] Hosted payment provisioning service implemented.
- [x] Hosted payment provisioning verification passed.
- [x] Hosted Stripe webhook tests written.
- [x] Hosted Stripe webhook route implemented.
- [x] Hosted Stripe webhook verification passed.
- [x] Hosted key delivery contract tests written.
- [x] Hosted key delivery gate implemented.
- [x] Hosted key delivery verification passed.
- [x] Hosted SMTP key delivery tests written.
- [x] Hosted SMTP key delivery implemented.
- [x] Hosted SMTP key delivery verification passed.

## Scope

Define and start the production-readiness foundation for hosted Scout:

- tenant model,
- API key lifecycle,
- Stripe/payment integration boundary,
- quota/credit policy,
- hosted usage limits,
- security risks,
- local-first vs hosted product decision.

This stream now includes SQLite account persistence, a Stripe-compatible payment
provisioning domain layer, and a signed Stripe webhook route for
`checkout.session.completed`. It still does not implement user login, secure
Customer Portal, production Postgres, a public dashboard, or a live SMTP/Stripe
sandbox smoke.

## Verification

- RED: `python3 -m pytest tests/unit/core/platform/test_hosted_policy.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.hosted'`.
- GREEN: `python3 -m pytest tests/unit/core/platform/test_hosted_policy.py -q`
  - Result: 6 passed.
- API-key RED: `python3 -m pytest tests/unit/core/platform/test_api_keys.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.api_keys'`.
- API-key GREEN: `python3 -m pytest tests/unit/core/platform/test_api_keys.py -q`
  - Result: 7 passed.
- URL safety RED: `python3 -m pytest tests/unit/core/platform/test_url_safety.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.url_safety'`.
- URL safety GREEN: `python3 -m pytest tests/unit/core/platform/test_url_safety.py -q`
  - Result: 9 passed.
- Hosted account service RED: `python3 -m pytest tests/unit/core/platform/test_account_service.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.account_service'`.
- Hosted account service GREEN: `python3 -m pytest tests/unit/core/platform/test_account_service.py -q`
  - Result: 6 passed.
- Hosted account checkpoint: `python3 -m pytest tests/unit/core/platform -q`
  - Result: 59 passed.
- Hosted admission RED: `python3 -m pytest tests/unit/core/platform/test_hosted_admission.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.hosted_admission'`.
- Hosted admission GREEN: `python3 -m pytest tests/unit/core/platform/test_hosted_admission.py -q`
  - Result: 6 passed.
- Hosted admission checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 440 passed.
- SQLite hosted account persistence RED:
  `python3 -m pytest tests/unit/core/platform/test_account_sqlite_store.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.account_sqlite_store'`.
- SQLite hosted account persistence GREEN:
  `python3 -m pytest tests/unit/core/platform/test_account_sqlite_store.py -q`
  - Result: 3 passed.
- SQLite hosted account persistence checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 443 passed.
- Hosted HTTP boundary RED:
  `python3 -m pytest tests/unit/api/test_hosted_scrape.py tests/unit/api/test_auth.py -q`
  - Result: failed because `get_hosted_account_service` did not exist.
- Hosted HTTP boundary GREEN:
  `python3 -m pytest tests/unit/api/test_hosted_scrape.py tests/unit/api/test_auth.py -q`
  - Result: 9 passed.
- Hosted HTTP boundary checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 447 passed.
- Hosted beta provisioning CLI RED:
  `python3 -m pytest tests/unit/cli/test_run_commands.py -q -k "hosted_provision"`
  - Result: failed with Typer exit code 2 because `hosted-provision` did not exist.
- Hosted beta provisioning CLI GREEN:
  `python3 -m pytest tests/unit/cli/test_run_commands.py -q -k "hosted_provision"`
  - Result: 2 passed.
- Hosted beta provisioning CLI checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 449 passed.
- Hosted payment provisioning RED:
  `python3 -m pytest tests/unit/core/platform/test_payment_provisioning.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.payment_provisioning'`.
- Hosted payment provisioning GREEN:
  `python3 -m pytest tests/unit/core/platform/test_payment_provisioning.py -q`
  - Result: 6 passed.
- Hosted payment provisioning checkpoint:
  `python3 -m pytest tests/unit/core/platform -q`
  - Result: 74 passed.
- Hosted Stripe webhook RED:
  `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py -q`
  - Result: failed because `get_hosted_payment_provisioning_service` did not exist.
- Hosted Stripe webhook GREEN:
  `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 12 passed.
- Hosted Stripe webhook API checkpoint:
  `python3 -m pytest tests/unit/api -q`
  - Result: 116 passed.
- Hosted Stripe webhook full unit checkpoint:
  `python3 -m pytest tests/unit/ -q`
  - Result: 461 passed.
- Hosted Stripe webhook static/lint checkpoint:
  `python3 -m pyright scout/` and `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: pyright 0 errors; Ruff passed.
- Hosted key delivery gate RED:
  `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.key_delivery'`.
- Hosted key delivery gate GREEN:
  `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 13 passed.
- Hosted key delivery gate full checkpoint:
  `python3 -m pytest tests/unit/api -q` and `python3 -m pytest tests/unit/ -q`
  - Result: API unit 117 passed; full unit 462 passed.
- Hosted key delivery static/lint checkpoint:
  `python3 -m pyright scout/` and `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: pyright 0 errors; Ruff passed.
- Hosted SMTP key delivery RED:
  `python3 -m pytest tests/unit/core/platform/test_key_delivery.py -q`
  - Result: failed because `SmtpHostedApiKeyDeliveryConfig` did not exist.
- Hosted SMTP key delivery GREEN:
  `python3 -m pytest tests/unit/core/platform/test_key_delivery.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 17 passed.
- Hosted SMTP key delivery full checkpoint:
  `python3 -m pytest tests/unit/api -q` and `python3 -m pytest tests/unit/ -q`
  - Result: API unit 117 passed; full unit 466 passed.
- Hosted SMTP key delivery static/lint checkpoint:
  `python3 -m pyright scout/` and `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: pyright 0 errors; Ruff passed.
