# Comparative Intelligence Technical Spike Plan

Date: 2026-07-09

## Recommended First Slice

Ship product price comparison first.

Reasoning:

- It reuses the existing `products` extraction contract.
- It is easy for non-technical users to understand.
- It creates reusable primitives for launch pricing and hotel rates: source
  fan-out, field normalization, identity matching, matrix rendering, citations,
  and exports.

Hotel rates are valuable, but they add date, occupancy, taxes, fees, rooms,
location radius, and OTA-specific complexity. They should be the second vertical
after the comparison engine proves itself.

## Architecture Sketch

Core modules:

- `scout/core/comparisons/types.py`
  - Pydantic request/response models.
  - `ComparisonType`, `ComparisonSource`, `ComparisonCell`,
    `ComparisonMatrix`, `ComparisonRunResult`.
- `scout/core/comparisons/service.py`
  - Orchestrates source fan-out, extraction, normalization, matching, validation,
    artifact writing.
- `scout/core/comparisons/product_prices.py`
  - Product-specific extraction and matching.
- `scout/core/comparisons/launch_pricing.py`
  - Category/product research and price-band analysis.
- `scout/core/comparisons/hotel_rates.py`
  - Deferred until product comparison primitives are stable.
- `scout/api/routers/comparisons.py`
  - Hosted/API entry point.
- `scout/cli.py`
  - CLI command, if current CLI structure supports it.

Artifacts:

- Reuse the standard Scout run artifact shape.
- Add `comparison_matrix.csv` and `comparison_matrix.json`.
- Keep raw records separately from interpreted matrix rows.

## Spike Phases

### Phase 0 - Source Policy And UX Contract

Deliverables:

- Confirm allowed source categories for hosted Scout.
- Decide V1 source mode: user-supplied URLs only, source presets, or both.
- Decide whether the hosted UI exposes this during beta.

Exit criteria:

- Written source policy.
- Approved V1 vertical.
- Approved pricing/credit treatment.

### Phase 1 - Fixture-First Product Comparison

Deliverables:

- Four retailer-like fixture pages for one TV model.
- One fixture page with wrong model.
- One fixture page with sale/list price.
- One fixture page with unavailable product.
- Product comparison service that produces a matrix.

Tests:

- Price parsing unit tests.
- Currency normalization unit tests.
- SKU/model matching unit tests.
- Wrong-model refusal test.
- Matrix artifact snapshot test.

Exit criteria:

- Fixture run returns a cited matrix with correct prices and confidence.
- Wrong model is not merged into the same comparison row.

### Phase 2 - API And Export Contract

Deliverables:

- `POST /v1/comparisons`.
- JSON/JSONL/CSV/SQLite export integration.
- `validation.json` includes blocked, sparse, ambiguous, and stale rows.

Tests:

- API contract tests.
- Auth tests.
- Artifact writer tests.
- Export tests.

Exit criteria:

- API returns typed response.
- Exported CSV is useful enough to send to a beta tester.

### Phase 3 - Hosted Workflow

Deliverables:

- UI workflow with comparison type, query, sources, constraints, and output
  matrix.
- Clear copy: "observed at crawl time" and confidence/citation states.

Tests:

- UI unit/snapshot tests if applicable.
- Playwright happy-path with fixture backend or local server.
- Mobile layout check for matrix overflow.

Exit criteria:

- A non-technical tester can run the workflow without knowing crawler terms.

### Phase 4 - Live Smoke

Deliverables:

- Small approved source set.
- One live product price comparison run.
- One launch-pricing dry run.

Tests:

- Live smoke test records output but does not block CI on third-party page drift
  unless using stable internal fixtures.

Exit criteria:

- Live results are honest: either useful matrix rows or explicit blocked-source
  evidence.

## Test Strategy Matrix

| Layer | What it proves |
|---|---|
| Unit | Price parsing, normalization, matching, confidence, caveat handling |
| Contract | Pydantic request/response shape and API error behavior |
| Integration fixtures | End-to-end matrix generation without third-party drift |
| CLI/API | Same core service exposed consistently |
| UI/E2E | Non-technical workflow is understandable and usable |
| Live smoke | Real websites produce either useful cited rows or honest blocked evidence |

## Build Order

1. Add comparison Pydantic contracts.
2. Add product fixture pages and failing tests.
3. Build product comparison service.
4. Add artifact writer and export integration.
5. Add API router.
6. Add CLI command if aligned with current CLI surface.
7. Add hosted workflow.
8. Run security/source policy review.
9. Run live smoke and capture beta-facing examples.

## Development Notes

- Use deterministic parsing for numeric prices wherever possible.
- Use LLM only for cited summarization or field extraction fallback, never as the
  sole source of numeric truth.
- Prefer "observed price" language over "best price."
- Store source timestamp and retrieval mode for every row.
- Low confidence is a product state, not an error to hide.
