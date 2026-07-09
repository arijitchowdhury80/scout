# Hosted Beta Signup Debug - 2026-07-09

## Trigger

A returning signup on `https://scout.chowmes.com/beta` displayed copy implying a fresh API-key email was sent, but no new email arrived.

## Evidence

- `https://scout.chowmes.com/health` returned HTTP 200 with `status: ok`.
- `https://scout.chowmes.com/v1/billing/stripe/status` reported `key_delivery_configured: true`, `ready_for_beta_key_delivery: true`, and no missing environment keys.
- The hosted signup ledger showed the tested account had an existing active hosted account and current attempts were recorded as `duplicate` with `delivery_status: account_exists`.
- `POST /v1/hosted/beta-key/status` for the same email returned `status: duplicate`, `delivery_status: account_exists`, and a message instructing the user to use the originally delivered key.
- DNS for `scout.chowmes.com` had ImprovMX MX records and SPF. No DMARC or DKIM TXT records were observed during this check.

## Root Cause

`website/assets/hosted-keygen.js` only handled `pending_delivery` specially. Every other successful response, including `account_exists`, fell through to copy that said Scout emailed a beta tester API key. The API response was accurate; the browser message was not.

## Fix

Add an explicit `account_exists` branch in the beta signup UI. Returning users now see that the email already has a Scout account and should use the originally delivered key or contact `support@scout.chowmes.com` from that address.

Follow-up UX hardening: duplicate signups use a non-success status, say "This email is already registered" and "This is a duplicate signup," keep the form intact, and do not claim a new email was sent. Scout does not resend the same raw API key because hosted keys are not stored in recoverable form after first delivery; replacement requires the support/operator path.

## Verification

- `python3 -m pytest tests/unit/website/test_launch_website.py::test_beta_signup_copy_does_not_claim_duplicate_accounts_were_emailed -q`
- `python3 -m pytest tests/unit/website/test_launch_website.py tests/unit/api/test_hosted_scrape.py tests/unit/scripts/test_hosted_beta_signup_smoke.py -q`
