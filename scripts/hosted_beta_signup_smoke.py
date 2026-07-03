#!/usr/bin/env python3
"""Smoke-test Scout public beta signup without printing API keys."""

from __future__ import annotations

import argparse
import json
import ssl
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import certifi


SECRET_MARKERS = ("sk_test_", "sk_live_", "whsec_", "scout_live_", "raw_api_key")


class HostedBetaSignupSmokeError(RuntimeError):
    """Raised when public beta signup is not live or leaks secret-looking data."""


@dataclass(frozen=True)
class HostedBetaSignupSmokeResult:
    """Non-secret result of a public beta signup smoke."""

    delivered: bool
    email: str
    status: str
    tenant_id: str = ""
    key_id: str = ""


def assert_no_secret_leak(text: str) -> None:
    """Raise if a public beta signup response contains secret-looking material."""
    leaked = [marker for marker in SECRET_MARKERS if marker in text]
    if leaked:
        raise HostedBetaSignupSmokeError(
            "Scout beta signup response exposed secret-looking material: " + ", ".join(leaked)
        )


def request_json(
    method: str,
    url: str,
    payload: dict[str, Any],
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Call a Scout public beta signup endpoint and return a JSON object."""
    data = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method=method,
    )
    context = _ssl_context(url)
    try:
        if context is None:
            response_handle = urlopen(request, timeout=timeout)
        else:
            response_handle = urlopen(request, timeout=timeout, context=context)
        with response_handle as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        assert_no_secret_leak(raw)
        raise HostedBetaSignupSmokeError(
            f"{method} {url} failed with HTTP {exc.code}: {raw}"
        ) from exc
    except URLError as exc:
        raise HostedBetaSignupSmokeError(f"{method} {url} failed: {exc.reason}") from exc
    assert_no_secret_leak(raw)
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise HostedBetaSignupSmokeError(f"{method} {url} did not return a JSON object.")
    return parsed


def run_smoke(
    base_url: str,
    email: str,
    name: str,
    timeout: float = 20.0,
) -> HostedBetaSignupSmokeResult:
    """Register a beta user and verify the public status endpoint."""
    normalized_base = base_url.rstrip("/") + "/"
    signup = request_json(
        "POST",
        urljoin(normalized_base, "v1/hosted/beta-key"),
        payload={
            "name": name,
            "email": email,
            "key_name": "Hosted beta smoke key",
        },
        timeout=timeout,
    )
    status = str(signup.get("delivery_status", ""))
    if status not in {"delivered", "account_exists"}:
        raise HostedBetaSignupSmokeError(
            f"Beta signup did not deliver an API key email. Status: {status or 'unknown'}."
        )
    lookup = request_json(
        "POST",
        urljoin(normalized_base, "v1/hosted/beta-key/status"),
        payload={"email": email},
        timeout=timeout,
    )
    delivered = bool(lookup.get("has_account")) and str(lookup.get("status", "")) in {
        "account_exists",
        "delivered",
    }
    if not delivered:
        raise HostedBetaSignupSmokeError(
            f"Beta signup status was not delivered. Status: {lookup.get('status', 'unknown')}."
        )
    return HostedBetaSignupSmokeResult(
        delivered=True,
        email=str(lookup.get("email", email)),
        status=str(signup.get("delivery_status", lookup.get("status", "delivered"))),
        tenant_id=str(lookup.get("tenant_id", signup.get("tenant_id", ""))),
        key_id=str(lookup.get("key_id", signup.get("key_id", ""))),
    )


def _ssl_context(url: str) -> ssl.SSLContext | None:
    """Return a certifi-backed TLS context for HTTPS URLs."""
    if not url.casefold().startswith("https://"):
        return None
    return ssl.create_default_context(cafile=certifi.where())


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://scout.chowmes.com")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--timeout", type=float, default=20.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a public beta signup smoke."""
    args = build_parser().parse_args(argv)
    try:
        result = run_smoke(
            base_url=args.base_url,
            email=args.email,
            name=args.name,
            timeout=args.timeout,
        )
    except (HostedBetaSignupSmokeError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print("PASS: Scout public beta signup delivered an API-key email.")
    print(f"Email: {result.email}")
    print(f"Status: {result.status}")
    print(f"Tenant ID: {result.tenant_id}")
    print(f"Key ID: {result.key_id}")
    print("The raw API key is delivered only by email and is not printed here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
