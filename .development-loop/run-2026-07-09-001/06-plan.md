# 06 - Plan: Comparative Intelligence

Date: 2026-07-09
Builder: feature-builder

## Branch Strategy

Create a dedicated branch when approved:

`feature/comparative-intelligence`

Do not mix with launch website copy or hosted billing changes.

## Recommended V1

Product price comparison with user-supplied sources.

## Implementation Tasks

- [ ] Add comparison Pydantic contracts.
- [ ] Add product-price fixture pages.
- [ ] Write RED tests for price parsing, currency normalization, product
      identity matching, wrong-model refusal, and matrix artifact output.
- [ ] Build comparison service orchestration.
- [ ] Add artifact output: `comparison_matrix.csv` and
      `comparison_matrix.json`.
- [ ] Add API route behind existing auth.
- [ ] Add export integration.
- [ ] Add hosted UI workflow after API contract stabilizes.
- [ ] Add source-policy and security review.
- [ ] Run one approved live smoke.

## Test Matrix

| Requirement | Test layer |
|---|---|
| Price normalization | Unit |
| Product identity matching | Unit |
| Wrong-model refusal | Unit |
| Matrix artifact generation | Integration fixture |
| API response shape | Contract |
| Auth boundary | API unit |
| CSV/JSON export | Unit/integration |
| Hosted workflow usability | Playwright |
| Live-source honesty | Live smoke |

## Build Gates

- No implementation before source-policy and V1 vertical approval.
- No production claim without unit, contract, fixture integration, UI, and live
  smoke evidence.
- No "best price" language; use "observed at crawl time."
