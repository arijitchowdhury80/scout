from __future__ import annotations

import json
from typing import Any

import pytest

from scripts import hosted_beta_signup_smoke


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_beta_signup_smoke_passes_when_registration_is_delivered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_urlopen(request: object, timeout: float, context: object = None) -> FakeResponse:
        del timeout, context
        url = str(getattr(request, "full_url"))
        method = str(getattr(request, "method"))
        payload = _payload(request)
        calls.append((method, url, payload))
        if url.endswith("/v1/hosted/beta-key/status"):
            return FakeResponse(
                {
                    "success": True,
                    "email": "tester@example.com",
                    "status": "account_exists",
                    "delivery_status": "delivered",
                    "has_account": True,
                    "tenant_id": "tenant_123",
                    "key_id": "key_123",
                    "message": "Scout emailed your beta API key.",
                }
            )
        return FakeResponse(
            {
                "success": True,
                "tenant_id": "tenant_123",
                "key_id": "key_123",
                "name": "Tester",
                "email": "tester@example.com",
                "plan": "hosted_beta_pass",
                "scopes": ["runs:create"],
                "standard_credits_remaining": 100,
                "browser_credits_remaining": 0,
                "delivery_status": "delivered",
                "warning": "",
            }
        )

    monkeypatch.setattr(hosted_beta_signup_smoke, "urlopen", fake_urlopen)

    result = hosted_beta_signup_smoke.run_smoke(
        base_url="https://scout.test",
        email="tester@example.com",
        name="Tester",
    )

    assert result.delivered is True
    assert result.status == "delivered"
    assert result.tenant_id == "tenant_123"
    assert result.key_id == "key_123"
    assert calls == [
        (
            "POST",
            "https://scout.test/v1/hosted/beta-key",
            {
                "name": "Tester",
                "email": "tester@example.com",
                "key_name": "Hosted beta smoke key",
            },
        ),
        (
            "POST",
            "https://scout.test/v1/hosted/beta-key/status",
            {"email": "tester@example.com"},
        ),
    ]


def test_beta_signup_smoke_fails_when_delivery_is_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: object, timeout: float, context: object = None) -> FakeResponse:
        del timeout, context
        return FakeResponse(
            {
                "success": True,
                "tenant_id": "",
                "key_id": "",
                "name": "Tester",
                "email": "tester@example.com",
                "plan": "hosted_beta_pass",
                "scopes": [],
                "standard_credits_remaining": 0,
                "browser_credits_remaining": 0,
                "delivery_status": "pending_delivery",
                "warning": "SMTP is not configured.",
            }
        )

    monkeypatch.setattr(hosted_beta_signup_smoke, "urlopen", fake_urlopen)

    with pytest.raises(hosted_beta_signup_smoke.HostedBetaSignupSmokeError, match="pending"):
        hosted_beta_signup_smoke.run_smoke(
            base_url="https://scout.test",
            email="tester@example.com",
            name="Tester",
        )


def test_beta_signup_smoke_rejects_secret_leaks() -> None:
    with pytest.raises(
        hosted_beta_signup_smoke.HostedBetaSignupSmokeError,
        match="secret-looking",
    ):
        hosted_beta_signup_smoke.assert_no_secret_leak('{"raw":"scout_live_leak"}')


def test_beta_signup_smoke_main_reports_without_raw_key(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        hosted_beta_signup_smoke,
        "run_smoke",
        lambda *_args, **_kwargs: hosted_beta_signup_smoke.HostedBetaSignupSmokeResult(
            delivered=True,
            email="tester@example.com",
            status="delivered",
            tenant_id="tenant_123",
            key_id="key_123",
        ),
    )

    exit_code = hosted_beta_signup_smoke.main(
        ["--base-url", "https://scout.test", "--email", "tester@example.com", "--name", "Tester"]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "PASS" in output
    assert "tester@example.com" in output
    assert "tenant_123" in output
    assert "key_123" in output
    assert "scout_live_" not in output


def _payload(request: object) -> dict[str, Any] | None:
    data = getattr(request, "data", None)
    if data is None:
        return None
    return json.loads(data.decode("utf-8"))
