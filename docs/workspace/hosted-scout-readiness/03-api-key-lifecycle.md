# Hosted API Key Lifecycle

Date: 2026-06-28
Status: Implementation slice

## Scope

Hosted Scout needs a safe API-key lifecycle before users can create keys on the
website and call a hosted API.

This slice creates pure domain primitives only. It does not replace the current
local `SCOUT_API_KEY` middleware and does not add persistence.

## Implementation Status

Implemented:

- `generate_api_key()`
- `hash_api_key(...)`
- `verify_api_key(...)`
- `mask_api_key(...)`
- `ApiKeyRecord`
- `ApiKeyStatus`
- `is_key_usable(...)`

Not yet implemented:

- persistence,
- API-key creation endpoint,
- hosted auth middleware,
- usage logging,
- key rotation.

## Requirements

- Generate high-entropy API keys with a stable Scout prefix.
- Store only hashed keys, never raw keys.
- Verify a provided raw key against a stored hash.
- Mask keys for display and logs.
- Attach key metadata: tenant ID, key ID, scopes, status, created timestamp,
  optional last-used timestamp.
- Keep inactive/revoked keys from verifying as usable.

## Non-Goals

- Database table migrations.
- Tenant resolver middleware.
- Stripe provisioning.
- Dashboard UI.
- Hosted key rotation endpoints.

## Future Integration

The hosted API gateway should eventually:

1. receive `Authorization: Bearer scout_live_...`,
2. hash and verify the key,
3. resolve tenant and scopes,
4. check plan and credits,
5. record usage,
6. admit or reject the run.
