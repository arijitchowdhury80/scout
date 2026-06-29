# Scout Launch Homepage Design Thinking

## 1. Mental Model

The visitor is not looking for an app dashboard. They are evaluating a
developer utility/service:

- Can I install it locally?
- What does it produce?
- When would I use hosted Scout?
- What are the limits and risks?

What would confuse them:

- Screenshots of the unfinished legacy `/app` UI.
- A vague "AI crawler" hero.
- A `Get API key` CTA before the hosted tenancy/payment flow is fully public.
- A `$22` offer that feels like unlimited lifetime infrastructure.

Dominant mental model: infrastructure field manual plus developer quickstart.

## 2. Information Architecture

Hero:

- One headline: "Turn messy web pages into citable, downstream-ready records."

Primary:

- Install locally.
- Join hosted beta.
- Operating model readout: Local free / Hosted finite credits / Artifact-owned.

Secondary:

- Evidence ledger.
- Acquisition ladder.
- Artifact contract.
- Export destinations.
- Launch status.

Supporting:

- Private beta status.
- CLI/HTTP/Docker/Skill labels.
- Legal/security caveats.
- Footer links.

Tier inflation risk: launch blockers and pricing warnings should be visible but
not visually louder than the main utility value.

## 3. Interaction Flow

Three most common actions:

1. Install locally from quickstart.
2. Inspect pricing/hosted beta limits.
3. Read docs/API reference.

Happy path:

1. Visitor lands on homepage.
2. Sees local-first operating model.
3. Opens Quickstart or Beta.
4. Runs local Scout or requests hosted beta.

Empty/loading/error:

- Hosted checkout form already has loading/error status.
- Homepage itself is static and should never depend on live data to explain
  Scout.

## 4. Cognitive Load Budget

First viewport should stay under five visible chunks:

1. Header.
2. Hero copy.
3. Primary CTAs.
4. Evidence ledger.
5. Operating-model readout.

Reduction strategy: the detailed product sections remain below the fold. The
new readout is compact and factual rather than another large card grid.

## 5. Emotional Journey

- Arrival: "This is serious infrastructure, not a toy app."
- Hero: "I understand the job: pages to records with proof."
- Operating model: "I know what is free, what is paid, and what is limited."
- Evidence sections: "I can trust and inspect the output."
- Launch status: "The limits are honest."

## 6. Design Pre-Mortem

Tigers:

- Generic AI crawler positioning. Mitigation: lead with evidence/artifact
  language, not magic.
- Website accidentally sells the broken app UI. Mitigation: use no `/app`
  screenshots or CTA.
- Hosted beta appears unlimited. Mitigation: top-level finite-credit readout.
- Mobile overflow. Mitigation: make the readout stack under 720px and avoid
  long unbreakable labels.
- Accessibility. Mitigation: use semantic sections, visible focus states, and
  readable text contrast.

Elephants:

- Public launch is blocked. Mitigation: keep launch status and readiness
  boundaries visible.
- Pricing still needs Arijit approval for public launch. Mitigation: call hosted
  pricing a private beta pass only.
