"""Tests for the static Scout launch website."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from scout.api.main import app


_WEBSITE_INDEX = Path(__file__).resolve().parents[3] / "website" / "index.html"


def test_launch_website_exposes_hosted_beta_checkout_form_without_secrets() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

    assert 'id="hostedBetaCheckout"' in html
    assert 'id="hostedBetaEmail"' in html
    assert 'type="email"' in html
    assert "Create hosted beta checkout" in html
    assert "/v1/billing/stripe/checkout-session" in html
    assert "checkout_url" in html
    assert "window.location.assign" in html
    assert "Hosted beta is not configured yet" in html
    assert "STRIPE_SECRET_KEY" not in html
    assert "sk_live_" not in html
    assert "sk_test_" not in html


def test_api_root_serves_launch_website_from_same_origin() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Turn messy web pages into citable, downstream-ready records." in response.text
    assert 'id="hostedBetaCheckout"' in response.text
    assert "/v1/billing/stripe/checkout-session" in response.text
    assert "Scout app" not in response.text


def test_api_serves_launch_website_static_assets_without_auth() -> None:
    client = TestClient(app)

    styles = client.get("/styles.css")
    design_system = client.get("/assets/warm-industrial-design-system/warm-industrial.css")

    assert styles.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    assert ".beta-form" in styles.text
    assert design_system.status_code == 200
    assert "text/css" in design_system.headers["content-type"]
    assert ".wi-grid-bg" in design_system.text
