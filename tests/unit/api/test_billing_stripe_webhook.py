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
from scout.core.platform.hosted import HostedPlan
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
    delivered_key = delivery_service.deliveries[0].raw_api_key
    delivered_key_auth = HostedAccountService(account_store).authenticate_key(
        delivered_key,
        required_scope="runs:create",
    )

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
    assert delivery_service.deliveries[0].email == "scout-beta-test@example.com"
    assert delivered_key.startswith("scout_live_")
    assert delivered_key_auth.allowed is True
    assert stored.email == "scout-beta-test@example.com"
    assert account_store.tenants[stored.tenant_id].name == "Builder Person"
    assert delivery_service.deliveries[0].name == "Builder Person"
    assert stored.package_id == "beta_trial"
    assert stored.amount_total_cents == 0


def test_stripe_webhook_paid_package_delivery_includes_package_credit_metadata(
    tmp_path: Path,
) -> None:
    account_store = InMemoryHostedAccountStore()
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    delivery_service = RecordingKeyDeliveryService()
    service = HostedPaymentProvisioningService(
        HostedAccountService(account_store),
        payment_store,
    )
    payload = _standard_1000_checkout_event_payload()
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
    delivered = delivery_service.deliveries[0]

    assert response.status_code == 200
    assert response.json()["delivery_status"] == "delivered"
    assert stored is not None
    assert stored.package_id == "standard_1000"
    assert stored.amount_total_cents == 1000
    assert delivered.package_id == "standard_1000"
    assert delivered.standard_credits == 1000
    assert delivered.browser_credits == 0
    assert delivered.trial_days == 0
    assert "scout_live_" not in response.text


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


def test_stripe_webhook_paid_checkout_tops_up_existing_account_without_key_email(
    tmp_path: Path,
) -> None:
    account_store = InMemoryHostedAccountStore()
    account_service = HostedAccountService(account_store)
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    beta = account_service.provision_account(
        email="scout-beta-test@example.com",
        name="Builder Person",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        key_name="Initial beta key",
    )
    account_service.set_balance(
        beta.tenant.tenant_id,
        standard_credits=60,
        browser_credits=0,
    )
    service = HostedPaymentProvisioningService(account_service, payment_store)
    delivery_service = RecordingKeyDeliveryService()
    payload = _standard_1000_checkout_event_payload()
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
    balance = account_service.get_balance(beta.tenant.tenant_id)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["delivery_status"] == "not_required"
    assert body["tenant_id"] == beta.tenant.tenant_id
    assert body["key_id"] == beta.api_key.key_id
    assert balance.standard_credits_remaining == 1060
    assert balance.browser_credits_remaining == 0
    assert stored is not None
    assert stored.package_id == "standard_1000"
    assert stored.amount_total_cents == 1000
    assert len(delivery_service.deliveries) == 0
    assert "scout_live_" not in response.text


def test_stripe_webhook_beta_trial_for_existing_account_does_not_add_free_credits(
    tmp_path: Path,
) -> None:
    account_store = InMemoryHostedAccountStore()
    account_service = HostedAccountService(account_store)
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    beta = account_service.provision_account(
        email="scout-beta-test@example.com",
        name="Builder Person",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        key_name="Initial beta key",
    )
    account_service.set_balance(
        beta.tenant.tenant_id,
        standard_credits=60,
        browser_credits=0,
    )
    service = HostedPaymentProvisioningService(account_service, payment_store)
    delivery_service = RecordingKeyDeliveryService()
    payload = _checkout_event_payload(checkout_session_id="cs_test_beta_repeat")
    client = _client(service, delivery_service)

    response = client.post(
        "/v1/billing/stripe/webhook",
        content=payload,
        headers={
            "content-type": "application/json",
            "Stripe-Signature": _signature_header(payload),
        },
    )
    stored = _stored_checkout(payment_store, checkout_session_id="cs_test_beta_repeat")
    balance = account_service.get_balance(beta.tenant.tenant_id)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["delivery_status"] == "not_required"
    assert body["tenant_id"] == beta.tenant.tenant_id
    assert body["key_id"] == beta.api_key.key_id
    assert balance.standard_credits_remaining == 60
    assert balance.browser_credits_remaining == 0
    assert stored is not None
    assert stored.package_id == "beta_trial"
    assert stored.amount_total_cents == 0
    assert len(delivery_service.deliveries) == 0
    assert "scout_live_" not in response.text


def test_stripe_webhook_invoice_paid_resets_subscriber_credits(tmp_path: Path) -> None:
    account_store = InMemoryHostedAccountStore()
    account_service = HostedAccountService(account_store)
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    service = HostedPaymentProvisioningService(account_service, payment_store)
    # Seed an active unlimited subscriber via a completed subscription checkout.
    checkout_payload = _unlimited_subscription_checkout_event_payload()
    delivery_service = RecordingKeyDeliveryService()
    client = _client(service, delivery_service)
    client.post(
        "/v1/billing/stripe/webhook",
        content=checkout_payload,
        headers={
            "content-type": "application/json",
            "Stripe-Signature": _signature_header(checkout_payload),
        },
    )
    seeded = _stored_checkout(payment_store, checkout_session_id="cs_sub_int_001")
    assert seeded is not None
    tenant_id = seeded.tenant_id
    account_service.set_balance(tenant_id, standard_credits=12345, browser_credits=0)

    invoice_payload = _invoice_paid_event_payload()
    response = client.post(
        "/v1/billing/stripe/webhook",
        content=invoice_payload,
        headers={
            "content-type": "application/json",
            "Stripe-Signature": _signature_header(invoice_payload),
        },
    )
    balance = account_service.get_balance(tenant_id)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["ignored"] is False
    assert balance.standard_credits_remaining == 50000
    assert "scout_live_" not in response.text


def test_stripe_webhook_subscription_deleted_revokes_subscriber(tmp_path: Path) -> None:
    account_store = InMemoryHostedAccountStore()
    account_service = HostedAccountService(account_store)
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    service = HostedPaymentProvisioningService(account_service, payment_store)
    checkout_payload = _unlimited_subscription_checkout_event_payload()
    client = _client(service, RecordingKeyDeliveryService())
    client.post(
        "/v1/billing/stripe/webhook",
        content=checkout_payload,
        headers={
            "content-type": "application/json",
            "Stripe-Signature": _signature_header(checkout_payload),
        },
    )
    seeded = _stored_checkout(payment_store, checkout_session_id="cs_sub_int_001")
    assert seeded is not None
    tenant_id = seeded.tenant_id

    deleted_payload = _subscription_deleted_event_payload()
    response = client.post(
        "/v1/billing/stripe/webhook",
        content=deleted_payload,
        headers={
            "content-type": "application/json",
            "Stripe-Signature": _signature_header(deleted_payload),
        },
    )
    balance = account_service.get_balance(tenant_id)
    tenant = account_service.get_tenant(tenant_id)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert balance.standard_credits_remaining == 0
    assert tenant is not None
    assert tenant.plan is not HostedPlan.HOSTED_UNLIMITED


def test_stripe_webhook_invoice_paid_rejects_bad_signature(tmp_path: Path) -> None:
    payment_store = SQLiteHostedPaymentStore(tmp_path / "hosted.sqlite")
    service = _payment_service(payment_store)
    client = _client(service, RecordingKeyDeliveryService())

    response = client.post(
        "/v1/billing/stripe/webhook",
        content=_invoice_paid_event_payload(),
        headers={
            "content-type": "application/json",
            "Stripe-Signature": "t=123,v1=wrong",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Stripe webhook signature."


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
    checkout_session_id: str = "cs_test_beta_001",
) -> HostedCheckoutProvisioningRecord | None:
    """Return the stored checkout fixture, if the webhook provisioned it."""
    return payment_store.get_checkout(
        HostedPaymentProvider.STRIPE,
        checkout_session_id,
    )


def _checkout_event_payload(checkout_session_id: str = "cs_test_beta_001") -> bytes:
    """Return a Stripe checkout.session.completed event payload."""
    return _event_payload(
        {
            "id": "evt_test_001",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": checkout_session_id,
                    "customer": "cus_test_001",
                    "setup_intent": "seti_test_001",
                    "amount_total": 0,
                    "currency": "usd",
                    "payment_status": "no_payment_required",
                    "metadata": {
                        "package_id": "beta_trial",
                        "name": "Builder Person",
                    },
                    "customer_details": {
                        "email": "scout-beta-test@example.com",
                        "name": "Builder Person",
                    },
                }
            },
        }
    )


def _standard_1000_checkout_event_payload() -> bytes:
    """Return a paid Stripe checkout.session.completed event payload."""
    return _event_payload(
        {
            "id": "evt_test_paid_001",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_beta_001",
                    "customer": "cus_test_001",
                    "payment_intent": "pi_test_001",
                    "amount_total": 1000,
                    "currency": "usd",
                    "payment_status": "paid",
                    "metadata": {
                        "package_id": "standard_1000",
                        "name": "Builder Person",
                    },
                    "customer_details": {
                        "email": "scout-beta-test@example.com",
                        "name": "Builder Person",
                    },
                }
            },
        }
    )


def _unlimited_subscription_checkout_event_payload() -> bytes:
    """Return an unlimited-subscription checkout.session.completed event payload."""
    return _event_payload(
        {
            "id": "evt_sub_checkout_001",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_sub_int_001",
                    "mode": "subscription",
                    "customer": "cus_sub_int_001",
                    "subscription": "sub_int_001",
                    "amount_total": 1200,
                    "currency": "usd",
                    "payment_status": "paid",
                    "metadata": {
                        "package_id": "unlimited_monthly",
                        "plan": "hosted_unlimited",
                        "name": "Builder Person",
                    },
                    "customer_details": {
                        "email": "scout-beta-test@example.com",
                        "name": "Builder Person",
                    },
                }
            },
        }
    )


def _invoice_paid_event_payload() -> bytes:
    """Return a Stripe invoice.paid event payload for the seeded subscriber."""
    return _event_payload(
        {
            "id": "evt_invoice_paid_001",
            "type": "invoice.paid",
            "data": {
                "object": {
                    "id": "in_int_001",
                    "customer": "cus_sub_int_001",
                    "subscription": "sub_int_001",
                }
            },
        }
    )


def _subscription_deleted_event_payload() -> bytes:
    """Return a Stripe customer.subscription.deleted event payload."""
    return _event_payload(
        {
            "id": "evt_sub_deleted_001",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_int_001",
                    "customer": "cus_sub_int_001",
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
