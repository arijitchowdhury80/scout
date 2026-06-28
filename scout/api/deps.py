"""Shared FastAPI dependencies — importable by all routers."""

from fastapi import Request

from scout.api.config import settings
from scout.api.db import RunDB
from scout.core.crawler import ScoutCrawler
from scout.core.platform.account_service import HostedAccountService
from scout.core.platform.key_delivery import (
    DisabledHostedApiKeyDeliveryService,
    HostedApiKeyDeliveryService,
)
from scout.core.platform.payment_provisioning import HostedPaymentProvisioningService
from scout.core.platform.hosted_rate_limit import HostedRateLimitConfig, HostedRateLimiter
from scout.core.platform.stripe_checkout import StripeCheckoutConfig, StripeCheckoutService


def get_crawler(request: Request) -> ScoutCrawler:
    """Return the ScoutCrawler instance stored on app.state at startup."""
    crawler: ScoutCrawler = request.app.state.crawler
    return crawler


def get_crawler_optional(request: Request) -> ScoutCrawler | None:
    """Return the crawler if available, else None (for seed-data fallback)."""
    return getattr(request.app.state, "crawler", None)


def get_run_db(request: Request) -> RunDB:
    """Return the RunDB instance stored on app.state at startup."""
    run_db: RunDB = request.app.state.run_db
    return run_db


def get_hosted_account_service(request: Request) -> HostedAccountService:
    """Return the hosted account service stored on app.state at startup."""
    service: HostedAccountService = request.app.state.hosted_account_service
    return service


def get_hosted_payment_provisioning_service(
    request: Request,
) -> HostedPaymentProvisioningService:
    """Return the hosted payment provisioning service stored on app.state."""
    service: HostedPaymentProvisioningService = request.app.state.hosted_payment_service
    return service


def get_stripe_webhook_secret() -> str:
    """Return the configured Stripe webhook signing secret."""
    return settings.stripe_webhook_secret


def get_stripe_checkout_service(request: Request) -> StripeCheckoutService:
    """Return the Stripe Checkout service stored on app.state."""
    service: StripeCheckoutService = getattr(
        request.app.state,
        "stripe_checkout_service",
        StripeCheckoutService(StripeCheckoutConfig()),
    )
    return service


def get_hosted_key_delivery_service(request: Request) -> HostedApiKeyDeliveryService:
    """Return the hosted API-key delivery service stored on app.state."""
    service: HostedApiKeyDeliveryService = getattr(
        request.app.state,
        "hosted_key_delivery_service",
        DisabledHostedApiKeyDeliveryService(),
    )
    return service


def get_hosted_rate_limiter(request: Request) -> HostedRateLimiter:
    """Return the hosted per-key rate limiter stored on app.state."""
    limiter: HostedRateLimiter = getattr(
        request.app.state,
        "hosted_rate_limiter",
        HostedRateLimiter(HostedRateLimitConfig(enabled=False)),
    )
    return limiter
