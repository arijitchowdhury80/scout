# XL Exec-Extraction — PILOT results (44 companies, hosted, post-deploy)

**Date:** 2026-07-28 · Ran the full harness against 44 stratified companies on the
freshly-deployed hosted API (fix live). Purpose: validate the pipeline end-to-end +
first read on quality before the 500-run.

## Headline
- **Harness works end-to-end**: 44 run, 1 error, Algolia push **40/40 pushed, 40/40 searchable**.
- **Recall 81%** (macro, vs SEC golden) — clears the 80% bar.
- **Cross-company leaks: 0** — the root-fixed bug class stays dead at scale.
- **Precision 41% (macro) — BUT this is a MEASUREMENT ARTIFACT, not the true precision** (see below).
- **VERDICT: precision not yet cleanly measurable; real breaking points found.**

## Why precision 41% is misleading
The SEC DEF 14A golden's `role_type=executive` roster is **NEO-narrow** (1–3 named
officers). Scout returns the **full leadership team**, so real current officers count
as "false positives" against the tiny roster. Examples flagged FP that are REAL execs:
- Snowflake (roster=3, scout=24): Brian Robins (CFO), Denise Persson (CMO), Christian Kleinerman (SVP Prod) — all real.
- MongoDB, Twilio, 3M, Asana: same pattern — recall 100%, "precision" 9–18% purely from roster narrowness.

→ **Confirms the plan's core thesis:** real precision needs a COMPLETE human-verified
golden (full C-suite), not narrow SEC NEO lists. The 500-run will reproduce this
artifact unless scored against a complete golden.

## Genuine issues surfaced (real, not artifacts)
1. **Staleness / former execs** (true precision hits): Jeff Lawson (former Twilio CEO,
   stepped down 2024), Moncef Slaoui + Henri Termeer (former/deceased Moderna). Scout
   returns former officers as current. A real sub-bug worth fixing.
2. **Coverage gaps** (0–1 sources): OpenAI (0), SAP (0), Siemens (0), Notion (1), Vercel (1).
   Private startups + EU industrials where the waterfall finds nothing.

## Breaking-point heatmap (coverage)
| Stratum | Coverage | Note |
|---|---|---|
| public | 92% (10.9 execs) | strong |
| private | 82% (4.0 execs) | weaker, thinner |
| geo=eu | **60%** | SAP/Siemens = 0 sources |
| size=startup | **66%** (1.0 execs) | Vercel = near zero |
| render=antibot | 100% | (Nike/Adobe/Lululemon/Patagonia OK) |
| vertical=industrial | 50% | Caterpillar timeout + EU |

## Robustness
- Coverage 88% overall · mean 8.2 execs · mean 2.8 sources · 1 error (Caterpillar poll timeout, slow server-render).
- Latency: most 60–120s; Palantir 385s (outlier).
- Algolia (Track C): 100% push + searchable — full pipeline (extract→index→search) verified.

## Implication for the 500-run
- **Robustness/coverage/leak breadth**: 500-run is valuable — finds coverage breaking points at scale. Ready to go.
- **Precision**: blocked on a COMPLETE human golden. Scoring 500 vs narrow SEC rosters = same 41% artifact.
  The real remaining bottleneck is MEASUREMENT (as the original moat docs concluded).
