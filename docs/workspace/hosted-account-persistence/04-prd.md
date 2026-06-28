# Hosted Account Persistence PRD

## Summary

Implement `SQLiteHostedAccountStore`, a durable local repository compatible with
`HostedAccountService` and `HostedAdmissionService`.

## Objective

- Persist `HostedTenantRecord`.
- Persist `ApiKeyRecord` without raw API keys.
- Persist `HostedUsageBalance`.
- Support lookup by API-key hash.
- Support key status updates.
- Support balance updates after admitted usage.

## Acceptance Criteria

- Provisioned tenant/key/balance survive a new store/service instance.
- A raw API key from provisioning authenticates through a fresh service.
- Credit debit through `HostedAdmissionService` persists to SQLite.
- Revoked key status persists to SQLite.
- The raw API key is not present in the SQLite database file.

## Not In Scope

- Postgres.
- Alembic migrations.
- Tenant/user login tables.
- Stripe customer/subscription tables.
- Hosted HTTP routes.
