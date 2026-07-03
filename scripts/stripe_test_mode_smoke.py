#!/usr/bin/env python3
"""Stripe test-mode smoke helper for Scout hosted beta payments.

This script intentionally does not know Stripe secrets. It talks only to a
running Scout server and verifies the non-secret billing readiness route plus,
optionally, real Checkout Session creation.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


SECRET_MARKERS = ("sk_test_", "sk_live_", "whsec_", "scout_live_")


class StripeSmokeError(RuntimeError):
    """Raised when the Stripe smoke cannot continue safely."""


@dataclass(frozen=True)
class StripeSmokeResult:
    """Non-secret Stripe smoke result."""

    ready: bool
    checkout_created: bool
    checkout_session_id: str = ""
    checkout_url: str = ""


def assert_no_secret_leak(text: str) -> None:
    """Raise if a Scout billing response contains obvious secret material."""
    leaked = [marker for marker in SECRET_MARKERS if marker in text]
    if leaked:
        raise StripeSmokeError(
            "Scout billing response exposed secret-looking material: " + ", ".join(leaked)
        )


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Call a Scout endpoint and return a JSON object."""
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        assert_no_secret_leak(raw)
        raise StripeSmokeError(f"{method} {url} failed with HTTP {exc.code}: {raw}") from exc
    except URLError as exc:
        raise StripeSmokeError(f"{method} {url} failed: {exc.reason}") from exc
    assert_no_secret_leak(raw)
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise StripeSmokeError(f"{method} {url} did not return a JSON object.")
    return parsed


def run_smoke(
    base_url: str,
    email: str,
    create_checkout: bool,
    package_id: str,
    timeout: float = 20.0,
) -> StripeSmokeResult:
    """Run the non-secret Stripe readiness and optional Checkout smoke."""
    normalized_base = base_url.rstrip("/") + "/"
    status = request_json(
        "GET",
        urljoin(normalized_base, "v1/billing/stripe/status"),
        timeout=timeout,
    )
    required_flags = _required_readiness_flags(package_id)
    missing_flags = [flag for flag in required_flags if status.get(flag) is not True]
    if missing_flags:
        raise StripeSmokeError(
            "Stripe paid-key delivery is not ready. Missing true flags: " + ", ".join(missing_flags)
        )
    if not create_checkout:
        return StripeSmokeResult(ready=True, checkout_created=False)

    checkout = request_json(
        "POST",
        urljoin(normalized_base, "v1/billing/stripe/checkout-session"),
        payload={"email": email, "package_id": package_id},
        timeout=timeout,
    )
    if checkout.get("success") is not True:
        raise StripeSmokeError(f"Checkout creation failed: {checkout.get('reason', '')}")
    session_id = str(checkout.get("checkout_session_id", ""))
    checkout_url = str(checkout.get("checkout_url", ""))
    if not session_id.startswith("cs_") or checkout_url == "":
        raise StripeSmokeError("Checkout creation response was missing session data.")
    return StripeSmokeResult(
        ready=True,
        checkout_created=True,
        checkout_session_id=session_id,
        checkout_url=checkout_url,
    )


def _required_readiness_flags(package_id: str) -> list[str]:
    """Return readiness flags required before creating a checkout for a package."""
    flags = [
        "checkout_configured",
        "webhook_configured",
        "key_delivery_configured",
    ]
    if package_id == "beta_trial":
        flags.append("ready_for_beta_checkout")
    else:
        flags.append("ready_for_paid_key_delivery")
    return flags


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Verify Scout Stripe test-mode readiness without printing secrets.",
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8421")
    parser.add_argument("--email", default="scout-beta-test@example.com")
    parser.add_argument(
        "--package-id",
        default="standard_1000",
        help="Hosted package to test, for example standard_1000 or beta_trial.",
    )
    parser.add_argument(
        "--create-checkout",
        action="store_true",
        help="Create a real Stripe Checkout Session through Scout.",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Stripe test-mode smoke."""
    args = build_parser().parse_args(argv)
    try:
        result = run_smoke(
            base_url=args.base_url,
            email=args.email,
            create_checkout=args.create_checkout,
            package_id=args.package_id,
            timeout=args.timeout,
        )
    except (StripeSmokeError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print("PASS: Scout Stripe paid-key delivery readiness is configured.")
    if result.checkout_created:
        print(f"Checkout session: {result.checkout_session_id}")
        print(f"Checkout URL: {result.checkout_url}")
        print("")
        print("Next manual verification steps:")
        print("1. Complete the Stripe test payment in the Checkout URL.")
        print("2. Forward/deliver the real Stripe webhook to /v1/billing/stripe/webhook.")
        print("3. Confirm the hosted API key email arrives at the test recipient.")
        print("4. Use the delivered key against /v1/hosted/me.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
