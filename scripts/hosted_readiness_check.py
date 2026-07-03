#!/usr/bin/env python3
"""Verify Scout hosted SaaS readiness without printing secrets."""

from __future__ import annotations

import argparse
import json
import ssl
import sys
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import certifi


SECRET_MARKERS = ("sk_test_", "sk_live_", "whsec_", "scout_live_")


class HostedReadinessError(RuntimeError):
    """Raised when hosted readiness cannot be checked safely."""


@dataclass(frozen=True)
class HostedReadinessResult:
    """Non-secret Scout hosted readiness result."""

    base_url: str
    health_ok: bool
    packages_ok: bool
    ready_for_beta_signup: bool
    ready_for_beta_checkout: bool
    ready_for_paid_checkout: bool
    blockers: list[str]
    missing_environment_keys: list[str] = field(default_factory=list)
    operator_next_actions: list[str] = field(default_factory=list)


def assert_no_secret_leak(text: str) -> None:
    """Raise if a hosted readiness response contains obvious secret material."""
    leaked = [marker for marker in SECRET_MARKERS if marker in text]
    if leaked:
        raise HostedReadinessError(
            "Scout hosted readiness response exposed secret-looking material: " + ", ".join(leaked)
        )


def request_json(method: str, url: str, timeout: float = 20.0) -> dict[str, Any]:
    """Call a Scout endpoint and return a JSON object."""
    request = Request(url, headers={"Accept": "application/json"}, method=method)
    context = _ssl_context(url)
    try:
        with urlopen(request, timeout=timeout, context=context) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        assert_no_secret_leak(raw)
        raise HostedReadinessError(f"{method} {url} failed with HTTP {exc.code}: {raw}") from exc
    except URLError as exc:
        raise HostedReadinessError(f"{method} {url} failed: {exc.reason}") from exc

    assert_no_secret_leak(raw)
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise HostedReadinessError(f"{method} {url} did not return a JSON object.")
    return parsed


def _ssl_context(url: str) -> ssl.SSLContext | None:
    """Return a certifi-backed TLS context for HTTPS URLs."""
    if not url.casefold().startswith("https://"):
        return None
    return ssl.create_default_context(cafile=certifi.where())


def run_readiness(base_url: str, timeout: float = 20.0) -> HostedReadinessResult:
    """Check live hosted signup, package, and billing readiness flags."""
    normalized_base = base_url.rstrip("/") + "/"
    health = request_json("GET", urljoin(normalized_base, "health"), timeout=timeout)
    packages = request_json(
        "GET",
        urljoin(normalized_base, "v1/billing/packages"),
        timeout=timeout,
    )
    billing = request_json(
        "GET",
        urljoin(normalized_base, "v1/billing/stripe/status"),
        timeout=timeout,
    )

    health_ok = health.get("status") == "ok"
    package_ids = {
        str(package.get("package_id", ""))
        for package in packages.get("packages", [])
        if isinstance(package, dict)
    }
    packages_ok = {"beta_trial", "standard_1000"}.issubset(package_ids)
    ready_for_beta_signup = billing.get("ready_for_beta_key_delivery") is True
    ready_for_beta_checkout = billing.get("ready_for_beta_checkout") is True
    ready_for_paid_checkout = billing.get("ready_for_paid_key_delivery") is True
    missing_environment_keys = [
        str(key) for key in billing.get("missing_environment_keys", []) if isinstance(key, str)
    ]
    operator_next_actions = [
        str(action)
        for action in billing.get("operator_next_actions", [])
        if isinstance(action, str)
    ]

    blockers: list[str] = []
    if not health_ok:
        blockers.append("health endpoint is not ok")
    if not packages_ok:
        blockers.append("billing packages are missing beta_trial or standard_1000")
    if billing.get("beta_signup_enabled") is not True:
        blockers.append("hosted beta signup disabled")
    if billing.get("key_delivery_configured") is not True:
        blockers.append("hosted API key email delivery not configured")
    if billing.get("checkout_configured") is not True:
        blockers.append("Stripe Checkout not configured")
    if billing.get("webhook_configured") is not True:
        blockers.append("Stripe webhook secret not configured")
    if not ready_for_beta_signup:
        blockers.append("self-service beta key delivery not ready")
    if not ready_for_beta_checkout:
        blockers.append("beta Stripe setup not ready")
    if not ready_for_paid_checkout:
        blockers.append("paid checkout/key delivery not ready")

    return HostedReadinessResult(
        base_url=normalized_base.rstrip("/"),
        health_ok=health_ok,
        packages_ok=packages_ok,
        ready_for_beta_signup=ready_for_beta_signup,
        ready_for_beta_checkout=ready_for_beta_checkout,
        ready_for_paid_checkout=ready_for_paid_checkout,
        blockers=blockers,
        missing_environment_keys=missing_environment_keys,
        operator_next_actions=operator_next_actions,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://scout.chowmes.com")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--require-beta-signup",
        action="store_true",
        help="Exit nonzero unless self-service beta signup is ready.",
    )
    parser.add_argument(
        "--require-paid-checkout",
        action="store_true",
        help="Exit nonzero unless paid checkout and key delivery are ready.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run hosted readiness checks."""
    args = build_parser().parse_args(argv)
    try:
        result = run_readiness(args.base_url, timeout=args.timeout)
    except (HostedReadinessError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
    else:
        print(f"Hosted Scout: {result.base_url}")
        print(f"Health: {'ready' if result.health_ok else 'blocked'}")
        print(f"Packages: {'ready' if result.packages_ok else 'blocked'}")
        print("Beta signup: " + ("ready" if result.ready_for_beta_signup else "blocked"))
        print("Beta Stripe setup: " + ("ready" if result.ready_for_beta_checkout else "blocked"))
        print("Paid checkout: " + ("ready" if result.ready_for_paid_checkout else "blocked"))
        if result.blockers:
            print("Blockers:", file=sys.stderr)
            for blocker in result.blockers:
                print(f"  - {blocker}", file=sys.stderr)
        if result.missing_environment_keys:
            print("Missing environment keys:")
            for key in result.missing_environment_keys:
                print(f"  - {key}")
        if result.operator_next_actions:
            print("Operator next actions:")
            for action in result.operator_next_actions:
                print(f"  - {action}")

    if args.require_beta_signup and not result.ready_for_beta_signup:
        return 2
    if args.require_paid_checkout and not result.ready_for_paid_checkout:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
