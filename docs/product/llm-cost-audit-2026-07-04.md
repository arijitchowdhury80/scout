# LLM Cost Audit — Scout Hosted Beta (250 testers)
**Date:** 2026-07-04 · **Auditor:** Claude (Opus 4.8) · **Verdict:** ✅ GREEN — $0 LLM exposure on tester-reachable paths

## ✅ PRODUCTION-VERIFIED (2026-07-04, via SSH into the live VPS Docker container `scout`)
Inspected the actual running production container, not just code. All three guarantees hold live:
- `SCOUT_PUBLIC_HOSTED_ONLY=true` — raw LLM routes are 403-blocked.
- `HOSTED_LLM_MODE=disabled` — the gate returns an empty key.
- `LLM_API_KEY` **EMPTY** — no key exists, so `LLMExtractionStrategy` can never be constructed.

**$0 LLM cost at launch is confirmed in production.** (The committed `secrets/scout-production.env`
snapshot is stale/incomplete, but the live container env is correct — discrepancy resolved.)

## Question
Can 250 beta testers run up a large LLM bill on the hosted Scout box?

## Answer: No. There is no reachable LLM call, because there is no LLM key.

## Evidence

### 1. LLM call sites (exactly three)
All use Crawl4AI `LLMExtractionStrategy(LLMConfig(provider=..., api_token=llm_api_key))`:
- `scout/core/modes/extract.py:42` — `/extract` route
- `scout/core/capture_extract.py:91` — `structure_capture()` (used by `/structure`, `/app_browser`)
- `scout/core/cdp_acquire.py:84` — `acquire_open_page()` (used by `/harvest`, `/app_browser`)

### 2. Default model is LOCAL and free
`ExtractRequest.llm_provider` default = `"ollama/llama3.2:3b"` (`scout/core/types.py:120`).
Ollama runs locally — no external API, no per-token cost, no vendor key.

### 3. Every call site is key-gated; the key is empty
- `extract.py:41` guards `if llm_api_key:` — else returns error or falls to CSS extraction.
- `capture_extract.py:89` / `cdp_acquire.py:82` guard `if llm_schema and llm_api_key:`.
- `LLM_API_KEY` is EMPTY in `secrets/scout-production.env`, not committed anywhere, and only
  appears as test fakes ("fake-key", "test-key"). With an empty key, `LLMExtractionStrategy`
  is never constructed. **No LLM request can be issued.**

### 4. Tester paths are double-gated in hosted mode
When `SCOUT_PUBLIC_HOSTED_ONLY=true`, `AuthMiddleware` (auth.py:84) returns 403 for every raw
route. Testers reach only `/v1/hosted/*`, `/v1/playground/*`, `/v1/billing/*`. The shared
crawler singleton is built with `llm_api_key=resolve_hosted_llm_api_key(settings)`
(`main.py:67`), which returns `""` whenever `hosted_llm_mode` is `disabled` (the default).
Even the playground `extract` workflow therefore makes no LLM call.

## Residual risk (must hold at launch)
The $0 guarantee depends on the VPS environment. Keep ALL of:
- `LLM_API_KEY` empty (primary guarantee — no key, no spend)
- `HOSTED_LLM_MODE=disabled`
- `SCOUT_PUBLIC_HOSTED_ONLY=true`
If anyone later sets a real `LLM_API_KEY` AND allowlists a paid provider (openai/anthropic/…)
via `HOSTED_LLM_MODE=allowlist`, cost exposure returns. `hosted_llm_policy.py` already
hard-blocks the paid provider prefixes even in allowlist mode — good defense in depth.

## ⚠️ Config discrepancy surfaced (separate from LLM cost)
Committed `secrets/scout-production.env` is MISSING: `SCOUT_PUBLIC_HOSTED_ONLY`, `SCOUT_API_KEY`,
`HOSTED_LLM_MODE`, and all `STRIPE_*_PRICE_ID` vars → they fall to insecure code defaults
(`scout_api_key="dev-key"`, `scout_public_hosted_only=False`). If the live VPS uses this exact
file, raw routes are open behind the default "dev-key". MUST verify the real VPS `.env.local`
via SSH before launch (blocks items 6/7/8). LLM cost is unaffected (key is empty either way).
