"""Tests for hosted URL safety and SSRF guard primitives.

# Scenario list:
# - public HTTPS URLs are allowed
# - non-HTTP schemes are rejected
# - missing hostnames are rejected
# - URL credentials/userinfo are rejected
# - localhost hostnames are rejected
# - private IPv4 literals are rejected
# - cloud metadata IP literals are rejected
# - resolved private IPs are rejected
# - redirect chains are rejected if any hop is unsafe
"""

from __future__ import annotations

from scout.core.platform.url_safety import validate_hosted_redirect_chain, validate_hosted_url


def test_validate_hosted_url_allows_public_https_url() -> None:
    result = validate_hosted_url("https://www.example.com/products")

    assert result.allowed is True
    assert result.reason == ""


def test_validate_hosted_url_rejects_non_http_scheme() -> None:
    result = validate_hosted_url("file:///etc/passwd")

    assert result.allowed is False
    assert "scheme" in result.reason


def test_validate_hosted_url_rejects_missing_hostname() -> None:
    result = validate_hosted_url("https:///missing-host")

    assert result.allowed is False
    assert "hostname" in result.reason


def test_validate_hosted_url_rejects_url_credentials() -> None:
    result = validate_hosted_url("https://user:pass@example.com/private")

    assert result.allowed is False
    assert "credentials" in result.reason


def test_validate_hosted_url_rejects_localhost_hostname() -> None:
    result = validate_hosted_url("http://localhost:8421/health")

    assert result.allowed is False
    assert "localhost" in result.reason


def test_validate_hosted_url_rejects_private_ipv4_literal() -> None:
    result = validate_hosted_url("http://192.168.1.10/admin")

    assert result.allowed is False
    assert "unsafe IP" in result.reason


def test_validate_hosted_url_rejects_cloud_metadata_ip_literal() -> None:
    result = validate_hosted_url("http://169.254.169.254/latest/meta-data/")

    assert result.allowed is False
    assert "unsafe IP" in result.reason


def test_validate_hosted_url_rejects_resolved_private_ip() -> None:
    result = validate_hosted_url("https://public-name.example", resolved_ips=["10.0.0.5"])

    assert result.allowed is False
    assert "resolved" in result.reason


def test_validate_hosted_redirect_chain_rejects_unsafe_hop() -> None:
    result = validate_hosted_redirect_chain(
        [
            "https://www.example.com/start",
            "http://127.0.0.1/admin",
        ]
    )

    assert result.allowed is False
    assert result.url == "http://127.0.0.1/admin"
