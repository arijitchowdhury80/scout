# Flux Design System — v1.0

A bold, high-contrast editorial design system for B2C SaaS. Aggressive display
typography paired with a clean sans body, a single golden-yellow accent, and
brutalist-lite structure.

---

## What's in this package

```
flux-design-system/
├── README.md                  ← you are here
├── tokens.css                 ← design tokens (CSS vars) + primitive component classes
├── fonts.css                  ← font @imports (Anton, Satoshi, JetBrains Mono)
├── guide/
│   └── Flux Design System.html   ← visual style guide (open in a browser)
└── examples/
    └── Flux Landing.html         ← full example landing page built on the system
```

Open either `.html` file directly in a browser — no build step.

---

## Quick start

```html
<head>
  <link rel="stylesheet" href="fonts.css">
  <link rel="stylesheet" href="tokens.css">
</head>
<body>
  <h1 class="flux-display" style="font-size: 96px;">
    Turn ideas into products people
    <span class="flux-highlight">love</span>
  </h1>
  <button class="flux-btn">Join waitlist</button>
</body>
```

---

## Foundations

### Color
| Token | Hex | Role |
|---|---|---|
| `--flux-yellow` | `#FFE17C` | Primary accent · CTAs · highlights |
| `--flux-charcoal` | `#171E19` | Ink · dark surfaces |
| `--flux-dark-gray` | `#272727` | Secondary dark surface |
| `--flux-sage` | `#B7C6C2` | Muted text on dark · borders |
| `--flux-offwhite` | `#F8F9FA` | Light card surface |
| `--flux-white` | `#FFFFFF` | Base background |

Borders: `rgba(23,30,25,.10)` on light sections, `rgba(183,198,194,.10)` on dark.

### Typography
- **Anton** — all headlines, numerals, logo. Uppercase, weight 400, line-height 0.9, normal tracking.
- **Satoshi** — all body, labels, UI text. Weights 400 / 500 / 700.
- **JetBrains Mono** — code snippets and hex labels.

Never set body copy in Anton; never set headlines in Satoshi.

### Motion
- Easing `cubic-bezier(0.4, 0, 0.2, 1)`, duration **300ms** for card transforms & shadows.
- Cards lift `translateY(-6px)` on hover; CTAs scale `1.05` on the final band.

### Radius ladder
`10` (inputs/buttons) · `14` (panels) · `16` (cards) · `999` (pills/badges).

### Grid background
`40px × 40px` linear-gradient grid in sage at ~20–32% opacity — `.flux-grid-bg`.

---

## Component classes (tokens.css)

`.flux-display` · `.flux-eyebrow` · `.flux-btn` (`--dark`) · `.flux-pill` ·
`.flux-input` · `.flux-card` (`--dark`) · `.flux-badge` · `.flux-grid-bg` ·
`.flux-highlight`

See `guide/Flux Design System.html` for live examples of every token and component.

---

© 2026 Flux Labs. Fonts: Anton (OFL), Satoshi (Fontshare license), JetBrains Mono (OFL).
