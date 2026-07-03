from __future__ import annotations

from scripts import hosted_production_smoke
from scripts.hosted_readiness_check import HostedReadinessResult


def test_production_smoke_stops_before_stripe_when_readiness_is_blocked() -> None:
    stripe_calls: list[str] = []

    def fake_readiness(base_url: str, timeout: float) -> HostedReadinessResult:
        assert base_url == "https://scout.chowmes.com"
        assert timeout == 12.0
        return HostedReadinessResult(
            base_url=base_url,
            health_ok=True,
            packages_ok=True,
            ready_for_beta_signup=False,
            ready_for_paid_checkout=False,
            blockers=[
                "hosted API key email delivery not configured",
                "Stripe Checkout not configured",
            ],
            missing_environment_keys=[
                "HOSTED_KEY_DELIVERY_SMTP_HOST",
                "STRIPE_SECRET_KEY",
            ],
        )

    def fake_stripe(**kwargs: object) -> object:
        stripe_calls.append(str(kwargs["package_id"]))
        raise AssertionError("Stripe smoke should not run while readiness is blocked")

    result = hosted_production_smoke.run_production_smoke(
        base_url="https://scout.chowmes.com",
        timeout=12.0,
        readiness_runner=fake_readiness,
        stripe_runner=fake_stripe,
    )

    assert result.ok is False
    assert result.health_ok is True
    assert result.packages_ok is True
    assert result.beta_key_delivery_ok is False
    assert result.paid_checkout_ok is False
    assert result.blockers == [
        "hosted API key email delivery not configured",
        "Stripe Checkout not configured",
    ]
    assert result.missing_environment_keys == [
        "HOSTED_KEY_DELIVERY_SMTP_HOST",
        "STRIPE_SECRET_KEY",
    ]
    assert "configure-production-env" in result.next_steps[0]
    assert stripe_calls == []


def test_production_smoke_checks_beta_delivery_and_paid_path_when_ready() -> None:
    stripe_calls: list[str] = []

    def fake_readiness(base_url: str, timeout: float) -> HostedReadinessResult:
        return HostedReadinessResult(
            base_url=base_url,
            health_ok=True,
            packages_ok=True,
            ready_for_beta_signup=True,
            ready_for_paid_checkout=True,
            blockers=[],
            missing_environment_keys=[],
        )

    def fake_stripe(**kwargs: object) -> object:
        stripe_calls.append(str(kwargs["package_id"]))
        return object()

    result = hosted_production_smoke.run_production_smoke(
        base_url="https://scout.chowmes.com",
        timeout=20.0,
        readiness_runner=fake_readiness,
        stripe_runner=fake_stripe,
    )

    assert result.ok is True
    assert result.beta_key_delivery_ok is True
    assert result.paid_checkout_ok is True
    assert result.blockers == []
    assert result.next_steps == ["Run a real Stripe Checkout + webhook + delivered-key E2E test."]
    assert stripe_calls == ["standard_1000"]


def test_production_smoke_json_output_never_contains_raw_secrets() -> None:
    result = hosted_production_smoke.ProductionSmokeResult(
        base_url="https://scout.chowmes.com",
        health_ok=True,
        packages_ok=True,
        beta_signup_ready=True,
        paid_checkout_ready=False,
        beta_key_delivery_ok=True,
        paid_checkout_ok=False,
        blockers=["paid checkout/key delivery not ready"],
        missing_environment_keys=["STRIPE_STANDARD_1000_PRICE_ID"],
        next_steps=["Configure Stripe paid package price IDs."],
    )

    payload = hosted_production_smoke.result_to_json(result)

    assert "scout_live_" not in payload
    assert "sk_test_" not in payload
    assert "whsec_" not in payload
    assert "STRIPE_STANDARD_1000_PRICE_ID" in payload
    assert '"ok": false' in payload
