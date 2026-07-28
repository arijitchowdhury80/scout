# The Moat Plan — Reliable Exec + Product Extraction on Any Site
**Date:** 2026-07-27 · **Owner:** Scout · **Status:** APPROVED + IN PROGRESS · **Gate:** do NOT launch beta until this hits its CLEAN hit-rate bar.

## PROGRESS (2026-07-27, this session)
- **Layer 1 render — DONE + verified live (Gate 1 PASS).** New `ScrapeRequest` knobs (`scan_full_page`, `wait_until`, `delay_before_return_html`, `block_images`) wired into the exec/product runners via `intelligence_render`. Vercel's CEO name only appeared with the moat render; no site regressed. See `docs/test-results-2026-07-27/moat-gauntlet/GATE1-RESULT.md`.
- **Layer 3 precision — DONE + verified live.** LLM adjudication (company-identity guarded) replaces the noisy regex. **Live gauntlet: CLEAN 5/5, zero foreign-CEO leaks** (Datadog now returns its real CEO; Stripe no longer returns Lightspeed's). 963 unit tests pass, pyright 0, ruff clean. See `LAYER3-RESULT.md`.
- **Layer 2 discovery — NEXT (the recall gap).** Precision solved; recall on JS / no-clean-page sites is now the bottleneck (runner feeds the adjudicator the wrong page, e.g. Anthropic's roster is at `/company`, not in the guessed path list). This is the clearly-scoped next phase.
- **Layer 4 anti-bot — provider DECIDED: ScraperAPI** (founder funds + key when Layer 4 starts).

## Why this is the only thing that matters
Scrape / crawl / map / screenshot are commodities — anyone can wrap Crawl4AI. Scout's *only* real differentiation is: **"give me any company's real executives and real products, correct, from just a domain."** Today that is not reliable. Until it is, Scout has no reason to exist. This plan makes it reliable and gives us an honest number for how reliable.

---

## Root cause — confirmed at the code level (do not re-derive)
The bottleneck is **not** the extractor (heuristic or LLM). It is **fetching + fully rendering the RIGHT page**, then **trusting the wrong thing** to read it. Three concrete, confirmed defects:

### D1 — The render is bare (the biggest lever)
`scout/core/modes/scrape.py:198` `_build_run_config()` sets only `cache_mode`, `screenshot`, `page_timeout`, `wait_for`, and the stealth trio. It does **not** set:
- `scan_full_page` — so lazy-loaded / infinite-scroll exec cards and product grids never load.
- `wait_until` / `delay_before_return_html` — so we grab the DOM before client-side hydration paints the team roster or product tiles.
- image blocking (`exclude_all_images`) — so ad/analytics-heavy sites (Datadog) blow the timeout on images we don't need.

Result: on any JS-rendered leadership or PLP page, the exec/product content **is not in the markdown we hand the extractor.** Neither heuristics nor an LLM can extract what isn't there. **crawl4ai 0.7.7 already supports every one of these knobs**, and `scan_full_page` is already used in-repo at `scout/core/cdp_acquire.py:101` — this is reuse, not new work.

### D2 — Discovery lands on the wrong page, and the "signal" check rubber-stamps it
`scout/core/use_cases/runners/company.py:25-34` tries a **fixed list** of `/about`, `/team`, `/leadership` paths. If the real roster lives at a path not in the list (`/our-people`, `/company/who-we-are`, a JS route), we never reach it. Worse: `_has_executive_signal()` (`company.py:333`) validates a candidate page using **the same noisy regex** that produces garbage — so a blog/press page that happens to contain "Firstname Lastname, CEO" passes as a "leadership page." This is exactly how Stripe returned Lightspeed's CEO and Datadog returned MongoDB's CEO.

### D3 — We trust the noisy heuristic and use the LLM only as an empty-fallback
`company.py:438` runs the regex `_extract_executives()` over **concatenated markdown from homepage + about + team**, so any name+title anywhere on any of those pages is harvested (authors, quoted customers, board-members-in-passing, other companies). The LLM only fires `if not executives` (`company.py:440`) — so it **never corrects garbage**, only fills a total blank. Same shape in `products.py:179` (`if not records and llm_api_key`). The 18-company gauntlet proved this: 9/18 non-empty, ~2-3/18 CLEAN.

### D4 — Anti-bot on big brands defeats every datacenter-IP fetch (products only)
Lacoste / Nike / EyeBuyDirect sit behind Akamai. Every fetch from the VPS datacenter IP is 301/blocked. The browser fallback (`products.py:320`) retries from the **same IP** → same block. `ScrapeRequest.proxy` exists (`types.py:46`) and maps to Crawl4AI `proxy_config`, but **nothing ever sets it.** No code change fixes an IP reputation block — this needs a residential proxy / unblocker. **This is a purchasing decision, not an engineering one.**

---

## Design principle
**"Right page → fully rendered → adjudicated by the model, cross-checked by heuristics, guarded by company identity."**

- Heuristics stop being the source of truth. They become a **cheap candidate generator + confidence cross-check**.
- The **LLM is the adjudicator**: given well-rendered content, it extracts *and* is explicitly told to return **only the leaders/products of THIS company**, excluding authors, other companies, board-in-passing, quoted customers.
- Every record carries provenance (which page, which extractor, confidence) — already the shape of `ExecutiveRecord`/`AlgoliaProductRecord`, keep it.
- **Prove the content is in the rendered markdown BEFORE touching the extractor.** Render is the gate.

---

## The build — 4 layers, sequenced so each unblocks the next

### Layer 1 — Robust intelligence render (fixes D1) — *do first, prove it, then stop*
Add an "intelligence render" profile to the scrape path for exec/product pages:
- New `ScrapeRequest` knobs (defaults inert, so nothing else changes): `scan_full_page: bool = False`, `wait_until: str = ""`, `delay_before_return_html: float | None = None`, `block_images: bool = False`.
- Map them in `_build_run_config()` to the crawl4ai params of the same name (`wait_until`, `delay_before_return_html`, `scan_full_page`, `exclude_all_images` + `exclude_external_images`).
- Exec/product runners request the intelligence profile: `use_js=True`, `scan_full_page=True`, `wait_until="domcontentloaded"` (**not** `networkidle` — it times out on ad-heavy sites, this is the Datadog failure), a bounded `delay_before_return_html` (~2-3s) as the hydration wait, `block_images=True` for speed.
- Prefer a **content-signal `wait_for`** (CSS/text selector that means "roster loaded") where we can infer one, falling back to the bounded delay.
- **Read-receipt required before writing this** (per ~/.claude/docs/protocol-read-receipt.md): confirm exact crawl4ai 0.7.7 semantics of `wait_until` vs `wait_for` vs `delay_before_return_html` interaction. Version pinned: crawl4ai 0.7.7.
- **GATE 1:** on a 10-site render probe (mix of server-rendered + JS-rendered leadership/PLP pages), assert the exec/product text is present in `markdown`/`raw_html`. No extractor work proceeds until this passes. This is measurable and cheap.

### Layer 2 — Smart page discovery (fixes D2)
- **Find the real page, don't guess it.** From the homepage render, harvest nav/footer links and rank by anchor text + URL tokens ("leadership", "team", "our people", "management", "board", "about") — reuse the token-scoring shape already in `discovery.py:select_category_urls`. Add JS routes seen after `scan_full_page`.
- **Replace the self-referential signal check.** `_has_executive_signal` must not be the same regex that creates garbage. Use a cheap page-type classifier: strong structural signals (multiple repeated person-card blocks, JSON-LD `Person` nodes, an `/leadership`-shaped canonical) → accept; a single name-title match in prose → reject. Optionally a **one-shot Haiku "is this THIS company's leadership page? yes/no"** on ambiguous candidates (bounded, cached per run).
- Same idea for products: prefer real category/PLP pages over asset URLs and unrelated subdomains (the `discovery.py` BUILD-1a guardrails already do part of this — extend, don't rebuild).

### Layer 3 — LLM-adjudicated extraction (fixes D3) — the trust flip
- Flip execs + products from **empty-only fallback** to **primary adjudication** over well-rendered content. Heuristic output becomes a cross-check that *raises* confidence when it agrees, never the sole source.
- Harden the prompt in `scout/core/llm_extract.py` (already drafted, extend): "Return only the actual leaders/executives of **{company}** as shown on this page. Exclude article authors, quoted customers, employees of other companies, investors/board members mentioned in passing, and anyone whose affiliation to {company} is not clear on the page. If none, return []." Pass `{company}` + `{page_url}` as explicit context (the schema/plumbing already supports it).
- Keep the never-fabricate discipline: model output that doesn't validate is dropped (`llm_extract.py:165`), and a company-identity guard drops names the page doesn't tie to this company.
- **Cost control:** bound to N pages/dossier (e.g. ≤5 LLM calls), Haiku tier, `max_tokens` already capped, `_MAX_CONTENT_CHARS=12000`. Meter honestly — see cost section.

### Layer 4 — Anti-bot escalation for products (fixes D4) — *gated on a founder purchasing decision*
- Wire an **escalation ladder** in the products fetch: datacenter fetch → (on block) residential-proxy fetch via `ScrapeRequest.proxy` → (still blocked) honest "blocked, needs unblocker" evidence (never a fabricated record — keep the current honesty).
- **Provider DECIDED 2026-07-27: ScraperAPI** (pay-as-you-go unblocker, cheapest to start). Founder funds + provides key when Layer 4 begins. Meter each proxied fetch at a higher credit cost (≈10 credits/fetch) so unit economics hold.
- **This layer is independent:** execs and non-Akamai products ship without it. Only anti-bot product sites are blocked on it.

---

## Verification harness — the CLEAN hit rate (this is how we avoid false-green)
The whole point is an honest number. "Non-empty" is not "correct."
1. **Build a labeled gauntlet:** ~15-20 companies spanning server-rendered (Algolia), JS-rendered (Stripe, Datadog), and anti-bot (Lacoste, EyeBuyDirect). For each, hand-label **ground truth**: the correct top execs (name+title) and a handful of real products. This label set is real work and is a prerequisite — without it "CLEAN" is unmeasurable.
2. **Score CLEAN hit rate**, not count: precision (no wrong/foreign execs) AND recall (got the real ones). A dossier with Lightspeed's CEO scores 0 on Stripe even if non-empty.
3. Reuse the `exec-gauntlet.sh` pattern from the prior session's scratchpad; add a product gauntlet.
4. **Bar to declare the moat "done" (proposed, founder confirms):** ≥80% CLEAN on execs across non-anti-bot sites; products ≥70% CLEAN on non-anti-bot sites, and on anti-bot sites once Layer 4 is funded.
5. Run against **deployed prod**, not just local (Done-Means-Live): the render/anti-bot behavior differs by IP.

---

## Cost & metering (keep unit economics honest)
- Haiku $1/$5 per 1M tokens. A dossier ≈ up to 5 pages × (~3k in + ~1.5k out) ≈ ~$0.01-0.03. Metering ~200 credits/dossier (per pricing model, $12→20,000 credits) covers it with margin.
- Layer 4 proxied product fetches cost real cash → meter higher (≈10 credits/fetch) and only escalate on confirmed block.
- Add a per-run LLM-call cap so a pathological site can't run up spend.

---

## Sequencing & effort (rough)
| Phase | Work | Gate |
|---|---|---|
| P0 | Build labeled gauntlet (15-20 cos, ground truth) + scoring harness | Ground truth exists |
| P1 | Layer 1 render profile + knobs (read-receipt first) | GATE 1: exec/product content in markdown on 10-site probe |
| P2 | Layer 2 discovery + real page-type classifier | Reaches correct page on gauntlet |
| P3 | Layer 3 LLM-adjudicated extraction + identity guard | CLEAN hit-rate bar on non-anti-bot sites |
| P4 | Layer 4 residential-proxy ladder | *Gated on founder provider+funding*; anti-bot CLEAN bar |
| P5 | Deploy to prod, re-run both gauntlets live, record honest number | Done-Means-Live |

Each phase is TDD (RED before GREEN), pyright clean, ruff clean, three test layers per Scout's hard constraints.

---

## Decisions needed from founder (blockers surfaced now)
1. **Residential proxy / unblocker: which provider, and funded?** (Zyte / ScraperAPI / Bright Data, ~$100/mo beta.) Blocks Layer 4 = anti-bot products only. Everything else proceeds without it.
2. **CLEAN hit-rate bar** to call the moat "done" — proposed 80% execs / 70% products on non-anti-bot sites. Confirm or set your own.
3. **This session:** execute the plan now (start P0/P1), or approve/adjust the plan first?

---

## Risks
- **Render still misses truly SPA-gated content** (auth-walled or heavily client-routed rosters). Mitigate: content-signal `wait_for`, and CDP/live-browser capture already exists in-repo (`cdp_acquire.py`) as a last rung.
- **LLM adjudication latency** adds seconds/dossier. Bounded by page cap + Haiku speed; acceptable for an intelligence product.
- **Ground-truth labeling drift** (execs change). Keep the gauntlet dated; re-label on a cadence.
- **Anti-bot arms race** — providers get blocked too. Layer 4 is a ladder, not a silver bullet; honest "blocked" evidence remains the floor.
