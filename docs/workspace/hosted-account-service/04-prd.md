# Hosted Account Service PRD

## Summary

Build a pure Python hosted-account service that provisions a tenant, generates
a one-time API key, stores only the hash, seeds plan credits, validates scopes,
and debits usage. This moves Scout closer to a hosted API without exposing
unsafe public endpoints yet.

## Objective

- Provision a hosted beta tenant with finite credits from `HostedPlan`.
- Authenticate API keys without storing raw keys.
- Reject disabled/revoked/wrong-scope keys.
- Debit standard and browser credits separately.
- Preserve a stable contract future HTTP routes and Stripe webhooks can call.

## Solution

### Models

- `HostedTenantRecord`
- `HostedAccountBalance`
- `HostedProvisioningResult`
- `HostedAccountDecision`
- `InMemoryHostedAccountStore`
- `HostedAccountService`

### Key Behaviors

- `provision_account(email, plan, scopes)` returns a raw API key once and stores
  only an `ApiKeyRecord` hash.
- `authenticate_key(raw_key, required_scope)` returns a decision with tenant and
  key metadata, never raw secret values.
- `consume_action(raw_key, action, required_scope)` checks key/scope/credits and
  decrements the correct bucket only when allowed.
- `HOSTED_BETA_PASS`, `HOSTED_STARTER`, and `HOSTED_PRO` can be provisioned.
- `LOCAL_FREE` is rejected for hosted account provisioning.

## Not In Scope

- HTTP routes.
- Stripe checkout/webhooks.
- Database persistence.
- Hosted worker execution.
- Public dashboard.

## Acceptance Criteria

- Tests prove raw API keys are not stored.
- Tests prove beta pass credits are seeded from plan limits.
- Tests prove scope checks work.
- Tests prove debit changes only the correct credit bucket.
- Tests prove insufficient credits do not mutate balances.
