# Hosted Beta Provisioning CLI PRD

## Summary

Add `scout hosted-provision` for admin/operator provisioning of hosted beta API
keys. The command writes to the hosted account SQLite store, seeds plan credits,
and prints the raw key only in the command response.

## Objective

- Provision a hosted account by email.
- Support hosted plans with default `hosted_beta_pass`.
- Support one or more scopes, defaulting to `runs:create`.
- Accept `--db` or derive default from `--workdir`.
- Return JSON with tenant ID, key ID, plan, balances, and `raw_api_key`.
- Never write raw API key to the SQLite store.

## Acceptance Criteria

- Command creates the SQLite database when missing.
- Command outputs raw key once.
- A fresh `HostedAccountService(SQLiteHostedAccountStore(db))` can authenticate
  the raw key.
- The DB file does not contain the raw key.
- Local-free plan is rejected.
