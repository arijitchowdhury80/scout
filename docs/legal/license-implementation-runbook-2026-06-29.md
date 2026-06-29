# Scout License Implementation Runbook

Date: 2026-06-29
Status: Prepared; waiting for license decision

## Purpose

This runbook makes the license gate executable after Arijit chooses Scout's
license path. It does not choose or apply a license.

Current recommendation remains Apache-2.0 for the local/core package, with
hosted/service monetization kept separate.

## Preconditions

Do not run this as a completion checklist until one of these decisions is
recorded:

- Apache-2.0 approved,
- MIT approved,
- source-available/proprietary path approved,
- legal counsel requires another path.

## Apache-2.0 Implementation Steps

If Apache-2.0 is approved:

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

## Non-Closure

Until this runbook is executed against the approved license and built artifacts:

- `License decision recorded` remains open,
- `Final license expression added to pyproject.toml` remains open,
- `LICENSE file added if Scout is open source or source-available` remains open,
- public package/container publishing remains blocked.
