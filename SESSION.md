# SESSION.md — Scout Launch-Readiness Program (updated 2026-07-27)

## Status (one line)
Moat exec extraction: ROOT-CAUSE FIX shipped — **identity reconciliation layer** (`scout/core/enrich/reconcile.py`) replaced the whack-a-mole per-source string-merge. Measured vs SEC DEF 14A golden set: **reconciliation DOUBLED precision 26→58% & recall 49→72%** (13 public cos). Still below 90/80 bar, BUT residual is precisely diagnosed: precision "gap" mostly a measurement artifact (real senior execs beyond narrow roster); genuine gap = outside-board-director recall (maybe out of scope). Branch `fix/launch-readiness-fx1-fx7`, HEAD 2a00b1f. 1029 tests, pyright 0, ruff clean.

## What shipped this session (~9 commits, HEAD ef04ee2)
- Layer 1 intelligence render + Layer 3 LLM adjudication + Layer 2 discovery + Pillar A LLM page-selection (killed keyword hardcoding) → coverage 43→94%.
- 4-source waterfall: Wikidata + SEC EDGAR (Form 3/4) + Wikipedia (`scout/core/enrich/{wikidata,wikipedia,sec}.py`); deceased/former-exec filter.
- **ROOT FIX: identity reconciliation** `scout/core/enrich/reconcile.py` (canonical/same_person/reconcile) — all sources yield ExecCandidate → reconcile once. Killed name/dedup/title bug class.
- Trustworthy measurement: SEC DEF 14A golden set (`golden_sec_build/score.py`). Reconciliation DOUBLED P/R (26→58, 49→72); exec-scope recall 79%≈bar, precision 83-100% where label complete.
- Founder scope decision: **executive team only** (not outside VC directors).

## RESUME ACTION (next session — do this)
1. Read this file + memory `scout-extraction-fix-plan-seed.md` + `docs/test-results-2026-07-27/moat-gauntlet/RECONCILIATION-RESULTS.md` (precise residual diagnosis) + plan `docs/workspace/scout-core/exec-reconciliation-plan-2026-07-28.md`.
2. DONE this session: metric split (officer/director) + founder scope decision (executive team ONLY, not outside VC directors). Exec-scope score: recall 79%≈bar, precision 83-100% where label complete; low 43% macro = label incompleteness NOT Scout error.
3. **BUILD ~30-co HUMAN-VERIFIED exec golden set** to CONFIRM precision — this is the real blocker. Automated refs hit their ceiling: no free source lists a complete C-suite (DEF14A names too few officers; company site = circular). This is the ONE place human labels are genuinely needed.
4. Fix Datadog-class recall misses (returns 2 of 8 named execs — investigate why so few).
5. **Then**: last ~6% coverage (Vercel/Notion, paid web-search, cost-gated); latency (concurrent enrichment via asyncio.gather, p50 55s); products flip (products.py empty-only); Layer 4 ScraperAPI.
6. Harness (all `docs/test-results-2026-07-27/moat-gauntlet/`): `golden_sec_build.py`+`golden_sec_score.py` (real P/R public cos), `scaled_eval.py` (coverage/latency), `golden_build/score.py` (Wikipedia recall).
7. Branch guard-blocked from push — founder pushes. Identity: `scout/core/enrich/reconcile.py`. Sources `enrich/{wikidata,wikipedia,sec}.py` yield ExecCandidate; gated by `ScoutCrawler.enrichment_enabled`.

## Where we stopped (EXACT)
- Branch `fix/launch-readiness-fx1-fx7`, HEAD `ef04ee2`, ~9 exec-extraction commits today (eee…ef04ee2 on top of df9632e), **1029 unit tests pass, pyright 0, ruff clean.** NOT pushed (guard-blocked, founder pushes). Today's exec work NOT yet deployed to prod.
- Exec extraction is ROOT-FIXED (was: Stripe→Lightspeed CEO garbage this morning). Identity reconciliation layer + 4-source waterfall. **Measured on SEC DEF 14A golden set: exec-scope recall 79%≈bar, precision 83-100% where the label is complete** (Figma/Oscar/Datadog/Warby); low 43% macro = DEF14A names too few officers, not Scout error.
- Just finished: the exec-only golden score (`golden_sec_score.py` with officer/director split). Result files in `docs/test-results-2026-07-27/moat-gauntlet/` (RECONCILIATION-RESULTS.md has the analysis).
- **NOT launchable yet:** precision unconfirmed (no free complete-C-suite reference). Products side untouched.

## THE MOAT PROBLEM — root diagnosis (gold for the plan; do not re-derive)
- **EXECS:** works only when the leadership page is server-rendered with tidy team-card markup (algolia: 11 clean live). Fails when (a) exec content is JS-rendered and not captured; (b) discovery lands on the WRONG page (blog/article listing random people → garbage); (c) `networkidle` times out on ad/analytics-heavy sites (datadog). Heuristic name/title parsing mis-splits.
- **PRODUCTS:** extraction+discovery logic correct (Common Crawl discovery finds URLs when sitemap/BFS blocked). BUT big brands (lacoste/nike) are behind **Akamai anti-bot** → every VPS-datacenter-IP fetch is 301/blocked. No code fix solves this; needs **residential proxy / unblocker** (Zyte/ScraperAPI/Bright Data, ~$0.005-0.02/hard fetch, ~$100/mo beta). Product data often JS-rendered (not JSON-LD, not in CC snapshot).
- **LLM layer (committed df9632e):** `scout/core/llm_extract.py` — Haiku (`anthropic/claude-haiku-4-5` via litellm, no new dep), heuristic-first, fires only on ZERO heuristic results, gated by `hosted_llm_policy` + `LLM_EXTRACTION_FALLBACK_ENABLED`. LIMITATION: empty-only trigger won't fix GARBAGE (non-zero-but-wrong); and can't extract un-fetched content.

## FIX APPROACH (likely plan spine — validate + detail next session)
1. **Robust full-JS render** for intelligence pages: replace `networkidle` with `scan_full_page` + bounded `delay_before_return_html` + content-signal wait; block images. Prove exec/product content lands in markdown.
2. **Smart page discovery**: find the REAL leadership/team + product listing pages; reject blog/article pages listing random people (LLM/classifier judges "is this a leadership page").
3. **LLM-PRIMARY extraction** (not empty-fallback) for execs+products over well-rendered content — gauntlet proved heuristics too noisy. Meter via credits (~200/dossier covers ~$0.01-0.05 Haiku).
4. **Residential-proxy/unblocker fallback** for anti-bot product sites (founder picks provider + funds).
5. **Validate with multi-company gauntlets** (exec-gauntlet.sh pattern + a product gauntlet) — measure CLEAN hit rate, not just non-empty.

## Decisions LOCKED this session
- Pricing: **$12/mo → 20,000 credits** (fungible: 1 credit = 1 op; example 5k pages + 5k products + 50 dossiers), **$10 one-time → 15,000 credits**. Removed $25/$100 packs. "unlimited"→"monthly" everywhere. Beta = 5,000.
- Capacity target **150 → 50 testers**. Box handles it (HOSTED_MAX_ACTIVE_REQUESTS=6). No new hardware for beta.
- Scout = HTTP API + Claude/Codex skill only. `/app` deleted. Skill via email→support→download link.
- Container non-root `scoutadmin:scoutgroup` (uid 10001), HOME=/app, CRAWL4AI_BASE_DIRECTORY=/app/.crawl4ai.
- Legal: draft + MANDATED lawyer review.
- **Do NOT launch on the "any company execs+products" promise until the moat works.**

## DONE & VERIFIED LIVE this session
- Signup/email/duplicate/status/reissue (root-caused; never broken — example.com rejected by Resend by design; domain verified; gmail delivers).
- **Real $12 Stripe payment PROVEN**: charge succeeded, $11.35 in balance, webhook invoice.paid → tenant auto-upgraded hosted_monthly + 20,000 credits. Live prices+webhook created via API. sk_live in prod .env.
- Non-root deploy, lxml 6.1.1 (CVE clear), 2-tier pricing live, /app gone (403), cap=100, plain copy, robots-respect default, error-hygiene.
- Exec extraction on structured sites (algolia 11 live). Algolia push works. Scrape/crawl/map/screenshot work single-request.
- DB: no card data, keys hashed, localhost-bound, non-root. Backup at /opt/prism/scout/backups/hosted_accounts.20260727-195352.sqlite.

## What has NOT been done (prevents false-completion)
- **EXEC precision NOT CONFIRMED** — measured 83-100% where the DEF14A label is complete, but no free source lists a full C-suite so the aggregate is unproven. Needs a ~30-co human-verified golden set. NOT launchable until confirmed.
- **PRODUCT extraction untouched** this session — `products.py` still LLM-empty-only; no reconciliation; Layer 4 anti-bot (ScraperAPI) not wired.
- Today's exec work NOT pushed (guard-blocked) + NOT deployed to prod.
- Datadog-class recall misses (2 of 8 named) not fixed. Latency (p50 55s) not optimized (enrichment still sequential).
- Junk-tenant purge NOT run (4,279 tenants; founder has the self-contained tightened command → keeps ~13 real + e2e key; backup exists).
- LLM layer committed but NOT deployed + NOT validated live (Anthropic now funded).
- Residential-proxy/unblocker for anti-bot products — NOT chosen/wired.
- PR #2 not merged. Lawyer not engaged. Mintlify docs/llms.txt not finished. Track B comms drafted-not-posted.
- Signup abuse protection (captcha/email-verify) NOT built.

## Reference files
- Branch `fix/launch-readiness-fx1-fx7`, PR https://github.com/arijitchowdhury80/scout/pull/2
- `docs/test-results-2026-07-26/` (FAILURE-REPORT, FIX-PLAN, DEPLOY-AND-REVERIFY) + `docs/test-results-2026-07-27/`
- `docs/launch/` (ph-gap-analysis, ph-run-plan, comms-pack, launch-calendar) — 50-tester scoped
- `docs/legal/launch/` (9 drafts + lawyer-sourcing-and-cost)
- Extraction code: `scout/core/use_cases/runners/company.py`, `scout/core/modes/products.py`, `scout/core/products/discovery.py`, `scout/core/modes/map.py`, `scout/core/llm_extract.py`
- Plan: `~/.claude/plans/this-is-scout-i-shimmering-backus.md`
- SSH `ssh chowmes-vps` (chowmesadmin, passwordless sudo docker). Deploy: `/opt/prism/scout` git checkout + `sudo docker compose build && up -d`.
- Test creds: session scratchpad `test-creds.env` (SCOUT_API_KEY; Algolia AppID V8R7CVBC8Y).

## Files written this session (2026-07-28 — exec extraction)
- NEW: `scout/core/enrich/reconcile.py` (identity layer), `scout/core/enrich/{wikidata,wikipedia,sec}.py` (waterfall sources), tests `tests/unit/core/enrich/test_{reconcile,wikidata,wikipedia,sec}.py`.
- CHANGED: `scout/core/use_cases/runners/company.py` (gather→reconcile), `scout/core/modes/scrape.py` (render knobs), `scout/core/llm_extract.py` (page-select + guard), `scout/core/crawler.py` (enrichment_enabled), `scout/core/types.py`.
- HARNESS/DOCS: `docs/test-results-2026-07-27/moat-gauntlet/*` (scaled_eval.py, golden_sec_build/score.py, golden_build/score.py, RECONCILIATION-RESULTS.md, COVERAGE-PROGRESSION.md, GATE1/LAYER3/GOLDEN-SET-FINDINGS.md), `docs/workspace/scout-core/{moat-extraction-plan,exec-reconciliation-plan}-2026-07-2[78].md`.
- ~9 commits eee…ef04ee2 on branch fix/launch-readiness-fx1-fx7. 1029 tests, pyright 0, ruff clean.

## Prior (2026-07-27) files — history
Many across scout/, tests/, docs/launch/, docs/legal/launch/, website/, docker/. 11 commits eee3c9e→df9632e.
