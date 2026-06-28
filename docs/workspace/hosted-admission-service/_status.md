# Hosted Admission Service Status

Status: Verified checkpoint
Date: 2026-06-28

## Goal

Create one tested hosted request admission path that future hosted HTTP routes
can call before running Scout work. The decision must authenticate the API key,
validate URL safety, enforce scopes, and debit finite credits only when the
request is actually admitted.

## Completed

- [x] Strategy and PRD written.
- [x] RED tests written and observed failing.
- [x] Minimal admission service implemented.
- [x] Verification run.
- [x] Hosted readiness docs updated.

## Boundary

This slice does not expose public hosted endpoints. It creates the domain
service that future `/v1/scrape`, `/v1/crawl`, `/v1/products`, and screenshot
routes should call.

## TDD Evidence

RED:

```bash
python3 -m pytest tests/unit/core/platform/test_hosted_admission.py -q
```

Result: failed with `ModuleNotFoundError: No module named
'scout.core.platform.hosted_admission'`.

GREEN:

```bash
python3 -m pytest tests/unit/core/platform/test_hosted_admission.py -q
```

Result: `6 passed, 2 warnings`.

## Final Verification

```bash
python3 -m pytest tests/unit/ -q
```

Result: `440 passed, 8 warnings`.

```bash
python3 -m pyright scout/
```

Result: `0 errors, 0 warnings, 0 informations`.

```bash
ruff check scout/ tests/
ruff format --check scout/ tests/
```

Result: `All checks passed!` and `184 files already formatted`.
