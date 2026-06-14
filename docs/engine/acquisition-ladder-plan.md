# Scout Acquisition Ladder — Build Program (the unblock solve)

Governing ADR: `docs/decisions/2026-06-14-scout-as-universal-acquisition-engine.md`. This is the engineering plan to make Scout the bulletproof, measured, universal acquisition engine.

## The goal, honestly stated

Not "100% unblock" (impossible vs Akamai/DataDome/PerimeterX/Cloudflare-Enterprise — true for everyone). The goal is:
1. A **tiered escalation ladder** that tries cheap→expensive and beats the **mid-tier (~84–90% of real sites)** mostly by *wiring features Crawl4AI 0.7.7 already ships*.
2. **Honest degradation** — every run reports got-data / got-screenshot / blocked, via which rung, with evidence. Never silent, never fabricated.
3. A **human/real-browser backstop** for the hardest tier and login-walled sites (LinkedIn, DataDome behavioral).
4. A **measured confidence map** per site-class so consumers (PRISM etc.) can trust and route.

## Baseline evidence (2026-06-14, `docs/audit/2026-06-14-unblock/`)

- **Zillow** (Roswell GA), real headed browser via CDP: front page → 8 listings extracted (addr/price/link); detail page → price/beds/baths/sqft + `RealEstateListing` JSON-LD; **zero block signatures**. → The real-browser rung cracks Zillow. Scout's *headless* tier almost certainly would not (IP + headless fingerprint).
- Earlier (Phase A): Patagonia products via crawl4ai → 10 records; Estée Lauder (Akamai) → honestly blocked. One block data point.
- Pending live tests (next): retail WAF (PetSmart, Savage X Fenty, L.L.Bean, Home Depot), Redfin/apartments.com, LinkedIn (needs the user's login — real-browser rung only).

## Current state of Scout's muscle (from code map)

- Stealth today = **3 booleans** (`enable_stealth`, `simulate_user`, `magic`) wired off `req.stealth`. That's the entire anti-detection surface.
- **Unused but already in crawl4ai 0.7.7:** `override_navigator`, `UndetectedAdapter`/`browser_type="undetected"`, `proxy`/`proxy_config`, `use_persistent_context`/`user_data_dir`, `user_agent_mode="random"`. Zero proxy support anywhere.
- Block detection = `products._is_blocked` only (2 string checks, no status codes, misses Cloudflare/DataDome/Turnstile). `scrape`/`crawl`/`map` have **no** block detection.
- Real-Chrome CDP bridge exists (`user_browser.ChromeCDPService`) but is **macOS-only, hard-coded path**, screenshot-on-demand, **no `Page.startScreencast`** (no embedded live view yet).

## The ladder to build (cheapest → strongest)

| Rung | Engine | Beats | Effort |
|---|---|---|---|
| **T0 TLS-impersonation HTTP** | `curl_cffi` (impersonate chrome131) | TLS/JA3 blocks; static/JSON/detail endpoints; ~84% targets, 10–100× cheaper | new dep, small |
| **T1 Hardened crawl4ai stealth** | crawl4ai + `enable_stealth` + **`override_navigator`** + random UA + viewport jitter | basic bot detection (sannysoft, navigator.webdriver) | wiring only |
| **T2 Undetected adapter + proxy** | crawl4ai `UndetectedAdapter`, headed, + **residential proxy** | Cloudflare mid-tier, older Akamai (~nodriver-class, 84–90%) | wiring + proxy acct |
| **T3 Patchright** (optional) | patchright (drop-in Playwright, Python) | Cloudflare where T2 underperforms | new dep |
| **T4 Camoufox** (hardest only) | camoufox (Firefox fork) + residential/mobile proxy | DataDome/Akamai v4/CF Enterprise behavioral | new engine, gated |
| **T5 Real browser / human** | `ChromeCDPService` + `Page.startScreencast` (embedded live) | login-walled (LinkedIn), interactive CAPTCHA, anything headless can't | productionize existing |

**Cross-cutting (every rung):** real block detection (status 403/429/503 + CF/DataDome/Turnstile/PerimeterX/Akamai signatures) lifted into a shared module so escalation auto-triggers; residential/mobile proxy config; the measurement harness.

## Phases (each: TDD, 3 test layers, pyright clean, honest verification)

- **P1 — Block detection + escalation spine.** Shared `scout/core/blocking.py` (status + signatures). Lift out of products; wire into scrape/crawl/map. Escalation controller that climbs the ladder on a block. *Fully autonomous, testable offline.* ← starting now.
- **P2 — Wire the free crawl4ai rungs (T1, T2).** `override_navigator`, random UA/viewport, `UndetectedAdapter` flag, `proxy_config` field. Measure lift on the target matrix.
- **P3 — Measurement harness + confidence map.** Runs each rung × site-class, records got-data/screenshot/blocked → `confidence-map.md`. This is the artifact that replaces speculation.
- **P4 — T0 curl_cffi tier.** Cheap TLS-impersonation first attempt for detail/JSON endpoints.
- **P5 — T5 embedded live browser.** `Page.startScreencast` over the existing CDP bridge, cross-platform path, streaming endpoint. The rung that carries Zillow/LinkedIn/hard sites with the human in the loop.
- **P6 — T4 camoufox** (only if P3 shows a residual hard tier worth it). Gated behind per-site escalation; honest cost note (>~10k pages/day → consider paid API).
- **P7 — Re-measure, publish confidence map, wire into consumers** (PRISM Track-1, audit-browser).

## What needs the user (genuine blockers, not check-ins)

1. **Residential/mobile proxy** account/budget — T2/T4 underperform without it (IP reputation is an independent signal from stealth). Decision needed before P2 validation is meaningful.
2. **Hardest-rung validation on your machine** — LinkedIn-as-you, Zillow-logged-in, job auto-apply run on *your* sessions; I can build + validate the mechanism here, you run the final hostile tests.
3. **Legal/ToS sign-off** — LinkedIn engagement capture and job auto-apply cross ToS lines. Build ≠ permission to use.

## Honest success criteria

- Mid-tier sites (retail WAF, Cloudflare mid): T2+proxy clears most — *measured*, not assumed.
- Hardest tier (DataDome/Akamai v4/LinkedIn): T5 human rung is the answer; headless will not be reliable.
- Every site, every run: truthful status + evidence. That guarantee ships regardless of block outcome.
