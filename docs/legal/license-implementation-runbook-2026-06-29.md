# Scout License Implementation Runbook

Date: 2026-06-29
Status: Apache-2.0 implemented; verification required on every release artifact

## Purpose

This runbook records the implemented Apache-2.0 license path and the recurring
release verification steps.

Current recommendation remains Apache-2.0 for the local/core package, with
hosted/service monetization kept separate.

## Preconditions

The license decision is recorded in
`docs/product/founder-decision-records/2026-06-29-apache-2-license.md`.
Before each release, rerun the verification steps below against fresh artifacts.

- Apache-2.0 approved,
- MIT approved,
- source-available/proprietary path approved,
- legal counsel requires another path.

## Apache-2.0 Implementation Steps

Apache-2.0 implemented:

1. Add `LICENSE` with Apache License 2.0 text.
2. Add the final SPDX expression to `pyproject.toml`:

   ```toml
   license = "Apache-2.0"
   ```

3. Update README license section.
4. Update `website/legal.html`.
5. Keep `THIRD_PARTY_NOTICES.md` included in wheel and sdist.
6. Rebuild distribution artifacts:

   ```bash
   rm -rf dist
   python3 -m build
   ```

7. Run the license gate:

   ```bash
   python3 scripts/license_release_gate_check.py \
     --expected-license Apache-2.0 \
     --dist-dir dist
   ```

8. Run focused package/legal tests:

   ```bash
   python3 -m pytest \
     tests/unit/test_package_metadata.py \
     tests/unit/test_legal_license_inventory.py \
     tests/unit/test_launch_governance_docs.py \
     -q
   ```

## Alternate License Path

If MIT, source-available, proprietary, beta-only, or dual-license is approved:

- update this runbook with the exact expected license expression,
- add the selected license or terms file,
- keep package metadata consistent with the selected legal posture,
- rerun `scripts/license_release_gate_check.py` with the selected expected
  expression only if the package metadata is meant to expose a single SPDX
  expression.

## Current Closure

These gates are closed in the release-hardening pass:

- `License decision recorded`,
- `Final license expression added to pyproject.toml`,
- `LICENSE file added if Scout is open source or source-available`.

These gates remain open:

- public package/container publishing remains blocked.
