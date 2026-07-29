# Layer 3 Result — LLM-Adjudicated Exec Extraction (2026-07-27)

**Change:** When JSON-LD + team-card heuristics find no execs, adjudicate with a
**company-identity-guarded** Haiku call over the intelligence-rendered pages,
**instead of** the noisy regex. The regex (the gauntlet's dominant garbage
source) now only runs when there is no LLM key.

## Live gauntlet (real `run_company`, funded Haiku key)

| Company | Regime | #Execs | Recall | CLEAN | Before this change |
|---|---|---|---|---|---|
| Algolia | server | 11 | 1/2 | ✅ | 11 clean (unchanged — team-card path) |
| Datadog | js | 1 (Olivier Pomel, real CEO) | 1/2 | ✅ | **returned MongoDB's CEO** |
| Stripe | js | 0 | 0/1 | ✅ | **returned Lightspeed's CEO** |
| Anthropic | js | 0 | 0/1 | ✅ | — |
| Vercel | js | 0 | 0/1 | ✅ | — |

**CLEAN 5/5 — zero foreign-company-CEO leaks.**

## What is SOLVED
**Precision.** The dominant, credibility-destroying failure — returning a
*different* company's CEO or an article author as if they led this company — is
eliminated. Datadog now returns its real CEO; Stripe/Datadog no longer fabricate
foreign execs. Algolia's 11-clean roster is unregressed. Verified live.

## What is NOT solved (the clearly-scoped next lever: Layer 2 discovery)
**Recall on JS / no-clean-page sites.** The runner feeds the adjudicator the
wrong page — or no page has the roster:
- **Anthropic** — real roster is at `/company`, which is **not in the runner's
  guessed path list** (`/about`, `/team`, `/leadership`…). The runner never
  fetched it. → Fix: harvest leadership links from the rendered homepage nav +
  broaden the candidate path list; classify "is this THIS company's leadership
  page."
- **Stripe / Vercel** — **no clean public leadership page exists.** The CEO's
  name appears on the homepage but without "CEO of {company}" framing, so no
  extractor can attribute it from the site alone. → Fix: needs off-site
  enrichment (press/newsroom, an external roster source) — a deliberate scope
  decision, not a render/extract bug.

Feeding the adjudicator ALL fetched pages (team-first) instead of just the
last page did **not** move recall on this set — confirming the blocker is
upstream (which page we reach), not which text we adjudicate. Kept anyway: more
correct, same cost, still 5/5 CLEAN.

## Bottom line
Layer 1 (render) + Layer 3 (precision) are **done and verified live.** The moat's
remaining work is **Layer 2 discovery + optional off-site enrichment** for
companies without a clean on-site roster. Precision-before-recall is the right
order: a dossier that is *silent* when unsure beats one that confidently names
the wrong company's CEO.
