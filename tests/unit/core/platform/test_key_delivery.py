"""Tests for hosted API-key delivery services.

# Scenario list:
# - disabled delivery service reports disabled without storing the raw key
# - SMTP delivery sends a one-time key email to the checkout customer
# - SMTP delivery includes non-secret hosted metadata and raw key in email body
# - SMTP delivery failures return structured failure results
# - SMTP config is disabled unless host and from email are configured
"""

from __future__ import annotations

from email import message_from_string
from email.message import EmailMessage
from email.policy import default
from types import TracebackType

from scout.core.platform.hosted import HostedPlan
from scout.core.platform.key_delivery import (
    DisabledHostedApiKeyDeliveryService,
    HostedApiKeyDeliveryRequest,
    SmtpHostedApiKeyDeliveryConfig,
    SmtpHostedApiKeyDeliveryService,
)


def test_disabled_delivery_service_reports_disabled() -> None:
    service = DisabledHostedApiKeyDeliveryService()

    result = service.deliver(_delivery_request())

    assert service.enabled is False
    assert result.delivered is False
    assert result.delivery_status == "disabled"
    assert result.reason == "Hosted API key delivery is not configured."


def test_smtp_delivery_service_sends_one_time_key_email() -> None:
    smtp_factory = FakeSmtpFactory()
    service = SmtpHostedApiKeyDeliveryService(
        config=SmtpHostedApiKeyDeliveryConfig(
            host="smtp.example.com",
            port=587,
            from_email="scout@example.com",
            username="scout-user",
            password="smtp-secret",
            use_tls=True,
        ),
        smtp_factory=smtp_factory,
    )

    result = service.deliver(_delivery_request())
    sent = smtp_factory.client.messages[0]

    assert service.enabled is True
    assert result.delivered is True
    assert result.delivery_status == "delivered"
    assert smtp_factory.client.started_tls is True
    assert smtp_factory.client.login_args == ("scout-user", "smtp-secret")
    assert sent.sender == "scout@example.com"
    assert sent.recipients == ["builder@example.com"]
    message = message_from_string(sent.message, policy=default)
    assert isinstance(message, EmailMessage)
    body = str(message.get_content())
    assert message["Subject"] == "Your Scout beta tester API key is ready"
    assert "Hi Builder Person," in body
    assert "I'm glad to have you testing Scout." in body
    assert "Your beta trial includes 100 standard credits for 30 days." in body
    assert "This is not unlimited hosted crawling." in body
    assert (
        "1 scrape, 1 returned crawl page, or 1 product/intelligence record = 1 standard credit."
        in body
    )
    assert "Hosted browser work is separately metered" in body
    assert "Use this key as a Bearer token" in body
    assert "Account and balance:" in body
    assert "Usage ledger:" in body
    assert "Purchase history:" in body
    assert "https://scout.chowmes.com/docs" in body
    assert "https://scout.chowmes.com/pricing" in body
    assert "scout_live_test_key" in body
    assert "tenant_123" in body
    assert "key_123" in body
    assert (
        "Do not paste this key into frontend code, screenshots, tickets, or public repos." in body
    )
    assert "Reply to this email with your use case, target site, and any failing run ID." in body
    assert "Founder, Chowmes" in body
    assert "Arijit Chowdhury" in body


def test_smtp_delivery_service_sends_smoke_test_email_without_real_key_claims() -> None:
    smtp_factory = FakeSmtpFactory()
    service = SmtpHostedApiKeyDeliveryService(
        config=SmtpHostedApiKeyDeliveryConfig(
            host="smtp.example.com",
            port=587,
            from_email="scout@example.com",
            username="scout-user",
            password="smtp-secret",
            use_tls=True,
        ),
        smtp_factory=smtp_factory,
    )

    result = service.deliver(_delivery_request(smoke_test=True))
    sent = smtp_factory.client.messages[0]
    message = message_from_string(sent.message, policy=default)
    assert isinstance(message, EmailMessage)
    body = str(message.get_content())

    assert result.delivered is True
    assert message["Subject"] == "Scout hosted key delivery smoke test"
    assert "This is a delivery smoke test." in body
    assert "No hosted account was created." in body
    assert "No real Scout API key was issued." in body
    assert "Smoke reference: smtp_smoke_test" in body
    assert "Your hosted beta tester API key is ready" not in body
    assert "Quick test:" not in body
    assert "scout_live_test_key" not in body
    assert "Arijit Chowdhury" in body
    assert "Founder, Chowmes" in body


def test_smtp_delivery_service_returns_failure_when_send_fails() -> None:
    smtp_factory = FakeSmtpFactory(send_error=RuntimeError("smtp down"))
    service = SmtpHostedApiKeyDeliveryService(
        config=SmtpHostedApiKeyDeliveryConfig(
            host="smtp.example.com",
            from_email="scout@example.com",
        ),
        smtp_factory=smtp_factory,
    )

    result = service.deliver(_delivery_request())

    assert result.delivered is False
    assert result.delivery_status == "failed"
    assert result.reason == "SMTP delivery failed: smtp down"


def test_smtp_delivery_config_requires_host_and_from_email() -> None:
    missing_host = SmtpHostedApiKeyDeliveryConfig(from_email="scout@example.com")
    missing_from = SmtpHostedApiKeyDeliveryConfig(host="smtp.example.com")

    assert missing_host.enabled is False
    assert missing_from.enabled is False


def _delivery_request(*, smoke_test: bool = False) -> HostedApiKeyDeliveryRequest:
    """Build a hosted API-key delivery request."""
    return HostedApiKeyDeliveryRequest(
        email="builder@example.com",
        name="Builder Person",
        tenant_id="tenant_123",
        key_id="key_123",
        plan=HostedPlan.HOSTED_BETA_PASS,
        raw_api_key="scout_live_test_key",
        checkout_session_id="smtp_smoke_test" if smoke_test else "cs_test_123",
        smoke_test=smoke_test,
    )


class SentMessage:
    """Captured SMTP message."""

    def __init__(self, sender: str, recipients: list[str], message: str) -> None:
        self.sender = sender
        self.recipients = recipients
        self.message = message


class FakeSmtpClient:
    """Fake SMTP client for unit tests."""

    def __init__(self, send_error: Exception | None = None) -> None:
        self.send_error = send_error
        self.started_tls = False
        self.login_args: tuple[str, str] | None = None
        self.messages: list[SentMessage] = []

    def __enter__(self) -> FakeSmtpClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def starttls(self) -> None:
        self.started_tls = True

    def login(self, user: str, password: str) -> None:
        self.login_args = (user, password)

    def sendmail(self, from_addr: str, to_addrs: list[str], msg: str) -> None:
        if self.send_error is not None:
            raise self.send_error
        self.messages.append(SentMessage(from_addr, to_addrs, msg))


class FakeSmtpFactory:
    """Fake SMTP factory for dependency-injected SMTP delivery tests."""

    def __init__(self, send_error: Exception | None = None) -> None:
        self.client = FakeSmtpClient(send_error)

    def __call__(self, host: str, port: int, timeout: float) -> FakeSmtpClient:
        return self.client
