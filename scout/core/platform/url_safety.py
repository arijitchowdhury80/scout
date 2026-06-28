"""Hosted URL safety checks for SSRF prevention."""

from __future__ import annotations

import ipaddress
import socket
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


def validate_hosted_url_with_dns(url: str) -> UrlSafetyResult:
    """Validate a hosted URL and block hostnames resolving to unsafe IPs."""
    base_result = validate_hosted_url(url)
    if not base_result.allowed:
        return base_result

    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return base_result
    if _is_unsafe_ip_literal(hostname.lower().rstrip(".")):
        return base_result

    resolved_ips = _resolve_hostname_ips(hostname)
    if not resolved_ips:
        return base_result
    return validate_hosted_url(url, resolved_ips=resolved_ips)


def validate_hosted_url_fields(values: list[str]) -> UrlSafetyResult:
    """Validate URL-like values from hosted request fields."""
    for value in values:
        candidate = value.strip()
        if not candidate or not _looks_url_like(candidate):
            continue
        result = validate_hosted_url_with_dns(candidate)
        if not result.allowed:
            return result
    return UrlSafetyResult(allowed=True, url="")


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


def _resolve_hostname_ips(hostname: str) -> list[str]:
    """Resolve a hostname to IP strings; unresolved hosts are left to the crawler."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except OSError:
        return []
    ips: list[str] = []
    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        ip_value = str(sockaddr[0])
        if ip_value not in ips:
            ips.append(ip_value)
    return ips


def _looks_url_like(value: str) -> bool:
    """Return true for values that should be treated as URLs, not company names."""
    return "://" in value or value.startswith(("http:", "https:"))
