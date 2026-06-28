# Product Export Adapters - PRD

Date: 2026-06-28

## Summary

Add generic product export adapters so Scout can write extracted product records
to local JSON, JSONL, CSV, and SQLite destinations. Algolia remains an adapter,
not the only product data path.

## Background

Launch planning identified a product risk: Scout's product flow currently reads
as "fetch product data for Algolia." The product needs to support broader local
data workflows and future adapters such as Google Sheets.

## Objective

Make product records portable.

Key results:

- Export a list of product records to JSON, JSONL, CSV, and SQLite.
- Preserve source/citation fields where the destination supports them.
- Return a typed manifest of written files/tables.

## Solution

### V1 Features

- `ProductExportFormat` enum.
- `ProductExportRequest` Pydantic model.
- `ProductExportResult` Pydantic model.
- `export_product_records(request)` public function.
- JSON export writes a list of records.
- JSONL export writes one record per line.
- CSV export writes common flat fields and serializes complex fields as JSON.
- SQLite export writes records to a configurable table.

### Acceptance Criteria

- Empty record lists still write valid empty artifacts.
- CSV includes `objectID`, `name`, `url`, `brand`, `price`, `currency`,
  `categories`, `source_url`, `citations`, and `completeness_score`.
- SQLite creates the target table and inserts rows.
- Unsupported formats fail via Pydantic enum validation.

## Later

- Google Sheets adapter.
- Webhook adapter.
- Hosted export jobs.
- Export endpoint in HTTP API.
- CLI command for standalone exports.

