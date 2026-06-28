"""Hosted API request rate limiting primitives."""

from __future__ import annotations

import time
from collections.abc import Callable
from math import ceil

from pydantic import BaseModel, Field


class HostedRateLimitConfig(BaseModel):
    """Configuration for per-key hosted API throttling."""

    enabled: bool = True
    max_requests: int = Field(default=60, ge=1)
    window_seconds: int = Field(default=60, ge=1)


class HostedRateLimitDecision(BaseModel):
    """Decision returned for one hosted API rate-limit admission check."""

    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int = 0
    reason: str = ""


class HostedRateLimiter:
    """Small in-memory sliding-window limiter for hosted API keys."""

    def __init__(
        self,
        config: HostedRateLimitConfig | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.config = config or HostedRateLimitConfig()
        self._clock = clock or time.time
        self._events: dict[str, list[float]] = {}

    def admit(self, key: str) -> HostedRateLimitDecision:
        """Record and return whether the key may make one more request."""
        if not self.config.enabled:
            return HostedRateLimitDecision(
                allowed=True,
                limit=self.config.max_requests,
                remaining=self.config.max_requests,
            )

        now = self._clock()
        window_start = now - self.config.window_seconds
        timestamps = [ts for ts in self._events.get(key, []) if ts > window_start]
        self._events[key] = timestamps

        if len(timestamps) >= self.config.max_requests:
            oldest = min(timestamps)
            retry_after = max(1, ceil((oldest + self.config.window_seconds) - now))
            return HostedRateLimitDecision(
                allowed=False,
                limit=self.config.max_requests,
                remaining=0,
                retry_after_seconds=retry_after,
                reason="Hosted API rate limit exceeded.",
            )

        timestamps.append(now)
        return HostedRateLimitDecision(
            allowed=True,
            limit=self.config.max_requests,
            remaining=self.config.max_requests - len(timestamps),
        )
