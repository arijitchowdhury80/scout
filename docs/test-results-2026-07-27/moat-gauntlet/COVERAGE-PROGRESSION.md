# Exec Coverage Progression — 35-company scaled eval (2026-07-27)

Auto-measured by `scaled_eval.py` over 35 diverse real companies (SaaS, retail,
finance, healthcare, industrial, non-US). Coverage = % returning ≥1 executive.
100% crash-free at every step.

| Step | Coverage | Latency p50 / p95 | Note |
|---|---|---|---|
| On-site only (initial) | 43% (15/35) | 71s / 204s | before any fixes |
| + tuple-order bug fix + latency cuts | ~46-49% (16-17/35) | 46s / 134s | GitLab 0→10; ±2-3 co variance at N=35 |
| + Wikidata enrichment (source #2) | 83% (29/35) | 69s / 174s | the waterfall payoff |
| **+ SEC EDGAR (#3) + Wikipedia (#4) + senior-guard** | **94% (33/35)** | 55s / 138s | **past the 90% launch bar** |

## Final waterfall (94%)
- Source #1 on-site → #2 Wikidata (structured) → #3 SEC EDGAR (authoritative
  officers/directors for US public cos; MongoDB now correct: Chirantan Desai
  President&CEO, Michael Berry CFO) → #4 Wikipedia (LLM over the article, gated
  to fire only when still uncovered; adds Everlane/Plaid).
- Exec extractor tightened to SENIOR leadership only (dropped the MongoDB "Head
  of Product Security" false positive Wikipedia first produced).

## Still zero after full waterfall (2): Vercel, Notion
Both blocked by strict domain-disambiguation: Vercel collides with a French
village on Wikidata; Notion's passed domain (notion.so) doesn't match its
Wikidata official-website field. SEC can't help (both private). These are the
deep long tail for **true paid web-search grounding** (Anthropic web_search or a
search API) — a later, cost-gated increment. 94% already clears the bar.

## What Wikidata recovered (companies with no on-site leadership page)
Stripe, Cloudflare, Figma, Shopify, Glossier, Klarna, Patagonia, Siemens, 3M,
Spotify, Wise, Robinhood, Canva — all publish nothing extractable on their own
site, all resolved via Wikidata with **domain-based disambiguation** (rejects the
"Vercel → French village" trap; returns nothing rather than a wrong company).

## Still zero after Wikidata (6) — the target of sources #3 and #4
- **MongoDB** — public company; Wikidata entity didn't resolve execs. → **SEC EDGAR**
  (source #3) has authoritative officers for every US public company.
- **Vercel** — Wikidata has no domain-matching company entity. → **search-grounded
  LLM** (source #4): "executives of Vercel" → Guillermo Rauch, with citation.
- **Notion, Warby Parker, Everlane, Plaid** — private; thin/absent Wikidata exec
  claims. → **search-grounded LLM** (source #4).

## Path to the 90%+ launch bar
Wikidata alone → 83%. Adding SEC EDGAR (public cos) + search-grounded LLM (private
long tail) should close most of the remaining 6 → **90%+ target is in reach.**
Honest ceiling reminder: a few obscure private firms have no public exec data
anywhere; those return an honest "not found" with provenance, never a fabrication.

## Latency note
Wikidata added ~3 sequential API calls/company (69s p50 vs 46s). Easy win pending:
run enrichment concurrently with the on-site fetch rather than after it.
