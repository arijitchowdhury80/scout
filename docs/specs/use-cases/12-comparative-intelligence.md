# Acquisition Contract: comparative intelligence

**Consumer:** Hosted Scout comparison workflows, API users, CLI users, and beta
market-research demos.

## Input contract

`comparison_type`: `product_price | launch_pricing | hotel_rate`

`query`: business-readable comparison question.

`sources[]`: user-supplied URLs or approved source presets. V1 should require
explicit sources unless source discovery is separately approved.

`constraints`: typed object per comparison type:

- product_price: product name/model/SKU/UPC, optional retailer labels.
- launch_pricing: category, market, target positioning, optional competitor
  URLs.
- hotel_rate: hotel/address/zip, stay date, nights, occupancy, optional radius.

## Acquisition plan

Source fan-out -> per-source extraction -> field normalization -> identity
matching -> confidence scoring -> matrix assembly -> validation report ->
standard artifacts and exports.

## Record types

New comparison records should keep raw observations separate from interpreted
matrix rows:

- `ComparisonObservation`: source URL, extracted fields, citations, timestamp,
  retrieval mode, caveats.
- `ComparisonMatrixRow`: normalized entity/product/service, fields by source,
  confidence, warnings.
- `ComparisonRunResult`: manifest, matrix, records, blocked sources, artifact
  paths.

## Golden e2e flow

Run `comparative-intelligence` on fixture retailer pages for one TV model. The
run completes with:

- at least four cited price observations,
- one normalized matrix row for the matching TV,
- no merge of the wrong-model fixture,
- `comparison_matrix.csv`,
- `validation.json` containing any blocked, sparse, or ambiguous sources.

## Required behavior

- Every price must carry currency, source URL, citation, and crawl timestamp.
- Rows with insufficient identity evidence must be marked ambiguous instead of
  merged.
- Hotel rates must not be compared unless date and occupancy context are
  confirmed.
- Output must use "observed at crawl time" language, not guaranteed-lowest-price
  language.
