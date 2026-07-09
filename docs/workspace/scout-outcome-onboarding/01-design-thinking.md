# Scout Outcome Onboarding Design Thinking

## Mental Model

First-time beta testers arrive with a consumer-app question: "What do I get if I use this?" Scout's current page answers the builder question: "What API primitives exist?" The draft should bridge those models without repositioning Scout as a consumer search tool.

Expected: a simple explanation of input, action, output, and examples. Confusing: more endpoint names before the user understands the outcome.

## Information Architecture

Hero: existing "Point Scout at any URL. Watch it return a citable record." remains the homepage thesis.

Primary:
- Outcome bridge: URL in, clean reusable data out.
- Video walkthrough frame: "Watch a URL become a citable record."
- Beta tester prompt: pick a real website and judge accuracy, usefulness, and reuse.

Secondary:
- Example use cases: pricing page, product page, company website, docs page, messy article.
- Output types: clean content, product/company data, site map, screenshots, source evidence.

Supporting:
- HTTP + Claude/Codex skill notes.
- 5,000 credits / 30 days / no card.
- Support email.

## Interaction Flow

Common actions:
1. Understand the product in one scan.
2. Watch the short demo or read its frame if the video is not ready.
3. Get an API key and test one real URL.

Happy path:
1. Read the outcome bridge.
2. See the demo frame that maps paste URL -> select primitive -> inspect evidence.
3. Sign up.
4. Test one known website and report whether output is accurate/useful/reusable.

Empty/loading/error states are not new in this draft. The form keeps existing status behavior.

## Cognitive Load Budget

Homepage first viewport remains hero + console. The new bridge must be a single section with 3 chunks: outcome, demo frame, tester checklist. The beta page gets one guided section before the form. Avoid adding more than five visible chunks in either area.

## Emotional Journey

Before: "This looks technical; what is the outcome?"

After: "I paste a URL, Scout gives me reusable data with proof, and I know exactly how to test it."

The emotional weight should sit in a clear video frame and concrete examples, not loud marketing claims.

## Design Pre-Mortem

Tiger: generic AI explainer section.
Mitigation: use Scout's existing console, tabs, evidence panel, and token system.

Tiger: premium feel lost through too much explanatory copy.
Mitigation: keep copy short, use neumorphic wells and dark screen, avoid tutorial clutter.

Tiger: video not ready yet.
Mitigation: ship a premium placeholder frame with the final intended script beats, and make it replaceable by a real video later.

Tiger: mobile overflow.
Mitigation: use existing responsive grid classes plus new wrappers that collapse to one column at mobile widths.

Elephant: non-technical feedback may keep coming.
Mitigation: beta page tells testers exactly how to test and what kind of feedback is useful.

