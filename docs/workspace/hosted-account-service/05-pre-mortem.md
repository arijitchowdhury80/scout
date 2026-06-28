# Hosted Account Service Pre-Mortem

## Tigers

### Raw API Keys Accidentally Stored

- Evidence: Hosted API-key systems often fail by treating generated keys like
  normal records.
- Impact: Secret leakage and trust failure.
- Classification: Launch-blocking.
- Mitigation: Service stores `ApiKeyRecord.key_hash` only; tests assert raw key
  does not appear in stored records.

### Credits Debited Incorrectly

- Evidence: Scout has two cost buckets: standard fetch credits and browser
  credits.
- Impact: Hosted economics break; $22 beta pass becomes unsustainable.
- Classification: Launch-blocking.
- Mitigation: Tests cover standard and browser debit separately.

### Public Routes Built Too Early

- Evidence: Without domain contracts, endpoints tend to embed business logic.
- Impact: Endpoint debt and inconsistent quota behavior.
- Classification: Fast-follow risk.
- Mitigation: Domain service first; routes later.

## Paper Tigers

### In-Memory Store Means It Is Not Useful

This slice is intentionally not production persistence. It proves the domain
contract. A database repository can later implement the same methods.

## Elephants

### Tenant Identity And Login Are Unresolved

Hosted Scout still needs user auth and payment identity decisions. This service
does not answer whether accounts are email-only, OAuth-backed, or organization
tenants.
