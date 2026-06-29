# Status Decision Workflow Design Thinking

## Mental Model

The user model is a launch status report with executable next steps. They expect plain status, blocker ownership, and commands that can be copied into a terminal. A decorative or app-like treatment would confuse the page because the job is launch governance, not product exploration.

## Information Architecture

Hero: existing page headline, unchanged.

Primary: current readiness verdict, owner summary, blocker summary, executable evidence.

Secondary: decision workflow commands. These belong near executable evidence because they are actions after blocker inspection.

Supporting: command examples, notes about drafts not counting as approval evidence.

## Interaction Flow

Common actions:

1. Run `scout launch-readiness`.
2. Generate the founder/shared decision draft packet.
3. Validate completed decision records.

Happy path:

1. Review public launch blockers on `/status`.
2. Copy the bulk draft command.
3. Edit drafts into completed decision records.
4. Run `scout launch-decision-check --check-existing`.

Empty/error states are command-line concerns; the status page only documents expected commands and failure semantics.

## Cognitive Load Budget

Existing status page already has multiple cards. This slice adds one compact section with one code block and two explanatory cards. It does not add a new navigation surface.

## Emotional Journey

The page should move from sober constraint to operational confidence: public launch is blocked, but the next actions are precise and executable.

## Design Pre-Mortem

Risk: page becomes a wall of commands.
Mitigation: keep one concise workflow section and use the existing `note-grid` pattern.

Risk: user interprets drafts as approval.
Mitigation: explicitly state drafts are not completed launch evidence until reviewed and validated.

Risk: visual drift from the warm industrial launch site.
Mitigation: reuse existing section, label, pre, note-grid, and card styles.
