"""Tests for creating Stripe Checkout Sessions for hosted Scout beta access.

# Scenario list:
# - configured service creates a beta trial setup checkout session
# - configured service creates a package payment checkout session
# - checkout payload includes package metadata and customer email when supplied
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


def test_stripe_checkout_creates_beta_trial_setup_session_with_expected_payload() -> None:
    transport = RecordingStripeCheckoutTransport()
    service = StripeCheckoutService(
        StripeCheckoutConfig(
            secret_key="sk_test_secret",
            standard_1000_price_id="price_standard_1000",
            success_url="https://scout.example/success",
            cancel_url="https://scout.example/cancel",
        ),
        transport=transport,
    )

    result = service.create_checkout_session(
        StripeCheckoutRequest(email="builder@example.com", package_id="beta_trial")
    )

    assert result.success is True
    assert result.checkout_session_id == "cs_test_checkout_001"
    assert result.checkout_url == "https://checkout.stripe.com/c/pay/cs_test_checkout_001"
    assert transport.calls == [
        {
            "url": "https://api.stripe.com/v1/checkout/sessions",
            "data": {
                "mode": "setup",
                "success_url": "https://scout.example/success",
                "cancel_url": "https://scout.example/cancel",
                "customer_email": "builder@example.com",
                "metadata[package_id]": "beta_trial",
                "metadata[plan]": "hosted_beta_pass",
                "metadata[product]": "scout_hosted",
            },
            "authorization": "Bearer sk_test_secret",
        }
    ]
    assert "sk_test_secret" not in result.model_dump_json()


def test_stripe_checkout_creates_standard_credit_payment_session() -> None:
    transport = RecordingStripeCheckoutTransport()
    service = StripeCheckoutService(
        StripeCheckoutConfig(
            secret_key="sk_test_secret",
            standard_1000_price_id="price_standard_1000",
            success_url="https://scout.example/success",
            cancel_url="https://scout.example/cancel",
        ),
        transport=transport,
    )

    result = service.create_checkout_session(
        StripeCheckoutRequest(email="builder@example.com", package_id="standard_1000")
    )

    assert result.success is True
    assert transport.calls[0]["data"] == {
        "mode": "payment",
        "line_items[0][price]": "price_standard_1000",
        "line_items[0][quantity]": "1",
        "success_url": "https://scout.example/success",
        "cancel_url": "https://scout.example/cancel",
        "customer_email": "builder@example.com",
        "metadata[package_id]": "standard_1000",
        "metadata[plan]": "hosted_beta_pass",
        "metadata[product]": "scout_hosted",
    }


def test_stripe_checkout_rejects_paid_package_without_price_id() -> None:
    transport = RecordingStripeCheckoutTransport()
    service = StripeCheckoutService(
        StripeCheckoutConfig(
            secret_key="sk_test_secret",
            success_url="https://scout.example/success",
            cancel_url="https://scout.example/cancel",
        ),
        transport=transport,
    )

    result = service.create_checkout_session(
        StripeCheckoutRequest(email="builder@example.com", package_id="standard_1000")
    )

    assert result.success is False
    assert result.reason == "Stripe price is not configured for package standard_1000."
    assert transport.calls == []


def test_stripe_checkout_missing_configuration_fails_without_transport_call() -> None:
    transport = RecordingStripeCheckoutTransport()
    service = StripeCheckoutService(
        StripeCheckoutConfig(
            secret_key="",
            standard_1000_price_id="price_standard_1000",
            success_url="https://scout.example/success",
            cancel_url="https://scout.example/cancel",
        ),
        transport=transport,
    )

    result = service.create_checkout_session(StripeCheckoutRequest(package_id="beta_trial"))

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
