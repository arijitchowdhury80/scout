# XL Exec-Extraction E2E — Results Summary (pilot, hosted, post-deploy)

**Date:** 2026-07-28 · 44-company stratified pilot on the live hosted API (moat fix
freshly deployed) + 18-company COMPLETE-leadership golden re-score.

## TL;DR
- The moat fix is **live and working**: cross-company leaks **0**, real CEOs returned.
- Measured against a **complete** current-leadership golden (18 co): **precision 67%,
  recall 55%** macro — true precision is meaningfully higher (see artifacts below).
- **Not launch-ready as-is.** Three concrete, fixable breaking points identified.

## Scores (18 companies, complete golden)
Perfect/strong: **Snowflake 100/100, MongoDB 100/100**, Oscar 89/89, Twilio 86/86,
Asana 89/100, GitLab 83/100. Weak: private companies (Notion/Brex/Plaid/Ramp ≈0 recall).

Macro **precision 67.1%, recall 54.7%** (bar P≥90 / R≥80). Leaks **0**.

## The three real breaking points (ranked)

### 1. Private companies — near-total recall failure (BIGGEST)
Notion 0 execs, Brex 1, Plaid 2, Ramp 1 returned. Scout can't reach private-company
leadership: no SEC filing, sparse/JS leadership pages, weak Wikidata. Also 0-source
companies in the wider pilot: OpenAI, SAP, Siemens. **This is the launch blocker for
the "works on private companies" claim.**

### 2. Recall is source-gated (public, uneven)
When SEC DEF 14A fires → full roster (MongoDB, Snowflake = 100% recall). When only
Wikidata fires → 2 names (Stripe 22%, Datadog 20% recall — got Collisons/Pomel but
missed the CFO/CRO/etc.). Recall swings on which waterfall source hits, not on the
company having public execs.

### 3. Staleness — former/deceased execs returned as current (real precision bug)
Jeff Lawson (ex-Twilio CEO), Moncef Slaoui + Tal Zaks + Henri Termeer (ex/deceased
Moderna), Mike Roman (ex-3M CEO). On-site/Wikidata pull stale names. Fixable.

## Measurement caveats (why true precision > 67%)
Some "false positives" are NOT Scout errors:
- **Matcher nickname gap**: Oscar "Vickie Baltrus" vs golden "Victoria Baltrus" = same
  person; `reconcile.same_name` missed it. Add Vickie↔Victoria class nicknames.
- **Golden under-count**: Databricks' 9 "FPs" (Tavakoli, Serna, Marur, Conway…) are real
  execs my golden missed. Anthropic's Chris Olah is a real co-founder.
- **Director/exec boundary**: board members (Amy Hood on 3M board; Anthropic Trust
  trustees) scored as FP though they're real, just not operating execs.

## Robustness (Track A) + pipeline (Track C)
- Coverage 88%, mean 8.2 execs, mean 2.8 sources, 1 error (Caterpillar poll timeout).
- Strata: eu 60% cov, startup 66%, private 82% vs public 92%.
- **Algolia push 40/40, searchable 40/40** — extract→index→search fully verified.

## Recommended next actions (priority order)
1. **Fix private-company recall** (biggest): better leadership-page discovery for
   JS/sparse sites; add a source that covers private execs (e.g. LinkedIn/press via LLM).
2. **Fix staleness**: filter former/deceased (tenure/"former"/"stepped down" cues; prefer
   current-officer sources; de-rank Wikidata historical entries).
3. **Close the recall-source gap**: when SEC roster is available, always merge it (some
   public cos fell back to Wikidata-only).
4. **Matcher**: add Vickie↔Victoria-class nicknames to `reconcile._NICKNAME_GROUPS`.
5. Then extend the complete golden to ~30 and run the 500 robustness sweep.

## Artifacts
- `hosted_xl_eval.py` (harness), `score_results.py` (scorer), `analyze_strata.py` (heatmap)
- `pilot_corpus.tsv` / `.results.jsonl`, `golden_complete.json` (18 co), `PILOT-RESULTS.md`
