"""Billing and payment webhook routes."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from scout.api.config import settings
from scout.api.deps import (
    get_hosted_account_service,
    get_hosted_key_delivery_service,
    get_hosted_payment_provisioning_service,
    get_stripe_checkout_service,
    get_stripe_webhook_secret,
)
from scout.core.platform.account_service import (
    HostedAccountService,
    HostedAccountSnapshot,
    HostedSignupEvent,
    HostedUsageLedgerEntry,
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
from scout.core.platform.pricing import (
    PackageUnitEconomics,
    credit_cost_table,
    credit_packages,
    package_unit_economics,
)
from scout.core.platform.stripe_checkout import (
    StripeCheckoutRequest,
    StripeCheckoutResult,
    StripeCheckoutService,
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


class StripeCheckoutSessionRequestBody(BaseModel):
    """Request body for creating a hosted Scout beta checkout session."""

    name: str = ""
    email: str = ""
    package_id: str = "beta_trial"


class StripeCheckoutSessionResponse(BaseModel):
    """Non-secret Stripe Checkout creation response."""

    success: bool
    checkout_session_id: str = ""
    checkout_url: str = ""
    reason: str = ""


class StripeBillingStatusResponse(BaseModel):
    """Non-secret Stripe billing readiness flags."""

    beta_signup_enabled: bool
    checkout_configured: bool
    webhook_configured: bool
    key_delivery_configured: bool
    ready_for_beta_key_delivery: bool
    ready_for_beta_checkout: bool
    ready_for_paid_key_delivery: bool


class HostedBillingPackagesResponse(BaseModel):
    """Public non-secret hosted package and credit metadata."""

    packages: list[dict[str, object]]
    credit_costs: dict[str, str]
    unit_economics: dict[str, PackageUnitEconomics]


class HostedBillingAdminMetricsResponse(BaseModel):
    """Service-key protected hosted billing and usage monitoring summary."""

    success: bool = True
    totals: dict[str, int]
    recent_accounts: list[HostedAccountSnapshot]
    recent_signup_events: list[HostedSignupEvent]
    recent_usage: list[HostedUsageLedgerEntry]
    recent_purchases: list[dict[str, object]]


@router.get("/packages", response_model=HostedBillingPackagesResponse)
async def billing_packages() -> HostedBillingPackagesResponse:
    """Return public hosted credit packages, credit meanings, and economics."""
    packages = [package.model_dump(mode="json") for package in credit_packages()]
    economics = {
        package["package_id"]: package_unit_economics(str(package["package_id"]))
        for package in packages
    }
    return HostedBillingPackagesResponse(
        packages=packages,
        credit_costs=credit_cost_table(),
        unit_economics=economics,
    )


@router.get("/admin/metrics", response_model=HostedBillingAdminMetricsResponse)
async def billing_admin_metrics(
    account_service: HostedAccountService = Depends(get_hosted_account_service),
    payment_service: HostedPaymentProvisioningService = Depends(
        get_hosted_payment_provisioning_service
    ),
) -> HostedBillingAdminMetricsResponse:
    """Return non-secret hosted signup, purchase, and usage telemetry for operators."""
    accounts = account_service.list_accounts(limit=100)
    signup_events = account_service.list_signup_events(limit=100)
    usage = account_service.list_all_usage(limit=500)
    purchases = payment_service.payment_store.list_checkouts(limit=100)
    totals = {
        "accounts": len(accounts),
        "active_accounts": sum(1 for account in accounts if account.account_status == "active"),
        "disabled_accounts": sum(1 for account in accounts if account.account_status == "disabled"),
        "signup_events": len(signup_events),
        "signup_delivered": sum(1 for event in signup_events if event.status == "delivered"),
        "signup_failed": sum(1 for event in signup_events if event.status == "failed"),
        "signup_duplicate": sum(1 for event in signup_events if event.status == "duplicate"),
        "standard_credits_remaining": sum(
            account.standard_credits_remaining for account in accounts
        ),
        "browser_credits_remaining": sum(account.browser_credits_remaining for account in accounts),
        "usage_events": len(usage),
        "standard_credits_used": sum(
            entry.credits for entry in usage if entry.credit_type == "standard"
        ),
        "browser_credits_used": sum(
            entry.credits for entry in usage if entry.credit_type == "browser"
        ),
        "purchases": len(purchases),
        "revenue_cents": sum(purchase.amount_total_cents for purchase in purchases),
    }
    return HostedBillingAdminMetricsResponse(
        totals=totals,
        recent_accounts=accounts,
        recent_signup_events=signup_events,
        recent_usage=usage[:100],
        recent_purchases=[purchase.model_dump(mode="json") for purchase in purchases],
    )


@router.get("/stripe/status", response_model=StripeBillingStatusResponse)
async def stripe_status(
    webhook_secret: str = Depends(get_stripe_webhook_secret),
    checkout_service: StripeCheckoutService = Depends(get_stripe_checkout_service),
    delivery_service: HostedApiKeyDeliveryService = Depends(get_hosted_key_delivery_service),
) -> StripeBillingStatusResponse:
    """Return non-secret Stripe readiness for the launch website."""
    beta_signup_enabled = settings.hosted_beta_signup_enabled
    checkout_configured = checkout_service.enabled
    webhook_configured = webhook_secret != ""
    key_delivery_configured = delivery_service.enabled
    return StripeBillingStatusResponse(
        beta_signup_enabled=beta_signup_enabled,
        checkout_configured=checkout_configured,
        webhook_configured=webhook_configured,
        key_delivery_configured=key_delivery_configured,
        ready_for_beta_key_delivery=beta_signup_enabled and key_delivery_configured,
        ready_for_beta_checkout=(
            beta_signup_enabled
            and checkout_configured
            and webhook_configured
            and key_delivery_configured
        ),
        ready_for_paid_key_delivery=(
            checkout_configured and webhook_configured and key_delivery_configured
        ),
    )


@router.post("/stripe/checkout-session", response_model=StripeCheckoutSessionResponse)
async def stripe_checkout_session(
    body: StripeCheckoutSessionRequestBody,
    webhook_secret: str = Depends(get_stripe_webhook_secret),
    checkout_service: StripeCheckoutService = Depends(get_stripe_checkout_service),
    delivery_service: HostedApiKeyDeliveryService = Depends(get_hosted_key_delivery_service),
) -> StripeCheckoutSessionResponse:
    """Create a Stripe Checkout Session for a hosted Scout credit package."""
    _assert_checkout_ready(body, webhook_secret, delivery_service)
    result = checkout_service.create_checkout_session(
        StripeCheckoutRequest(name=body.name, email=body.email, package_id=body.package_id)
    )
    if not result.success:
        raise HTTPException(status_code=503, detail=result.reason)
    return _checkout_session_response(result)


def _assert_checkout_ready(
    body: StripeCheckoutSessionRequestBody,
    webhook_secret: str,
    delivery_service: HostedApiKeyDeliveryService,
) -> None:
    """Fail closed before creating Stripe sessions that cannot provision keys."""
    if body.package_id == "beta_trial" and not settings.hosted_beta_signup_enabled:
        raise HTTPException(status_code=503, detail="Hosted beta signup is disabled.")
    if webhook_secret == "":
        raise HTTPException(status_code=503, detail="Stripe webhook secret is not configured.")
    if not delivery_service.enabled:
        raise HTTPException(status_code=503, detail="Hosted API key delivery is not configured.")


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


def _checkout_session_response(
    result: StripeCheckoutResult,
) -> StripeCheckoutSessionResponse:
    """Translate the core checkout result to the public API response."""
    return StripeCheckoutSessionResponse(
        success=result.success,
        checkout_session_id=result.checkout_session_id,
        checkout_url=result.checkout_url,
        reason=result.reason,
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
    if result.raw_api_key == "":
        return "not_required"
    delivery = delivery_service.deliver(
        HostedApiKeyDeliveryRequest(
            email=checkout.email,
            name=checkout.name,
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
        payment_intent_id=_checkout_payment_reference(session),
        email=_checkout_email(session),
        name=_checkout_name(session),
        package_id=_checkout_package_id(session),
        amount_total_cents=_checkout_amount_total(session),
        currency=_checkout_currency(session),
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


def _checkout_name(session: dict[str, object]) -> str:
    """Return the best customer name from a Stripe checkout session."""
    details = session.get("customer_details")
    if isinstance(details, dict) and details.get("name"):
        return str(details["name"])
    metadata = session.get("metadata")
    if isinstance(metadata, dict) and metadata.get("name"):
        return str(metadata["name"])
    return ""


def _checkout_amount_total(session: dict[str, object]) -> int:
    """Return checkout amount total from a Stripe checkout session."""
    amount = session.get("amount_total", 0)
    if isinstance(amount, int):
        return amount
    if isinstance(amount, str):
        return int(amount)
    return 0


def _checkout_package_id(session: dict[str, object]) -> str:
    """Return the hosted package id from Stripe metadata."""
    metadata = session.get("metadata")
    if isinstance(metadata, dict) and metadata.get("package_id"):
        return str(metadata["package_id"])
    return "beta_trial"


def _checkout_currency(session: dict[str, object]) -> str:
    """Return checkout currency, defaulting setup sessions to USD."""
    currency = str(session.get("currency", "")).lower()
    if currency:
        return currency
    return "usd"


def _checkout_payment_reference(session: dict[str, object]) -> str:
    """Return payment or setup intent reference from a Stripe checkout session."""
    payment_intent = str(session.get("payment_intent", ""))
    if payment_intent:
        return payment_intent
    return str(session.get("setup_intent", ""))


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
