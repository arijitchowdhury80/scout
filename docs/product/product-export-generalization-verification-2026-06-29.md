# Product Export Generalization Verification

Date: 2026-06-29

Status: **Verified for private beta.**

## Summary

Scout's product workflow is no longer Algolia-only. Product records can be
exported through generic local adapters:

- JSON
- JSONL
- CSV
- SQLite
- Google Sheets import CSV
- Google Sheets import instructions

Algolia remains a supported downstream destination through preview/push
workflows, but local product records now have usable non-Algolia export paths.

## Implementation Evidence

Core implementation:

- `scout/core/products/exports.py`
- `ProductExportFormat.JSON`
- `ProductExportFormat.JSONL`
- `ProductExportFormat.CSV`
- `ProductExportFormat.SQLITE`
- `ProductExportFormat.GOOGLE_SHEETS`
- `export_product_records(...)`

CLI:

- `scout product-export`

Documentation:

- `README.md`
- `docs/distribution.md`
- `docs/use-cases.md`
- `docs/competetor-website-knowledge/production-readiness-and-distribution.md`

## Verification Commands

Focused tests:

```bash
python3 -m pytest tests/unit/core/products/test_exports.py tests/unit/cli/test_run_commands.py -q
```

Result:

```text
24 passed, 8 warnings in 16.46s
```

Warnings were unrelated third-party deprecation warnings from Crawl4AI/Pydantic
and BeautifulSoup.

CLI smoke:

```bash
python3 -m scout.cli product-export \
  /tmp/scout-product-export-smoke/records.json \
  --output-dir /tmp/scout-product-export-smoke/exports \
  --format json \
  --format jsonl \
  --format csv \
  --format sqlite \
  --format google_sheets
```

Result:

```json
{
  "success": true,
  "record_count": 1,
  "files": {
    "json": "/tmp/scout-product-export-smoke/exports/products.json",
    "jsonl": "/tmp/scout-product-export-smoke/exports/products.jsonl",
    "csv": "/tmp/scout-product-export-smoke/exports/products.csv",
    "sqlite": "/tmp/scout-product-export-smoke/exports/products.sqlite",
    "google_sheets_csv": "/tmp/scout-product-export-smoke/exports/products.google-sheets.csv",
    "google_sheets_instructions": "/tmp/scout-product-export-smoke/exports/products.google-sheets-import.md"
  }
}
```

Artifact check:

```text
/tmp/scout-product-export-smoke/exports/products.csv
/tmp/scout-product-export-smoke/exports/products.google-sheets-import.md
/tmp/scout-product-export-smoke/exports/products.google-sheets.csv
/tmp/scout-product-export-smoke/exports/products.json
/tmp/scout-product-export-smoke/exports/products.jsonl
/tmp/scout-product-export-smoke/exports/products.sqlite
json_records 1
jsonl_lines 1
csv_rows 1
sqlite_rows 1
google_sheets_csv_exists True
google_sheets_guide_exists True
```

## Security And Product Boundaries

Verified:

- SQLite table names are validated before SQL interpolation.
- Google Sheets export is an import-ready CSV plus guide, not an API push.
- Direct Google Sheets API push is intentionally not enabled because it would
  require user OAuth/service-account credentials and a separate security review.
- Algolia credentials are still handled through explicit preview/push paths,
  not through the generic export command.

## Remaining Future Work

- Direct Google Sheets API push.
- Webhook export adapter.
- Hosted export jobs with tenant ownership, object storage, retention, and
  quota controls.
- Rename internal `AlgoliaProductRecord` type to a more generic product record
  name in a later breaking-contract cleanup. The current external behavior is
  already generic enough for private beta.
