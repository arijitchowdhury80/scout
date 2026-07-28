# GATE 1 Result — Intelligence Render Probe (2026-07-27)

**Question:** Does the intelligence render (`scan_full_page` + `delay_before_return_html=2.5` + `block_images`) surface exec content the bare render (`use_js` only) misses — without regressing?

**Verdict: PASS, and it sharpened the diagnosis.**

| Company | Regime | BARE words | MOAT words | BARE exec hits | MOAT exec hits | Note |
|---|---|---|---|---|---|---|
| Algolia | server | 2542 | 2871 | 1/2 | 1/2 | control holds; 2nd label may be stale |
| Anthropic | js | 1037 | 1037 | 1/1 | 1/1 | present both |
| **Vercel** | js | 156 | 156 | **0/1 (html)** | **1/1 (html)** | **`Rauch` absent in bare HTML, present with MOAT — decisive render win** |
| Datadog | js | 4757 | 4757 | 2/2 | 2/2 | content already present in bare |
| Stripe | js | 1890 | **2570** | 1/1 | 1/1 | MOAT surfaces +36% content |

## What this proves
1. **The render fix works and never regresses.** Vercel is the clean proof: the CEO's name only appeared in the DOM after `scan_full_page`. Stripe gained 36% more content. Every other site held or improved.
2. **The render fix is necessary but NOT sufficient for the marquee failures.** Datadog (had returned MongoDB's CEO) and Stripe (had returned Lightspeed's CEO) BOTH already had the *correct* execs fetchable in the bare render (Pomel+Obstler 2/2, Collison 1/1). So those wrong-answer failures are **discovery + extraction-trust failures, not render failures.**

## Priority revision (honest, evidence-based)
- The "wrong company's CEO" bug is a **Layer 2 (discovery lands on wrong page) + Layer 3 (heuristic trusts garbage)** problem. Gate 1 proves the raw material Layer 3 needs is present in the fetched content.
- **Layer 3 (LLM adjudication with a company-identity guard) is now the top lever**, followed by Layer 2 discovery. Render (Layer 1, shipped) is the enabler that guarantees content is present, and it's essential for JS-heavy product grids.
- The earlier "networkidle times out on Datadog" theory is **not** what's happening on crawl4ai 0.7.7 (its default wait_until is already `domcontentloaded`; Datadog's page renders fine). Render's value is `scan_full_page` (lazy content) + hydration delay, not the wait condition.

## Artifacts
- `render_probe.py` — the probe (bare vs moat), reusable.
- `gauntlet.json` — labeled company set (re-verify exec labels on a cadence).
- `render_probe_result.json` — raw output.
