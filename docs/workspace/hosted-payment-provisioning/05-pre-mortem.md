# Hosted Payment Provisioning Pre-Mortem

Assume this ships and fails.

## Tigers

| Risk | Evidence | Impact | Class |
|---|---|---|---|
| Webhook retry creates duplicate keys | Stripe retries are normal; duplicate events happen. | Customers get multiple keys/credits for one payment. | Launch-blocking |
| Raw API key is stored | Existing account design intentionally stores only hashes. | Credential leak. | Launch-blocking |
| Underpaid checkout provisions access | Payment amount must map to plan economics. | Abuse and revenue leakage. | Launch-blocking |
| Account write succeeds but event write fails | Account and payment tables are separate operations in V1. | Retry could create another account. | Fast-follow |

## Paper Tigers

- Full Stripe SDK is required now: overblown. The domain service can be tested
  without Stripe and called by a later webhook adapter.
- Multi-currency pricing is needed now: overblown for a USD beta pass.

## Elephants

- Production needs a transactional store boundary for event + account creation.
- Raw key delivery needs a user-facing secure handoff story before public launch.

## Launch-Blocking Mitigations

- Use a unique provider/session idempotency table.
- Return raw key only for first processing.
- Validate paid status, currency, and amount before provisioning.

