"""Billing and payment webhook routes."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from scout.api.deps import (
    get_hosted_key_delivery_service,
    get_hosted_payment_provisioning_service,
    get_stripe_webhook_secret,
)
from scout.core.platform.hosted import HostedPlan
from scout.core.platform.key_delivery import (
    HostedApiKeyDeliveryRequest,
    HostedApiKeyDeliveryService,
)
from scout.core.platform.payment_provisioning import (
    HostedCheckoutPaymentStatus,
    HostedCheckoutProvisioningRequest,
    HostedCheckoutProvisioningResult,
    HostedPaymentProvider,
    HostedPaymentProvisioningService,
)

router = APIRouter(prefix="/v1/billing", tags=["billing"])

STRIPE_SIGNATURE_TOLERANCE_SECONDS = 300


class StripeWebhookResponse(BaseModel):
    """Non-secret billing webhook result."""

    success: bool
    ignored: bool = False
    already_processed: bool = False
    tenant_id: str = ""
    key_id: str = ""
    reason: str = ""
    delivery_status: str = ""


@router.post("/stripe/webhook", response_model=StripeWebhookResponse)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(default="", alias="Stripe-Signature"),
    webhook_secret: str = Depends(get_stripe_webhook_secret),
    payment_service: HostedPaymentProvisioningService = Depends(
        get_hosted_payment_provisioning_service
    ),
    delivery_service: HostedApiKeyDeliveryService = Depends(get_hosted_key_delivery_service),
) -> StripeWebhookResponse:
    """Verify a Stripe webhook and provision hosted beta access."""
    payload = await request.body()
    _verify_stripe_signature(payload, stripe_signature, webhook_secret)
    event = _parse_event(payload)
    if event.get("type") != "checkout.session.completed":
        return StripeWebhookResponse(success=True, ignored=True)
    checkout = _checkout_request(event)
    if not delivery_service.enabled:
        raise HTTPException(status_code=503, detail="Hosted API key delivery is not configured.")
    result = payment_service.process_checkout(checkout)
    delivery_status = _deliver_api_key(result, checkout, delivery_service)
    return StripeWebhookResponse(
        success=result.success,
        already_processed=result.already_processed,
        tenant_id=result.tenant_id,
        key_id=result.key_id,
        reason=result.reason,
        delivery_status=delivery_status,
    )


def _verify_stripe_signature(payload: bytes, header: str, secret: str) -> None:
    """Raise when the Stripe signature header is missing or invalid."""
    if header == "":
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header.")
    if secret == "":
        raise HTTPException(status_code=500, detail="Stripe webhook secret is not configured.")

    timestamp = _signature_timestamp(header)
    signature = _signature_value(header)
    if timestamp is None or signature == "":
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature.")
    if abs(int(time.time()) - timestamp) > STRIPE_SIGNATURE_TOLERANCE_SECONDS:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature.")

    expected = _expected_signature(payload, timestamp, secret)
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook signature.")


def _deliver_api_key(
    result: HostedCheckoutProvisioningResult,
    checkout: HostedCheckoutProvisioningRequest,
    delivery_service: HostedApiKeyDeliveryService,
) -> str:
    """Deliver a newly generated API key or return the replay status."""
    if result.already_processed:
        return "not_required"
    if not result.success:
        return "not_delivered"
    delivery = delivery_service.deliver(
        HostedApiKeyDeliveryRequest(
            email=checkout.email,
            tenant_id=result.tenant_id,
            key_id=result.key_id,
            plan=checkout.plan,
            raw_api_key=result.raw_api_key,
            checkout_session_id=checkout.checkout_session_id,
        )
    )
    if not delivery.delivered:
        raise HTTPException(status_code=502, detail=delivery.reason)
    return delivery.delivery_status


def _parse_event(payload: bytes) -> dict[str, object]:
    """Parse the Stripe event payload."""
    try:
        event = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook payload.") from exc
    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook payload.")
    return event


def _checkout_request(event: dict[str, object]) -> HostedCheckoutProvisioningRequest:
    """Translate a Stripe checkout event to the hosted payment domain request."""
    session = _checkout_session(event)
    return HostedCheckoutProvisioningRequest(
        provider=HostedPaymentProvider.STRIPE,
        checkout_session_id=str(session.get("id", "")),
        customer_id=str(session.get("customer", "")),
        payment_intent_id=str(session.get("payment_intent", "")),
        email=_checkout_email(session),
        amount_total_cents=_checkout_amount_total(session),
        currency=str(session.get("currency", "")).lower(),
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
        status=HostedCheckoutPaymentStatus(str(session.get("payment_status", "unpaid"))),
    )


def _checkout_session(event: dict[str, object]) -> dict[str, object]:
    """Return the checkout session object from a Stripe event."""
    data = event.get("data")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Invalid Stripe checkout session.")
    session = data.get("object")
    if not isinstance(session, dict):
        raise HTTPException(status_code=400, detail="Invalid Stripe checkout session.")
    return session


def _checkout_email(session: dict[str, object]) -> str:
    """Return the best customer email from a Stripe checkout session."""
    details = session.get("customer_details")
    if isinstance(details, dict) and details.get("email"):
        return str(details["email"])
    return str(session.get("customer_email", ""))


def _checkout_amount_total(session: dict[str, object]) -> int:
    """Return checkout amount total from a Stripe checkout session."""
    amount = session.get("amount_total", 0)
    if isinstance(amount, int):
        return amount
    if isinstance(amount, str):
        return int(amount)
    return 0


def _signature_timestamp(header: str) -> int | None:
    """Extract the Stripe signature timestamp."""
    for part in header.split(","):
        key, _, value = part.partition("=")
        if key == "t":
            try:
                return int(value)
            except ValueError:
                return None
    return None


def _signature_value(header: str) -> str:
    """Extract the first Stripe v1 signature from a header."""
    for part in header.split(","):
        key, _, value = part.partition("=")
        if key == "v1":
            return value
    return ""


def _expected_signature(payload: bytes, timestamp: int, secret: str) -> str:
    """Return the expected Stripe webhook HMAC digest."""
    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    return hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
