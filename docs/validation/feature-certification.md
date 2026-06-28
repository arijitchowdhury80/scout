# Scout Feature Certification

Scout cannot be considered launch-ready because a route returns `success=true`.
Feature certification requires expected-vs-actual evidence for every public
surface: Skill contract, CLI, HTTP API, browser/CDP capture capability,
artifacts, and intelligence modules.

Scout is a utility/service, not a dashboard product. The `/app` route may exist
as a local landing/status page, but a full app UI is no longer part of the
feature certification gate.

## Certification Command

Generate the canonical matrix and report scaffold:

```bash
scout certify-generate --evidence-dir validation-output/current-evidence
scout certify \
  --output-root validation-output \
  --report docs/validation/scout-feature-certification-YYYY-MM-DD.md \
  --evidence validation-output/current-evidence
```

The command writes:

- `validation-output/<timestamp>/feature-results.json`
- `validation-output/<timestamp>/actual-responses/*.json`
- `validation-output/<timestamp>/screenshots/`
- `docs/validation/scout-feature-certification-YYYY-MM-DD.md`

The default report is a scaffold: every scenario starts as `not_run` until a
test runner records actual evidence. A feature is not validated until the
scenario has expected output, actual output, pass/fail reason, and artifact
paths.

## Feature Areas

The matrix covers:

- core modes: scrape, crawl, map, extract, screenshot, products
- intelligence: company, PRISM, investor, careers, jobs, news/blogs, research,
  docs, social, locations, website quality
- browser/CDP capture capability for blocked or user-session pages
- product-to-Algolia path
- CLI, API, run persistence/artifacts, Docker/distribution, docs

## Validation Tiers

| Tier | Scope | Launch Meaning |
|---|---|---|
| L0 | Unit tests, no network | Required for every commit |
| L1 | Deterministic fixtures and local server | Required before claiming feature readiness |
| L2 | Live websites with `SCOUT_LIVE_TESTS=1` | Required before private beta |
| L3 | Manual/user-browser hard-site checks | Required before hard-site claims |

## Acceptance Rules

- Records must match the feature schema and contain meaningful fields.
- Every extracted claim needs source evidence or a validation warning.
- Product records must be Algolia-previewable.
- Zero records pass only with complete blocked/fallback evidence.
- Blocked evidence must include URL, provider attempts when available, reason,
  source evidence, and artifact path.
- The local `/app` page is not a core feature. If present, it should be treated
  as a minimal service/status page, not as a product UI claim.
- Browser/CDP validation must capture real screenshot/DOM/text evidence or
  preserve complete blocked evidence; a placeholder panel is not enough.
- Docs cannot claim stale test counts or unsupported features.

## Required Verification Commands

```bash
python3 -m pytest tests/unit/ -v
python3 tests/validate_endpoints.py --base-url http://127.0.0.1:8421
python3 tests/e2e_real_websites.py
SCOUT_LIVE_TESTS=1 python3 -m pytest tests/live/test_app_live_targets.py -v
python3 -m scout.cli certify-generate --evidence-dir validation-output/current-evidence
python3 -m scout.cli certify --evidence validation-output/current-evidence
python3 -m pyright scout/
ruff check scout/ tests/
ruff format --check scout/ tests/
python3 -m build
docker build -f docker/Dockerfile -t scout:validation .
```

Live and Docker checks may be run as a pre-beta gate rather than on every local
edit, but they must be represented in the final certification report before
Scout is offered to testers.
