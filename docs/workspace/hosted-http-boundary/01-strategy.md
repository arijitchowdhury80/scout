# Hosted HTTP Boundary Strategy

## Fit

Scout cannot claim hosted API readiness until a hosted route can use the hosted
account/admission services instead of the local `dev-key` middleware. This
slice proves that boundary with the smallest useful acquisition endpoint:
scrape.

## Target Segment

Hosted beta API users who have a `scout_live_...` key and want to call Scout
without running a local server.

## Trade-Off

We are not building a full hosted dashboard or all routes yet. A single
`/v1/hosted/scrape` endpoint reveals whether auth, URL safety, credit debit,
and crawler invocation compose cleanly.

## Key Metric

A hosted scrape request is accepted only when Bearer auth, required scope, URL
safety, and credit availability all pass.

## Defensibility

This endpoint is not the moat. The value is the shared admission path that keeps
hosted security and usage economics consistent across all future endpoints.
