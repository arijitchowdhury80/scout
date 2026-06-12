# Acquisition Contract: prospect bundle (was "prism")

**Consumer:** PRISM / `algolia-audit-research` orchestration.

A composition, not a capability: runs company → careers → news → investor (+ filings for public companies, + social verification) across a target list, into one merged run output. Contains zero logic of its own beyond sequencing and merging.

## Input contract
`targets[]`: 1..N company domains (the prospect, plus competitor domains chosen BY THE CONSUMER — competitor selection is interpretation and never happens here). Options: `include[]` (default: company, careers, news, investor, social; opt-in: filings, website-quality, docs), shared lookback/caps.

## Acquisition plan
Per target, sequentially (rate-limit friendly): company → social (uses company.v1 socials) → careers → news → investor → filings (if included and public-company signals present, e.g. IR page found). Each sub-run follows its own contract verbatim.

## Output
- Per-target subdirectories with each sub-run's standard artifact set.
- Bundle-level `manifest.json`: targets, sub-runs, statuses, totals, failures (a failed sub-run does not abort the bundle — it is recorded).
- Merged `records.json`/`records.jsonl` across all sub-runs (records carry target + use_case fields).

## Golden e2e flow
Run `bundle` with targets [algolia.com] include [company, careers, news] → complete; merged records contain ≥1 company.v1 + ≥5 job_posting.v1 + ≥3 news_signal.v1, all citing real fetched sources; bundle manifest lists 3 sub-runs with statuses. Two-target run produces per-target separation in artifacts.
