# History, Presets, And Targets Workflow

## User Intent

Let users reuse previous runs, standard templates, and approved validation
targets without retyping configuration.

## Required Inputs

- History: existing run ID or selected row.
- Presets: saved template.
- Targets: company/URL from balanced validation matrix.

## Run States

- History rows reopen completed/failed/cancelled runs in Results Review.
- Presets populate Run Setup without starting execution.
- Targets populate Run Setup with use case, URL, and recommended mode.

## Result Tabs

These screens are utility screens. Selecting a run returns to the shared run
workspace and its normal result tabs.

## Right Drawer

History and targets can use the drawer for run metadata, target notes, and
artifact links.

## Empty, Error, And Blocked States

Empty history, no presets, or no targets must be visible empty states, not blank
screens. Broken artifact links must show a clear missing-file warning.

## Expected Artifacts

No new run artifacts until a user starts a run. History reads existing app-run
state and run artifact paths.

## Controls

Open run, clear run from history, load preset, save preset, delete preset,
select target, filter target matrix, and start from selected template.
