# Hosted SSRF Review

Date: 2026-06-28
Status: Admission-layer control implemented and tested; deeper network egress
hardening still required before public hosted launch

## Scope

This review covers the hosted HTTP API admission boundary for:

- `POST /v1/hosted/scrape`
- `POST /v1/hosted/crawl`
- `POST /v1/hosted/products`
- `POST /v1/hosted/run/{use_case}`

It does not certify the underlying crawler, browser automation runtime, cloud
network, redirect-following implementation, object storage, or production
deployment firewall.

## Implemented Controls

- Bearer API key authentication happens before URL admission.
- Hosted URL admission only allows `http` and `https`.
- URL credentials/userinfo are rejected.
- Missing hostnames are rejected.
- `localhost` and `*.localhost` hostnames are rejected.
- Unsafe IP literals are rejected, including private, loopback, link-local,
  multicast, reserved, and unspecified ranges.
- Hostnames are resolved at admission time and rejected if any resolved IP is
  unsafe; this blocks DNS-resolved unsafe IPs before crawler work starts.
- Hosted high-level runs validate URL-like values in `url`, `targets`, and
  nested request fields before running a use case.
- Unsafe hosted requests are rejected before crawler invocation and before
  credit debit.

## Current Limits

- DNS resolution is an admission-time check. Production hosting should also add
  egress firewall policy so infrastructure enforces the same boundary.
- Redirect-chain validation exists as a primitive, but the hosted crawler still
  needs a deeper review to prove every redirect and retry path is revalidated
  before network access.
- Unresolvable hostnames are left to the crawler to fail naturally. If a
  hostname resolves inside the hosted network, unsafe resolved IPs are blocked.
- User-browser capture should remain local-first and is not approved as a
  hosted browser-session feature.

## Evidence

Test coverage:

```bash
python3 -m pytest \
  tests/unit/core/platform/test_url_safety.py \
  tests/unit/api/test_hosted_scrape.py \
  tests/unit/api/test_hosted_crawl.py \
  tests/unit/api/test_hosted_products.py \
  tests/unit/api/test_hosted_run.py \
  tests/unit/api/test_hosted_run_retrieval.py -q
```

Expected result from the implementation checkpoint:

```text
42 passed
```

## Launch Impact

The release checklist item "Hosted SSRF checks reviewed" is satisfied for the
hosted admission layer. Public hosted launch still requires the remaining
security gates, especially dependency audit resolution, artifact authorization
review, deployment egress policy, and redirect/retry validation in crawler
workers.
