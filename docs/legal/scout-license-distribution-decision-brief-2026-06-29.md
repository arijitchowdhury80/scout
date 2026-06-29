# Scout License And Distribution Decision Brief

Date: 2026-06-29

Status: **Decision required before public registry publishing.**

This document is not legal advice. It is a product/legal decision brief for the
Scout launch path.

## Executive Recommendation

Recommended path:

1. **Private beta now:** keep Scout distribution controlled through GitHub branch
   install, Docker-from-source, and hosted beta keys. Do not publish to PyPI,
   Docker Hub, or GHCR yet.
2. **Before public launch:** choose **Apache-2.0 for Scout's local/core package**
   unless there is a strong business reason to keep the code proprietary.
3. **Commercial model:** monetize hosted Scout, managed browser capacity,
   enterprise support, integrations, and private deployment help rather than
   charging for the local package.

Why Apache-2.0 is the default recommendation:

- It aligns with Crawl4AI's Apache-2.0 licensing posture.
- It is permissive for commercial users and reduces adoption friction.
- It includes explicit patent language that MIT does not include.
- It supports the intended local-first story: users can run Scout locally,
  inspect it, and trust the acquisition pipeline.
- It keeps hosted Scout differentiated by convenience, metering, managed
  infrastructure, and support rather than by hiding the local utility.

This recommendation does **not** close the gate. Arijit must approve or revise
the license choice.

## Key Upstream License Facts Checked

| Component | Current upstream license signal | Launch implication |
|---|---|---|
| Crawl4AI | Apache License 2.0 | Commercial use is generally compatible if notices/license terms are preserved. No royalty signal found. |
| lxml | BSD-3-Clause | Commercial use is generally compatible if notices are preserved. Security CVE remains separate from license. |
| Playwright Python | Apache License 2.0 | Compatible with commercial distribution if notices/license terms are preserved. Browser binaries may require separate notice review. |
| FastAPI | MIT | Compatible with commercial distribution if notices are preserved. |
| Pydantic | MIT | Compatible with commercial distribution if notices are preserved. |
| Uvicorn | BSD-3-Clause | Compatible with commercial distribution if notices are preserved. |
| Typer | MIT | Compatible with commercial distribution if notices are preserved. |

Primary references:

- Crawl4AI license: https://github.com/unclecode/crawl4ai/blob/main/LICENSE
- lxml license metadata: https://pypi.org/project/lxml/
- lxml license text: https://github.com/lxml/lxml/blob/master/LICENSES.txt
- Playwright Python license: https://github.com/microsoft/playwright-python/blob/main/LICENSE
- FastAPI repository/license: https://github.com/fastapi/fastapi
- Pydantic license: https://github.com/pydantic/pydantic/blob/main/LICENSE
- Uvicorn license: https://github.com/encode/uvicorn/blob/master/LICENSE.md
- Typer license: https://github.com/fastapi/typer/blob/master/LICENSE

## What This Means For Crawl4AI

Current conclusion:

- Using Crawl4AI internally is not blocked by a royalty requirement based on
  the checked Apache-2.0 license signal.
- Selling Scout as a product while using Crawl4AI appears compatible with
  Apache-2.0 obligations if Scout preserves required notices, does not imply
  endorsement, and includes the license/notice posture in distributions.
- The unresolved issue is **not royalty**. The unresolved issues are:
  - preserving notices correctly,
  - avoiding endorsement confusion,
  - handling the current `lxml` CVE in Crawl4AI's dependency path,
  - obtaining real legal review before broad commercial launch.

## License Options For Scout

### Option A: Apache-2.0 open-source core

Release Scout's local/core package under Apache-2.0.

Pros:

- Best match for local-first trust and adoption.
- Strongest alignment with Crawl4AI.
- Easier for companies to approve than a custom source-available license.
- Enables community testing and extensions.
- Hosted business still works through managed infrastructure, support, quotas,
  browser capacity, and enterprise deployment.

Cons:

- Competitors can reuse the code.
- Differentiation must come from product quality, hosted convenience, data
  contracts, integrations, and trust.

Recommended if Scout's core identity is local-first acquisition infrastructure.

### Option B: MIT open-source core

Release Scout under MIT.

Pros:

- Very adoption-friendly.
- Familiar and short.
- Works for commercial users.

Cons:

- Less explicit patent language than Apache-2.0.
- Less aligned with Crawl4AI's own license.

Acceptable, but Apache-2.0 is cleaner for this project.

### Option C: Proprietary / all-rights-reserved public repo

Publish source but no permissive license, or keep repo private and distribute
only managed artifacts.

Pros:

- Maximizes control.
- Avoids easy competitor reuse.

Cons:

- Conflicts with the local-first trust story.
- Makes public GitHub distribution awkward.
- Slows adoption and contribution.
- Users cannot confidently use, modify, or redistribute without explicit terms.

Not recommended for the local/core package if the goal is developer adoption.

### Option D: Source-available beta license

Use a temporary beta license that permits evaluation but restricts commercial
reuse until the final public launch decision.

Pros:

- Gives short-term control during private beta.
- Lets testers see code while preventing accidental broad commercial claims.

Cons:

- Adds legal complexity.
- Less friendly than open source.
- Requires drafting a real license/terms document, not just a README statement.

Possible temporary path, but not ideal as the long-term public posture.

### Option E: Dual license

Open-source core plus commercial terms for hosted, enterprise, support, or
private deployment.

Pros:

- Preserves adoption while keeping a revenue model.
- Common SaaS pattern.

Cons:

- Requires crisp boundaries between open core and paid hosted/service features.
- More legal/packaging work.

Recommended long-term model if Scout grows beyond private beta.

## Distribution Policy Recommendation

Until Arijit approves the license:

- Do not publish to PyPI.
- Do not publish Docker images to Docker Hub or GHCR.
- Do not create broad public release artifacts.
- Continue private beta distribution through:
  - branch-qualified GitHub install,
  - Docker build from source,
  - hosted beta keys for approved testers.

After license approval:

| Surface | Recommended policy |
|---|---|
| Local Python package | Publish to PyPI if Scout is Apache-2.0 or MIT. |
| Docker image | Publish to GHCR first; Docker Hub later if needed. |
| Hosted API | Keep behind paid/free beta keys, quotas, and abuse controls. |
| Skill docs | Ship in package and repo. |
| App UI | Do not market until rebuilt/certified. |

## Required Files After Approval

If Apache-2.0 is approved:

- Add `LICENSE` with Apache-2.0 text.
- Add `license = "Apache-2.0"` or the equivalent SPDX license expression in
  `pyproject.toml`.
- Update README license section.
- Update website legal/third-party page.
- Keep `THIRD_PARTY_NOTICES.md` in wheel and sdist.
- Rebuild package and verify license files are included.
- Implementation runbook:
  `docs/legal/license-implementation-runbook-2026-06-29.md`.
- Verification helper:
  `scripts/license_release_gate_check.py --expected-license Apache-2.0 --dist-dir dist`.

If a proprietary/source-available path is approved:

- Add the chosen license/terms file.
- Add explicit allowed/prohibited beta uses.
- Keep `pyproject.toml` license metadata consistent with that decision.
- Review whether public GitHub visibility still makes sense.

## Decision Needed

Arijit needs to choose one:

- [ ] Approve Apache-2.0 for Scout local/core.
- [ ] Approve MIT for Scout local/core.
- [ ] Keep Scout proprietary/source-available for now.
- [ ] Use a temporary beta license and revisit before public launch.
- [ ] Ask legal counsel before any license expression is added.

## Launch Gate Impact

This brief supports but does not close these release checklist items:

- `License decision recorded`
- `Final license expression added to pyproject.toml`
- `LICENSE file added if Scout is open source or source-available`
- `Registry publishing policy approved`

Public package/container publishing remains blocked until the decision is made.
