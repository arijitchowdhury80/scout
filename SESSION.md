# SESSION — 2026-06-12
## Status: Phase A COMPLETE (audit + fixes + one-pager + layout fix, all committed). Phase B (design & specs) is next. Plan approved by user.

---

## Resume Action (next session, in order)

1. Read this file fully.
2. Read the approved program plan: `~/.claude/plans/i-am-building-scout-glittery-jellyfish.md` (it contains Phases B and C in executable detail, including the Embedded Live Browser addendum).
3. Read the audit report: `docs/audit/2026-06-12/ui-audit.md` — it is the evidence base for everything in Phases B/C.
4. Confirm with the user, then start **Phase B**:
   a. Write ADR: embedded-Python-string frontend → no-build static SPA in `scout/api/static/` (`docs/decisions/2026-06-XX-frontend-static-spa.md`).
   b. Write ADR: Embedded Live Browser via CDP screencast (`docs/decisions/2026-06-XX-embedded-live-browser.md`).
   c. Run the **frontend-builder** skill (full design workflow — design thinking, aesthetic selection, mockups). Outputs to `docs/design/scout-redesign/`: design brief + clickable HTML mockups (launcher, run setup, live run with streaming + embedded browser workbench, results, history, settings, Algolia push) + PNG exports.
   d. Add a "Live Acquisition Spec" per use case to/alongside `docs/ui/workflows/*.md` (input contract, provider plan, extraction, record types, golden e2e flow as testable assertions).
   e. STOP for user approval before any Phase C code.

## Where we stopped (exact)

Last assistant message ended with: "Ready to start Phase B — the design phase now covers the redesign, the embedded browser workbench, and the per-use-case acquisition specs. Shall I proceed?" The user then ran `/persist and /handoff` instead of answering — so Phase B is queued but not explicitly green-lit. Confirm and proceed.

Two untracked screenshots exist (`docs/audit/2026-06-12/screenshots/13-layout-1440x820.png`, `14-layout-fixed-1440x820.png` — the before/after of the layout fix). Not yet committed; fold into the next docs commit.

## Decisions locked this session

1. **Program plan approved** (4 user choices via AskUserQuestion): all 9 intelligence use cases go live breadth-first; ONE one-pager with SE/AE/BDR persona sections; sequencing audit→fix→design→build with user checkpoints; PROPER UI redesign (not polish).
2. **Frontend direction** (to be ADR'd in Phase B): static SPA-lite, no build step, in `scout/api/static/`.
3. **Embedded Live Browser** (user request, 2026-06-12): CDP screencast streaming of Scout's server-side Playwright Chromium into the UI over WebSocket, input forwarded back via CDP Input dispatch. Iframes are impossible (X-Frame-Options). It slots BETWEEN scout-browser and user-browser in the escalation ladder; the user's real Chrome stays the final escape hatch for hard WAFs (Akamai-class). Phase B ADR + mockup centerpiece; Phase C build slice C0.6 (after C0.3 SSE, shares streaming infra).
4. **Phase C storage**: SQLite (`runs` + `run_events`) replacing in-memory `_APP_RUNS`; **streaming**: SSE not WebSockets for run events; **Algolia push**: official `algoliasearch` Python client server-side (MCP unavailable in server process); **secrets**: keyring/Keychain.
5. **Run-artifact files in tests/ are NOT to be deleted without asking** — user denied an `rm`; they are gitignored instead.

## What was done this session (all verified, all committed)

Branch `codex/scout-platform-foundation`, commits this session:
- `49e2e9d` feat(browser): user browser capture via Chrome CDP bridge — committed the pre-existing WIP (18 files) after verifying 211 tests + pyright clean.
- `60c8e22` fix(app): mode help copy (4 modes wrongly said "crawler session"), Download Records guarded when empty, records table headers adapt to use case (was product-only columns for company runs). TDD: 3 failing tests → green.
- `91859a7` docs(audit): `docs/audit/2026-06-12/ui-audit.md` + 12 screenshots.
- `26130b6` docs(one-pager): `docs/one-pager/scout-one-pager.{md,html,pdf}` + preview PNG. Single A4 page, editorial serif style, SE/AE/BDR three-column layout.
- `3272aea` chore: gitignore remaining run-artifact patterns under tests/.
- `3cc7b57` fix(app): closed drawer no longer reserves 360px grid gutter (workspace 524→884px at 1440w); app shell fixed to viewport height with per-pane scrolling (no more whole-page scroll / cut-off). TDD e2e test added.

Verification evidence: 214 unit + 15 e2e tests passing, pyright strict 0 errors, ruff clean (run before every commit; outputs shown in session).

## Audit findings (full table in docs/audit/2026-06-12/ui-audit.md)

- **All 9 intelligence use cases are STUBS**: they report `complete` but emit fabricated seed records (0.35 confidence, invented LinkedIn URLs, citations saying "live extraction is pending"). Verified via UI run (company) and API runs (careers/jobs/news/investor/research/docs/website-quality/prism). THE core Phase C scope.
- **Products mode is real**: Patagonia run → 10 records with names/prices/SKUs; Estée Lauder → honestly blocked with preserved evidence. Quality gaps deferred to Phase C: "Hang Tight! Routing to checkout..." junk records, duplicate variants, empty brand.
- Zero JS console errors across entire UI walk.
- Security note: `/app` HTML embeds SCOUT_API_KEY (public path serves the key). OK single-user localhost; must change for shared deployment.
- UX notes for Phase B: "Use Target" doesn't set a matching use case; history is per-browser-session only; settings read-only; Algolia integration is preview-only.

## Remaining work (in order)

1. **Phase B** (next): two ADRs, frontend-builder design workflow + mockups, Live Acquisition Specs, user approval gate.
2. **Phase C0**: SQLite run persistence → acquisition core (`scout/core/acquisition/` — fetcher implementing the provider ladder, site_map.py canonical-path prober) → SSE streaming → Embedded Live Browser (C0.6) → algoliasearch push → editable settings/secrets.
3. **Phase C1**: 9 use cases live, order: company → careers → news → investor → docs → research → website-quality → social → prism (composition). Each: fixture RED → extractor GREEN → integration → e2e → opt-in live test → commit. `locations` descoped.
4. **Phase C2**: UI rebuild on approved mockups (extract embedded HTML to static files as a pure-move commit FIRST, e2e green, then restyle).
5. Open decisions for the user (raised, not yet decided): robots.txt/compliance ADR, legal check on social scraping, retention policy, per-user vs shared deployment.

## What has NOT been done (do not claim otherwise)

- NO Phase B artifacts exist yet (no ADRs for static SPA or embedded browser, no mockups, no design brief, no acquisition specs).
- NO live acquisition for any intelligence use case — all 9 still emit fake seeds.
- NO Algolia push, NO SQLite persistence, NO SSE, NO embedded browser code.
- Products quality bugs (junk/dupe records, empty brand) NOT fixed.
- Default workdir still points at repo `tests/` folder.
- The Scout Claude skill (`scout/skill/scout.md`) still not registered; PRISM integration still pending (pre-dates this effort).
- Branch NOT pushed to remote this session; nothing merged to main.

## Reference files

| Path | Purpose |
|---|---|
| `~/.claude/plans/i-am-building-scout-glittery-jellyfish.md` | THE approved program plan (Phases A–C, updated with embedded browser) |
| `docs/audit/2026-06-12/ui-audit.md` | Audit evidence base, verdict per control |
| `docs/one-pager/scout-one-pager.{md,html,pdf}` | Field-team one-pager deliverable |
| `docs/ui/workflows/*.md` | 10 existing UI workflow specs — Phase B gap-analyzes these |
| `docs/target-matrix.md` | Validation targets for Phase C live tests |
| `scout/core/use_cases/intelligence_runner.py` | The stub generator Phase C replaces |
| `scout/api/routers/app_runs.py` | Run lifecycle (1,011 lines) — SQLite/SSE land here |
| `scout/api/frontend.py` | Embedded UI (~1,600 lines) — Phase C2 extracts to static |
| `~/.claude/projects/-Users-arijitchowdhury-AI-Development-Scout/memory/` | Cross-session memory (plan state, session pointer) |

## Files written this session

- `docs/audit/2026-06-12/ui-audit.md` + 14 screenshots (12 committed, 2 pending)
- `docs/one-pager/scout-one-pager.md` / `.html` / `.pdf` / `-preview.png`
- `scout/api/frontend.py` (3 fix edits + layout fix), `.gitignore` (2 edits)
- `tests/unit/api/test_app_frontend.py` (+3 tests), `tests/e2e/test_app_ui_exhaustive.py` (+1 test)
- `~/.claude/plans/i-am-building-scout-glittery-jellyfish.md` (plan + 2 addendum edits)
- Memory: `scout-phased-rebuild-plan.md`, `session_pointer.md`, `MEMORY.md` index
- This file; project `CLAUDE.md` refreshed; vault dev-log entry appended

## How to run

```bash
python3 -m scout.cli serve --port 8421    # app at http://localhost:8421/app
python3 -m pytest tests/unit -q           # 214 tests
python3 -m pytest tests/e2e -q            # 15 Playwright tests (starts own server)
python3 -m pyright scout/ && ruff check scout/ tests/
```
