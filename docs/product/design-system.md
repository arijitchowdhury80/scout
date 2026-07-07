# Scout Design System — LOCKED 2026-07-06

The canonical spec for the site + app rebuild. Feeds the Fable5 build prompt. Language and logo are
locked; screens are being built to this. Style = **premium mint neumorphism, demo-first (E) IA**.

## Logo (locked)
- **Wordmark:** "Scout", weight 800, letter-spacing ≈ -0.04em, color forest `#143C2B`, subtle emboss
  (`text-shadow: 0 1px 0 rgba(255,255,255,.7)`). The **"o" is a full reticle** (target): outer ring +
  4 crosshair ticks breaking the ring + an **amber `#C77A1E` center dot** (the verified hit). The
  reticle is baseline-seated and x-height sized so it reads as a true lowercase o.
- **Favicon / avatar / app badge = the reticle alone.** No separate mark.
- Reticle SVG (viewBox 0 0 40 40): `<circle cx=20 cy=20 r=15 stroke=#143C2B sw=4 fill=none>` + 4 ticks
  N/E/S/W (`20,1.5→20,9` etc., sw=4 round) + `<circle cx=20 cy=20 r=4.2 fill=#C77A1E>`.
- Meaning: Scout scans/locates a target; the amber core = evidence/verified. Ties name → promise.

## Color tokens
| Token | Hex | Use |
|---|---|---|
| `--bg` | `#E6EFEA` | mint page surface (everything molded from this) |
| `--fg` | `#26302A` | primary text (WCAG AA on bg) |
| `--mut` | `#566259` | secondary text |
| `--acc` | `#0E8A61` | emerald — inline accents, tags, labels, active states |
| `--accd` | `#143C2B` | dark forest — filled primary buttons, wordmark |
| `--onacc` | `#E9F2EC` | text on forest fills |
| `--amber` / `--amber2` | `#C77A1E` / `#E0912F` | **RESERVED for evidence only** — verified ✓, citation |
| dark screen | `#141D18` bg, `#1C271F` panel, `#EAF2ED` fg, `#7BD4AC` syntax | the crisp data display |
| verified (on dark) | `#47DBA0` | verified ✓ inside the dark screen |

**Accent rule:** green is the working accent (forest fills + emerald inline). Amber appears ONLY on
evidence marks (verified, citation) — the one warm spark, marking Scout's differentiator.

## Neumorphic shadow tokens (the physics)
- `--ex` (extruded): `7px 7px 15px rgba(158,184,171,.7), -7px -7px 15px rgba(255,255,255,.9)`
- `--exs` (small): `4px 4px 9px rgba(158,184,171,.62), -4px -4px 9px rgba(255,255,255,.82)`
- `--in` (inset): `inset 5px 5px 10px rgba(158,184,171,.7), inset -5px -5px 10px rgba(255,255,255,.7)`
- `--ind` (deep inset, for input wells + framing the dark screen): `inset 8px 8px 16px rgba(158,184,171,.78), inset -8px -8px 16px rgba(255,255,255,.78)`
- Hover = lift (`translateY(-2px)` + deeper `--exh`); active = press (`translateY(1px)` + `--in`).
- Contrast is SHARPENED vs default neumorphism (deeper dark shadow, darker text) for legibility + WCAG.

## The crisp-screen rule (non-negotiable)
All code / JSON / records / tables render on a **crisp dark screen** (`#141D18`) set INTO the soft body
via `--ind` framing — "soft ceramic device, sharp display." Neumorphism never touches the data itself;
it only wraps it. This is what keeps a soft aesthetic legible for a dev tool.

## Voice — speak human (Arijit's rule, 2026-07-06)
Public copy talks to PEOPLE, not engineers. Every sentence must survive: "would a smart person who
doesn't live in this jargon get it in one read?"
- Say what it does FOR them, not what it is technically. "Clean, usable data" not "typed data";
  "shows you where every piece came from, so you can trust it" not "source, hash, and proof attached".
- Banned in headlines/subheads: hash, typed, JSON/JSONL, Pydantic, endpoint, self-hosted, Crawl4AI,
  "no black box", schema, dedup. These live in docs/API reference and the small trust strip only.
- **No em dashes (—) anywhere customer-facing** — standing rule; use a period or comma. Guarded by
  test_no_em_dashes_in_customer_facing_copy + test_delivery_email_has_no_em_dashes.
- Mechanism words (citation, verified, evidence) are OK when the sentence explains the benefit.
- Tech credibility (Crawl4AI, architecture) = footer/trust-strip/docs garnish, never the hero.
- Applies to: website pages, the key-delivery email, docs landing pages, in-app copy.

## Typography
- Font: system stack (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`); mono =
  `ui-monospace, "SF Mono", Menlo` for endpoints, data, labels. (Fable5 may swap in Plus Jakarta Sans
  / DM Sans via proper @font-face at build — system stack is the CSP-safe stand-in.)
- Sentence case everywhere. Headlines 800 weight, tight tracking. Labels: mono, uppercase, tracked.

## Components
- **Buttons:** radius 12–16px. Primary = forest `--accd` fill + `--onacc` text + `--ex`. Secondary =
  soft `--bg` + `--exs`. Tabs: pressed (`--in`) = active, emerald text.
- **Cards:** radius 22–32px, `--bg`, `--ex` (or `--exs` for minor). Icon wells = `--ind` (drilled-in).
- **Inputs:** `--ind` well, radius 12–14px.
- **Dark data-screen:** see rule above; tab row (Preview/JSON/JSONL/Table-CSV/cURL), evidence panel,
  footer (status + save + destinations).
- **Tables:** on the dark screen; hairline `#28332B` rows; amber citation column; emerald/`#47DBA0` ✓.

## IA + PLG (locked)
Homepage = live demo console (E IA). Funnel: anonymous taste (scrape+map, 5 runs/IP/day, preview only)
→ free 10k signup (all endpoints, download, save) → paid (Destinations). App shell: sidebar
(Playground / Your runs / Destinations / API keys / Usage / Docs) + credit meter. Results render
INLINE (tabs + evidence panel); Download ▾ (JSON/JSONL/CSV/MD); Save → RunDB "Your runs"; Algolia +
webhook live in **Destinations** (authed only, after a run — never on the GTM homepage). See
[[plg-playground-ux]].

## Reference screens (built in this language)
Home (console hero) ✅ · App playground-result ✅ · Pricing · Product (overview + per-capability) ·
Docs (Mintlify) · Account/Destinations-connect. These become the pattern library Fable5 fans out from.
