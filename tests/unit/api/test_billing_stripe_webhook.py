"""Tests for hosted Stripe webhook provisioning.

# Scenario list:
# - missing Stripe-Signature rejects without provisioning
# - invalid Stripe-Signature rejects without provisioning
# - valid checkout.session.completed provisions hosted beta access
# - duplicate checkout.session.completed returns idempotent metadata
# - irrelevant Stripe event is acknowledged and ignored
# - webhook response never leaks raw scout_live API keys
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scout.api.deps import get_hosted_payment_provisioning_service, get_stripe_webhook_secret
from scout.api.main import app
from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.payment_provisioning import (
    HostedCheckoutProvisioningRecord,
    HostedPaymentProvider,
    HostedPaymentProvisioningService,
    SQLiteHostedPaymentStore,
)
from scout.core.platform.key_delivery import (
    HostedApiKeyDeliveryRequest,
    HostedApiKeyDeliveryResult,
)

_WEBHOOK_SECRET = "whsec_test_secret"


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Iterator[None]:
    """Clear FastAPI dependency overrides after each webhook test."""
    yield
    app.dependency_overrides.clear()


def test_stripe_webhook_rejects_missing_signature_without_provisioning(
    tmp_path: Path,
) -> None:
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    service = _payment_service(payment_store)
    client = _client(service)

    response = client.post(
        "/v1/billing/stripe/webhook",
        content=_checkout_event_payload(),
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Missing Stripe-Signature header."
    assert _stored_checkout(payment_store) is None


def test_stripe_webhook_rejects_invalid_signature_without_provisioning(
    tmp_path: Path,
) -> None:
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    service = _payment_service(payment_store)
    client = _client(service)

    response = client.post(
        "/v1/billing/stripe/webhook",
        content=_checkout_event_payload(),
        headers={
            "content-type": "application/json",
            "Stripe-Signature": "t=123,v1=wrong",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Stripe webhook signature."
    assert _stored_checkout(payment_store) is None


def test_stripe_webhook_checkout_completed_provisions_without_leaking_raw_key(
    tmp_path: Path,
) -> None:
    account_store = InMemoryHostedAccountStore()
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    delivery_service = RecordingKeyDeliveryService()
    service = HostedPaymentProvisioningService(
        HostedAccountService(account_store),
        payment_store,
    )
    payload = _checkout_event_payload()
    client = _client(service, delivery_service)

    response = client.post(
        "/v1/billing/stripe/webhook",
        content=payload,
        headers={
            "content-type": "application/json",
            "Stripe-Signature": _signature_header(payload),
        },
    )
    stored = _stored_checkout(payment_store)

    assert response.status_code == 200
    body = response.json()
    assert stored is not None
    assert body["success"] is True
    assert body["ignored"] is False
    assert body["already_processed"] is False
    assert body["delivery_status"] == "delivered"
    assert body["tenant_id"] == stored.tenant_id
    assert body["key_id"] == stored.key_id
    assert "scout_live_" not in response.text
    assert len(account_store.api_keys) == 1
    assert delivery_service.deliveries[0].email == "builder@example.com"
    assert delivery_service.deliveries[0].raw_api_key.startswith("scout_live_")
    assert stored.email == "builder@example.com"
    assert stored.amount_total_cents == 2200


def test_stripe_webhook_blocks_provisioning_when_key_delivery_is_disabled(
    tmp_path: Path,
) -> None:
    account_store = InMemoryHostedAccountStore()
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    service = HostedPaymentProvisioningService(
        HostedAccountService(account_store),
        payment_store,
    )
    payload = _checkout_event_payload()
    client = _client(service, DisabledKeyDeliveryService())

    response = client.post(
        "/v1/billing/stripe/webhook",
        content=payload,
        headers={
            "content-type": "application/json",
            "Stripe-Signature": _signature_header(payload),
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Hosted API key delivery is not configured."
    assert len(account_store.api_keys) == 0
    assert _stored_checkout(payment_store) is None


def test_stripe_webhook_checkout_completed_replay_is_idempotent(
    tmp_path: Path,
) -> None:
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    service = _payment_service(payment_store)
    payload = _checkout_event_payload()
    delivery_service = RecordingKeyDeliveryService()
    client = _client(service, delivery_service)

    first = client.post(
        "/v1/billing/stripe/webhook",
        content=payload,
        headers={
            "content-type": "application/json",
            "Stripe-Signature": _signature_header(payload),
        },
    )
    second = client.post(
        "/v1/billing/stripe/webhook",
        content=payload,
        headers={
            "content-type": "application/json",
            "Stripe-Signature": _signature_header(payload),
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["key_id"] == second.json()["key_id"]
    assert second.json()["already_processed"] is True
    assert second.json()["delivery_status"] == "not_required"
    assert "scout_live_" not in second.text
    assert len(delivery_service.deliveries) == 1


def test_stripe_webhook_ignores_irrelevant_event_type(tmp_path: Path) -> None:
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    service = _payment_service(payment_store)
    payload = _event_payload({"type": "customer.created", "data": {"object": {"id": "cus_1"}}})
    client = _client(service, RecordingKeyDeliveryService())

    response = client.post(
        "/v1/billing/stripe/webhook",
        content=payload,
        headers={
            "content-type": "application/json",
            "Stripe-Signature": _signature_header(payload),
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["ignored"] is True
    assert _stored_checkout(payment_store) is None


def _client(
    payment_service: HostedPaymentProvisioningService,
    delivery_service: object | None = None,
) -> TestClient:
    """Build a test client with billing dependencies overridden."""
    from scout.api.deps import get_hosted_key_delivery_service

    app.dependency_overrides[get_hosted_payment_provisioning_service] = lambda: payment_service
    app.dependency_overrides[get_stripe_webhook_secret] = lambda: _WEBHOOK_SECRET
    if delivery_service is not None:
        app.dependency_overrides[get_hosted_key_delivery_service] = lambda: delivery_service
    return TestClient(app)


def _payment_service(
    payment_store: SQLiteHostedPaymentStore,
) -> HostedPaymentProvisioningService:
    """Build a payment provisioning service for webhook tests."""
    return HostedPaymentProvisioningService(
        HostedAccountService(InMemoryHostedAccountStore()),
        payment_store,
    )


def _stored_checkout(
    payment_store: SQLiteHostedPaymentStore,
) -> HostedCheckoutProvisioningRecord | None:
    """Return the stored checkout fixture, if the webhook provisioned it."""
    return payment_store.get_checkout(
        HostedPaymentProvider.STRIPE,
        "cs_test_beta_001",
    )


def _checkout_event_payload() -> bytes:
    """Return a Stripe checkout.session.completed event payload."""
    return _event_payload(
        {
            "id": "evt_test_001",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_beta_001",
                    "customer": "cus_test_001",
                    "payment_intent": "pi_test_001",
                    "amount_total": 2200,
                    "currency": "usd",
                    "payment_status": "paid",
                    "customer_details": {"email": "builder@example.com"},
                }
            },
        }
    )


def _event_payload(event: dict[str, object]) -> bytes:
    """Encode an event like Stripe sends it."""
    return json.dumps(event, separators=(",", ":")).encode("utf-8")


def _signature_header(payload: bytes) -> str:
    """Sign a payload with the Stripe webhook test secret."""
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    digest = hmac.new(
        _WEBHOOK_SECRET.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


class RecordingKeyDeliveryService:
    """Test delivery service that captures raw API keys in memory only."""

    enabled = True

    def __init__(self) -> None:
        self.deliveries: list[HostedApiKeyDeliveryRequest] = []

    def deliver(self, request: HostedApiKeyDeliveryRequest) -> HostedApiKeyDeliveryResult:
        """Capture the delivery request."""
        self.deliveries.append(request)
        return HostedApiKeyDeliveryResult(delivered=True, delivery_status="delivered")


class DisabledKeyDeliveryService:
    """Test delivery service that simulates missing launch delivery config."""

    enabled = False

    def deliver(self, request: HostedApiKeyDeliveryRequest) -> HostedApiKeyDeliveryResult:
        """Return disabled delivery status."""
        return HostedApiKeyDeliveryResult(
            delivered=False,
            delivery_status="disabled",
            reason="Hosted API key delivery is not configured.",
        )
