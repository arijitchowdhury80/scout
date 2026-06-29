"""Tests for the static Scout launch website."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from scout.api.main import app


_WEBSITE_INDEX = Path(__file__).resolve().parents[3] / "website" / "index.html"
_WEBSITE_DIR = _WEBSITE_INDEX.parent
_REPO_ROOT = _WEBSITE_DIR.parent


def test_launch_website_exposes_hosted_beta_checkout_form_without_secrets() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

    assert 'id="hostedBetaCheckout"' in html
    assert 'id="hostedBetaEmail"' in html
    assert 'type="email"' in html
    assert "Create hosted beta checkout" in html
    assert "/v1/billing/stripe/checkout-session" in html
    assert "/v1/billing/stripe/status" in html
    assert "Hosted beta payment is not configured yet" in html
    assert "Hosted beta payment is configured" in html
    assert "Run ledger" in html
    assert "Hosted crawlers return content. Scout returns an evidence trail." in html
    assert "Product data should not be trapped in one destination." in html
    assert "JSONL / CSV / SQLite / Google Sheets / Algolia" in html
    assert "checkout_url" in html
    assert "window.location.assign" in html
    assert "Hosted beta is not configured yet" in html
    assert "STRIPE_SECRET_KEY" not in html
    assert "sk_live_" not in html
    assert "sk_test_" not in html


def test_launch_website_states_current_launch_readiness_boundaries() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    assert "Launch status" in normalized_html
    assert "Public launch is blocked" in normalized_html
    assert "Crawl4AI currently resolves lxml 5.4.0" in normalized_html
    assert "Private beta is limited" in normalized_html
    assert "No clean security claim" in normalized_html
    assert "Local install remains the primary path" in normalized_html
    assert "dependency audit is clean" in normalized_html
    assert "Production-ready multi-tenant SaaS" not in html
    assert "Unlimited hosted scraping" not in html


def test_api_root_serves_launch_website_from_same_origin() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Turn messy web pages into citable, downstream-ready records." in response.text
    assert "Run ledger" in response.text
    assert "Hosted crawlers return content. Scout returns an evidence trail." in response.text
    assert "Public launch is blocked" in response.text
    assert "Private beta is limited" in response.text
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


def test_launch_website_has_beta_onboarding_pages() -> None:
    pages = {
        "quickstart.html": [
            "Scout Quickstart",
            "Local install is the primary beta path.",
            "codex/scout-platform-foundation",
            'pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"',
            "SCOUT_WORKDIR",
            "Readiness check",
            "python3 scripts/launch_readiness_check.py",
            "Private beta: ready_with_limits",
            "--require-public",
            "docker compose",
            "Use hosted Scout only after you receive an API key.",
            "SCOUT_HOSTED_API_KEY",
            "/v1/hosted/me",
            "/v1/hosted/scrape",
            "finite credits",
        ],
        "pricing.html": [
            "Scout Pricing",
            "Free local beta",
            "$22 hosted beta pass",
            "finite hosted credits",
            "No unlimited hosted crawling",
        ],
        "beta.html": [
            "Scout Private Beta",
            "Choose your beta path",
            "Hosted beta checkout",
            "/v1/billing/stripe/checkout-session",
            "Private beta is limited",
            "Run the launch readiness checker.",
            "python3 scripts/launch_readiness_check.py",
            "ready_with_limits",
            "--require-public",
            "Beta support is evidence-first.",
            "private beta bug template",
            "private beta feature template",
            "Keep secrets out",
            "Security reports should not be filed as public issues.",
        ],
        "legal.html": [
            "Scout Legal And Third-Party Notices",
            "This is not legal advice.",
            "Crawl4AI",
            "https://x.com/unclecode",
            "Apache License, Version 2.0",
            "Scout license is not final",
            "Public launch remains blocked",
        ],
        "terms.html": [
            "Scout Beta Terms Placeholder",
            "This is not a final Terms of Service.",
            "Use Scout only for websites and data you are allowed to access.",
            "No guaranteed hard-site bypass.",
            "Hosted beta is capped and metered.",
        ],
        "privacy.html": [
            "Scout Beta Privacy Placeholder",
            "This is not a final Privacy Policy.",
            "Local Scout keeps run artifacts on your machine.",
            "Hosted beta stores run metadata and artifacts for limited retention.",
            "Do not submit secrets or regulated personal data.",
        ],
    }

    for page_name, expected_strings in pages.items():
        html = (_WEBSITE_DIR / page_name).read_text(encoding="utf-8")
        normalized_html = " ".join(html.split())
        for expected in expected_strings:
            assert expected in normalized_html
        assert "sk_live_" not in html
        assert "sk_test_" not in html


def test_api_serves_launch_website_beta_onboarding_pages_without_auth() -> None:
    client = TestClient(app)

    expected = {
        "/quickstart": "Scout Quickstart",
        "/pricing": "Scout Pricing",
        "/beta": "Scout Private Beta",
        "/legal": "Scout Legal And Third-Party Notices",
        "/terms": "Scout Beta Terms Placeholder",
        "/privacy": "Scout Beta Privacy Placeholder",
        "/quickstart.html": "Scout Quickstart",
        "/pricing.html": "Scout Pricing",
        "/beta.html": "Scout Private Beta",
        "/legal.html": "Scout Legal And Third-Party Notices",
        "/terms.html": "Scout Beta Terms Placeholder",
        "/privacy.html": "Scout Beta Privacy Placeholder",
    }

    for path, text in expected.items():
        response = client.get(path)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert text in response.text


def test_api_serves_third_party_notices_without_auth() -> None:
    client = TestClient(app)

    response = client.get("/third-party-notices")

    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "Third-Party Notices" in response.text
    assert "Crawl4AI" in response.text
    assert "Apache License, Version 2.0" in response.text


def test_fastapi_docs_remain_api_docs_not_marketing_docs() -> None:
    client = TestClient(app)

    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text
    assert "Scout Quickstart" not in response.text


def test_crawl4ai_attribution_is_consistent_across_public_docs() -> None:
    attribution = (
        "This product includes software developed by UncleCode "
        "(https://x.com/unclecode) as part of the Crawl4AI project"
    )

    notice = (_REPO_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    readme = (_REPO_ROOT / "README.md").read_text(encoding="utf-8")
    legal = (_WEBSITE_DIR / "legal.html").read_text(encoding="utf-8")
    normalized_legal = " ".join(legal.split())

    assert attribution in " ".join(notice.split())
    assert attribution in " ".join(readme.split())
    assert attribution in normalized_legal
