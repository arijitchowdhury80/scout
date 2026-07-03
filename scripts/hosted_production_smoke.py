#!/usr/bin/env python3
"""Operator smoke gate for Scout hosted production readiness."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import hosted_readiness_check, stripe_test_mode_smoke  # noqa: E402
from scripts.hosted_readiness_check import HostedReadinessResult  # noqa: E402


@dataclass(frozen=True)
class ProductionSmokeResult:
    """Non-secret production smoke summary."""

    base_url: str
    health_ok: bool
    packages_ok: bool
    beta_signup_ready: bool
    beta_checkout_ready: bool
    paid_checkout_ready: bool
    beta_key_delivery_ok: bool
    beta_checkout_ok: bool
    paid_checkout_ok: bool
    blockers: list[str]
    next_steps: list[str]
    missing_environment_keys: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Return whether all hosted production smoke gates passed."""
        return (
            self.health_ok
            and self.packages_ok
            and self.beta_signup_ready
            and self.beta_checkout_ready
            and self.paid_checkout_ready
            and self.beta_key_delivery_ok
            and self.beta_checkout_ok
            and self.paid_checkout_ok
            and not self.blockers
        )


ReadinessRunner = Callable[[str, float], HostedReadinessResult]
StripeRunner = Callable[..., object]


def run_production_smoke(
    base_url: str,
    timeout: float,
    readiness_runner: ReadinessRunner = hosted_readiness_check.run_readiness,
    stripe_runner: StripeRunner = stripe_test_mode_smoke.run_smoke,
) -> ProductionSmokeResult:
    """Run hosted health, package, signup, and checkout readiness smoke checks."""
    readiness = readiness_runner(base_url, timeout)
    blockers = list(readiness.blockers)
    next_steps = _next_steps_for_blockers(blockers)

    beta_key_delivery_ok = readiness.ready_for_beta_signup and not blockers
    beta_checkout_ok = False
    paid_checkout_ok = False
    if (
        not blockers
        and readiness.ready_for_beta_signup
        and readiness.ready_for_beta_checkout
        and readiness.ready_for_paid_checkout
    ):
        stripe_runner(
            base_url=readiness.base_url,
            email="scout-beta-smoke@example.com",
            name="Scout Beta Smoke",
            create_checkout=False,
            package_id="beta_trial",
            timeout=timeout,
        )
        beta_checkout_ok = True
        stripe_runner(
            base_url=readiness.base_url,
            email="scout-paid-smoke@example.com",
            name="Scout Paid Smoke",
            create_checkout=False,
            package_id="standard_1000",
            timeout=timeout,
        )
        paid_checkout_ok = True
        next_steps = ["Run a real Stripe Checkout + webhook + delivered-key E2E test."]

    return ProductionSmokeResult(
        base_url=readiness.base_url,
        health_ok=readiness.health_ok,
        packages_ok=readiness.packages_ok,
        beta_signup_ready=readiness.ready_for_beta_signup,
        beta_checkout_ready=readiness.ready_for_beta_checkout,
        paid_checkout_ready=readiness.ready_for_paid_checkout,
        beta_key_delivery_ok=beta_key_delivery_ok,
        beta_checkout_ok=beta_checkout_ok,
        paid_checkout_ok=paid_checkout_ok,
        blockers=blockers,
        missing_environment_keys=readiness.missing_environment_keys,
        next_steps=next_steps,
    )


def result_to_json(result: ProductionSmokeResult) -> str:
    """Serialize production smoke output with no secret material."""
    payload = asdict(result)
    payload["ok"] = result.ok
    return json.dumps(payload, indent=2, sort_keys=True)


def _next_steps_for_blockers(blockers: list[str]) -> list[str]:
    """Return concrete operator actions for known readiness blockers."""
    if not blockers:
        return ["Run a real Stripe Checkout + webhook + delivered-key E2E test."]
    steps: list[str] = []
    if any("email delivery" in blocker for blocker in blockers):
        steps.append(
            "Configure SMTP with scripts/scout-hosted-admin configure-production-env "
            "--secrets-file secrets/scout-production.env --require beta --restart"
        )
        steps.append(
            "Smoke-test email delivery with scripts/scout-hosted-admin send-test-email "
            "--email you@example.com --name 'Your Name'"
        )
    if any("Stripe" in blocker or "paid checkout" in blocker for blocker in blockers):
        steps.append(
            "Configure Stripe prices/webhook with scripts/scout-hosted-admin "
            "bootstrap-stripe-prices and configure-production-env --require all --restart"
        )
        steps.append(
            "Run scripts/stripe_test_mode_smoke.py --base-url https://scout.chowmes.com "
            "--package-id beta_trial and --package-id standard_1000"
        )
    if any("health" in blocker for blocker in blockers):
        steps.append("Check the Scout container, Caddy route, and /health endpoint.")
    if any("billing packages" in blocker for blocker in blockers):
        steps.append("Check /v1/billing/packages and package registry configuration.")
    return steps


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://scout.chowmes.com")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero unless all non-manual hosted production smoke gates pass.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the hosted production smoke gate."""
    args = build_parser().parse_args(argv)
    try:
        result = run_production_smoke(base_url=args.base_url, timeout=args.timeout)
    except (
        hosted_readiness_check.HostedReadinessError,
        stripe_test_mode_smoke.StripeSmokeError,
        json.JSONDecodeError,
    ) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(result_to_json(result))
    else:
        print(f"Hosted Scout: {result.base_url}")
        print(f"Health: {'ready' if result.health_ok else 'blocked'}")
        print(f"Packages: {'ready' if result.packages_ok else 'blocked'}")
        print(f"Beta key email delivery: {'ready' if result.beta_signup_ready else 'blocked'}")
        print(f"Beta Stripe setup: {'ready' if result.beta_checkout_ready else 'blocked'}")
        print(f"Paid checkout/key delivery: {'ready' if result.paid_checkout_ready else 'blocked'}")
        print(f"Beta key delivery smoke: {'ready' if result.beta_key_delivery_ok else 'not run'}")
        print(f"Beta Stripe smoke: {'ready' if result.beta_checkout_ok else 'not run'}")
        print(f"Paid Stripe smoke: {'ready' if result.paid_checkout_ok else 'not run'}")
        if result.blockers:
            print("Blockers:", file=sys.stderr)
            for blocker in result.blockers:
                print(f"  - {blocker}", file=sys.stderr)
        if result.missing_environment_keys:
            print("Missing environment keys:")
            for key in result.missing_environment_keys:
                print(f"  - {key}")
        if result.next_steps:
            print("Next steps:")
            for step in result.next_steps:
                print(f"  - {step}")

    if args.require_ready and not result.ok:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
