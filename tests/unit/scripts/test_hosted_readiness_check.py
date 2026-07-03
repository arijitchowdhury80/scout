from __future__ import annotations

import json
from typing import Any

import pytest

from scripts import hosted_readiness_check


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_hosted_readiness_reports_ready_when_all_live_flags_are_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = {
        "http://scout.test/health": {"status": "ok"},
        "http://scout.test/v1/billing/packages": {
            "packages": [
                {"package_id": "beta_trial"},
                {"package_id": "standard_1000"},
            ],
        },
        "http://scout.test/v1/billing/stripe/status": {
            "beta_signup_enabled": True,
            "checkout_configured": True,
            "webhook_configured": True,
            "key_delivery_configured": True,
            "key_delivery_response_fallback_enabled": False,
            "ready_for_beta_key_delivery": True,
            "ready_for_paid_key_delivery": True,
        },
    }
    calls: list[str] = []

    def fake_urlopen(request: object, timeout: float, context: object = None) -> FakeResponse:
        del timeout, context
        url = str(getattr(request, "full_url"))
        calls.append(url)
        return FakeResponse(responses[url])

    monkeypatch.setattr(hosted_readiness_check, "urlopen", fake_urlopen)

    result = hosted_readiness_check.run_readiness("http://scout.test")

    assert result.health_ok is True
    assert result.packages_ok is True
    assert result.ready_for_beta_signup is True
    assert result.ready_for_paid_checkout is True
    assert result.blockers == []
    assert calls == [
        "http://scout.test/health",
        "http://scout.test/v1/billing/packages",
        "http://scout.test/v1/billing/stripe/status",
    ]


def test_hosted_readiness_lists_missing_smtp_and_stripe_blockers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = {
        "https://scout.chowmes.com/health": {"status": "ok"},
        "https://scout.chowmes.com/v1/billing/packages": {
            "packages": [
                {"package_id": "beta_trial"},
                {"package_id": "standard_1000"},
            ],
        },
        "https://scout.chowmes.com/v1/billing/stripe/status": {
            "beta_signup_enabled": False,
            "checkout_configured": False,
            "webhook_configured": False,
            "key_delivery_configured": False,
            "key_delivery_response_fallback_enabled": False,
            "ready_for_beta_key_delivery": False,
            "ready_for_paid_key_delivery": False,
        },
    }

    def fake_urlopen(request: object, timeout: float, context: object = None) -> FakeResponse:
        del timeout, context
        return FakeResponse(responses[str(getattr(request, "full_url"))])

    monkeypatch.setattr(hosted_readiness_check, "urlopen", fake_urlopen)

    result = hosted_readiness_check.run_readiness("https://scout.chowmes.com/")

    assert result.ready_for_beta_signup is False
    assert result.ready_for_paid_checkout is False
    assert result.blockers == [
        "hosted beta signup disabled",
        "hosted API key email delivery not configured",
        "Stripe Checkout not configured",
        "Stripe webhook secret not configured",
        "paid checkout/key delivery not ready",
    ]


def test_hosted_readiness_ignores_removed_beta_key_response_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = {
        "https://scout.chowmes.com/health": {"status": "ok"},
        "https://scout.chowmes.com/v1/billing/packages": {
            "packages": [
                {"package_id": "beta_trial"},
                {"package_id": "standard_1000"},
            ],
        },
        "https://scout.chowmes.com/v1/billing/stripe/status": {
            "beta_signup_enabled": True,
            "checkout_configured": False,
            "webhook_configured": False,
            "key_delivery_configured": False,
            "key_delivery_response_fallback_enabled": True,
            "ready_for_beta_key_delivery": False,
            "ready_for_paid_key_delivery": False,
        },
    }

    def fake_urlopen(request: object, timeout: float, context: object = None) -> FakeResponse:
        del timeout
        del context
        return FakeResponse(responses[str(getattr(request, "full_url"))])

    monkeypatch.setattr(hosted_readiness_check, "urlopen", fake_urlopen)

    result = hosted_readiness_check.run_readiness("https://scout.chowmes.com/")

    assert result.ready_for_beta_signup is False
    assert result.blockers == [
        "hosted API key email delivery not configured",
        "Stripe Checkout not configured",
        "Stripe webhook secret not configured",
        "paid checkout/key delivery not ready",
    ]


def test_hosted_readiness_rejects_secret_leaks() -> None:
    with pytest.raises(hosted_readiness_check.HostedReadinessError, match="secret-looking"):
        hosted_readiness_check.assert_no_secret_leak('{"key":"sk_live_leak"}')


def test_hosted_readiness_main_fails_require_beta_when_blocked(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        hosted_readiness_check,
        "run_readiness",
        lambda *_args, **_kwargs: hosted_readiness_check.HostedReadinessResult(
            base_url="https://scout.chowmes.com",
            health_ok=True,
            packages_ok=True,
            ready_for_beta_signup=False,
            ready_for_paid_checkout=False,
            blockers=["hosted API key email delivery not configured"],
        ),
    )

    exit_code = hosted_readiness_check.main(["--require-beta-signup"])

    assert exit_code == 2
    assert "hosted API key email delivery not configured" in capsys.readouterr().err
