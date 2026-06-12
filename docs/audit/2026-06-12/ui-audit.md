# Scout App UI Audit — 2026-06-12

Live audit of `http://127.0.0.1:8421/app` on branch `codex/scout-platform-foundation` (commit `49e2e9d`), driven with Playwright. Every visible control was exercised; screenshots in `screenshots/`. Zero JavaScript console errors or warnings across the entire session.

## Verdict legend

- **WORKING** — does what the workflow specs (`docs/ui/workflows/*.md`) promise
- **BROKEN** — errors, dead behavior, or wrong/misleading output (fixed in Phase A)
- **STUB** — UI exists, backend returns placeholder output (Phase C scope)
- **UX** — works but behavior is confusing/mismatched (Phase B redesign input)

## Run Setup (screenshots/01-run-setup-default.png)

| Control | Observed | Verdict |
|---|---|---|
| Use Case dropdown (10 options) | Each option updates target label, placeholder, example, help, expected outputs | WORKING |
| Target URL input + clear (×) | Updates dev details; clears | WORKING |
| Execution Mode tabs (8) | Selection + help text updates; **but WebFetch, WebSearch, Saved, API all show "Scout will use a crawler session."** — wrong copy for 4 of 8 modes | BROKEN → fixed |
| Crawl Settings chips | Remove works; "+ Add option" menu lists removed options; restore works | WORKING |
| Working Directory + Browse | Field edits; Browse wired to `/workdir/pick-native` (not click-tested — opens a native dialog) | WORKING (unit-tested) |
| Run Readiness panel | Tracks Target/Mode/Output/Browser reality/Start state live | WORKING |
| Start Execution with empty target | Inline validation: "Enter a Target / Start URL before starting execution." + readiness flips Not ready | WORKING |
| Developer Details | CLI + HTTP previews regenerate with form state | WORKING |

## Live Execution + Results (screenshots/09–11)

| Control | Observed | Verdict |
|---|---|---|
| Start → Live state | Run ID, status badge, timeline, event log all update via 700 ms polling | WORKING |
| Capture Workbench | URL shown; Back/Forward/Refresh/Save visibly disabled with honest "not a live embedded browser" copy | WORKING (honest) |
| Cancel Run / Clear Run | Cancel sets cancelled; Clear resets to Setup | WORKING |
| Results metrics (5 cards) | Pages/Records/Sources/Blocked/Warnings populate | WORKING |
| Results tabs (7) | All switch and render | WORKING |
| Records table | Rows render; row click opens detail drawer with real data | WORKING |
| Records table headers | **Always "PRODUCT NAME / BRAND / PRICE / SKU" — even for company/news/etc. runs** | BROKEN → fixed |
| Record detail drawer | Name, price, URL, evidence source, citations; close works | WORKING |

### End-to-end run evidence

- **products / Patagonia** (`screenshots/11-products-run-records.png`): `complete`, **10 records** with real names, prices, SKUs. Quality gaps for Phase C: 3 junk records titled "Hang Tight! Routing to checkout..." (checkout interstitial scraped as product), one duplicate pair (SKU 25551-AMRE twice), `brand` empty on all records.
- **products / Estée Lauder**: `complete`, 0 records, **1 blocked page preserved with evidence + warning** — the designed honest-blocking behavior for hard (WAF-protected) sites. User Browser escalation is the documented recovery path.
- **company / algolia.com** (`screenshots/09-company-run-results.png`): `complete`, 3 records — **all fabricated seeds**: name = the raw URL, LinkedIn URL invented as `linkedin.com/company/https-www-algolia-com/`, citation snippet literally says "Leadership seed record; live executive extraction is pending.", confidence 0.35.

### Stub confirmation across all intelligence use cases (via API)

| Use case | Status | Records | Citation snippet |
|---|---|---|---|
| careers | complete | 1 | "Derived careers URL seed; live careers extraction is pending." |
| jobs | complete | 1 | "Company was explicitly listed in the JobSearchProfile." (seed) |
| news | complete | 1 | "Derived news URL seed; live news extraction is pending." |
| investor | complete | 1 | "Derived investor relations URL seed; live investor extraction is pending." |
| research | complete | 1 | "Research seed record; acquisition providers collect evidence in later slices." |
| docs | complete | 1 | same seed text | 
| website-quality | complete | 1 | same seed text |
| prism | complete | 6 | composition of company seeds |

**All 9 intelligence use cases are STUBs** — they report `complete` and render records that are placeholders. This is the core Phase C build scope. The run completing with status "complete" and no user-visible warning that the data is synthetic is the single biggest honesty gap in the product today.

## Utility screens (screenshots/02–08)

| Screen | Observed | Verdict |
|---|---|---|
| History | Honest empty state; populates per browser session only — **lost on restart** (no persistence) | WORKING / STUB (persistence: Phase C0.1) |
| Presets (6) | "Use Preset" applies use case + URL and returns to Run Setup | WORKING |
| Targets (8) | "Use Target" applies URL **but keeps the current use case** (Algolia + "products" mismatch possible) | UX → Phase B |
| Data Browser | Renders panels; **"Download Records" enabled with no run → downloads empty scout-records.json** (violates UI interaction contract: enabled controls must work meaningfully or be disabled) | BROKEN → fixed |
| Integrations | Algolia form + "Preview Readiness" validates honestly ("Not ready: missing index name, records"); **no actual push** | STUB (push: Phase C0.4) |
| Settings | Displays workdir, API-key status, live-test flag; **read-only** | STUB (Phase C0.5) |
| Help | 3-step static guide | WORKING |
| Top nav: Runs/Projects/Settings/Docs | All route correctly; Docs → /docs Swagger | WORKING |

## Security & platform notes

1. **API key embedded in `/app` HTML**: `/app` is on the auth middleware's public whitelist and the served page carries the `SCOUT_API_KEY` so its JS can call protected endpoints. Anyone who can reach the port gets the key. Acceptable for localhost single-user; must be redesigned before any shared deployment (Phase C0.5 / deployment decision).
2. **Default workdir is the repo's `tests/` folder** — run artifacts pollute the working tree (now gitignored as a stopgap). Should default to a runs directory outside the repo (Phase B/C decision).
3. Run state is in-memory only (`_APP_RUNS` dict) — restart loses all history (Phase C0.1, SQLite).

## Phase A fixes applied (this session)

1. Mode help copy: per-mode descriptions for WebFetch/WebSearch/Saved/API (was: generic "crawler session").
2. Data Browser "Download Records" disabled (with hint) when no run artifacts exist.
3. Records table headers adapt to use case (product columns only for products runs; generic Name/Type/Source columns otherwise).

## Deferred (tagged)

- Phase B (design): Targets→use-case pairing, run-history UX, results views per use case, workdir default.
- Phase C0: SQLite persistence, SSE streaming, Algolia push, editable settings/secrets.
- Phase C1: live acquisition for all 9 use cases (kill the seed records).
- Phase C (products deepening): filter checkout-interstitial junk records, dedupe variants, populate `brand` from site context.
