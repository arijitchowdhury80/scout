# SESSION.md — Scout (updated 2026-07-06 pm)

## Status
**NEW SITE + PLG BACKEND LIVE IN PROD** — commit `908f6d9`, deploy snapshot `20260706-2001`, all
surfaces live-verified. **Beta invites HELD until fully e2e ready** (Arijit's call, no fixed date).
Design phase complete (language + logo + pricing locked); build phase shipped its first drop; next =
enablement wiring + docs + GTM.

## Resume action (do in order)
1. Read this file + `docs/product/launch-readiness-roadmap.md` (living tracker) +
   `docs/product/design-system.md` + `docs/product/pricing-model-2026-07-06.md` +
   `docs/product/plg-playground-ux.md`. These are LOCKED specs — don't re-litigate.
2. Ask Arijit for Lane C status: (a) ImprovMX + Hostinger DNS for support@scout.chowmes.com —
   records given: MX `scout`→mx1.improvmx.com(10)/mx2.improvmx.com(20) + TXT `scout`
   "v=spf1 include:spf.improvmx.com ~all"; verify with `dig +short MX scout.chowmes.com` + live test
   email to support@ → his Gmail. (b) Mintlify signup + repo connect. (c) I can check Stripe test
   keys on VPS myself (`ssh chowmes-vps`).
3. Wire the branded enablement email into the key-delivery sender (TDD). Approved design = scratchpad
   artifact `scout-email.html` (published https://claude.ai/code/artifact/fb6a8614-cd12-4c59-bdcc-80802d4cacb2):
   flat email-safe brand, key in dark code block, "first 5 minutes" curl steps, evidence angle,
   docs+playground buttons, "try this first" story, support line, signed Arijit. Rebuild as a proper
   template in the scout/core/platform/ key-delivery path.
4. Then in order: Mintlify docs migration · GTM plan → `docs/product/gtm-and-site-launch-plan.md`
   (NOT yet written) · prod e2e of new signup→playground→run→download→destination flow · visual QA
   pass of the LIVE site with Arijit (he hasn't reviewed the live build in detail yet).

## Where we stopped (exact)
Deployed + live-verified the rebuilt site; ran /persist (this file). Last open ask to Arijit: Lane C
status (DNS + Mintlify). Branded email TEMPLATE approved but NOT wired into the backend sender —
key-delivery emails still send the old plain copy.

## Decisions locked this session (full rationale in the named docs)
- **Invites HELD until e2e ready** — no launch-date pressure; quality gate first.
- **Design language:** premium MINT neumorphism + demo-first (E) IA + crisp dark data-screen rule +
  green accent (forest fills, emerald inline) + **amber reserved for evidence marks only** →
  `docs/product/design-system.md`. Rejected: Poster Modernist, grey/violet neumorphism, Firecrawl
  clone; A/C round-1 were one language in two modes (Arijit caught it).
- **Logo:** "Scout" wordmark, the "o" = full-reticle target with amber core; reticle = favicon.
  (3 rounds; bracketed-[Scout] and mono `[scout·]` rejected — latter as "AI-output" look.)
- **Pricing:** Free GA 5,000 · Monthly $12 = 50,000/mo (NEVER "unlimited" — brand honesty) · pay-go
  demoted + repriced $10/10k · $25/30k · $100/150k · dossier ≈ 200 credits · Monthly mix "20k pages +
  10k products + 100 dossiers" (sums exactly; both cards use "+" mix logic) · beta cohort stays 10k ·
  higher tier ($49/$99) penciled, not launched → `docs/product/pricing-model-2026-07-06.md`.
- **Market the subscription** (MRR engine); free = PLG hook; pay-go = quiet fallback.
- **PLG funnel:** anon demo (scrape+map only, 5 runs/IP/day + global ceiling, preview-only) → free
  signup (all endpoints, downloads, saved runs) → paid (Destinations) → `docs/product/plg-playground-ux.md`.
- **Destinations are GENERIC:** Webhook (universal) + Algolia connectors behind one interface;
  public copy = "your search index, warehouse, or webhook" — never leads with Algolia.
- **Support model:** NO self-serve reissue UI; support@scout.chowmes.com (→ Arijit's Gmail) is the
  path; backend reissue endpoint KEPT for operator use.
- **Email ≠ neumorphic:** clients strip shadows → flat brand variant for email.
- Earlier today (commit 70c7e07, also deployed): beta grant 1k→10k + simple email-only /beta page.

## Remaining work (order)
1. Lane C verify (Arijit: DNS, Mintlify) → live test email to support@.
2. Branded enablement email wired into the sender (TDD) + Resend smoke.
3. Mintlify docs at docs.scout.chowmes.com + llms.txt.
4. GTM strategy + launch/execution plan doc (HITL with Arijit).
5. Prod e2e: new signup→run→download→destination flow (real user journey).
6. Load-test finish / GA capacity characterization (Redis+workers scaling documented, not built).
7. Visual QA + per-element copy review of the LIVE pages with Arijit.
8. Remaining app screens as real pages: per-capability marketing pages, Your runs, API keys, Usage,
   Account/Destinations-connect (app.html is the shell/reference).
9. Deferred backlog: operator dashboard; purge ~4.2k test tenants; XSS-name escaping check; signup
   abuse hardening (email verify); rotate exposed Resend key; swap Stripe sandbox before LIVE;
   non-root container patch (see prod-architecture-security-review-2026-07-04.md).

## What has NOT been done (do not claim)
Branded email NOT wired (template only). support@ DNS NOT set (mailto live on site but bounces).
Mintlify NOT started. GTM doc NOT written. New-flow prod e2e NOT run. Load test NOT 100% (stability +
isolation proven; sustained mixed soak not done). Higher tier NOT built. Fable5 prompt exists
(~/.claude/prompt-library/2026-07-06-scout-site-build-fable5.md) but the build ran as an in-session
workflow instead; remaining screens above NOT built.

## Reference files
| Path | Purpose |
|---|---|
| docs/product/design-system.md | LOCKED design language + logo spec (tokens, reticle SVG, crisp-screen rule) |
| docs/product/pricing-model-2026-07-06.md | LOCKED pricing + unit economics |
| docs/product/plg-playground-ux.md | PLG funnel, anon-demo limits, Destinations, support model |
| docs/product/launch-readiness-roadmap.md | Living tracker: phases, gates, % |
| docs/competitor-crawl/firecrawl/ | Scout-dogfooded Firecrawl teardown (urls, pages/, shots/, analysis.md) |
| docs/product/design-language-verdict.md | Why the old Flux brutalism was replaced |
| ~/.claude/prompt-library/2026-07-06-scout-launch-enablement.md | Approved engagement shape |
| scout/core/platform/destinations.py, scout/api/routers/{destinations,demo}.py | New backend (this build) |
| website/app.html | New signed-in app shell (reference implementation) |

## Files written this session (beyond repo commits 70c7e07 + 908f6d9)
- Repo docs: design-system.md, pricing-model-2026-07-06.md, plg-playground-ux.md,
  launch-readiness-roadmap.md, design-language-verdict.md, competitor-crawl/firecrawl/*
- Prompt library: 2026-07-06-scout-launch-enablement.md, 2026-07-06-scout-site-build-fable5.md
- Memory: scout-saas-launch-state.md (rewritten), scout-design-decisions-hitl.md (new),
  session_pointer.md, MEMORY.md
- Scratchpad artifacts (design iterations, all published as claude.ai artifacts): scout-A/B/C/D/E,
  scout-neu*, scout-logos, scout-logo-v2, scout-logo-A, scout-wordmarks, scout-app-playground,
  scout-pricing(-v2), **scout-email.html ← approved email template (lives ONLY in scratchpad +
  artifact URL — copy into repo when wiring)**

## Session context worth knowing
- The build ran as an 11-agent workflow (~2.2M tokens, 85 min). Its final self-reports were garbage
  (agents wedged in a hook loop at the end) but the work was real — all gates re-verified by the
  main loop (zero-trust relay): 888 tests, pyright 0, ruff clean, live checks green.
- VPS ssh alias `chowmes-vps` (user chowmesadmin); deploy = stash docker-compose.yml → pull --ff-only
  → pop → `sudo docker/scout-deploy.sh`; rollback image kept (20260706-1513).
- chowmes.com DNS = Hostinger (dns-parking NS); NO MX records exist anywhere on the domain yet.
- Old SESSION content (pre-4am state: dual-path beta, "Monday launch") is SUPERSEDED by this file.
