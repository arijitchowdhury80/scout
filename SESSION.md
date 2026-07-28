# SESSION.md — Scout Launch-Readiness Program (updated 2026-07-27)

## Status (one line)
Moat exec extraction **HITS 94% coverage across 35 diverse cos — PAST the 90% launch bar** (branch `fix/launch-readiness-fx1-fx7`, HEAD 47f0bc5). Precision solved (senior-only guard, no foreign leaks); 4-source waterfall (on-site→Wikidata→SEC→Wikipedia). 1005 tests, pyright 0, ruff clean. Remaining: PRECISION golden-set validation, last ~6% (Vercel/Notion) via paid web-search, latency (p50 55s), then products.

## What shipped this session (5 commits: 5927e0f, 9639ecf, eb747a1, 4a19489)
- Layer 1 render (scan_full_page/delay/block_images), Layer 3 LLM adjudication + company-identity guard (CLEAN 5/5), Layer 2 discovery (nav-anchor harvest + sitemap + anchor-text scoring), Pillar A LLM-driven page selection (killed keyword hardcoding), scaled auto-eval harness, tuple-order coverage bug fix (GitLab 0→10), latency −35%.

## RESUME ACTION (next session — do this)
1. Read this file + memory `scout-extraction-fix-plan-seed.md` + `docs/test-results-2026-07-27/moat-gauntlet/COVERAGE-PROGRESSION.md`.
2. **Validate PRECISION, not just coverage** (the critical next gate — 94% coverage ≠ 94% correct): build a ~200-co GOLDEN SET labeled via SEC/Wikidata cross-ref; run `scaled_eval.py` at larger N; measure precision/recall (no wrong execs, no junior/foreign names). Coverage variance is ±2-3 at N=35 — need bigger N.
3. **Last ~6% (Vercel/Notion class):** true web-search grounding — Anthropic web_search tool via existing LLM_API_KEY (billable ~$10/1k searches) OR a search API key. Cost-gated — get founder nod.
4. **Latency** (p50 55s): run the 4 enrichment sources CONCURRENTLY with the on-site fetch (asyncio.gather) instead of sequentially. Clean the asyncio sitemap-cancel "GeneratorExit" noise.
5. Then **products** flip (products.py still empty-only) + **Layer 4 anti-bot = ScraperAPI** (founder funds+key).
6. Branch guard-blocked from push — founder pushes. Enrich modules: `scout/core/enrich/{wikidata,wikipedia,sec}.py`; gated by `ScoutCrawler.enrichment_enabled`.

## Where we stopped (EXACT)
- Branch `fix/launch-readiness-fx1-fx7`, HEAD `df9632e`, ~11 fix commits, 952 unit tests pass, pyright 0, ruff clean. **Deployed to prod** (scout.chowmes.com) through `68a940a` (LLM layer df9632e committed but NOT yet deployed).
- 18-company exec gauntlet: **9/18 returned execs but MOST ARE WRONG** (Stripe→Lightspeed CEO, Datadog→MongoDB CEO, mis-parsed names/titles). Clean ≈ algolia only (~2-3/18). Products: 0 on lacoste/eyebuydirect (Akamai blocks the datacenter IP).
- LLM validation: Anthropic account was $0 (now funded). LLM returned 0 on Stripe/Datadog because exec content wasn't in the fetched markdown (JS-render / wrong page / networkidle timeout). **Bottleneck is fetching+rendering the right page, NOT the extractor.**

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
- **Moat: reliable exec + product extraction across sites — NOT DONE (the whole next-session job).**
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

## Files written this session
Many across scout/, tests/, docs/launch/, docs/legal/launch/, docs/test-results-2026-07-2[67]/, website/, docker/, pyproject.toml, .env.example. 11 commits eee3c9e→df9632e on the branch.
