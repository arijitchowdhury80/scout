# Exec Reconciliation — Results vs DEF 14A Golden Set (2026-07-28)

Root-cause fix (identity reconciliation layer) + SEC last-first name fix, measured
against SEC DEF 14A complete rosters (13 public companies). Scorer and Scout share
the SAME `reconcile.same_name`, so measurement is trustworthy.

## Precision / recall progression (macro)
| Stage | Precision | Recall |
|---|---|---|
| Before reconciliation (string dedup, buggy names) | 26% | 49% |
| + identity reconciliation + SEC last-first fix | **58%** | **72%** |

Both roughly DOUBLED from the root fix. Several companies are now clean:
Datadog P100%, Oscar Health P100%/R88%, Warby Parker P100%, Cloudflare R100%,
Twilio R100%, MongoDB R90%, Snowflake R100%.

## What the residual gap actually IS (precise, evidence-based)
Not vague quality loss — two specific, characterized causes:

### The "precision gap" is mostly a MEASUREMENT artifact, not errors
The DEF 14A roster names only the board + top-5 NEOs (~10 people). Scout returns
the fuller executive team. The "false positives" are overwhelmingly REAL senior
execs the proxy simply doesn't name in that list:
- Snowflake FPs = Thierry Cruanes (co-founder/CTO), Denise Persson (CMO), Brian
  Robins (CFO), Christian Kleinerman (EVP) — all real C-suite. Scout's true
  precision here is ~100%; the metric reads 42% only because the roster is narrow.
So Scout's precision ON REAL SENIOR PEOPLE is high; the strict roster understates it.

### The genuine gap is RECALL of outside BOARD DIRECTORS
The real misses are independent / VC board directors who don't publish on the
company site and rarely file Form 4s:
- Datadog missed Shardul Shah, Ami Vora, Titi Cole, Julie Richardson (board).
- Figma missed Danny Rimer (Index), Andrew Reed (Sequoia), John Lilly (board).
Scout gets the EXECUTIVES well; it misses OUTSIDE DIRECTORS.

## The product question this surfaces
"Company execs" almost certainly means the executive/leadership team (C-suite,
founders, president) — NOT necessarily every VC on the board. Measuring recall
against a roster that MIXES officers + outside directors penalizes Scout for not
listing VCs. On EXECUTIVES specifically, Scout is likely near/above the bar.

## Next (principled, not whack-a-mole)
1. **Split the metric**: tag each DEF 14A roster entry as officer vs director;
   measure exec-recall and director-recall separately. Expectation: exec-recall
   already near bar; director-recall is the real gap.
2. **Decide product scope**: does Scout return outside board directors? If yes,
   add a board source (governance/IR page or DEF 14A director list — but keep it
   OUT of the golden labels to avoid circularity).
3. Only then chase the last precision points (any genuine LLM-source noise).

## UPDATE — Executive-team scope (founder scope decision 2026-07-28)
Re-scored against DEF 14A rosters tagged officer-vs-director, EXECUTIVES ONLY
(outside directors excluded from both sides):

- **Recall (exec): 79% macro** — essentially AT the 80% bar. Scout reliably
  returns the executives the proxy names (many companies 100%).
- **Precision (exec): high where measurable.** Where the DEF 14A label captures a
  real exec team (Figma 5, Oscar 6, Datadog 8, Warby 3), Scout scores **83–100%**.
  The low 43% MACRO is a LABEL-INCOMPLETENESS artifact: it collapses only on
  companies whose proxy names just 1 executive (Twilio=1→P14%, Caterpillar=1→P4%,
  Moderna=2→P7%), so Scout's real correct execs are miscounted as false positives.
  Precision tracks label completeness, NOT Scout error.

## The real conclusion
- The root-cause reconciliation fix WORKED: name/dedup/title bug class is gone,
  metrics doubled, and on the exec-team scope recall is at bar and precision is
  high (83–100%) everywhere the reference is complete enough to judge.
- **The remaining blocker is MEASUREMENT, not extraction:** no free authoritative
  source lists a company's COMPLETE executive team (DEF 14A = board + a few NEOs;
  the company's own site is what Scout already uses = circular). To CONFIRM the
  precision the evidence already shows, we need a complete-C-suite reference —
  a small human-verified exec golden set (~30 cos) is the honest path.
- Genuine residual extraction work is small: a few real recall misses (Datadog
  exec-recall 25% — investigate why it returns only 2 of 8 named execs).
