"""Tests for creating Stripe Checkout Sessions for hosted Scout beta access.

# Scenario list:
# - configured service creates a one-time payment checkout session
# - checkout payload includes beta plan metadata and customer email when supplied
# - missing Stripe configuration fails before any outbound request
# - service result never exposes the Stripe secret key
"""

from __future__ import annotations

from scout.core.platform.stripe_checkout import (
    StripeCheckoutConfig,
    StripeCheckoutRequest,
    StripeCheckoutService,
    StripeCheckoutSession,
)


def test_stripe_checkout_creates_beta_session_with_expected_payload() -> None:
    transport = RecordingStripeCheckoutTransport()
    service = StripeCheckoutService(
        StripeCheckoutConfig(
            secret_key="sk_test_secret",
            beta_price_id="price_beta_22",
            success_url="https://scout.example/success",
            cancel_url="https://scout.example/cancel",
        ),
        transport=transport,
    )

    result = service.create_beta_checkout_session(
        StripeCheckoutRequest(email="builder@example.com")
    )

    assert result.success is True
    assert result.checkout_session_id == "cs_test_checkout_001"
    assert result.checkout_url == "https://checkout.stripe.com/c/pay/cs_test_checkout_001"
    assert transport.calls == [
        {
            "url": "https://api.stripe.com/v1/checkout/sessions",
            "data": {
                "mode": "payment",
                "line_items[0][price]": "price_beta_22",
                "line_items[0][quantity]": "1",
                "success_url": "https://scout.example/success",
                "cancel_url": "https://scout.example/cancel",
                "customer_email": "builder@example.com",
                "metadata[plan]": "hosted_beta_pass",
                "metadata[product]": "scout_hosted_beta",
            },
            "authorization": "Bearer sk_test_secret",
        }
    ]
    assert "sk_test_secret" not in result.model_dump_json()


def test_stripe_checkout_missing_configuration_fails_without_transport_call() -> None:
    transport = RecordingStripeCheckoutTransport()
    service = StripeCheckoutService(
        StripeCheckoutConfig(
            secret_key="",
            beta_price_id="price_beta_22",
            success_url="https://scout.example/success",
            cancel_url="https://scout.example/cancel",
        ),
        transport=transport,
    )

    result = service.create_beta_checkout_session(StripeCheckoutRequest())

    assert result.success is False
    assert result.checkout_url == ""
    assert result.checkout_session_id == ""
    assert result.reason == "Stripe Checkout is not configured."
    assert transport.calls == []


class RecordingStripeCheckoutTransport:
    """Record Stripe form posts and return a deterministic checkout session."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def post_form(
        self,
        url: str,
        data: dict[str, str],
        headers: dict[str, str],
    ) -> StripeCheckoutSession:
        self.calls.append(
            {
                "url": url,
                "data": data,
                "authorization": headers["Authorization"],
            }
        )
        return StripeCheckoutSession(
            id="cs_test_checkout_001",
            url="https://checkout.stripe.com/c/pay/cs_test_checkout_001",
        )
