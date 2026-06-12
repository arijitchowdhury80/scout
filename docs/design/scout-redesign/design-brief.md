# Scout Redesign — Design Brief (Phase B)

**Status:** awaiting user approval. Nothing here is built; Phase C2 implements this on the static-SPA architecture.

## The design in one paragraph

Scout is a **mission console**: brief a run (target + use case), watch it execute with full transparency (live counters, event stream, and — the centerpiece — an embedded live browser you can see and steer), then debrief over evidence-grade records where every value traces to a source. The UI never expresses an opinion about the data, because Scout never has one (scope-boundary ADR); it expresses *provenance* — citations, confidence, blocked-page evidence — everywhere.

## Artifacts

| File | What |
|---|---|
| `mockup.html` | Clickable mockup — all 7 screens, navigable rail, fake data shaped exactly by the acquisition contracts (`docs/specs/use-cases/`) |
| `screens/01-launcher.png` … `07-settings.png` | Per-screen exports at 1680×1000 |
| `screens/08-results-1280.png` | 1280px verification |
| `../../workspace/scout-redesign/01-design-thinking.md` | Steps 1–6: mental model, tiers, flows, load budget, emotional arc, pre-mortem |
| `../../workspace/scout-redesign/07b-uiux-constraints.md` | Aesthetic choice (theme-dashboard) + SOP constraints |

## The seven screens

1. **Launcher** — use-case cards ARE the product surface: each shows its record-type field chips straight from the contract, products carries a LIVE tag, stubs don't pretend. Quick target bar + recent runs.
2. **Run setup** — contract-driven: a "This run will gather" card lists the exact fields promised by the spec. Mode is a segmented ladder (Auto default); options collapsed; readiness strip.
3. **Live run** — embedded live browser as hero (CDP screencast pane with real URL bar/back/forward, Capture and *Crawl from here* actions), permanent honesty chip about WAF detection, escalation-ladder indicator, live counters, activity ticker. Crawler-only runs swap the pane for the timeline as hero.
4. **Results** — records table whose columns follow the use case's record type (jobs ≠ quotes ≠ products — 7 column presets, 1 component); evidence drawer with verbatim snippet highlighting, proof pills, confidence source; actions: Re-run / Export / Push to Algolia. Blocked runs show evidence + escalation CTAs as the primary content.
5. **History** — persistent (SQLite) runs table, filterable, with Open / Re-run / "Retry in Live Browser" on blocked runs.
6. **Push to Algolia** — dry-run preview is the hero (record diff incl. `_scout` provenance envelope), index + masked keychain credentials, push history. Algolia blue used only here, as destination accent.
7. **Settings** — editable: runs directory, retention, acquisition etiquette (robots/UA/delay/caps — surfaced, not hidden), API + Algolia keys (keychain).

## Aesthetic

`theme-dashboard`: dark console (#09090b), IBM Plex Sans/Mono, glass panels, #0C5CAB primary. Scout's own identity — not Algolia-branded (it feeds Algolia; it isn't Algolia). Distinctive elements: the browser pane with console chrome, the evidence-trace drawer, contract-chip use-case cards.

## What approval covers

- The 7-screen structure and the launcher-first flow (replaces the setup-pane-first layout)
- The embedded browser pane as the live-run hero
- Per-record-type results presets
- The honesty patterns (mock chip, WAF chip, blocked-as-content)
- theme-dashboard aesthetic direction

Changes requested at this gate are cheap; after C2 starts they aren't.
