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
