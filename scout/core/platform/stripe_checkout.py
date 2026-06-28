"""Stripe Checkout Session creation for hosted Scout beta access."""

from __future__ import annotations

import json
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field


class StripeCheckoutConfig(BaseModel):
    """Configuration required to create Stripe Checkout Sessions."""

    secret_key: str = Field(default="", exclude=True)
    beta_price_id: str = ""
    success_url: str = ""
    cancel_url: str = ""
    endpoint_url: str = "https://api.stripe.com/v1/checkout/sessions"
    timeout_seconds: float = 20.0

    @property
    def enabled(self) -> bool:
        """Return whether the checkout integration has all required settings."""
        return all(
            [
                self.secret_key,
                self.beta_price_id,
                self.success_url,
                self.cancel_url,
            ]
        )


class StripeCheckoutRequest(BaseModel):
    """Request to create a hosted beta Checkout Session."""

    email: str = ""


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

    def create_beta_checkout_session(
        self,
        request: StripeCheckoutRequest,
    ) -> StripeCheckoutResult:
        """Create a Stripe Checkout Session for the hosted beta pass."""
        if not self._config.enabled:
            return StripeCheckoutResult(
                success=False,
                reason="Stripe Checkout is not configured.",
            )
        data = {
            "mode": "payment",
            "line_items[0][price]": self._config.beta_price_id,
            "line_items[0][quantity]": "1",
            "success_url": self._config.success_url,
            "cancel_url": self._config.cancel_url,
            "metadata[plan]": "hosted_beta_pass",
            "metadata[product]": "scout_hosted_beta",
        }
        if request.email.strip():
            data["customer_email"] = request.email.strip()
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
