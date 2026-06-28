# Detect-Secrets Candidate Audit

Date: 2026-06-28
Status: Current candidates audited as false positives; baseline committed

No candidate secret values are reproduced in this report.

## Summary

- Tool: `detect-secrets`
- Scope: git-tracked files
- Excluded generated/local paths:
  - `dist/`
  - `validation-output/`
  - `scout-runs/`
  - `.pytest_cache/`
  - `.ruff_cache/`
- Files with candidates: 18
- Total candidates reviewed: 26
- Disposition: False positive for every current candidate
- Enforcement file: `.secrets.baseline`

## Verification Command

```bash
detect-secrets-hook --baseline .secrets.baseline --no-verify \
  --exclude-files '(^dist/|^validation-output/|^scout-runs/|^\.pytest_cache/|^\.ruff_cache/)' \
  $(git ls-files)
```

## Candidate Review

| File | Lines | Finding type | Disposition | Rationale |
| --- | --- | --- | --- | --- |
| `README.md` | 130 | Basic Auth Credentials | False positive | Documentation proxy URL example, not a credential. |
| `README.md` | 476 | Hex High Entropy String | False positive | Documentation output/example value, not a live secret. |
| `README.md` | 647 | Secret Keyword | False positive | Documentation JSON field name/example, not a live secret. |
| `docs/workspace/hosted-scout-readiness/_status.md` | 94 | Secret Keyword | False positive | Mentions environment variable names only. |
| `scout/api/frontend.py` | 736 | Secret Keyword | False positive | Frontend variable name for configured API key handling; no live value committed. |
| `scout/core/types.py` | 46 | Basic Auth Credentials | False positive | Proxy URL type/example documentation, not a credential. |
| `tests/e2e/test_app_ui_exhaustive.py` | 17 | Secret Keyword | False positive | Test constant placeholder. |
| `tests/e2e_real_websites.py` | 460 | Secret Keyword | False positive | Test/request payload field name. |
| `tests/unit/api/test_algolia_push.py` | 48, 74, 107 | Secret Keyword | False positive | Mock Algolia key fields in unit tests. |
| `tests/unit/api/test_app_frontend.py` | 183 | Secret Keyword | False positive | Frontend test assertion around key handling text. |
| `tests/unit/api/test_auth.py` | 42 | Secret Keyword | False positive | Auth test fixture response field. |
| `tests/unit/api/test_billing_stripe_webhook.py` | 41 | Secret Keyword | False positive | Stripe webhook test fixture value. |
| `tests/unit/api/test_config.py` | 9, 10 | Base64 High Entropy String | False positive | Temporary `.env` and `.env.local` fixture values in config tests. |
| `tests/unit/api/test_config.py` | 14 | Secret Keyword | False positive | Config test assertion for API key value loading. |
| `tests/unit/api/test_routers.py` | 25 | Secret Keyword | False positive | API router test fixture value. |
| `tests/unit/core/modes/test_extract.py` | 45 | Secret Keyword | False positive | Extractor test fixture argument. |
| `tests/unit/core/platform/test_key_delivery.py` | 43, 97 | Secret Keyword | False positive | SMTP/API-key delivery test fixtures. |
| `tests/unit/core/platform/test_stripe_checkout.py` | 24 | Secret Keyword | False positive | Stripe checkout test fixture value. |
| `tests/unit/core/products/test_listing.py` | 303 | Base64 High Entropy String | False positive | Product listing fixture string, not a credential. |
| `tests/unit/core/test_crawler.py` | 94 | Secret Keyword | False positive | Crawler test fixture argument. |
| `tests/validate_endpoints.py` | 1086, 1207 | Secret Keyword | False positive | Endpoint validation payload field names. |

## Launch Impact

The current tracked-file entropy candidates are audited and baselined. Public
launch still requires this hook to pass on the final release commit and any new
candidate findings to be removed or explicitly reviewed before release.

