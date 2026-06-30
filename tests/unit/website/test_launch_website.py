"""Tests for the static Scout launch website."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from scout.api.main import app
from scout.launch_readiness import build_report


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
    assert "Beta operating model" in html
    assert "Local free" in html
    assert "Hosted metered credits" in html
    assert "Artifacts owned by you" in html
    assert "Hosted crawlers return content. Scout returns an evidence trail." in html
    assert "Product data should not be trapped in one destination." in html
    assert "JSONL / CSV / SQLite / Google Sheets / Algolia" in html
    assert "checkout_url" in html
    assert "window.location.assign" in html
    assert "Hosted beta is not configured yet" in html
    assert "Scout beta demo" in html
    assert "URL to evidence to records in under a minute." in html
    assert "/assets/scout-product-demo.gif" in html
    assert "No hard-site bypass guarantee." in html
    assert "STRIPE_SECRET_KEY" not in html
    assert "sk_live_" not in html
    assert "sk_test_" not in html


def test_launch_website_handles_stripe_checkout_return_states_without_secrets() -> None:
    for page_name in ("index.html", "beta.html"):
        html = (_WEBSITE_DIR / page_name).read_text(encoding="utf-8")

        assert "checkout=success" in html
        assert "checkout=cancelled" in html
        assert "Stripe payment completed. Scout will email your hosted API key" in html
        assert "Stripe checkout was cancelled." in html
        assert "handleCheckoutReturnState" in html
        assert "sk_live_" not in html
        assert "sk_test_" not in html


def test_launch_website_states_current_launch_readiness_boundaries() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    assert "Launch status" in normalized_html
    assert "Public launch is blocked" in normalized_html
    assert "Crawl4AI currently resolves lxml 5.4.0" in normalized_html
    assert "Private beta is limited" in normalized_html
    assert "Hosted metered credits" in normalized_html
    assert "Pricing is not approved yet" in normalized_html
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
    demo_gif = client.get("/assets/scout-product-demo.gif")
    logo = client.get("/assets/scout-wordmark.svg")
    mark = client.get("/assets/scout-mark.svg")

    assert styles.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    assert ".beta-form" in styles.text
    assert ".brand-logo" in styles.text
    assert "aria-current" in styles.text
    assert design_system.status_code == 200
    assert "text/css" in design_system.headers["content-type"]
    assert ".wi-grid-bg" in design_system.text
    assert demo_gif.status_code == 200
    assert demo_gif.headers["content-type"] == "image/gif"
    assert demo_gif.content.startswith((b"GIF87a", b"GIF89a"))
    assert logo.status_code == 200
    assert logo.headers["content-type"] in {"image/svg+xml", "image/svg+xml; charset=utf-8"}
    assert "SCOUT" in logo.text
    assert mark.status_code == 200
    assert mark.headers["content-type"] in {"image/svg+xml", "image/svg+xml; charset=utf-8"}
    assert "Scout mark" in mark.text


def test_homepage_has_section_aware_nav_and_scrollspy() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

    for section_id in (
        "top",
        "demo",
        "ledger",
        "modes",
        "evidence",
        "use-cases",
        "pricing",
        "beta",
    ):
        assert f'data-section-link="{section_id}"' in html
        assert f'id="{section_id}"' in html

    assert 'aria-current="true"' in html
    assert "IntersectionObserver" in html
    assert "setActiveSection" in html
    assert 'src="/assets/scout-wordmark.svg"' in html
    assert 'href="/assets/scout-mark.svg"' in html


def test_launch_website_demo_gif_is_real_beta_safe_media() -> None:
    demo_gif = _WEBSITE_DIR / "assets" / "scout-product-demo.gif"

    data = demo_gif.read_bytes()

    assert data.startswith((b"GIF87a", b"GIF89a"))
    assert len(data) > 20_000
    assert b"sk_live_" not in data
    assert b"sk_test_" not in data


def test_launch_website_has_beta_onboarding_pages() -> None:
    pages = {
        "quickstart.html": [
            "Scout Quickstart",
            "Local install is the primary beta path.",
            "codex/scout-platform-foundation",
            'pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"',
            "SCOUT_WORKDIR",
            "Readiness check",
            "scout launch-readiness",
            "Private beta: ready_with_limits",
            "--require-public",
            "docker compose",
            "Use hosted Scout only after you receive an API key.",
            "SCOUT_HOSTED_API_KEY",
            "/v1/hosted/me",
            "/v1/hosted/scrape",
            "invite-only and metered",
            "unit economics",
            "Final credits, retention, and overage",
        ],
        "pricing.html": [
            "Scout Pricing",
            "Free local beta",
            "Metered",
            "Hosted private beta",
            "Pay-as-you-go candidate",
            "unit economics",
            "No arbitrary one-time price",
            "No unlimited hosted crawling",
        ],
        "examples.html": [
            "Scout Examples",
            "Beta-safe workflows you can run today.",
            "Page to markdown",
            "Product category to records",
            "Company intelligence packet",
            "Captured HTML to records",
            "Product records to JSONL, CSV, SQLite, Google Sheets, and Algolia",
            "records.json",
            "source_pages.json",
            "blocked_pages.json",
            "extraction_report.md",
            "No guaranteed hard-site bypass",
            "No certified legacy /app UI claim",
        ],
        "guide.html": [
            "Scout Developer Guide",
            "Choose the right Scout surface before you run.",
            "Local CLI",
            "Local HTTP service",
            "Hosted beta API",
            "Claude/Codex skill backend",
            "SCOUT_WORKDIR",
            "X-API-Key",
            "Authorization: Bearer",
            "/v1/hosted/me",
            "/v1/hosted/scrape",
            "records.json",
            "source_pages.json",
            "blocked_pages.json",
            "extraction_report.md",
            "Hosted API examples live in this guide; local Swagger docs remain available only when running Scout locally",
            "No unlimited hosted crawling",
            "No certified legacy /app UI claim",
        ],
        "status.html": [
            "Scout Launch Status",
            "Private beta: ready_with_limits",
            "Public launch: blocked",
            "Owner summary",
            "Arijit: 4",
            "Codex: 4",
            "Codex + Arijit: 1",
            "Codex-actionable now: 0",
            "Blocker summary",
            "founder_decision: 3",
            "engineering: 4",
            "Decision packet for Arijit",
            "License: Apache-2.0 for Scout local/core",
            "Pricing: derive hosted pricing from unit economics",
            "Publishing: artifact-only private-beta v* tag first",
            "Public hosted: do not approve public self-serve hosted launch yet",
            "public-pricing-and-hosted-usage-limits",
            "github-release-workflow-run",
            "stripe-real-test-mode-smoke",
            "scout launch-readiness --owner Arijit",
            "scout launch-readiness --blocker-type engineering",
            "scout launch-readiness --blocker-id public-pricing-and-hosted-usage-limits",
            "Decision workflow",
            "scout launch-decision-drafts",
            "scout launch-decision-draft",
            "scout launch-decision-check --check-existing",
            "scout launch-decision-check --check-drafts",
            "Drafts are not approvals",
            "Review the draft first",
            "Move approved content into",
            "Do not edit the release checklist from a draft alone.",
            "Only after validation passes",
            "docs/product/founder-decision-record-SCOUT-DEC-YYYYMMDD-NN.md",
            "No certified legacy /app UI claim",
            "No unlimited hosted crawling",
        ],
        "beta.html": [
            "Scout Private Beta",
            "Choose your beta path",
            "Tester handoff packet",
            "docs/product/private-beta-tester-handoff.md",
            "Hosted beta checkout",
            "unit economics are",
            "Final credits, price, retention, and overage rules",
            "Limited credits, not",
            "/v1/billing/stripe/checkout-session",
            "Private beta is limited",
            "Run the launch readiness checker.",
            "scout launch-readiness",
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
            "Scout local/core is Apache-2.0",
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
        "/guide": "Scout Developer Guide",
        "/pricing": "Scout Pricing",
        "/examples": "Scout Examples",
        "/status": "Scout Launch Status",
        "/beta": "Scout Private Beta",
        "/legal": "Scout Legal And Third-Party Notices",
        "/terms": "Scout Beta Terms Placeholder",
        "/privacy": "Scout Beta Privacy Placeholder",
        "/quickstart.html": "Scout Quickstart",
        "/guide.html": "Scout Developer Guide",
        "/pricing.html": "Scout Pricing",
        "/examples.html": "Scout Examples",
        "/status.html": "Scout Launch Status",
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


def test_status_page_lists_all_current_unique_launch_blocker_keys() -> None:
    report = build_report(_REPO_ROOT)
    blocker_ids = {blocker["id"] for blocker in report["public_launch"]["blockers"]}
    html = (_WEBSITE_DIR / "status.html").read_text(encoding="utf-8")

    assert f"{len(blocker_ids)} unique public-launch blocker keys" in html
    for blocker_id in blocker_ids:
        assert blocker_id in html


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
