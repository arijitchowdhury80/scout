"""Tests for the static Scout launch website."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageSequence

from scout.api.main import app
from scout.launch_readiness import build_report


_WEBSITE_INDEX = Path(__file__).resolve().parents[3] / "website" / "index.html"
_WEBSITE_DIR = _WEBSITE_INDEX.parent
_REPO_ROOT = _WEBSITE_DIR.parent


def test_homepage_focuses_on_demo_features_use_cases_and_beta_ctas() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

    assert "What Scout returns" in html
    assert "Clean records with evidence attached." in html
    assert "The crawler is only the first step." in html
    assert "Citation-grade evidence" in html
    assert "Typed records" in html
    assert "Algolia-ready exports" in html
    assert "Demo and search builds" in html
    assert "Request hosted access" in html
    assert 'href="/beta"' in html
    assert 'id="hostedBetaCheckout"' not in html
    assert "/v1/billing/stripe/checkout-session" not in html
    assert "checkout_url" not in html
    assert "window.location.assign" not in html
    assert "Scout beta demo" in html
    assert "URL to evidence to records in under a minute." in html
    assert "/assets/scout-product-demo.gif?v=20260630-slow-readable" in html
    assert "No hard-site bypass guarantee." in html
    assert "STRIPE_SECRET_KEY" not in html
    assert "sk_live_" not in html
    assert "sk_test_" not in html


def test_launch_website_handles_stripe_checkout_return_states_without_secrets() -> None:
    for page_name in ("beta.html",):
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

    assert "The crawler is only the first step." in normalized_html
    assert "Acquisition ladder" in normalized_html
    assert "Citation-grade evidence" in normalized_html
    assert "Typed records" in normalized_html
    assert "Portable artifacts" in normalized_html
    assert "Hosted beta" in normalized_html
    assert "Local beta" in normalized_html
    assert "Pay-as-you-go candidate" in normalized_html
    assert "Launch status" not in normalized_html
    assert "Production-ready multi-tenant SaaS" not in html
    assert "Unlimited hosted scraping" not in html


def test_api_root_serves_launch_website_from_same_origin() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Turn messy web pages into citable, downstream-ready records." in response.text
    assert "Clean records with evidence attached." in response.text
    assert "The crawler is only the first step." in response.text
    assert "Demo and search builds" in response.text
    assert 'id="hostedBetaCheckout"' not in response.text
    assert "/v1/billing/stripe/checkout-session" not in response.text
    assert "Scout app" not in response.text


def test_removed_app_ui_routes_are_not_public_product_surfaces() -> None:
    client = TestClient(app)

    for path in ("/app", "/api/config", "/app/live-browser"):
        response = client.get(path)
        assert response.status_code == 403
        assert "text/html" not in response.headers.get("content-type", "")


def test_api_serves_launch_website_static_assets_without_auth() -> None:
    client = TestClient(app)

    styles = client.get("/styles.css")
    design_system = client.get("/assets/warm-industrial-design-system/warm-industrial.css")
    demo_gif = client.get("/assets/scout-product-demo.gif")
    logo = client.get("/assets/scout-wordmark.svg")
    mark = client.get("/assets/scout-mark.svg")
    copy_code = client.get("/assets/copy-code.js")

    assert styles.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    assert ".beta-form" in styles.text
    assert ".brand-logo" in styles.text
    assert "aria-current" in styles.text
    assert ".code-copy__button" in styles.text
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
    assert copy_code.status_code == 200
    assert "javascript" in copy_code.headers["content-type"]
    assert "navigator.clipboard.writeText" in copy_code.text
    assert "Copy code sample" in copy_code.text


def test_homepage_has_section_aware_nav_and_scrollspy() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

    for section_id in (
        "top",
        "demo",
        "features",
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


def test_launch_website_demo_gif_is_slow_enough_to_read() -> None:
    demo_gif = _WEBSITE_DIR / "assets" / "scout-product-demo.gif"

    with Image.open(demo_gif) as image:
        durations = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(image)]

    assert len(durations) >= 3
    assert min(durations) >= 10_000


def test_quickstart_support_notes_are_compact_not_empty_card_grid() -> None:
    css = (_WEBSITE_DIR / "styles.css").read_text(encoding="utf-8")

    assert ".step-section .note-grid" in css
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in css
    assert ".step-section .note-grid article" in css
    assert "min-height: auto;" in css


def test_homepage_hero_evidence_card_is_not_bottom_aligned() -> None:
    css = (_WEBSITE_DIR / "styles.css").read_text(encoding="utf-8")

    assert ".hero-grid" in css
    assert ".hero-evidence-card" in css
    assert "align-items: start;" in css
    assert "align-self: start;" in css
    assert "align-self: end;" not in css


def test_launch_website_has_beta_onboarding_pages() -> None:
    pages = {
        "quickstart.html": [
            "Scout Quickstart",
            "Use hosted Scout with an API key, or run it locally.",
            "Call the live Scout API.",
            "https://scout.chowmes.com",
            "Do not use localhost for hosted calls.",
            "codex/scout-platform-foundation",
            'pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-platform-foundation"',
            "SCOUT_WORKDIR",
            "Readiness check",
            "scout launch-readiness",
            "Private beta: ready_with_limits",
            "--require-public",
            "docker compose",
            "Run Scout on your own machine.",
            "SCOUT_HOSTED_API_KEY",
            "/v1/hosted/me",
            "/v1/hosted/scrape",
            "invite-only and metered",
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
            "No app UI claim",
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
            "No app UI surface",
        ],
        "status.html": [
            "Scout Launch Status",
            "Controlled beta: ready_with_limits",
            "Launch readiness: ready",
            "What changed in the blocker burndown?",
            "Arijit decisions: closed",
            "Codex gates: closed",
            "Stripe paid checkout: deferred",
            "Current blockers: 0",
            "Blocker summary",
            "Future public registry work",
            "Future paid checkout work",
            "Future security-clean work",
            "Decisions recorded for the beta path.",
            "License: Apache-2.0 for Scout local/core",
            "Pricing: controlled beta posture",
            "Publishing: artifact-only private-beta v* tag first",
            "Hosted: invite-only keys",
            "public-pricing-and-hosted-usage-limits",
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
            "Controlled beta is ready; public self-serve remains deferred.",
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


def test_quickstart_is_hosted_first_and_localhost_is_secondary() -> None:
    html = (_WEBSITE_DIR / "quickstart.html").read_text(encoding="utf-8")

    hosted_index = html.index("https://scout.chowmes.com")
    localhost_index = html.index("http://127.0.0.1:8421")

    assert hosted_index < localhost_index
    assert "Do not use localhost for hosted calls." in html
    assert "Only after `scout serve` is running locally" in html
    assert 'src="/assets/copy-code.js"' in html


def test_command_docs_include_copy_code_behavior() -> None:
    for page_name in ("quickstart.html", "guide.html", "examples.html", "status.html", "beta.html"):
        html = (_WEBSITE_DIR / page_name).read_text(encoding="utf-8")

        assert "<pre><code>" in html
        assert 'src="/assets/copy-code.js"' in html


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

    if blocker_ids:
        assert f"{len(blocker_ids)} unique public-launch blocker keys" in html
    else:
        assert "Current blockers: 0" in html
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
