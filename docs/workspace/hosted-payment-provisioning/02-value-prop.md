# Hosted Payment Provisioning Value Proposition

## JTBD

1. **Who**: future checkout webhooks, beta operators, and hosted signup flows.
2. **Why**: they need to grant hosted Scout access after payment without manual
   key handling or duplicate account creation.
3. **What Before**: operators can run `scout hosted-provision`, but there is no
   payment-aware event record or idempotency boundary.
4. **How**: the module validates a checkout event, provisions a hosted account
   through `HostedAccountService`, records the checkout event, and returns the
   raw API key only on first processing.
5. **What After**: hosted beta payment can safely map to one tenant/key and
   webhook retries do not leak or duplicate credentials.
6. **Alternatives**: Stripe webhook code could call account provisioning
   directly, but that couples HTTP, Stripe payloads, security, and persistence
   too early.

Value prop:

For hosted Scout signup flows that need to convert paid checkouts into API
access, Hosted Payment Provisioning is a domain boundary that creates one safe,
metered hosted account per paid checkout. Unlike direct webhook-to-key creation,
it is idempotent, testable without Stripe, and never stores raw API keys.

Tagline: Paid checkout to safe Scout key.

