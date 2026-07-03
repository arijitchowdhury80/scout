# Risk Assessment

## Highest Risks

1. Runaway API/LLM spend
   - Impact: catastrophic bill.
   - Mitigation: hosted LLM disabled by default, env scan, provider deny tests, no external LLM API keys.

2. 250 concurrent users overwhelm single VPS
   - Impact: timeouts, failed demo, noisy logs.
   - Mitigation: load-test script, explicit hardware check, rate limits, low credits, global caps.

3. Self-service key generation abused
   - Impact: key spam, crawler abuse.
   - Mitigation: per-email uniqueness, per-process rate limit, low credits, operator listing scripts.

4. Misleading distribution surface
   - Impact: users try Docker/local flows that are not launch-supported.
   - Mitigation: public copy and docs position only HTTP hosted and Claude/Codex skill.

5. Metering race conditions
   - Impact: concurrent requests can overspend credits.
   - Mitigation: keep credits low for tomorrow, document Postgres/atomic debit requirement for real scale.

## Go/No-Go

Proceed only as controlled public beta if:

- hosted keygen is deployed and verified,
- credits are low,
- external LLM keys are absent,
- hosted LLM mode is disabled,
- a real load test has been run against staging/production,
- the VPS has enough headroom or the invite volume is throttled.
