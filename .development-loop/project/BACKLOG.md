# BACKLOG

## Comparative Intelligence

**RICE Score:** Reach 7 x Impact 9 x Confidence 6 / Effort 6 = 63
**Status:** Proposed
**Dependencies:** Source policy, product extraction contract, hosted run
artifacts, export adapters, comparison UI decision.

**Problem:** Non-technical users understand competitive-pricing and market
research outcomes faster than crawler terminology.

**Acceptance criteria:**

- Product comparison V1 accepts a query and user-supplied source URLs.
- Scout returns a cited comparison matrix with price, currency, source URL,
  timestamp, confidence, and caveats.
- Wrong product/model rows are marked ambiguous or excluded from the matched row.
- Fixture, contract, API, export, and UI tests exist before production.

**First slice:** Product price comparison with user-supplied sources.

**Deferred:** Hotel-rate benchmarking, source discovery, recurring monitors.
