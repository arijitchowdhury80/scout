"""Stripe Checkout Session creation for hosted Scout beta access."""

from __future__ import annotations

import json
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from scout.core.platform.pricing import credit_packages, get_credit_package


class StripeCheckoutConfig(BaseModel):
    """Configuration required to create Stripe Checkout Sessions."""

    secret_key: str = Field(default="", exclude=True)
    beta_price_id: str = ""
    standard_1000_price_id: str = ""
    standard_3000_price_id: str = ""
    standard_15000_price_id: str = ""
    browser_100_price_id: str = ""
    success_url: str = ""
    cancel_url: str = ""
    beta_success_url: str = ""
    beta_cancel_url: str = ""
    endpoint_url: str = "https://api.stripe.com/v1/checkout/sessions"
    timeout_seconds: float = 20.0

    @property
    def enabled(self) -> bool:
        """Return whether the checkout integration has all required settings."""
        return all(
            [
                self.secret_key,
                self.success_url,
                self.cancel_url,
            ]
        )

    def price_id_for_package(self, package_id: str) -> str:
        """Return the configured Stripe price id for a paid package."""
        price_ids = {
            "standard_1000": self.standard_1000_price_id,
            "standard_3000": self.standard_3000_price_id,
            "standard_15000": self.standard_15000_price_id,
            "browser_100": self.browser_100_price_id,
        }
        return price_ids.get(package_id, "")

    @property
    def paid_packages_configured(self) -> bool:
        """Return whether every public paid package has a Stripe price id."""
        public_paid_package_ids = [
            package.package_id
            for package in credit_packages()
            if package.is_public_purchase and package.amount_cents > 0
        ]
        return all(
            self.price_id_for_package(package_id) != "" for package_id in public_paid_package_ids
        )

    def success_url_for_package(self, package_id: str) -> str:
        """Return the package-specific success URL when configured."""
        if package_id == "beta_trial" and self.beta_success_url:
            return self.beta_success_url
        return self.success_url

    def cancel_url_for_package(self, package_id: str) -> str:
        """Return the package-specific cancel URL when configured."""
        if package_id == "beta_trial" and self.beta_cancel_url:
            return self.beta_cancel_url
        return self.cancel_url


class StripeCheckoutRequest(BaseModel):
    """Request to create a hosted beta Checkout Session."""

    email: str = ""
    name: str = ""
    package_id: str = "beta_trial"


class StripeCheckoutSession(BaseModel):
    """Minimal Stripe Checkout Session response Scout needs."""

    id: str
    url: str


class StripeCheckoutResult(BaseModel):
    """Non-secret result returned to callers after checkout creation."""

    success: bool
    checkout_session_id: str = ""
    checkout_url: str = ""
    reason: str = ""


class StripeCheckoutTransport(Protocol):
    """Transport boundary for posting form-encoded data to Stripe."""

    def post_form(
        self,
        url: str,
        data: dict[str, str],
        headers: dict[str, str],
    ) -> StripeCheckoutSession:
        """Post a form-encoded request and return a checkout session."""
        ...


class UrllibStripeCheckoutTransport:
    """Stdlib transport for Stripe Checkout Session creation."""

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._timeout_seconds = timeout_seconds

    def post_form(
        self,
        url: str,
        data: dict[str, str],
        headers: dict[str, str],
    ) -> StripeCheckoutSession:
        """Post form data to Stripe and parse the minimal session response."""
        encoded = urlencode(data).encode("utf-8")
        request = Request(url, data=encoded, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise StripeCheckoutError(f"Stripe Checkout request failed: {message}") from exc
        except (OSError, URLError, json.JSONDecodeError) as exc:
            raise StripeCheckoutError("Stripe Checkout request failed.") from exc
        if not isinstance(payload, dict):
            raise StripeCheckoutError("Stripe Checkout response was invalid.")
        session_id = str(payload.get("id", ""))
        checkout_url = str(payload.get("url", ""))
        if session_id == "" or checkout_url == "":
            raise StripeCheckoutError("Stripe Checkout response was missing session data.")
        return StripeCheckoutSession(id=session_id, url=checkout_url)


class StripeCheckoutService:
    """Create hosted Scout beta payment sessions through Stripe Checkout."""

    def __init__(
        self,
        config: StripeCheckoutConfig,
        transport: StripeCheckoutTransport | None = None,
    ) -> None:
        self._config = config
        self._transport = transport or UrllibStripeCheckoutTransport(config.timeout_seconds)

    @property
    def enabled(self) -> bool:
        """Return whether Stripe Checkout creation has required configuration."""
        return self._config.enabled

    @property
    def paid_packages_configured(self) -> bool:
        """Return whether public paid packages can create checkout sessions."""
        return self._config.paid_packages_configured

    def create_checkout_session(
        self,
        request: StripeCheckoutRequest,
    ) -> StripeCheckoutResult:
        """Create a Stripe Checkout Session for a hosted credit package."""
        if not self._config.enabled:
            return StripeCheckoutResult(
                success=False,
                reason="Stripe Checkout is not configured.",
            )
        try:
            package = get_credit_package(request.package_id)
        except ValueError as exc:
            return StripeCheckoutResult(success=False, reason=str(exc))
        if package.amount_cents == 0:
            data = {
                "mode": "setup",
                "payment_method_types[0]": "card",
                "success_url": self._config.success_url_for_package(package.package_id),
                "cancel_url": self._config.cancel_url_for_package(package.package_id),
                "metadata[package_id]": package.package_id,
                "metadata[plan]": "hosted_beta_pass",
                "metadata[product]": "scout_hosted",
            }
        else:
            price_id = self._config.price_id_for_package(package.package_id)
            if price_id == "":
                return StripeCheckoutResult(
                    success=False,
                    reason=f"Stripe price is not configured for package {package.package_id}.",
                )
            data = {
                "mode": "payment",
                "customer_creation": "always",
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": "1",
                "success_url": self._config.success_url_for_package(package.package_id),
                "cancel_url": self._config.cancel_url_for_package(package.package_id),
                "metadata[package_id]": package.package_id,
                "metadata[plan]": "hosted_beta_pass",
                "metadata[product]": "scout_hosted",
            }
        if request.email.strip():
            data["customer_email"] = request.email.strip()
        if request.name.strip():
            data["metadata[name]"] = request.name.strip()
        return self._post_checkout_session(data)

    def create_beta_checkout_session(
        self,
        request: StripeCheckoutRequest,
    ) -> StripeCheckoutResult:
        """Compatibility wrapper for the hosted beta trial checkout."""
        return self.create_checkout_session(
            request.model_copy(update={"package_id": request.package_id or "beta_trial"})
        )

    def _post_checkout_session(self, data: dict[str, str]) -> StripeCheckoutResult:
        """Send a prepared Checkout Session form payload to Stripe."""
        headers = {
            "Authorization": f"Bearer {self._config.secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            session = self._transport.post_form(
                self._config.endpoint_url,
                data,
                headers,
            )
        except StripeCheckoutError as exc:
            return StripeCheckoutResult(success=False, reason=str(exc))
        return StripeCheckoutResult(
            success=True,
            checkout_session_id=session.id,
            checkout_url=session.url,
        )


class StripeCheckoutError(RuntimeError):
    """Raised when Stripe Checkout Session creation fails."""
