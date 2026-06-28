# Hosted Payment Provisioning Status

Status: implemented and verified

Goal: add a Stripe-compatible domain layer that turns a paid hosted checkout
into one hosted Scout account and API key, exactly once.

Current slice:

- [x] create the workspace planning notes,
- [x] write TDD tests for paid checkout provisioning, idempotency, amount
  validation, unpaid rejection, and raw-key storage safety,
- [x] implement a pure domain service plus SQLite event store,
- [x] update hosted readiness docs after verification.

Non-goals for this slice:

- no public signup UI,
- no real Stripe SDK calls,
- no email delivery,
- no Customer Portal.

## Verification

- RED: `python3 -m pytest tests/unit/core/platform/test_payment_provisioning.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.payment_provisioning'`.
- GREEN: `python3 -m pytest tests/unit/core/platform/test_payment_provisioning.py -q`
  - Result: 6 passed.
- Platform checkpoint: `python3 -m pytest tests/unit/core/platform -q`
  - Result: 74 passed.
- Full unit checkpoint: `python3 -m pytest tests/unit/ -q`
  - Result: 455 passed, 8 warnings.
- Static typing: `python3 -m pyright scout/`
  - Result: 0 errors, 0 warnings, 0 informations.
- Lint: `ruff check scout/ tests/`
  - Result: all checks passed.
- Format: `ruff format --check scout/ tests/`
  - Result: 190 files already formatted.

## Remaining Hosted Payment Work

- Add customer email/key delivery or portal-based key display.
- Add production transactional persistence, likely Postgres.
- Add subscription/Customer Portal handling for non-beta plans.
