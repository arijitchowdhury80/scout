# Hosted Beta Provisioning CLI Strategy

## Fit

Scout now has hosted account persistence and a hosted Bearer scrape endpoint,
but no way for an operator to create a usable hosted key. A CLI command closes
that beta-operation gap without prematurely building a dashboard.

## Target Segment

Scout operators running a private hosted beta. They need to issue a key for a
beta user after manual approval or payment confirmation.

## Trade-Off

This does not solve self-serve signup. We intentionally avoid public key
creation endpoints until user auth, Stripe webhooks, abuse controls, and email
verification exist.

## Key Metric

An operator can create a tenant/key/balance in a SQLite hosted account DB and
copy the raw key once, while the DB stores only the key hash.

## Defensibility

The command is operational plumbing, not differentiation. It protects the
hosted beta path from ad hoc database edits and unsafe raw-key storage.
