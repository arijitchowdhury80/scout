# Hosted Admission Service PRD

## Summary

Build a pure domain service that admits or rejects hosted URL/action requests.
The service composes the hosted account service, URL safety checks, and credit
policy so public routes do not duplicate security or billing logic.

## Objective

- Reject unknown, revoked, or wrong-scope API keys.
- Reject unsafe hosted URLs before any usage is consumed.
- Debit credits only after auth and URL safety pass.
- Preserve reason strings for user-facing/API error responses.
- Preserve tenant/key IDs for request ownership and audit logs.

## API Contract

- `HostedAdmissionService(account_service)`
- `admit_url_action(raw_key, url, action, required_scope="", resolved_ips=None)`
- returns `HostedAdmissionDecision`

## Acceptance Criteria

- Unknown keys are denied and do not expose URL safety details.
- Unsafe URLs are denied and do not debit credits.
- Safe URLs with valid keys and sufficient credits are allowed and debit the
  right bucket.
- Insufficient credits deny the request and preserve the balance.
- Decisions carry tenant ID, key ID, URL safety result, and usage decision when
  available.
