"""Tests for hosted API-key delivery services.

# Scenario list:
# - disabled delivery service reports disabled without storing the raw key
# - SMTP delivery sends a one-time key email to the checkout customer
# - SMTP delivery includes non-secret hosted metadata and raw key in email body
# - SMTP delivery failures return structured failure results
# - SMTP config is disabled unless host and from email are configured
"""

from __future__ import annotations

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
    assert "Your Scout hosted API key" in sent.message
    assert "Hi Builder Person," in sent.message
    assert "scout_live_test_key" in sent.message
    assert "tenant_123" in sent.message
    assert "key_123" in sent.message
    assert "Arijit Chowdhury" in sent.message


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


def _delivery_request() -> HostedApiKeyDeliveryRequest:
    """Build a hosted API-key delivery request."""
    return HostedApiKeyDeliveryRequest(
        email="builder@example.com",
        name="Builder Person",
        tenant_id="tenant_123",
        key_id="key_123",
        plan=HostedPlan.HOSTED_BETA_PASS,
        raw_api_key="scout_live_test_key",
        checkout_session_id="cs_test_123",
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
