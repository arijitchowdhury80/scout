"""Tests for hosted API request rate limiting."""

from __future__ import annotations

from scout.core.platform.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter


def test_hosted_rate_limiter_denies_after_limit_and_reports_retry_after() -> None:
    now = 100.0
    limiter = HostedRateLimiter(
        HostedRateLimitConfig(max_requests=2, window_seconds=10),
        clock=lambda: now,
    )

    first = limiter.admit("key_123")
    second = limiter.admit("key_123")
    third = limiter.admit("key_123")

    assert first.allowed is True
    assert first.remaining == 1
    assert second.allowed is True
    assert second.remaining == 0
    assert third.allowed is False
    assert third.remaining == 0
    assert third.retry_after_seconds == 10
    assert third.reason == "Hosted API rate limit exceeded."


def test_hosted_rate_limiter_allows_again_after_window_expires() -> None:
    current_time = [100.0]
    limiter = HostedRateLimiter(
        HostedRateLimitConfig(max_requests=1, window_seconds=10),
        clock=lambda: current_time[0],
    )

    assert limiter.admit("key_123").allowed is True
    assert limiter.admit("key_123").allowed is False

    current_time[0] = 111.0
    decision = limiter.admit("key_123")

    assert decision.allowed is True
    assert decision.remaining == 0


def test_disabled_hosted_rate_limiter_always_allows() -> None:
    limiter = HostedRateLimiter(HostedRateLimitConfig(enabled=False, max_requests=1))

    assert limiter.admit("key_123").allowed is True
    assert limiter.admit("key_123").allowed is True
