# Status Decision Workflow Slice

Status: Complete
Date: 2026-06-29

## Scope

Add the packaged founder decision workflow to the Scout launch status website so the website mirrors the CLI launch workflow:

- inspect readiness blockers,
- generate one or many decision drafts,
- validate completed decision records.

## Checklist

- [x] Read frontend-builder and frontend-design instructions.
- [x] Read available UI/UX constraints index.
- [x] Write design thinking note.
- [x] Add failing website assertion.
- [x] Update status page copy.
- [x] Run focused and full verification.
- [x] Browser-render `/status` at desktop and mobile.
- [x] Commit and push.

## Verification

- `python3 -m pytest tests/unit/website/test_launch_website.py -q` -> 11
  passed, 2 warnings.
- `python3 -m pytest tests/unit/test_launch_governance_docs.py -q` -> 25
  passed.
- `python3 scripts/launch_readiness_check.py --json` summary ->
  `ready_with_limits blocked 14 14`.
- Browser render check through `python3 -m scout.cli serve --host 127.0.0.1
  --port 8767` passed for `/status` at 1440x1000 and 390x844, with no console
  messages. Screenshots were written to ignored local output under
  `validation-output/status-decision-workflow/`.
