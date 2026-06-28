# Product Export Adapters Status

Date: 2026-06-28
Status: In progress

## Checklist

- [x] Strategy/PRD written.
- [x] SOP constraints loaded.
- [x] Existing tests mapped and baseline run.
- [x] Failing tests written.
- [x] Implementation written.
- [x] Focused verification passed.

## Scope

Generalize product output beyond Algolia by adding local export adapters for
already-extracted product records.

V1 targets:

- JSON
- JSONL
- CSV
- SQLite
- CLI command: `scout product-export`

Deferred:

- Google Sheets live write.
- Hosted export jobs.
- Credential storage.

## Verification

- Baseline before implementation: `python3 -m pytest tests/unit/core/products -q`
  - Result: 44 passed.
- RED: `python3 -m pytest tests/unit/core/products/test_exports.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.products.exports'`.
- GREEN: `python3 -m pytest tests/unit/core/products/test_exports.py -q`
  - Result: 6 passed.
- CLI RED: `python3 -m pytest tests/unit/cli/test_run_commands.py -q -k "product_export"`
  - Result: failed because `product-export` was not registered.
- CLI GREEN: `python3 -m pytest tests/unit/cli/test_run_commands.py -q -k "product_export"`
  - Result: 3 passed.
