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
    assert "Acquisition primitives for real workflows." in html
    assert "Features in Scout are organized by what people need to do" in html
    assert "Demo and search builds" in html
    assert "Scout Playground" in html
    assert "Try every Scout capability before you buy." in html
    assert "Request hosted beta" in html
    assert 'href="/beta"' in html
    assert 'id="hostedBetaCheckout"' not in html
    assert "/v1/billing/stripe/checkout-session" not in html
    assert "checkout_url" not in html
    assert "window.location.assign" not in html
    assert "Scout beta demo" in html
    assert "URL to evidence to records in under a minute." in html
    assert "./assets/scout-product-demo.gif?v=20260630-slow-readable" in html
    assert "No hard-site bypass guarantee." in html
    assert "STRIPE_SECRET_KEY" not in html
    assert "sk_live_" not in html
    assert "sk_test_" not in html


def test_launch_website_keeps_paid_checkout_paused_without_secrets() -> None:
    html = (_WEBSITE_DIR / "pricing.html").read_text(encoding="utf-8")

    assert "Paid credit checkout stays paused" in html
    assert 'href="/beta#hosted-checkout"' in html
    assert 'id="pricingCheckoutForm"' not in html
    assert "/v1/billing/stripe/checkout-session" not in html
    assert "window.location.assign" not in html
    assert "sk_live_" not in html
    assert "sk_test_" not in html


def test_launch_website_states_current_launch_readiness_boundaries() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    assert "Acquisition primitives for real workflows." in normalized_html
    assert "Product catalogs" in normalized_html
    assert "Competitive intelligence" in normalized_html
    assert "Research archives" in normalized_html
    assert "Browser-assisted capture" in normalized_html
    assert "Hosted beta" in normalized_html
    assert "Claude/Codex skill" in normalized_html
    assert "Pay-as-you-go candidate" in normalized_html
    assert "Launch status" not in normalized_html
    assert "Production-ready multi-tenant SaaS" not in html
    assert "Unlimited hosted scraping" not in html


def test_public_distribution_copy_is_http_and_skill_only() -> None:
    public_files = [
        _WEBSITE_DIR / "index.html",
        _WEBSITE_DIR / "quickstart.html",
        _WEBSITE_DIR / "pricing.html",
        _REPO_ROOT / "README.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in public_files)
    normalized = " ".join(combined.split()).lower()

    assert "hosted http" in normalized
    assert "claude/codex skill" in normalized
    assert "docker" not in normalized


def test_api_root_serves_launch_website_from_same_origin() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Turn messy web pages into citable, downstream-ready records." in response.text
    assert "Clean records with evidence attached." in response.text
    assert "Acquisition primitives for real workflows." in response.text
    assert "Demo and search builds" in response.text
    assert 'id="hostedBetaCheckout"' not in response.text
    assert "/v1/billing/stripe/checkout-session" not in response.text
    assert "Scout app" not in response.text


def test_public_site_responses_are_reload_safe_after_deploys() -> None:
    client = TestClient(app)

    homepage = client.get("/")
    docs = client.get("/docs")
    styles = client.get("/styles.css")
    playground = client.get("/assets/playground.js")
    demo_gif = client.get("/assets/scout-product-demo.gif")

    for response in (homepage, docs):
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"

    for response in (styles, playground, demo_gif):
        assert response.status_code == 200
        assert response.headers["cache-control"] == "public, max-age=0, must-revalidate"


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
    pricing = client.get("/assets/pricing.js")
    account = client.get("/assets/account.js")
    old_hosted_keygen = client.get("/assets/hosted-keygen.js")

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
    assert pricing.status_code == 200
    assert "javascript" in pricing.headers["content-type"]
    assert "/v1/billing/packages" in pricing.text
    assert account.status_code == 200
    assert "javascript" in account.headers["content-type"]
    assert "/v1/hosted/me" in account.text
    assert "localStorage" not in account.text
    assert "sessionStorage" not in account.text
    assert old_hosted_keygen.status_code == 403


def test_launch_website_uses_flux_not_warm_industrial() -> None:
    for page in _WEBSITE_DIR.glob("*.html"):
        html = page.read_text(encoding="utf-8")
        assert "assets/flux-design-system/fonts.css" in html
        assert "assets/flux-design-system/tokens.css" in html
        assert "warm-industrial-design-system" not in html


def test_public_pages_share_streamlined_header_ia() -> None:
    expected_nav = (
        ">Overview</a>",
        ">Features</a>",
        ">Demo</a>",
        ">Docs</a>",
        ">Pricing</a>",
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
        assert ">Use Cases</a>" not in normalized_header
        assert ">Beta</a>" not in normalized_header
        assert "site-nav--utility" not in normalized_header


def test_homepage_has_streamlined_primary_nav_and_scrollspy() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

    normalized_html = " ".join(html.split())

    for nav_item in (
        ">Overview</a>",
        ">Features</a>",
        ">Demo</a>",
        ">Docs</a>",
        ">Pricing</a>",
    ):
        assert nav_item in normalized_html

    assert ">Quickstart</a>" not in normalized_html
    assert ">Examples</a>" not in normalized_html
    assert ">Guide</a>" not in normalized_html
    assert ">Use Cases</a>" not in normalized_html
    assert ">Beta</a>" not in normalized_html
    assert "API guide" not in normalized_html
    assert '<nav class="site-nav" aria-label="Primary navigation">' in normalized_html
    assert "site-nav--utility" not in normalized_html
    assert 'href="#use-cases" data-section-link="use-cases">Features</a>' in html
    assert 'href="#demo" data-section-link="demo">Demo</a>' in html
    assert 'href="#purchase" data-section-link="purchase">Pricing</a>' in html
    assert 'id="top"' in html
    assert 'id="use-cases"' in html
    assert 'data-nav-section="use-cases"' in html
    assert 'data-nav-section="demo"' in html
    assert 'id="playground"' in html
    assert 'id="purchase"' in html
    assert 'class="section feature-section"' not in html
    assert 'class="marquee-band"' not in html
    assert 'id="features"' not in html
    assert 'aria-current="true"' in html
    assert "IntersectionObserver" in html
    assert "setActiveSection" in html
    assert "dataset.navSection" in html
    assert 'src="./assets/scout-wordmark.svg"' in html
    assert 'href="./assets/scout-mark.svg"' in html


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
            "Technical documentation for Scout.",
            "Documentation map",
            "Start with the path you need.",
            "Try Scout in the homepage playground.",
            "The hosted playground lives under the demo flow",
            "Open playground",
            "Call the live Scout API.",
            "Register for a beta API key.",
            "Scout emails the API key, or shows it once when response fallback is enabled",
            'href="/beta#hosted-checkout"',
            "API reference",
            "The endpoints testers actually need.",
            "POST /v1/hosted/beta-key",
            "POST /v1/hosted/products",
            "POST /v1/hosted/run/{use_case}",
            "https://scout.chowmes.com",
            "Do not use localhost for hosted calls.",
            "codex/scout-saas-prod-ready",
            'pip install "git+https://github.com/arijitchowdhury80/scout.git@codex/scout-saas-prod-ready"',
            "SCOUT_WORKDIR",
            "Readiness check",
            "scout launch-readiness",
            "Private beta: ready_with_limits",
            "--require-public",
            "Local package is not the tester beta path.",
            "SCOUT_HOSTED_API_KEY",
            "/v1/hosted/me",
            "/v1/hosted/scrape",
            "email-based or one-time-key-display based",
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
            "Operator local verification",
            "Beta trial",
            "Hosted beta tester key",
            "$10",
            "1,000 standard credits",
            "Pay-as-you-go candidate",
            "unit economics",
            "Estimated gross margin: 74.1%",
            "No unlimited hosted crawling",
        ],
        "status.html": [
            "Scout Launch Status",
            "Hosted beta: ready_with_limits",
            "Launch readiness: ready",
            "What changed in the blocker burndown?",
            "Arijit decisions: closed",
            "Codex gates: closed",
            "Self-service beta keys: active",
            "Current blockers: 0",
            "Blocker summary",
            "Future public registry work",
            "Future paid checkout work",
            "Future security-clean work",
            "Decisions recorded for the beta path.",
            "License: Apache-2.0 for Scout local/core",
            "Pricing: controlled beta posture",
            "Publishing: artifact-only private-beta v* tag first",
            "Hosted: self-service beta keys",
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
                "Generate your hosted beta key",
                "Tester handoff packet",
                "docs/product/private-beta-tester-handoff.md",
                "Hosted beta checkout",
                "Request hosted API access.",
                "Scout provisions the beta trial after Stripe confirms the setup",
                "100 standard credits",
                "beta_trial",
                "/v1/billing/stripe/checkout-session",
                "Private beta is hosted HTTP first",
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
    assert "not use localhost for hosted calls." in html


def test_docs_beta_access_is_self_service_email_delivery_without_password() -> None:
    html = (_WEBSITE_DIR / "quickstart.html").read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())
    css = (_WEBSITE_DIR / "styles.css").read_text(encoding="utf-8")

    assert '<form id="hostedKeyForm"' not in html
    assert 'src="./assets/hosted-keygen.js"' not in html
    assert 'name="invite_password"' not in html
    assert 'type="password"' not in html
    assert 'id="copyHostedKey"' not in html
    assert "Register for a beta API key." in normalized_html
    assert (
        "Scout emails the API key, or shows it once when response fallback is enabled"
        in normalized_html
    )
    assert 'href="/beta#hosted-checkout"' in html
    assert "/v1/hosted/beta-key" in html
    assert ".hosted-key-card" in css
    assert ".hosted-key-result" in css
    assert "Only after `scout serve` is running on your own machine" in html
    assert "http://127.0.0.1:8421" not in html
    assert 'src="./assets/copy-code.js"' in html


def test_pricing_page_explains_credit_packages_and_unit_economics() -> None:
    html = (_WEBSITE_DIR / "pricing.html").read_text(encoding="utf-8")
    pricing_js = (_WEBSITE_DIR / "assets" / "pricing.js").read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    expected_strings = [
        "$10",
        "1,000 standard credits",
        "1 scrape = 1 standard credit",
        "1 returned crawl page = 1 standard credit",
        "1 screenshot = 3 standard credits",
        "1 browser minute = 10 browser credits",
        "Estimated cost for 1,000 standard credits: $2.59",
        "Estimated gross margin: 74.1%",
        "Break-even: 17 packs/month",
        "Beta trial",
        "30 days",
        "100 standard credits",
    ]

    for expected in expected_strings:
        assert expected in normalized_html

    assert 'data-packages-endpoint="/v1/billing/packages"' in html
    assert 'id="pricingPackageGrid"' in html
    assert 'id="pricingCreditCosts"' in html
    assert 'id="pricingUnitEconomics"' in html
    assert 'id="pricingCheckoutForm"' not in html
    assert 'id="pricingCheckoutReturnStatus"' not in html
    assert 'data-success-query="checkout=success"' not in html
    assert 'data-cancel-query="checkout=cancelled"' not in html
    assert "$0" in normalized_html
    assert "Paid packages are shown for unit-economics visibility" in normalized_html
    assert "Paid credit checkout stays paused" in normalized_html
    assert "/v1/billing/stripe/checkout-session" not in html
    assert 'href="/beta#hosted-checkout"' in html
    assert "/v1/billing/packages" in pricing_js
    assert "amount_cents" in pricing_js
    assert "gross_margin_percent" in pricing_js
    assert "sk_live_" not in pricing_js
    assert "sk_test_" not in pricing_js


def test_beta_signup_collects_name_and_email_without_password() -> None:
    html = (_WEBSITE_DIR / "beta.html").read_text(encoding="utf-8")
    pricing_js = (_WEBSITE_DIR / "assets" / "pricing.js").read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    assert 'id="pricingCheckoutForm"' in html
    assert 'name="name"' in html
    assert 'name="email"' in html
    assert 'name="package_id"' in html
    assert 'value="beta_trial"' in html
    assert 'data-endpoint="/v1/billing/stripe/checkout-session"' in html
    assert 'data-ready-flag="ready_for_beta_checkout"' in html
    assert "through the hosted checkout flow" in normalized_html
    assert "Public signup never shows raw keys" in normalized_html
    assert "Scout opens Stripe Checkout" in normalized_html
    assert "100 standard credits" in normalized_html
    assert "pricingCheckoutForm" in html
    assert "/v1/hosted/beta-key" not in html
    assert "/v1/billing/stripe/status" in html
    assert "ready_for_beta_checkout" in html
    assert "/v1/billing/stripe/checkout-session" in html
    assert "payload.raw_api_key" not in html
    assert "Hosted beta checkout is paused" in pricing_js
    assert 'type="password"' not in html
    assert 'name="invite_password"' not in html


def test_account_page_lets_hosted_users_inspect_usage_without_login() -> None:
    html = (_WEBSITE_DIR / "account.html").read_text(encoding="utf-8")
    account_js = (_WEBSITE_DIR / "assets" / "account.js").read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    assert "Hosted Account" in html
    assert "Check credits, usage, and purchases" in normalized_html
    assert 'id="hostedAccountForm"' in html
    assert 'id="hostedAccountKey"' in html
    assert 'autocomplete="off"' in html
    assert 'name="api_key"' in html
    assert 'id="hostedAccountSummary"' in html
    assert 'id="hostedUsageLedger"' in html
    assert 'id="hostedPurchaseLedger"' in html
    assert 'src="./assets/account.js"' in html
    assert "/v1/hosted/me" in account_js
    assert "/v1/hosted/usage" in account_js
    assert "/v1/hosted/purchases" in account_js
    assert "Authorization" in account_js
    assert "Bearer" in account_js
    assert "localStorage" not in account_js
    assert "sessionStorage" not in account_js
    assert "sk_live_" not in html
    assert "sk_live_" not in account_js


def test_command_docs_include_copy_code_behavior() -> None:
    for page_name in ("quickstart.html", "status.html", "beta.html"):
        html = (_WEBSITE_DIR / page_name).read_text(encoding="utf-8")

        assert "<pre><code>" in html
        assert 'src="./assets/copy-code.js"' in html


def test_homepage_has_hosted_playground_controls_under_demo_flow() -> None:
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

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
    assert (
        'id="playgroundUrl"\n                      name="url"\n                      type="text"'
        in html
    )
    assert 'inputmode="url"' in html
    assert "normalizePublicUrl" in (_WEBSITE_DIR / "assets" / "playground.js").read_text(
        encoding="utf-8"
    )
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
    assert 'src="./assets/playground.js"' in html


def test_docs_page_links_to_playground_without_embedding_controls() -> None:
    html = (_WEBSITE_DIR / "quickstart.html").read_text(encoding="utf-8")

    assert "Technical documentation for Scout." in html
    assert 'class="docs-layout"' in html
    assert 'class="docs-sidebar"' in html
    assert 'class="docs-content"' in html
    assert "Try Scout in the homepage playground." in html
    assert 'href="/#playground"' in html
    assert "API setup" in html
    assert "Operator verification" in html
    assert "Artifact contract" in html
    assert 'id="playgroundForm"' not in html
    assert 'id="playgroundWorkflow"' not in html
    assert 'src="./assets/playground.js"' not in html


def test_api_serves_launch_website_beta_onboarding_pages_without_auth() -> None:
    client = TestClient(app)

    expected = {
        "/quickstart": "Scout Docs",
        "/docs": "Scout Docs",
        "/guide": "Scout Docs",
        "/pricing": "Scout Pricing",
        "/examples": "Scout Docs",
        "/status": "Scout Launch Status",
        "/beta": "Scout Private Beta",
        "/account": "Scout Hosted Account",
        "/legal": "Scout Legal And Third-Party Notices",
        "/terms": "Scout Beta Terms Placeholder",
        "/privacy": "Scout Beta Privacy Placeholder",
        "/quickstart.html": "Scout Docs",
        "/docs.html": "Scout Docs",
        "/guide.html": "Scout Docs",
        "/pricing.html": "Scout Pricing",
        "/examples.html": "Scout Docs",
        "/status.html": "Scout Launch Status",
        "/beta.html": "Scout Private Beta",
        "/account.html": "Scout Hosted Account",
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


def test_public_docs_route_serves_software_docs_and_api_docs_move_to_api_docs() -> None:
    client = TestClient(app)

    public_docs = client.get("/docs")
    api_docs = client.get("/api/docs")

    assert public_docs.status_code == 200
    assert "Scout Docs" in public_docs.text
    assert "Technical documentation for Scout." in public_docs.text
    assert "Swagger UI" not in public_docs.text
    assert api_docs.status_code == 200
    assert "Swagger UI" in api_docs.text


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
