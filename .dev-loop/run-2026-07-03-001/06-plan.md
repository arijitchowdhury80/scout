# Build Plan

1. Add RED tests for beta keygen without invite password, finite low beta credits, hosted LLM disable policy, and public distribution copy.
2. Implement configuration and policy changes.
3. Add email-only beta key generation with safe defaults and operator-visible stored email.
4. Add 250-user hosted load-test script with endpoint coverage and clear thresholds.
5. Remove Docker from public distribution positioning while keeping internal docker files untouched unless separately approved.
6. Run unit, pyright, ruff, artifact smoke, production smoke, and hardware/env checks.
7. Record remaining blockers truthfully.
