"""Hosted API-key delivery contracts."""

from __future__ import annotations

import smtplib
from collections.abc import Callable
from email.message import EmailMessage
from types import TracebackType
from typing import Any, Protocol

from pydantic import BaseModel, EmailStr, Field

from scout.core.platform.hosted import HostedPlan


class HostedApiKeyDeliveryRequest(BaseModel):
    """One-time raw API-key delivery request."""

    email: EmailStr
    name: str = ""
    tenant_id: str
    key_id: str
    plan: HostedPlan
    package_id: str = "beta_trial"
    standard_credits: int = Field(default=100, ge=0)
    browser_credits: int = Field(default=0, ge=0)
    trial_days: int = Field(default=30, ge=0)
    raw_api_key: str
    checkout_session_id: str
    smoke_test: bool = False


class HostedApiKeyDeliveryResult(BaseModel):
    """Result of attempting to deliver a raw hosted API key."""

    delivered: bool
    delivery_status: str
    reason: str = ""


class HostedApiKeyDeliveryService(Protocol):
    """Delivery contract for one-time raw API-key handoff."""

    enabled: bool

    def deliver(self, request: HostedApiKeyDeliveryRequest) -> HostedApiKeyDeliveryResult:
        """Deliver a raw API key exactly once."""
        ...


class DisabledHostedApiKeyDeliveryService:
    """Disabled delivery service used until email or portal delivery exists."""

    enabled = False

    def deliver(self, request: HostedApiKeyDeliveryRequest) -> HostedApiKeyDeliveryResult:
        """Return a disabled delivery result."""
        return HostedApiKeyDeliveryResult(
            delivered=False,
            delivery_status="disabled",
            reason="Hosted API key delivery is not configured.",
        )


class SmtpHostedApiKeyDeliveryConfig(BaseModel):
    """Configuration for SMTP-based hosted API-key delivery."""

    host: str = ""
    port: int = 587
    from_email: str = ""
    username: str = ""
    password: str = Field(default="", exclude=True)
    use_tls: bool = True
    timeout_seconds: float = 10.0

    @property
    def enabled(self) -> bool:
        """Return whether enough SMTP config exists to deliver keys."""
        return (
            self.host != ""
            and self.from_email != ""
            and self.username != ""
            and self.password != ""
        )


class SmtpClient(Protocol):
    """Minimal SMTP client protocol used by the delivery service."""

    def __enter__(self) -> SmtpClient:
        """Enter SMTP context manager."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit SMTP context manager."""
        ...

    def starttls(self) -> Any:
        """Start TLS for SMTP."""
        ...

    def login(self, user: str, password: str) -> Any:
        """Authenticate to SMTP."""
        ...

    def sendmail(self, from_addr: str, to_addrs: list[str], msg: str) -> Any:
        """Send an SMTP message."""
        ...


SmtpFactory = Callable[[str, int, float], SmtpClient]


def _default_smtp_factory(host: str, port: int, timeout: float) -> SmtpClient:
    """Create a standard-library SMTP client."""
    return smtplib.SMTP(host, port, timeout=timeout)


class SmtpHostedApiKeyDeliveryService:
    """SMTP implementation for one-time hosted API-key delivery."""

    def __init__(
        self,
        config: SmtpHostedApiKeyDeliveryConfig,
        smtp_factory: SmtpFactory | None = None,
    ) -> None:
        self.config = config
        self.smtp_factory = smtp_factory or _default_smtp_factory

    @property
    def enabled(self) -> bool:
        """Return whether SMTP delivery is configured."""
        return self.config.enabled

    def deliver(self, request: HostedApiKeyDeliveryRequest) -> HostedApiKeyDeliveryResult:
        """Send a one-time hosted API key email."""
        if not self.enabled:
            return HostedApiKeyDeliveryResult(
                delivered=False,
                delivery_status="disabled",
                reason="Hosted API key delivery is not configured.",
            )
        try:
            self._send_message(request)
        except Exception as exc:
            return HostedApiKeyDeliveryResult(
                delivered=False,
                delivery_status="failed",
                reason=f"SMTP delivery failed: {exc}",
            )
        return HostedApiKeyDeliveryResult(delivered=True, delivery_status="delivered")

    def _send_message(self, request: HostedApiKeyDeliveryRequest) -> None:
        """Send the SMTP message through the configured client."""
        message = _delivery_message(self.config.from_email, request)
        with self.smtp_factory(
            self.config.host,
            self.config.port,
            self.config.timeout_seconds,
        ) as smtp:
            if self.config.use_tls:
                smtp.starttls()
            if self.config.username:
                smtp.login(self.config.username, self.config.password)
            smtp.sendmail(
                self.config.from_email,
                [str(request.email)],
                message.as_string(),
            )


def _delivery_message(sender: str, request: HostedApiKeyDeliveryRequest) -> EmailMessage:
    """Build the one-time API-key delivery email."""
    message = EmailMessage()
    message["From"] = sender
    message["To"] = str(request.email)
    if request.smoke_test:
        message["Subject"] = "Scout hosted key delivery smoke test"
        message.set_content(_smoke_test_body(request))
    else:
        message["Subject"] = _delivery_subject(request)
        message.set_content(_delivery_body(request))
    return message


def _delivery_subject(request: HostedApiKeyDeliveryRequest) -> str:
    """Return the correct non-secret email subject for this delivery."""
    if request.package_id == "beta_trial":
        return "Your Scout beta tester API key is ready"
    return "Your Scout hosted API key is ready"


def _smoke_test_body(request: HostedApiKeyDeliveryRequest) -> str:
    """Build the plaintext body for SMTP smoke-test delivery."""
    greeting_name = request.name.strip() or "there"
    return "\n".join(
        [
            f"Hi {greeting_name},",
            "",
            "This is a delivery smoke test.",
            "It verifies the hosted Scout API-key email path.",
            "No hosted account was created.",
            "No real Scout API key was issued.",
            "No credits were granted or charged.",
            "",
            f"Smoke reference: {request.checkout_session_id}",
            f"Recipient: {request.email}",
            "",
            "If you received this, Scout's SMTP delivery path can reach this inbox.",
            "",
            "Thanks,",
            "Arijit Chowdhury",
            "Founder, Chowmes",
        ]
    )


def _delivery_body(request: HostedApiKeyDeliveryRequest) -> str:
    """Build the plaintext body for one-time API-key delivery."""
    greeting_name = request.name.strip() or "there"
    if request.package_id != "beta_trial":
        return _paid_delivery_body(request, greeting_name)
    return "\n".join(
        [
            f"Hi {greeting_name},",
            "",
            "Welcome to the Scout private beta. I'm glad to have you testing Scout.",
            "",
            "Your hosted beta tester API key is ready.",
            (
                "Your beta trial includes "
                f"{request.standard_credits:,} standard credits for {request.trial_days} days."
            ),
            _browser_credit_line(request),
            "1 scrape, 1 returned crawl page, or 1 product/intelligence record = 1 standard credit.",
            "This is not unlimited hosted crawling.",
            _browser_metering_line(request),
            "",
            "Store this key now. Scout stores only a hash and cannot show the raw key again.",
            "Do not paste this key into frontend code, screenshots, tickets, or public repos.",
            "",
            f"API key: {request.raw_api_key}",
            f"Plan: {request.plan.value}",
            f"Tenant ID: {request.tenant_id}",
            f"Key ID: {request.key_id}",
            f"Reference: {request.checkout_session_id}",
            "",
            "Use this key as a Bearer token when calling hosted Scout endpoints.",
            "",
            "Quick test:",
            "curl https://scout.chowmes.com/v1/hosted/me \\",
            f"  -H 'Authorization: Bearer {request.raw_api_key}'",
            "",
            "First hosted scrape:",
            "curl -X POST https://scout.chowmes.com/v1/hosted/scrape \\",
            f"  -H 'Authorization: Bearer {request.raw_api_key}' \\",
            "  -H 'Content-Type: application/json' \\",
            '  -d \'{"url":"https://example.com","formats":["markdown"]}\'',
            "",
            "Account and balance:",
            "https://scout.chowmes.com/v1/hosted/me",
            "",
            "Usage ledger:",
            "https://scout.chowmes.com/v1/hosted/usage",
            "",
            "Purchase history:",
            "https://scout.chowmes.com/v1/hosted/purchases",
            "",
            "Docs: https://scout.chowmes.com/docs",
            "Pricing and credit model: https://scout.chowmes.com/pricing",
            "",
            "Reply to this email with your use case, target site, and any failing run ID.",
            "",
            "Thanks,",
            "Arijit Chowdhury",
            "Founder, Chowmes",
        ]
    )


def _paid_delivery_body(request: HostedApiKeyDeliveryRequest, greeting_name: str) -> str:
    """Build the plaintext body for paid hosted API-key delivery."""
    return "\n".join(
        [
            f"Hi {greeting_name},",
            "",
            "Your hosted Scout API key is ready.",
            "",
            f"Package: {request.package_id}",
            f"Credits: {_credit_summary(request)}",
            "Store this key now. Scout stores only a hash and cannot show the raw key again.",
            "Do not paste this key into frontend code, screenshots, tickets, or public repos.",
            "",
            f"API key: {request.raw_api_key}",
            f"Plan: {request.plan.value}",
            f"Tenant ID: {request.tenant_id}",
            f"Key ID: {request.key_id}",
            f"Reference: {request.checkout_session_id}",
            "",
            "Use this key as a Bearer token when calling hosted Scout endpoints.",
            "",
            "Quick test:",
            "curl https://scout.chowmes.com/v1/hosted/me \\",
            f"  -H 'Authorization: Bearer {request.raw_api_key}'",
            "",
            "Account and balance:",
            "https://scout.chowmes.com/account",
            "",
            "Docs: https://scout.chowmes.com/docs",
            "Pricing and credit model: https://scout.chowmes.com/pricing",
            "",
            "Reply to this email with your use case, target site, and any failing run ID.",
            "",
            "Thanks,",
            "Arijit Chowdhury",
            "Founder, Chowmes",
        ]
    )


def _browser_credit_line(request: HostedApiKeyDeliveryRequest) -> str:
    """Return beta browser-credit line for the email body."""
    if request.browser_credits > 0:
        return f"Your beta trial also includes {request.browser_credits:,} hosted browser credits."
    return "Hosted browser credits are not included in this beta key."


def _browser_metering_line(request: HostedApiKeyDeliveryRequest) -> str:
    """Return browser metering copy for the beta email body."""
    if request.browser_credits > 0:
        return "Hosted browser work draws from the separate browser-credit balance."
    return "Hosted browser work is separately metered and is not included in this beta key."


def _credit_summary(request: HostedApiKeyDeliveryRequest) -> str:
    """Return a customer-readable credit summary."""
    return (
        f"{request.standard_credits:,} standard credits, "
        f"{request.browser_credits:,} browser credits"
    )
