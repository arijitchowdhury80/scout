# Hosted API Key Delivery Status

Status: SMTP delivery implemented and verified

Goal: prevent hosted checkout webhooks from creating API keys that cannot be
delivered to the customer.

Built:

- `HostedApiKeyDeliveryRequest`
- `HostedApiKeyDeliveryResult`
- `HostedApiKeyDeliveryService` protocol
- `DisabledHostedApiKeyDeliveryService`
- `SmtpHostedApiKeyDeliveryConfig`
- `SmtpHostedApiKeyDeliveryService`
- Stripe webhook delivery gate

Behavior:

- The webhook requires an enabled delivery service before provisioning a new
  hosted API key.
- When delivery is disabled, the webhook returns `503` before account/key
  creation.
- When delivery is enabled, the webhook passes the raw API key to the delivery
  adapter exactly once and still excludes the raw key from the webhook response.
- Idempotent replay does not redeliver the key.
- SMTP delivery is enabled when `hosted_key_delivery_smtp_host` and
  `hosted_key_delivery_smtp_from_email` are configured.
- SMTP delivery sends the one-time raw key to the checkout customer and returns
  a structured failure if SMTP delivery fails.

Verification so far:

- RED: `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.key_delivery'`.
- SMTP RED: `python3 -m pytest tests/unit/core/platform/test_key_delivery.py -q`
  - Result: failed because `SmtpHostedApiKeyDeliveryConfig` did not exist.
- GREEN: `python3 -m pytest tests/unit/api/test_billing_stripe_webhook.py -q`
  - Result: 6 passed.
- SMTP GREEN: `python3 -m pytest tests/unit/core/platform/test_key_delivery.py -q`
  - Result: 4 passed.
- Focused checkpoint:
  `python3 -m pytest tests/unit/core/platform/test_key_delivery.py tests/unit/api/test_billing_stripe_webhook.py tests/unit/api/test_auth.py -q`
  - Result: 17 passed.
- Focused pyright and Ruff checks passed.

Broad verification:

- API unit checkpoint: `python3 -m pytest tests/unit/api -q`
  - Result: 117 passed, 2 warnings.
- Full unit checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 462 passed, 8 warnings.
- Static typing: `python3 -m pyright scout/`
  - Result: 0 errors, 0 warnings, 0 informations.
- Lint/format: `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: all checks passed; 193 files already formatted.

Still pending:

- SMTP provider smoke with real test SMTP credentials.
- Portal or one-time customer handoff as an alternative to email.
- Stripe sandbox smoke with a configured delivery adapter.
- Operational runbook for key recovery when delivery fails after creation.

Broad verification:

- API unit checkpoint: `python3 -m pytest tests/unit/api -q`
  - Result: 117 passed, 2 warnings.
- Full unit checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 466 passed, 8 warnings.
- Static typing: `python3 -m pyright scout/`
  - Result: 0 errors, 0 warnings, 0 informations.
- Lint/format: `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: all checks passed; 194 files already formatted.
