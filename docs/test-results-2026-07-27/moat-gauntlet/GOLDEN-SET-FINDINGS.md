# Golden-Set Precision/Recall Findings (2026-07-28)

Bootstrap golden set (Wikipedia infobox `key_people`, no human audit — founder's
choice), scored against Scout's real company runner. Harness: `golden_build.py`
(labels) + `golden_score.py` (scoring). 23 of 35 companies had usable labels.

## Headline: coverage ≠ correctness
The 94% "coverage" number (returned ≥1 exec) badly overstated quality. Measured
against the golden labels:
- **key-person RECALL: micro 60% (26/43), macro 64%** — BELOW the 80% bar.
- **206 unconfirmed extra names** across 23 companies.

But the raw numbers need interpretation — the golden set surfaced BOTH a real bug
AND its own label limits:

### Real bug found + FIXED: former/deceased execs leaking (the important one)
Siemens returned **Werner von Siemens (died 1892)**, Georg von Siemens, and
former CEOs (Löscher, Kleinfeld) as *current* leadership — Wikidata structured
claims include historical/former officeholders and long-dead founders, and
nothing filtered them.
**Fix (committed):** drop position claims with a P582 end-time qualifier (former
role) and any person with a P570 date-of-death (deceased). Live after fix →
`Siemens: Roland Busch (CEO)` only. This is the trust-killing class; now closed.

### The recall number is deflated by sparse/quirky labels
- **Shopify scored 0%** — but the label was wrong: Wikipedia listed only the
  *president* (Finkelstein); Scout correctly returned the *CEO/founder* (Lütke).
- **Klarna/Caterpillar/Datadog** — Scout returned FULLER, correct teams (SEC
  officers) than the 1-2-name labels; the "misses" were single board chairs.
So true key-person recall is materially higher than 60%; the Wikipedia-infobox
label set is too sparse/idiosyncratic to be the final word.

### Precision is still NOT cleanly measured (the honest remaining gap)
The 206 "unconfirmed extras" are mostly LEGIT (full SEC officer/director lists
Wikipedia omits — Caterpillar's real 12 officers), so they are NOT 206 errors.
But without a COMPLETE roster or a TRAP-name set per company, precision can't be
scored honestly. A minor dedup gap also exists (Datadog returned "Olivier Pomel"
twice across sources).

## What this means
- **Not launchable on quality yet.** Coverage is high, but verified key-person
  recall and precision are not yet at the bar.
- **The measurement infrastructure now exists** (build + score), and it already
  paid for itself by catching the deceased/former-exec bug that coverage-only
  testing completely missed.

## Next (to actually clear precision ≥90% / recall ≥80%)
1. **Better ground truth**: SEC DEF 14A officer/director tables for public cos
   (complete + authoritative) + trap-name sets → enables REAL precision scoring.
2. **Recall**: diagnose per-source misses (why a listed CEO isn't returned);
   improve cross-source merge; fuzzy cross-source dedup (fixes Pomel×2).
3. **Larger N** — 23 labeled is too few for stable per-segment numbers.
