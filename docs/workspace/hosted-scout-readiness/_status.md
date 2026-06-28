# Hosted Scout Readiness Status

Date: 2026-06-28
Status: In progress

## Checklist

- [x] Existing auth/settings/run persistence inspected.
- [x] Production architecture written.
- [x] Security and scale audit written.
- [x] Failing hosted policy tests written.
- [x] Minimal hosted policy module implemented.
- [x] Focused verification passed.
- [x] API-key lifecycle tests written.
- [x] API-key lifecycle module implemented.
- [x] API-key focused verification passed.
- [x] URL safety/SSRF tests written.
- [x] URL safety/SSRF module implemented.
- [x] URL safety focused verification passed.

## Scope

Define and start the production-readiness foundation for hosted Scout:

- tenant model,
- API key lifecycle,
- Stripe/payment integration boundary,
- quota/credit policy,
- hosted usage limits,
- security risks,
- local-first vs hosted product decision.

This slice does not implement Stripe checkout, database persistence, or a public
dashboard.

## Verification

- RED: `python3 -m pytest tests/unit/core/platform/test_hosted_policy.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.hosted'`.
- GREEN: `python3 -m pytest tests/unit/core/platform/test_hosted_policy.py -q`
  - Result: 6 passed.
- API-key RED: `python3 -m pytest tests/unit/core/platform/test_api_keys.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.api_keys'`.
- API-key GREEN: `python3 -m pytest tests/unit/core/platform/test_api_keys.py -q`
  - Result: 7 passed.
- URL safety RED: `python3 -m pytest tests/unit/core/platform/test_url_safety.py -q`
  - Result: failed with `ModuleNotFoundError: No module named 'scout.core.platform.url_safety'`.
- URL safety GREEN: `python3 -m pytest tests/unit/core/platform/test_url_safety.py -q`
  - Result: 9 passed.
