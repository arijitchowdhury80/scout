# Hosted URL Safety / SSRF Guard

Date: 2026-06-28
Status: Implementation slice

## Scope

Hosted Scout accepts user-submitted URLs. Before any hosted fetch, crawl,
screenshot, browser render, or redirect follow, Scout must reject URLs that can
target internal infrastructure.

This slice creates deterministic URL safety primitives only. It does not yet
wire the guard into scrape/crawl/browser routes because local Scout still needs
to support localhost and private-network development workflows.

## Requirements

- Allow only `http` and `https`.
- Reject missing hostnames.
- Reject URL credentials/userinfo.
- Reject localhost-style hostnames.
- Reject private, loopback, link-local, multicast, reserved, and unspecified IP
  literals.
- Reject resolved IPs in unsafe ranges.
- Validate redirect chains by checking every URL in the chain.

## Future Hosted Integration

Hosted API admission should call this guard before:

- `/scrape`,
- `/crawl`,
- `/map`,
- `/screenshot`,
- `/products`,
- app run creation,
- browser render,
- each redirect target.

Local mode can keep this guard disabled by default.

