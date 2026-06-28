# Hosted Account Persistence Status

Status: Verified checkpoint
Date: 2026-06-28

## Goal

Add a durable hosted account store so Scout can preserve tenants, API-key
metadata, and credit balances across service instances. This is the persistence
step between pure in-memory domain tests and a production Postgres-backed hosted
deployment.

## Completed

- [x] Strategy and PRD written.
- [x] RED SQLite persistence tests written and observed failing.
- [x] Minimal SQLite store implemented.
- [x] Verification run.
- [x] Hosted readiness docs updated.

## Boundary

SQLite is not the final hosted production database. It is a local/dev durable
repository that proves the persistence contract before adding Postgres,
migrations, and hosted deployment infrastructure.

## TDD Evidence

RED:

```bash
python3 -m pytest tests/unit/core/platform/test_account_sqlite_store.py -q
```

Result: failed with `ModuleNotFoundError: No module named
'scout.core.platform.account_sqlite_store'`.

GREEN:

```bash
python3 -m pytest tests/unit/core/platform/test_account_sqlite_store.py -q
```

Result: `3 passed, 2 warnings`.

## Final Verification

```bash
python3 -m pytest tests/unit/core/platform -q
```

Result: `68 passed, 2 warnings`.

```bash
python3 -m pytest tests/unit/ -q
```

Result: `443 passed, 8 warnings`.

```bash
python3 -m pyright scout/
```

Result: `0 errors, 0 warnings, 0 informations`.

```bash
ruff check scout/ tests/
ruff format --check scout/ tests/
```

Result: `All checks passed!` and `186 files already formatted`.
