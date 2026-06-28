# Product Export Adapters - Strategy

Date: 2026-06-28

## Does This Fit The Product Vision?

Yes. Scout's launch position is "records, not blobs." If product data can only
flow into Algolia, Scout looks like an Algolia-specific demo tool. Generic local
exports make Scout useful for broader AI, data, and research workflows.

## Target Segment

Users who extract ecommerce/product data and need to inspect, store, enrich, or
load it into tools that are not Algolia:

- AI builders,
- search/demo builders,
- competitive intelligence researchers,
- data analysts,
- RevOps/prospecting teams.

## Trade-Off

We are not building a full connector marketplace or live Google Sheets OAuth
flow in this slice. We are choosing a durable local adapter boundary first.

## Key Metric

A product run can produce local records in at least three non-Algolia formats
without changing extraction logic.

## Defensibility

The defensibility is not the file format itself. It is the combination of
extracted records, citations, artifact contract, and repeatable local outputs.

