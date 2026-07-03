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
    raw_api_key: str
    checkout_session_id: str


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
        return self.host != "" and self.from_email != ""


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
    message["Subject"] = "Your Scout beta tester API key is ready"
    message.set_content(_delivery_body(request))
    return message


def _delivery_body(request: HostedApiKeyDeliveryRequest) -> str:
    """Build the plaintext body for one-time API-key delivery."""
    greeting_name = request.name.strip() or "there"
    return "\n".join(
        [
            f"Hi {greeting_name},",
            "",
            "Welcome to the Scout private beta. I'm glad to have you testing Scout.",
            "",
            "Your hosted beta tester API key is ready.",
            "Your beta trial includes 100 standard credits for 30 days.",
            "1 scrape, 1 returned crawl page, or 1 product/intelligence record = 1 standard credit.",
            "This is not unlimited hosted crawling.",
            "Hosted browser work is separately metered and is not included in this beta key.",
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
