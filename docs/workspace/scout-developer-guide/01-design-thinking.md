# Scout Developer Guide Design Thinking

## Mental Model

The user is carrying a "developer guide" mental model: they want one page that tells them which Scout surface to use, how to authenticate, how to run local versus hosted, and where artifacts appear. Swagger answers endpoint shapes; this guide answers operating judgment.

## Information Architecture

| Content | Tier | Treatment |
|---|---|---|
| "Scout Developer Guide" headline | Hero | Large page headline |
| Surface chooser: local CLI, local HTTP, hosted API, skill | Primary | Four-card grid |
| Auth and workdir rules | Primary | Step sections with code |
| Artifact contract and citations | Primary | File list and evidence explanation |
| Hosted limits and boundaries | Primary | Caution block |
| Swagger link | Secondary | Clear link to `/docs` |
| Navigation/footer | Supporting | Existing launch-site nav |

No tier inflation: endpoint examples remain inside code blocks; public launch caveats stay explicit.

## Interaction Flow

Most common actions:

1. Choose local, hosted, or skill usage.
2. Copy the relevant command or curl shape.
3. Open Swagger only when they need exact schemas.

Happy path:

1. Visitor opens `/guide`.
2. Visitor chooses "Local HTTP" or "Hosted API."
3. Visitor follows the auth/workdir section.
4. Visitor inspects the artifact contract.

States:

- Empty/loading/error states are not dynamic because this is a static guide.
- Route failure is covered by API tests.

## Cognitive Load Budget

Visible chunks:

1. Hero.
2. Surface chooser.
3. Auth/workdir.
4. Artifact contract.
5. Boundaries/Swagger.

The page is intentionally five chunks and avoids introducing a docs app.

## Emotional Journey

The guide should reduce anxiety: "I understand how to try Scout without accidentally treating hosted beta as unlimited production infrastructure." It should feel useful before the reader opens Swagger.

## Design Pre-Mortem

- Risk: duplicates README. Mitigation: focus on decision and operation flow, not exhaustive reference.
- Risk: competes with `/docs`. Mitigation: explicitly say `/docs` remains Swagger API docs.
- Risk: overclaims hosted readiness. Mitigation: repeat finite hosted beta and public launch blocked boundaries.
- Risk: page gets too dense on mobile. Mitigation: reuse stacked cards and scrollable code blocks.

## Aesthetic Choice

Use the existing Supadesign IndustrialGray launch-site aesthetic. This is a product docs extension, not a new design system.

