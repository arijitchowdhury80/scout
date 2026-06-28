"""Hosted API-key delivery contracts."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, EmailStr

from scout.core.platform.hosted import HostedPlan


class HostedApiKeyDeliveryRequest(BaseModel):
    """One-time raw API-key delivery request."""

    email: EmailStr
    tenant_id: str
    key_id: str
    plan: HostedPlan
    raw_api_key: str
    checkout_session_id: str


class HostedApiKeyDeliveryResult(BaseModel):
    """Result of attempting to deliver a raw hosted API key."""

    delivered: bool
    delivery_status: str
    reason: str = ""


class HostedApiKeyDeliveryService(Protocol):
    """Delivery contract for one-time raw API-key handoff."""

    enabled: bool

    def deliver(self, request: HostedApiKeyDeliveryRequest) -> HostedApiKeyDeliveryResult:
        """Deliver a raw API key exactly once."""
        ...


class DisabledHostedApiKeyDeliveryService:
    """Disabled delivery service used until email or portal delivery exists."""

    enabled = False

    def deliver(self, request: HostedApiKeyDeliveryRequest) -> HostedApiKeyDeliveryResult:
        """Return a disabled delivery result."""
        return HostedApiKeyDeliveryResult(
            delivered=False,
            delivery_status="disabled",
            reason="Hosted API key delivery is not configured.",
        )
