# Build Log - Scout Product Launch Checkpoint

Date: 2026-06-28
Status: Checkpoint verified, not product-launch complete

## Scope Built

- Competitor website research baseline under `docs/competetor-website-knowledge/`.
- Scout private-beta website foundation under `website/`, using the
  Supadesign IndustrialGray design system.
- Generic product export adapters for JSON, JSONL, CSV, and SQLite.
- CLI command `scout product-export`.
- Hosted-readiness primitives:
  - API key generation, hashing, masking, and usability checks.
  - Hosted plan and credit policy definitions.
  - Hosted URL safety / SSRF validation helpers.
- Workspace planning docs for hosted readiness, launch website, and product
  export adapters.

## Verification Run

Commands run from `/Users/arijitchowdhury/Dropbox/AI-Development/Scout`.

```bash
python3 -m pytest tests/unit/core/platform tests/unit/core/products tests/unit/cli/test_run_commands.py -q
```

Result: `116 passed, 8 warnings`.

```bash
python3 -m pytest tests/unit/ -q
```

Result: `428 passed, 8 warnings`.

```bash
python3 -m pyright scout/
```

Result: `0 errors, 0 warnings, 0 informations`.

```bash
ruff check scout/ tests/
ruff format --check scout/ tests/
```

Result: `All checks passed!` and `180 files already formatted`.

```bash
python3 -m http.server 8766 --directory website
```

Then a Python Playwright Chromium check validated:

- desktop viewport `1440x1000`
- mobile viewport `390x844`
- hero heading visible
- `#why`, `#evidence`, `#pricing`, `#quickstart`, and `#beta` sections present
- 14 links present
- no browser console messages

Screenshots were written to ignored local output:

- `validation-output/website-scout-launch/desktop.png`
- `validation-output/website-scout-launch/mobile.png`

## Not Complete Yet

This checkpoint does not finish the full launch objective. Remaining work:

- Hosted multi-tenant persistence and API-key management endpoints.
- Hosted quota middleware, Stripe checkout, and webhook handling.
- Deployment architecture and infrastructure.
- Local distribution package validation across install paths.
- Full product website beyond one static landing page.
- Current competitor/pricing research refresh before public launch.
- Legal/license review for Crawl4AI attribution and distribution posture.
- Broader live feature certification before making public product claims.

## Follow-Up Checkpoint - Hosted Account Service

Date: 2026-06-28

Built:

- `scout.core.platform.account_service`
- `HostedTenantRecord`
- `HostedAccountStatus`
- `HostedProvisioningResult`
- `HostedAccountDecision`
- `InMemoryHostedAccountStore`
- `HostedAccountService`

Behavior:

- provisions hosted tenants for hosted-enabled plans only,
- generates one-time raw API keys while storing only hashes,
- seeds standard and browser credits from the selected hosted plan,
- authenticates keys by hash and required scope,
- rejects revoked keys,
- debits standard and browser credit buckets separately,
- denies insufficient-credit actions without mutating balances.

TDD:

- RED: `python3 -m pytest tests/unit/core/platform/test_account_service.py -q`
  failed with missing `scout.core.platform.account_service`.
- GREEN: same command passed with `6 passed`.

Verification:

- `python3 -m pytest tests/unit/core/platform -q` -> `59 passed`.
- `python3 -m pytest tests/unit/ -q` -> `434 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/` -> `All checks passed!`.
- `ruff format --check scout/ tests/` -> `182 files already formatted`.

## Follow-Up Checkpoint - Hosted Admission Service

Date: 2026-06-28

Built:

- `scout.core.platform.hosted_admission`
- `HostedAdmissionDecision`
- `HostedAdmissionService`

Behavior:

- authenticates API key and scope before URL safety checks,
- rejects unknown/wrong-scope keys without leaking URL safety details,
- validates hosted URLs and resolved IPs before any credit debit,
- denies unsafe URLs without mutating balances,
- debits credits only after auth and URL safety pass,
- preserves URL safety and usage decisions for future API error responses.

TDD:

- RED: `python3 -m pytest tests/unit/core/platform/test_hosted_admission.py -q`
  failed with missing `scout.core.platform.hosted_admission`.
- GREEN: same command passed with `6 passed`.

Verification:

- `python3 -m pytest tests/unit/ -q` -> `440 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/` -> `All checks passed!`.
- `ruff format --check scout/ tests/` -> `184 files already formatted`.

## Follow-Up Checkpoint - Hosted Account Persistence

Date: 2026-06-28

Built:

- `scout.core.platform.account_sqlite_store`
- `SQLiteHostedAccountStore`

Behavior:

- persists hosted tenants,
- persists API-key metadata and scopes without storing raw API keys,
- persists standard and browser credit balances,
- supports lookup by key hash,
- supports persisted key revocation,
- preserves credit debits across fresh service instances.

TDD:

- RED: `python3 -m pytest tests/unit/core/platform/test_account_sqlite_store.py -q`
  failed with missing `scout.core.platform.account_sqlite_store`.
- GREEN: same command passed with `3 passed`.

Verification:

- `python3 -m pytest tests/unit/core/platform -q` -> `68 passed`.
- `python3 -m pytest tests/unit/ -q` -> `443 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/` -> `All checks passed!`.
- `ruff format --check scout/ tests/` -> `186 files already formatted`.

## Follow-Up Checkpoint - Hosted HTTP Boundary

Date: 2026-06-28

Built:

- `/v1/hosted/scrape`
- hosted Bearer auth extraction,
- hosted account service dependency,
- hosted account SQLite service binding on FastAPI startup,
- static local auth middleware pass-through for `/v1/hosted/*`,
- `HostedAccountStore` protocol so account services can use in-memory or
  SQLite stores cleanly.

Behavior:

- hosted endpoint does not require local `X-API-Key`,
- missing Bearer token returns 401,
- unsafe URL returns 403 and does not call crawler,
- valid hosted key with `runs:create` scope calls crawler once,
- admitted request debits one standard credit,
- response includes tenant/key IDs and credit charge but never echoes the raw
  API key.

TDD:

- RED: `python3 -m pytest tests/unit/api/test_hosted_scrape.py tests/unit/api/test_auth.py -q`
  failed because `get_hosted_account_service` did not exist.
- GREEN: same command passed with `9 passed`.

Verification:

- `python3 -m pytest tests/unit/api -q` -> `110 passed`.
- `python3 -m pytest tests/unit/ -q` -> `447 passed`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/` -> `All checks passed!`.
- `ruff format --check scout/ tests/` -> `188 files already formatted`.
