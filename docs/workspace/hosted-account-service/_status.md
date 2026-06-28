# Hosted Account Service Status

Status: Verified checkpoint
Date: 2026-06-28

## Goal

Create the first tested hosted-account domain layer for Scout so future hosted
routes and Stripe webhooks have a safe place to provision tenants, issue API
keys, seed finite credits, authorize scopes, and debit usage.

## Completed

- [x] Strategy, PRD, pre-mortem, and SOP constraints written.
- [x] RED tests written and observed failing.
- [x] Minimal service implementation.
- [x] Focused verification.
- [x] Docs updated with final status.

## Boundary

This slice does not add public HTTP routes, persistent database migrations, or
Stripe integration. It creates the tested domain contract those layers should
use.

## TDD Evidence

RED:

```bash
python3 -m pytest tests/unit/core/platform/test_account_service.py -q
```

Result: failed with `ModuleNotFoundError: No module named
'scout.core.platform.account_service'`.

GREEN:

```bash
python3 -m pytest tests/unit/core/platform/test_account_service.py -q
```

Result: `6 passed, 2 warnings`.

## Final Verification

```bash
python3 -m pytest tests/unit/core/platform -q
```

Result: `59 passed, 2 warnings`.

```bash
python3 -m pytest tests/unit/ -q
```

Result: `434 passed, 8 warnings`.

```bash
python3 -m pyright scout/
```

Result: `0 errors, 0 warnings, 0 informations`.

```bash
ruff check scout/ tests/
ruff format --check scout/ tests/
```

Result: `All checks passed!` and `182 files already formatted`.
