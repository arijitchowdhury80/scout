# Scout Redesign — Design Thinking (Steps 1–6)

Feature: full UI redesign of the Scout Intelligence Platform (Phase B mockups → Phase C2 build).
Inputs: `docs/audit/2026-06-12/ui-audit.md`, `docs/specs/use-cases/*`, ADRs (scope boundary, static SPA, embedded live browser).

## 1. Mental model

The dominant metaphor is a **mission console** — closest to "flight deck": you brief a mission (target + use case), watch it execute live (timeline + a window into the browser doing the work), then debrief over the evidence. Secondary metaphor: **evidence locker** for results — records you can pick up, inspect, and trace back to sources.

What the user expects: pick a company → pick what to gather → press go → watch it happen → get records they can trust and export. What would confuse them: synthesis-flavored UI (scores, "insights") — the scope ADR says Scout never has an opinion, so the UI must present *evidence quantities and provenance*, never judgments; and any control that looks live but isn't (audit caught four disabled browser buttons — the embedded browser pane makes them real, anything not real stays out).

The current app already has the right 3-phase bones (Setup → Live → Results). The redesign keeps that skeleton and fixes: discovery (use-case dropdown hides the product's breadth — a launcher should show it), the dead Capture Workbench (becomes the live browser), product-only results views, and buried history.

## 2. Information architecture (emphasis tiers)

**Launcher screen** — Hero: use-case cards grid (the product IS its capabilities). Primary: target input + recent runs resume. Secondary: presets/target catalog entry points. Supporting: docs links, version.

**Run setup** — Hero: target input (the one required decision). Primary: selected use-case contract summary (what will be gathered — from the spec), Start Execution. Secondary: execution mode ladder, crawl options, workdir. Supporting: developer details (CLI/HTTP), readiness checklist.

**Live run** — Hero: the embedded live browser pane (when browser rung active) OR the activity timeline (crawler-only runs). Primary: status badge + record/source/blocked counters ticking live; Cancel. Secondary: event log. Supporting: run id, output dir.

**Results** — Hero: records table in the use-case's shape (job postings table ≠ quotes table ≠ products table). Primary: evidence drawer for the selected record; export/push actions. Secondary: sources, blocked pages, artifacts tabs. Supporting: logs, manifest metadata.

**History** — Hero: runs table (persistent, SQLite-backed). Primary: re-open + re-run actions. Supporting: filters.

**Settings** — Primary: workdir, API key, Algolia credentials (editable per C0.5). Supporting: runtime info.

**Algolia push** — Hero: dry-run preview diff (what will be pushed). Primary: index name + push button. Secondary: credential status. Supporting: push history.

Tier inflation watch: counters are Primary not Hero; mode ladder is Secondary (Auto is right 90% of the time — don't make 8 tabs shout).

## 3. Interaction flow

Three most common actions: (1) launch a run on a target — 2 clicks + paste (card → paste → Start); (2) inspect a record's evidence — 1 click (row → drawer); (3) re-run a previous target — 2 clicks from history/launcher recents.

Happy path: Launcher → click use-case card → setup pre-filled with contract summary → paste target → Start → live view (watch browser/timeline) → auto-transition to Results on completion → click records, view evidence → Export / Push to Algolia. No dead ends: results always offer "New run", "Re-run", "Push/Export"; blocked runs offer "Retry in embedded browser" / "Open in User Browser" as the explicit escalation actions.

Empty states: launcher with no history shows cards + a worked example; results with 0 records shows the blocked-evidence panel front and center with escalation CTAs (honest-blocking is a feature — design it, don't apologize). Loading: skeleton counters + immediately-live event stream (SSE). Errors: failed run keeps Results layout with error banner + log tab focused.

## 4. Cognitive load budget

Per screen ≤5 chunks: Launcher = cards grid (1) + target quick-input (1) + recents (1) = 3. Setup = contract card (1) + target (1) + mode (1) + options accordion (1, collapsed) + readiness (1) = 5. Live = browser/timeline hero (1) + counters strip (1) + event log (1) = 3. Results = counters (1) + records table (1) + tab strip (1) + drawer (on demand) = 3–4. Reduction strategy already applied: crawl options and developer details collapse by default; mode ladder is a single segmented control.

## 5. Emotional journey

Brief: *capable anticipation* (cards show breadth, contract summary shows exactly what you'll get). Execute: *trust through transparency* (you can SEE the browser working — the single biggest emotional upgrade of the redesign; counters tick, nothing is a black box). Block: *control, not failure* ("Scout was blocked — here's the evidence, here's the next rung" reads as the tool protecting you). Debrief: *confidence* (every value has a source link; export is one click). The embedded browser pane and the evidence drawer carry the emotional weight.

## 6. Pre-mortem

**Tigers**
- *Generic AI dashboard look* → committed aesthetic (theme-dashboard dark console), distinctive elements: live browser pane with chrome, evidence-trace drawer, use-case cards with per-case record iconography.
- *Information overload on Live* → only one hero (browser OR timeline); counters limited to 4; log collapsed to a ticker with expand.
- *Embedded browser pane overpromises* → pane carries a persistent honesty chip ("automated Chromium — hard WAFs may still block; escalate to your Chrome"), per ADR.
- *Per-use-case results views explode scope* → one table component with column presets per record type (7 presets, 1 component), drawer shared.
- *Mobile breakage* → console is desktop-first; defined breakpoint behavior: ≤768px stacks panes vertically, browser pane becomes screenshot-only. 375px is read-only review, not operation.
- *Dark-mode-only blindness* → theme-dashboard is dark by design; ensure AA contrast on status colors (amber/red on dark).
- *Accessibility* → keyboard path for launcher→setup→start; canvas browser pane gets keyboard navigation disclaimer + all its actions duplicated as real buttons (URL bar, back/forward are buttons, not canvas-only).

**Elephants**
- No second real user has tested the flow — mitigation: SE walkthrough after Phase C2 with one scripted task.
- Mockups could ossify wrong spec — mitigation: mockups use fake data shaped EXACTLY by the acquisition contracts (specs 01–11); if a view can't be drawn from contract fields, the contract is wrong — catch now.
- SSE/screencast performance unknowns at mockup stage — flagged to C0.3/C0.6 with fps/quality tunables.
