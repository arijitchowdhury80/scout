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

    assert "./assets/flux-design-system/fonts.css" in html
    assert "./assets/flux-design-system/tokens.css" in html
    assert "warm-industrial-design-system" not in html
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
    flux_fonts = client.get("/assets/flux-design-system/fonts.css")
    flux_tokens = client.get("/assets/flux-design-system/tokens.css")
    demo_gif = client.get("/assets/scout-product-demo.gif")
    logo = client.get("/assets/scout-wordmark.svg")
    mark = client.get("/assets/scout-mark.svg")
    copy_code = client.get("/assets/copy-code.js")
    playground = client.get("/assets/playground.js")

    assert styles.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    assert ".beta-form" in styles.text
    assert ".brand-logo" in styles.text
    assert "aria-current" in styles.text
    assert ".code-copy__button" in styles.text
    assert flux_fonts.status_code == 200
    assert "text/css" in flux_fonts.headers["content-type"]
    assert "Satoshi" in flux_fonts.text
    assert flux_tokens.status_code == 200
    assert "text/css" in flux_tokens.headers["content-type"]
    assert "--flux-yellow" in flux_tokens.text
    assert ".flux-card" in flux_tokens.text
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
    assert playground.status_code == 200
    assert "javascript" in playground.headers["content-type"]
    assert "/v1/playground/run" in playground.text
    assert "Download JSON" not in playground.text


def test_launch_website_uses_flux_not_warm_industrial() -> None:
    for page in _WEBSITE_DIR.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        assert "assets/flux-design-system/fonts.css" in html
        assert "assets/flux-design-system/tokens.css" in html
        assert "warm-industrial-design-system" not in html


def test_public_pages_share_streamlined_header_ia() -> None:
    expected_nav = (
        ">Overview</a>",
        ">Demo</a>",
        ">Use Cases</a>",
        ">Docs</a>",
        ">Pricing</a>",
        ">Beta</a>",
    )

    for page in _WEBSITE_DIR.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        header = html.split('<header class="site-header">', 1)[1].split("</header>", 1)[0]
        normalized_header = " ".join(header.split())

        assert '<nav class="site-nav" aria-label="Primary navigation">' in normalized_header
        for nav_item in expected_nav:
            assert nav_item in normalized_header
        assert ">Quickstart</a>" not in normalized_header
        assert ">Examples</a>" not in normalized_header
        assert ">Guide</a>" not in normalized_header
        assert "API guide" not in normalized_header
        assert ">Status</a>" not in normalized_header
        assert ">Legal</a>" not in normalized_header
        assert "site-nav--utility" not in normalized_header


def test_homepage_has_streamlined_primary_nav_and_scrollspy() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

    normalized_html = " ".join(html.split())

    for nav_item in (
        ">Overview</a>",
        ">Demo</a>",
        ">Use Cases</a>",
        ">Docs</a>",
        ">Pricing</a>",
        ">Beta</a>",
    ):
        assert nav_item in normalized_html

    assert ">Quickstart</a>" not in normalized_html
    assert ">Examples</a>" not in normalized_html
    assert ">Guide</a>" not in normalized_html
    assert "API guide" not in normalized_html
    assert '<nav class="site-nav" aria-label="Primary navigation">' in normalized_html
    assert "site-nav--utility" not in normalized_html
    assert 'data-section-link="top"' in html
    assert 'data-section-link="demo"' in html
    assert 'data-section-link="use-cases"' in html
    assert 'id="top"' in html
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
            "Scout Docs",
            "One page for hosted API, local install, examples, and artifacts.",
            "Scout Playground",
            "Try every Scout capability before you buy.",
            "The playground rejects local/private URLs",
            "Download JSON",
            "Download Markdown",
            "This replaces separate Quickstart, Guide, Examples, and API Guide pages.",
            "Call the live Scout API.",
            "API reference",
            "The endpoints testers actually need.",
            "POST /products",
            "POST /run/{use_case}",
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
            "Examples",
            "Page to markdown",
            "Product category to records",
            "Company intelligence packet",
            "Artifact contract",
            "records.json",
            "source_pages.json",
            "blocked_pages.json",
            "extraction_report.md",
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
    localhost_index = html.index("http://localhost:8421")

    assert hosted_index < localhost_index
    assert "Do not use localhost for hosted calls." in html
    assert "Only after `scout serve` is running on your own machine" in html
    assert "http://127.0.0.1:8421" not in html
    assert 'src="/assets/copy-code.js"' in html


def test_command_docs_include_copy_code_behavior() -> None:
    for page_name in ("quickstart.html", "status.html", "beta.html"):
        html = (_WEBSITE_DIR / page_name).read_text(encoding="utf-8")

        assert "<pre><code>" in html
        assert 'src="/assets/copy-code.js"' in html


def test_docs_page_has_hosted_playground_controls() -> None:
    html = (_WEBSITE_DIR / "quickstart.html").read_text(encoding="utf-8")

    assert "Scout Playground" in html
    assert "Choose a Scout capability" in html
    assert "Acquire" in html
    assert "Intelligence" in html
    assert "Commerce" in html
    assert "Evidence And Exports" in html
    assert 'id="playgroundForm"' in html
    assert 'name="workflow"' in html
    for capability in (
        "scrape",
        "crawl",
        "map",
        "extract",
        "screenshot",
        "products",
        "company",
        "prism",
        "investor",
        "careers",
        "jobs",
        "news",
        "research",
        "docs",
        "social",
        "locations",
        "website-quality",
    ):
        assert f'value="{capability}"' in html
    assert 'id="playgroundUrl"' in html
    assert 'id="playgroundQuery"' in html
    assert 'name="output_format"' in html
    assert 'value="json"' in html
    assert 'value="markdown"' in html
    assert 'id="playgroundStatus"' in html
    assert 'id="playgroundResults"' in html
    assert 'id="playgroundCurl"' in html
    assert 'data-playground-tab="preview"' in html
    assert 'data-playground-tab="json"' in html
    assert 'data-playground-tab="markdown"' in html
    assert 'data-playground-tab="curl"' in html
    assert 'id="playgroundDownloadJson"' in html
    assert 'id="playgroundDownloadMarkdown"' in html
    assert 'src="/assets/playground.js"' in html


def test_api_serves_launch_website_beta_onboarding_pages_without_auth() -> None:
    client = TestClient(app)

    expected = {
        "/quickstart": "Scout Docs",
        "/guide": "Scout Docs",
        "/pricing": "Scout Pricing",
        "/examples": "Scout Docs",
        "/status": "Scout Launch Status",
        "/beta": "Scout Private Beta",
        "/legal": "Scout Legal And Third-Party Notices",
        "/terms": "Scout Beta Terms Placeholder",
        "/privacy": "Scout Beta Privacy Placeholder",
        "/quickstart.html": "Scout Docs",
        "/guide.html": "Scout Docs",
        "/pricing.html": "Scout Pricing",
        "/examples.html": "Scout Docs",
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
