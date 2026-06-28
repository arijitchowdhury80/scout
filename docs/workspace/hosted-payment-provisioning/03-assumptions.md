# Hosted Payment Provisioning Assumptions

## Assumptions

| Category | Assumption | Confidence | If Wrong |
|---|---|---:|---|
| Value | A one-time beta pass needs automated provisioning before launch. | High | Operators keep manually issuing keys and checkout cannot be self-serve. |
| Usability | Future webhook/API routes can call a provider-neutral domain request. | High | We will need provider-specific glue at the HTTP edge only. |
| Viability | $22 beta pass must be limited, not unlimited usage. | High | Hosted costs can exceed revenue. |
| Feasibility | Existing `HostedAccountService` can provision the required account/key. | High | Account service contract must be extended. |
| Security | Raw API keys must be returned once and never stored. | High | Credential leakage risk becomes launch-blocking. |
| Integration | SQLite is enough for local/beta event idempotency. | Medium | Production Postgres adapter will be needed sooner. |

## Impact Risk Matrix

| | Low Risk | High Risk |
|---|---|---|
| High Impact | Raw key never stored; paid status required; duplicate checkout idempotency | SQLite transaction boundary across payment and account writes |
| Low Impact | Provider enum starts with Stripe only | Multi-currency pricing |

## Top Risks

1. Account provisioning succeeds but payment event recording fails.
2. A retry reprints a raw API key.
3. Wrong amount/currency provisions access.

## Experiments

- Unit/integration-style SQLite tests for idempotency and raw-key storage.
- Negative tests for unpaid status and wrong amount/currency.
- Future webhook route can reuse the same tests with Stripe signature fixtures.

