# Scout Launch-Readiness Roadmap (living tracker)

**Goal:** make scout.chowmes.com production-ready — work e2e AND look e2e ready — then launch.
**Timeline:** invites HELD until fully ready. **Processing model:** Claude owns the goal e2e, drives
each phase, stops at the ⛳ gates below for Arijit's call. Big site build → Fable5 from a prompt this
engagement produces. Source of truth for status. Updated 2026-07-06.

**Overall: ~15% complete** (research + design decision done; design system, content, all screens,
email, build, GTM ahead).

| Phase | Item | Status | Owner |
|---|---|---|---|
| **0 · Research & foundation** | Firecrawl crawl + teardown (dogfood) | ✅ done | Claude |
| | Prod-readiness status + capacity answer | ✅ done | Claude |
| | Design-language verdict (replace, evidence-first) | ✅ decided | Claude |
| **1 · Design system** | Design DIRECTION | ✅ **LOCKED** | — |
| | Palette + typography + tokens | ✅ locked (see below) | Claude |
| | **New logo / brand mark** | ✅ **LOCKED** — "Scout" wordmark, the "o" is a full-reticle target (amber verified core); reticle = favicon | Claude |
| | Component kit (buttons, cards, nav, code blocks) | 🟡 in build (via reference screens) | Claude |
| | Reference screens (home ✅, playground-result, pricing, docs, dashboard) | 🔵 **building now** | Claude → Fable5 fans out |

**LOCKED design language (2026-07-06):** Premium **mint** neumorphism (`#E6EFEA` base, dual soft
shadows, sharpened contrast) · **demo-first (E) IA** — homepage is a live console · **crisp dark
data-screen** for all code/records (the legibility rule) · **green accent** (dark-forest `#143C2B`
filled CTAs + emerald `#0E8A61` inline) · **amber reserved ONLY for evidence marks** (verified ✓ +
citation — Scout's differentiator gets the one warm spark) · PLG funnel (anon demo → signup → app +
Destinations). Reference (not adopted): Poster Modernist, grey/violet neumorphism.
| **2 · Content & copy** ⛳ | Homepage copy — per-element HITL review | 🟡 started (mock) | Claude ↔ Arijit |
| | All screens' copy (Product, Pricing, Playground, About, Changelog…) | ⬜ pending | Claude ↔ Arijit |
| | How-to guides, success stories, customer/social proof | ⬜ pending | Claude ↔ Arijit |
| **3 · Enablement (Track A)** ⛳ | Branded key-delivery email (HTML + text) | ⬜ pending | Claude → Arijit approves |
| | support@scout.chowmes.com → Gmail + support process | ⬜ pending | Claude builds / Arijit does DNS |
| **4 · Site build** ⛳ | Full multi-screen site in chosen system | ⬜ pending | **Fable5** (or Claude — see gate) |
| | Mintlify docs at docs.scout.chowmes.com + llms.txt | ⬜ pending | Fable5 / Arijit account |
| | Playground surfaced as demo-hero | ⬜ pending | Fable5 |
| **5 · GTM & launch** ⛳ | GTM strategy + launch + execution plan | ⬜ pending | Claude ↔ Arijit |
| | Load-test finish (GA capacity characterization) | ⬜ pending | Claude |
| | Final Fable5 goal + prompt | ⬜ pending | Claude → Arijit approves |
| | Go-live: invites out | ⬜ pending | Arijit |

## Approval gates (⛳ = I stop here for your call)
1. **Design direction** (now) — you pick the visual language from real mockups.
2. **Logo** — you pick from concepts.
3. **Copy** — per-element sign-off on every screen.
4. **Email** — you approve before it can ever send.
5. **Site build handoff** — you approve the Fable5 prompt (or redirect the build to me).
6. **Pre-launch** — you approve before invites go out.

## Screens to design + build (site map, modeled on the Firecrawl teardown)
Home · Product overview + per-capability pages (scrape/crawl/map/products/company/screenshots) ·
Pricing · Playground · Docs (Mintlify) · About · Changelog · Legal/Terms/Privacy · Beta signup · Account.
