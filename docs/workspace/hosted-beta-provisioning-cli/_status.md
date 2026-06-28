# Hosted Beta Provisioning CLI Status

Status: Verified checkpoint
Date: 2026-06-28

## Goal

Add an operator/admin CLI command that provisions a hosted beta account into the
hosted account SQLite store and prints the raw `scout_live_...` key exactly
once.

## Completed

- [x] Strategy and PRD written.
- [x] RED CLI tests written and observed failing.
- [x] CLI command implemented.
- [x] Verification run.
- [x] Hosted readiness docs updated.

## Boundary

This is not self-serve signup and not Stripe. It is the minimum safe beta
operator path for issuing keys while the hosted dashboard/payment flow remains
under construction.

## TDD Evidence

RED:

```bash
python3 -m pytest tests/unit/cli/test_run_commands.py -q -k "hosted_provision"
```

Result: failed with Typer exit code `2` because `hosted-provision` did not
exist.

GREEN:

```bash
python3 -m pytest tests/unit/cli/test_run_commands.py -q -k "hosted_provision"
```

Result: `2 passed, 13 deselected, 2 warnings`.

## Final Verification

```bash
python3 -m pytest tests/unit/cli/test_run_commands.py -q
```

Result: `15 passed, 8 warnings`.

```bash
python3 -m pytest tests/unit/ -q
```

Result: `449 passed, 8 warnings`.

```bash
python3 -m pyright scout/
```

Result: `0 errors, 0 warnings, 0 informations`.

```bash
ruff check scout/ tests/
ruff format --check scout/ tests/
```

Result: `All checks passed!` and `188 files already formatted`.
