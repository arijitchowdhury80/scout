# Warm Industrial — Design System

An industrial-chic system: structural grids, warm-gray surfaces, high-impact
editorial typography, and technical "readout" accents. A constant subtle noise
overlay gives the digital UI a tactile, analog feel.

```
warm-industrial-design-system/
├─ warm-industrial.css   ← the kit: tokens + components (drop-in)
├─ index.html            ← visual reference / documentation page
└─ README.md             ← you are here
```

## Quick start

```html
<link rel="stylesheet" href="warm-industrial.css">
<body class="wi">
  <!-- fixed background layers -->
  <div class="wi-grid-bg"><div class="wi-grid-bg__inner">
    <!-- 12 × <div class="wi-grid-bg__col"></div> -->
  </div></div>
  <div class="wi-noise"></div>

  <h1 class="wi-display wi-stroke">STRUCTURE</h1>
  <a class="wi-btn">Start <span class="wi-btn__arrow">↗</span></a>
</body>
```

Put your real content inside a `position:relative; z-index:1` wrapper so it sits
above the grid + noise layers.

## Tokens (CSS variables)

| Token | Value | Use |
|---|---|---|
| `--wi-bg` | `#EBEBE8` | Warm canvas — keep everywhere |
| `--wi-surface` | `#F4F4F5` | Raised bands / marquee |
| `--wi-fg` | `#18181B` | Foreground ink + footer |
| `--wi-accent` | `#BC8A2E` | Amber/ochre accent (categories, ticks, stars) |
| `--wi-accent-blue` | `#0066FF` | Alt accent from the original text spec |
| `--wi-border` | `#D4D4D8` | 1px hairlines |
| `--wi-muted` | `#71717A` | Secondary text |
| `--wi-green` | `#22C55E` | Live / operational pulse |
| `--wi-ease` | `cubic-bezier(.16,1,.3,1)` | All transforms / clip-paths |

> **Note on the accent.** The written brief specified `#0066FF` (blue), but the
> approved visual reference uses a warm amber `#BC8A2E`. The kit ships amber as
> the default `--wi-accent` and keeps blue available as `--wi-accent-blue`.
> Re-point one line in `:root` to switch.

## Components / utilities

- **Type** — `.wi-display` `.wi-h1` `.wi-h2` `.wi-h3` `.wi-body` `.wi-serif` (Playfair italic) `.wi-mono`
- **Stroke text** — `.wi-stroke` / `.wi-stroke--thin` (outline-only display type)
- **Labels** — `.wi-label` (10px bold uppercase, 0.25em) · `.wi-label--accent` · `.wi-readout` (mono)
- **Buttons** — `.wi-btn` (sharp, rotating `.wi-btn__arrow`) · `.wi-btn--ghost` · `.wi-pill` (rounded CTA)
- **Status** — `.wi-status` + `.wi-pulse` (green live indicator) · `.wi-badge` / `.wi-badge--accent`
- **Cards** — `.wi-card` (sharp) · `.wi-card--glass` (glassmorphism overlay)
- **Layout** — `.wi-container` · `.wi-12` · `.wi-divider` · `.wi-dark` · `.wi-grid-bg` · `.wi-noise`
- **Header / logo** — `.wi-header` (sticky, blur) · `.wi-logo` (`__serif` + `__sans`)
- **Marquee** — `.wi-marquee` + `.wi-marquee__track` (duplicate children for seamless loop)
- **Project row** — `.wi-proj` `.wi-proj__meta` `.wi-proj__cat` `.wi-proj__title` `.wi-tag`
- **Clip reveal** — `.wi-reveal-row` + `.wi-reveal` (image revealed right→left on hover) + `.wi-view-disc` (dark View disc pinned right)
- **Scroll-in** — `.wi-fade` → toggle `.is-in` with the IntersectionObserver snippet below

### Scroll-in reveal snippet

```js
const io = new IntersectionObserver(es => es.forEach(e => {
  if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
}), { threshold: .12, rootMargin: '0px 0px -8% 0px' });
document.querySelectorAll('.wi-fade').forEach(el => io.observe(el));
```

## Rules

- **MUST** keep `#EBEBE8` as the background throughout. The only near-black
  surface is the footer (`.wi-dark`).
- **MUST** align text and boxes to the 12-column grid.
- **MUST** keep the noise overlay visible but subtle (`opacity:0.045`).
- **DO NOT** use rounded corners anywhere except `.wi-btn`, `.wi-pill`, badges
  and the status pulse. Everything else stays sharp and rectangular.

## Fonts

Inter (400/700/900) and Playfair Display (italic 400) load from Google Fonts via
`@import` at the top of `warm-industrial.css`. Mono falls back to JetBrains Mono
→ system mono.

v1.0 · 2026
