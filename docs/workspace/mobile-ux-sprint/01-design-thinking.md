# Mobile UX Sprint - Design Thinking

Date: 2026-07-09

## 1. Mental Model

Mobile visitors are not arriving to operate a developer console. They are
asking, "What does this do, and should I get a key?" The desktop console is a
credible proof object, but on phone it becomes a dense artifact that blocks
understanding.

Mobile mental model: short product explanation, proof snapshot, clear test
examples, one primary CTA.

## 2. Information Architecture

Hero:

- Scout identity.
- One-sentence outcome.
- Get API key CTA.

Primary:

- Three-step mobile proof: paste URL, Scout extracts, inspect evidence.
- Compact examples of what to test.
- API key CTA.

Secondary:

- Video proof.
- Records/proof/exports cards.
- Pricing/docs links.

Supporting:

- Footer/legal links.
- Endpoint labels.
- Credit details.

Tier inflation risk: the desktop console, capability grid, and walkthrough all
try to be primary on mobile. They must be hidden or compressed.

## 3. Interaction Flow

Common mobile actions:

1. Tap "Get API key".
2. Watch or scrub the demo video.
3. Tap Pricing or Docs if they need context.

Happy path:

1. Read the outcome.
2. See the 3-step proof.
3. See concrete beta test examples.
4. Tap "Get API key".

## 4. Cognitive Load Budget

Baseline phone first page shows header, CTA, nav, hero, lede, console tabs, URL
form, code output, evidence panel, and console CTA: more than 10 chunks.

Target phone first two screens:

- Header.
- Hero.
- Proof card.
- Test examples.
- CTA.

## 5. Emotional Journey

The phone experience should feel calmer and more intentional:

- First view: "I understand what Scout does."
- Proof section: "This is real, not marketing fluff."
- Examples: "I know what to test."
- CTA: "Getting a key is low-risk."

## 6. Design Pre-Mortem

Risks:

- The mobile page becomes too stripped down and loses the premium feel.
  Mitigation: reuse Scout's mint neumorphic cards and dark evidence screen.
- Hiding the console feels like removing functionality.
  Mitigation: say "full live console works best on tablet/desktop" only inside
  a compact mobile proof card, not as a blocker.
- Touch targets remain too small.
  Mitigation: set min-height rules for nav links, tabs, inputs, buttons, and
  footer links.
- Tablet gets caught between mobile and desktop.
  Mitigation: keep tablet console active but improve touch target sizing.
