# Hosted Stripe Webhook Status

Status: implemented and verified

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

- Add secure key delivery after webhook provisioning. The webhook response
  intentionally never returns raw `scout_live_...` keys to Stripe.
- Add Stripe CLI/live sandbox smoke test when a webhook secret is available.
