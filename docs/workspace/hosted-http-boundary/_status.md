# Hosted HTTP Boundary Status

Status: Verified checkpoint
Date: 2026-06-28

## Goal

Expose the first hosted-mode HTTP boundary that uses Scout hosted API keys
instead of the local static `X-API-Key`. This proves the hosted request path:
Bearer key -> hosted admission -> URL safety -> credit debit -> Scout scrape.

## Completed

- [x] Strategy and PRD written.
- [x] RED API tests written and observed failing.
- [x] Hosted router and middleware pass-through implemented.
- [x] Verification run.
- [x] Hosted readiness docs updated.

## Boundary

This checkpoint began with `/v1/hosted/scrape` and now includes hosted
`/v1/hosted/crawl`, `/v1/hosted/products`, `/v1/hosted/run/{use_case}`, and
owned-run artifact retrieval. It does not yet implement user signup dashboard,
production key delivery, production Stripe operations, object storage, or
production worker queues.

## SSRF Update

Hosted admission now validates URL safety with DNS resolution before crawler
work starts. Unsafe schemes, credentials, localhost, unsafe IP literals,
DNS-resolved unsafe IPs, and URL-like values in high-level run fields are
blocked before crawler invocation and before credit debit. Evidence:
`docs/security/hosted-ssrf-review-2026-06-28.md`.

## Artifact Authorization Update

Hosted run retrieval is authorized by persisted tenant ownership. Artifact
download and `/records` paths are restricted to known artifact names inside the
stored run output directory. Evidence:
`docs/security/hosted-artifact-authorization-review-2026-06-28.md`.

## TDD Evidence

RED:

```bash
python3 -m pytest tests/unit/api/test_hosted_scrape.py tests/unit/api/test_auth.py -q
```

Result: failed because `get_hosted_account_service` did not exist.

GREEN:

```bash
python3 -m pytest tests/unit/api/test_hosted_scrape.py tests/unit/api/test_auth.py -q
```

Result: `9 passed, 2 warnings`.

## Final Verification

```bash
python3 -m pytest tests/unit/api -q
```

Result: `110 passed, 2 warnings`.

```bash
python3 -m pytest tests/unit/ -q
```

Result: `447 passed, 8 warnings`.

```bash
python3 -m pyright scout/
```

Result: `0 errors, 0 warnings, 0 informations`.

```bash
ruff check scout/ tests/
ruff format --check scout/ tests/
```

Result: `All checks passed!` and `188 files already formatted`.
