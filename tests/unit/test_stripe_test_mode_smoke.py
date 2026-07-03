from __future__ import annotations

import json
from email.message import Message
from io import BytesIO
from typing import Any

import pytest

from scripts import stripe_test_mode_smoke


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_stripe_smoke_detects_secret_leaks() -> None:
    with pytest.raises(stripe_test_mode_smoke.StripeSmokeError, match="secret-looking"):
        stripe_test_mode_smoke.assert_no_secret_leak('{"secret":"sk_test_leak"}')


def test_stripe_smoke_uses_certifi_tls_context_for_https(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contexts: list[object] = []

    def fake_urlopen(request: object, timeout: float, context: object) -> FakeResponse:
        del request, timeout
        contexts.append(context)
        return FakeResponse({"ok": True})

    monkeypatch.setattr(stripe_test_mode_smoke, "urlopen", fake_urlopen)

    response = stripe_test_mode_smoke.request_json("GET", "https://scout.test/status")

    assert response == {"ok": True}
    assert contexts
    assert contexts[0] is not None


def test_stripe_smoke_status_only_passes_when_all_readiness_flags_are_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        del timeout
        calls.append(str(getattr(request, "full_url")))
        return FakeResponse(
            {
                "checkout_configured": True,
                "webhook_configured": True,
                "key_delivery_configured": True,
                "ready_for_paid_key_delivery": True,
            }
        )

    monkeypatch.setattr(stripe_test_mode_smoke, "urlopen", fake_urlopen)

    result = stripe_test_mode_smoke.run_smoke(
        base_url="http://scout.test",
        email="beta@example.com",
        name="Beta Tester",
        create_checkout=False,
        package_id="standard_1000",
    )

    assert result.ready is True
    assert result.checkout_created is False
    assert calls == ["http://scout.test/v1/billing/stripe/status"]


def test_stripe_smoke_fails_when_paid_key_delivery_is_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        del request, timeout
        return FakeResponse(
            {
                "checkout_configured": True,
                "webhook_configured": False,
                "key_delivery_configured": True,
                "ready_for_paid_key_delivery": False,
            }
        )

    monkeypatch.setattr(stripe_test_mode_smoke, "urlopen", fake_urlopen)

    with pytest.raises(stripe_test_mode_smoke.StripeSmokeError, match="webhook_configured"):
        stripe_test_mode_smoke.run_smoke(
            base_url="http://scout.test",
            email="beta@example.com",
            name="Beta Tester",
            create_checkout=False,
            package_id="standard_1000",
        )


def test_stripe_smoke_fails_with_beta_specific_message_when_beta_checkout_is_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        del request, timeout
        return FakeResponse(
            {
                "checkout_configured": True,
                "webhook_configured": True,
                "key_delivery_configured": False,
                "ready_for_beta_checkout": False,
                "ready_for_paid_key_delivery": True,
            }
        )

    monkeypatch.setattr(stripe_test_mode_smoke, "urlopen", fake_urlopen)

    with pytest.raises(stripe_test_mode_smoke.StripeSmokeError, match="beta checkout"):
        stripe_test_mode_smoke.run_smoke(
            base_url="http://scout.test",
            email="beta@example.com",
            name="Beta Tester",
            create_checkout=False,
            package_id="beta_trial",
        )


def test_stripe_smoke_can_create_checkout_without_printing_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        {
            "checkout_configured": True,
            "webhook_configured": True,
            "key_delivery_configured": True,
            "ready_for_paid_key_delivery": True,
        },
        {
            "success": True,
            "checkout_session_id": "cs_test_123",
            "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_123",
            "reason": "",
        },
    ]
    payloads: list[bytes | None] = []

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        del timeout
        payloads.append(getattr(request, "data", None))
        return FakeResponse(responses.pop(0))

    monkeypatch.setattr(stripe_test_mode_smoke, "urlopen", fake_urlopen)

    result = stripe_test_mode_smoke.run_smoke(
        base_url="http://scout.test",
        email="beta@example.com",
        name="Beta Tester",
        create_checkout=True,
        package_id="standard_1000",
    )

    assert result.ready is True
    assert result.checkout_created is True
    assert result.checkout_session_id == "cs_test_123"
    assert result.checkout_url == "https://checkout.stripe.com/c/pay/cs_test_123"
    assert payloads[0] is None
    assert payloads[1] == (
        b'{"email": "beta@example.com", "name": "Beta Tester", "package_id": "standard_1000"}'
    )


def test_stripe_smoke_uses_beta_checkout_readiness_for_beta_trial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        {
            "checkout_configured": True,
            "webhook_configured": True,
            "key_delivery_configured": True,
            "ready_for_beta_checkout": True,
            "ready_for_paid_key_delivery": False,
        },
        {
            "success": True,
            "checkout_session_id": "cs_test_setup_123",
            "checkout_url": "https://checkout.stripe.com/c/setup/cs_test_setup_123",
            "reason": "",
        },
    ]
    payloads: list[bytes | None] = []

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        del timeout
        payloads.append(getattr(request, "data", None))
        return FakeResponse(responses.pop(0))

    monkeypatch.setattr(stripe_test_mode_smoke, "urlopen", fake_urlopen)

    result = stripe_test_mode_smoke.run_smoke(
        base_url="http://scout.test",
        email="beta@example.com",
        name="Beta Tester",
        create_checkout=True,
        package_id="beta_trial",
    )

    assert result.ready is True
    assert result.checkout_created is True
    assert result.checkout_session_id == "cs_test_setup_123"
    assert payloads[1] == (
        b'{"email": "beta@example.com", "name": "Beta Tester", "package_id": "beta_trial"}'
    )


def test_stripe_smoke_main_reports_checkout_next_steps(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        stripe_test_mode_smoke,
        "run_smoke",
        lambda **_kwargs: stripe_test_mode_smoke.StripeSmokeResult(
            ready=True,
            checkout_created=True,
            checkout_session_id="cs_test_123",
            checkout_url="https://checkout.stripe.com/c/pay/cs_test_123",
        ),
    )

    assert stripe_test_mode_smoke.main(["--create-checkout"]) == 0

    output = capsys.readouterr().out
    assert "PASS" in output
    assert "Checkout session: cs_test_123" in output
    assert "Use the delivered key against /v1/hosted/me." in output
    assert "sk_test_" not in output


def test_stripe_smoke_http_error_body_is_checked_for_secret_leaks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error = stripe_test_mode_smoke.HTTPError(
        url="http://scout.test/v1/billing/stripe/status",
        code=503,
        msg="Service Unavailable",
        hdrs=Message(),
        fp=BytesIO(b'{"detail":"Stripe Checkout is not configured."}'),
    )

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        del request, timeout
        raise error

    monkeypatch.setattr(stripe_test_mode_smoke, "urlopen", fake_urlopen)

    with pytest.raises(stripe_test_mode_smoke.StripeSmokeError, match="HTTP 503"):
        stripe_test_mode_smoke.request_json(
            "GET",
            "http://scout.test/v1/billing/stripe/status",
        )
