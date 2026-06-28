# Hosted Stripe Webhook Status

Status: implemented and re-verified with key-delivery gate

Goal: add the HTTP boundary that receives Stripe checkout events, verifies the
Stripe signature, and calls the hosted payment provisioning service without
leaking raw API keys in webhook responses.

Non-goals:

- no Stripe SDK dependency,
- no Customer Portal,
- no email/key delivery,
- no public dashboard,
- no subscription lifecycle handling.

## Verification So Far

- RED: `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py -q`
  - Result: failed because `get_hosted_payment_provisioning_service` did not exist.
- GREEN: `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 12 passed.
- Focused static typing:
  `python3 -m pyright scout/api/routers/billing.py scout/api/deps.py scout/api/main.py tests/unit/api/test_billing_stripe_webhook.py`
  - Result: 0 errors.
- Focused lint/format:
  `ruff check ...` and `ruff format --check ...`
  - Result: passed.

## Broad Verification

- API unit checkpoint: `python3 -m pytest tests/unit/api -q`
  - Result: 116 passed, 2 warnings.
- Full unit checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 461 passed, 8 warnings.
- Static typing: `python3 -m pyright scout/`
  - Result: 0 errors, 0 warnings, 0 informations.
- Lint/format: `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: all checks passed; 192 files already formatted.

## Remaining Work

- Add Stripe CLI/live sandbox smoke test when a webhook secret is available.
- Add production key recovery/support policy. The webhook response
  intentionally never returns raw `scout_live_...` keys to Stripe.

## Key Delivery Gate Update

The webhook now refuses to provision a new hosted key unless an enabled
`HostedApiKeyDeliveryService` is configured. This prevents the unsafe state
where Stripe payment succeeds, the webhook creates a raw API key, and then no
customer-facing channel exists to deliver that key.

Focused verification:

- RED: `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.key_delivery'`.
- GREEN: `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 13 passed.
- Focused pyright and Ruff checks passed.

Broad re-verification:

- `python3 -m pytest tests/unit/api -q` -> `117 passed`.
- `python3 -m pytest tests/unit/ -q` -> `462 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/ && ruff format --check scout/ tests/` -> passed.
