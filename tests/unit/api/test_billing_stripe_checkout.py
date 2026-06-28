"""Tests for hosted Stripe Checkout Session creation.

# Scenario list:
# - public checkout route returns a Stripe Checkout URL and session id
# - route never returns Stripe secret material
# - missing checkout configuration returns a clear 503 without creating a session
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from scout.api.deps import get_stripe_checkout_service
from scout.api.main import app
from scout.core.platform.stripe_checkout import (
    StripeCheckoutResult,
    StripeCheckoutService,
)


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Iterator[None]:
    """Clear FastAPI dependency overrides after each checkout route test."""
    yield
    app.dependency_overrides.clear()


def test_stripe_checkout_route_returns_checkout_url_without_static_api_key() -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(
            success=True,
            checkout_session_id="cs_test_checkout_001",
            checkout_url="https://checkout.stripe.com/c/pay/cs_test_checkout_001",
        )
    )
    client = _client(service)

    response = client.post(
        "/v1/billing/stripe/checkout-session",
        json={"email": "builder@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "checkout_session_id": "cs_test_checkout_001",
        "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_checkout_001",
        "reason": "",
    }
    assert service.emails == ["builder@example.com"]
    assert "sk_test" not in response.text


def test_stripe_checkout_route_returns_503_when_checkout_is_not_configured() -> None:
    service = RecordingStripeCheckoutService(
        StripeCheckoutResult(
            success=False,
            reason="Stripe Checkout is not configured.",
        )
    )
    client = _client(service)

    response = client.post("/v1/billing/stripe/checkout-session", json={})

    assert response.status_code == 503
    assert response.json()["detail"] == "Stripe Checkout is not configured."
    assert service.emails == [""]


def _client(service: StripeCheckoutService) -> TestClient:
    """Build a test client with the checkout service dependency overridden."""
    app.dependency_overrides[get_stripe_checkout_service] = lambda: service
    return TestClient(app)


class RecordingStripeCheckoutService:
    """Record checkout requests and return a deterministic result."""

    def __init__(self, result: StripeCheckoutResult) -> None:
        self.result = result
        self.emails: list[str] = []

    def create_beta_checkout_session(self, request: object) -> StripeCheckoutResult:
        self.emails.append(str(getattr(request, "email", "")))
        return self.result
