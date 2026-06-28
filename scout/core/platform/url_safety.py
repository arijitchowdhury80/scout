"""Hosted URL safety checks for SSRF prevention."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from pydantic import BaseModel

_ALLOWED_SCHEMES = {"http", "https"}
_LOCAL_HOSTNAMES = {"localhost", "localhost.localdomain"}


class UrlSafetyResult(BaseModel):
    """URL safety decision for hosted fetch admission."""

    allowed: bool
    url: str
    reason: str = ""


def validate_hosted_url(url: str, resolved_ips: list[str] | None = None) -> UrlSafetyResult:
    """Return whether a URL is safe for hosted Scout to fetch."""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        return _blocked(url, f"Unsupported URL scheme: {parsed.scheme or '<missing>'}.")
    if not parsed.hostname:
        return _blocked(url, "URL is missing a hostname.")
    if parsed.username or parsed.password:
        return _blocked(url, "URL credentials are not allowed.")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in _LOCAL_HOSTNAMES or hostname.endswith(".localhost"):
        return _blocked(url, "localhost hostnames are not allowed.")
    if _is_unsafe_ip_literal(hostname):
        return _blocked(url, f"URL targets unsafe IP address: {hostname}.")

    for resolved_ip in resolved_ips or []:
        if _is_unsafe_ip_literal(resolved_ip):
            return _blocked(url, f"URL resolved to unsafe IP address: {resolved_ip}.")

    return UrlSafetyResult(allowed=True, url=url)


def validate_hosted_redirect_chain(urls: list[str]) -> UrlSafetyResult:
    """Validate every URL in a hosted redirect chain."""
    for url in urls:
        result = validate_hosted_url(url)
        if not result.allowed:
            return result
    return UrlSafetyResult(allowed=True, url=urls[-1] if urls else "")


def _blocked(url: str, reason: str) -> UrlSafetyResult:
    """Return a blocked URL safety result."""
    return UrlSafetyResult(allowed=False, url=url, reason=reason)


def _is_unsafe_ip_literal(value: str) -> bool:
    """Return whether a hostname string is an unsafe IP literal."""
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(
        [
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        ]
    )
