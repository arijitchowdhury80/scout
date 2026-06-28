# Hosted Account Persistence Strategy

## Fit

Hosted Scout needs durable tenants, hashed API keys, and usage balances. The
current in-memory store is good for domain tests but cannot support a hosted
beta or even a local server restart.

## Target Segment

Future hosted Scout operators and API users. Operators need reliable account
state; users need API keys and credits that survive process restarts.

## Trade-Off

This slice adds SQLite persistence rather than jumping directly to Postgres.
That keeps the implementation testable in the local repo while proving the
repository contract future production storage must satisfy.

## Key Metric

A tenant provisioned with one service instance can be authenticated and charged
by a fresh service instance reading the same SQLite file.

## Defensibility

Persistence itself is not defensible. The value is protecting Scout's hosted
economics: raw keys are never stored, and credit balances are debited exactly
once across restarts.
