# Requirements

## Problem

Scout is scheduled for a public beta demo to roughly 250 testers. Testers need a hosted HTTP path and Claude/Codex skill path that they can actually use, with self-service API key generation, metering, and hard spend controls. The launch must not expose the project to runaway crawler or LLM bills.

## Actors

- Beta tester: submits an email, generates an API key, tests hosted Scout endpoints.
- Operator: monitors accounts, usage, rate limits, hardware, and cost exposure.
- Agent user: invokes Scout through the Claude/Codex skill.

## In Scope

- Hosted HTTP API remains available for all current hosted feature categories.
- Email-based beta key generation is available without a manual invite password.
- Generated beta keys store email, tenant, key hash, scopes, and finite credits.
- Per-key metering and credit decrement remain enforced.
- Beta credit allocation is intentionally low enough for 250 testers.
- External LLM usage is disabled by default in hosted production.
- Distribution messaging is simplified to HTTP and Claude/Codex skill.
- Docker is removed from public distribution positioning.
- A load-test script exists for 250 concurrent users across hosted endpoints.
- Local artifact download path remains verified.

## Out Of Scope For This Emergency Slice

- Real login/account portal.
- Stripe billing.
- True multi-region or horizontal scaling.
- Guaranteed millions of calls on the current VPS.
- CAPTCHA or commercial abuse prevention.

## Success Metrics

- Unit, type, and lint checks pass.
- Hosted beta key generation can be tested without secrets in unit tests.
- Hosted beta credits are finite and low.
- Hosted LLM policy cannot accidentally use OpenAI, Anthropic, Gemini, or other paid frontier providers.
- Load-test script can simulate 250 users and report pass/fail latency/error/throughput.
- Production readiness report states hardware truth instead of assuming capacity.

## Launch Truth

All features may be available to testers, but availability must mean quota-bound, metered access. It must not mean unlimited compute, unlimited browser sessions, or arbitrary LLM calls.
