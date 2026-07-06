"""Tests for the static Scout launch website (neumorphic rebuild, 2026-07-06).

Reconciled to docs/product/design-system.md, docs/product/plg-playground-ux.md,
and docs/product/pricing-model-2026-07-06.md. The homepage is now the live
demo console (direction E): reticle wordmark, mint neumorphic shell, anonymous
scrape+map demo wired to /v1/demo/*, authed app shell at /app, and pricing
copy that names the credit number instead of claiming "unlimited".
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from scout.api.main import app
from scout.launch_readiness import build_report


_WEBSITE_DIR = Path(__file__).resolve().parents[3] / "website"
_WEBSITE_INDEX = _WEBSITE_DIR / "index.html"
_REPO_ROOT = _WEBSITE_DIR.parent


def test_homepage_is_live_demo_console_with_reticle_lockup() -> None:
    """Homepage IS the live demo console (locked design-system.md, 2026-07-06)."""
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

    assert "warm-industrial-design-system" not in html
    assert "Point Scout at any URL." in html
    assert "Watch it return a citable record." in html
    assert 'id="scoutConsole"' in html
    assert 'id="consoleForm"' in html
    assert 'id="consoleUrl"' in html
    assert 'data-endpoint="scrape"' in html
    assert 'data-endpoint="map"' in html
    assert "/v1/demo/scrape" in html
    assert "/v1/demo/map" in html
    assert "RECORDS" in html
    assert "PROOF" in html
    assert "EXPORTS" in html
    assert "One API. Every acquisition primitive." in html
    assert "Start with" in html
    assert "free credits" in html
    assert 'href="/beta"' in html
    # Reticle lockup: outer ring + 4 crosshair ticks + amber center dot, sized
    # to sit as the "o" in "Scout".
    assert 'viewBox="0 0 40 40"' in html
    assert 'aria-label="Scout reticle mark"' in html
    assert 'fill="#C77A1E"' in html
    # No paid-checkout wiring or secrets leak onto the public homepage.
    assert 'id="hostedBetaCheckout"' not in html
    assert "/v1/billing/stripe/checkout-session" not in html
    assert "checkout_url" not in html
    assert "window.location.assign" not in html
    assert "STRIPE_SECRET_KEY" not in html
    assert "sk_live_" not in html
    assert "sk_test_" not in html


def test_launch_website_keeps_paid_checkout_gated_behind_readiness_without_secrets() -> None:
    html = (_WEBSITE_DIR / "pricing.html").read_text(encoding="utf-8")
    pricing_js = (_WEBSITE_DIR / "assets" / "pricing.js").read_text(encoding="utf-8")

    assert "credit_policy" in pricing_js
    assert "operator_next_actions" in pricing_js
    assert "readinessDetailsMessage" in pricing_js
    assert "window.location.assign" in pricing_js
    assert "amount_cents" in pricing_js
    assert "sk_live_" not in html
    assert "sk_test_" not in html
    assert "sk_live_" not in pricing_js
    assert "sk_test_" not in pricing_js


def test_homepage_capability_grid_states_current_shipped_primitives_only() -> None:
    """Homepage per-capability grid states real, currently-shipped primitives only."""
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    assert "One API. Every acquisition primitive." in normalized_html
    assert "Scrape" in normalized_html
    assert "Crawl" in normalized_html
    assert "Map" in normalized_html
    assert "Products" in normalized_html
    assert "Company" in normalized_html
    assert "Screenshot" in normalized_html
    assert "Launch status" not in normalized_html
    assert "Production-ready multi-tenant SaaS" not in html
    assert "Unlimited hosted scraping" not in html
    assert "unlimited" not in html.lower()


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
    assert "Point Scout at any URL." in response.text
    assert "Watch it return a citable record." in response.text
    assert 'id="scoutConsole"' in response.text
    assert "/v1/demo/scrape" in response.text
    assert 'id="hostedBetaCheckout"' not in response.text
    assert "/v1/billing/stripe/checkout-session" not in response.text


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


def test_app_shell_is_now_a_shipped_authed_playground_surface() -> None:
    """/app was previously a removed surface; design-system.md now locks in an
    authed app shell (sidebar: Playground / Your runs / Destinations / API
    keys / Usage / Docs + credit meter). It must be served, and other
    surfaces that were NOT reintroduced stay 403."""
    client = TestClient(app)

    app_response = client.get("/app")
    assert app_response.status_code == 200
    assert "text/html" in app_response.headers["content-type"]
    assert "Scout App" in app_response.text

    for path in ("/api/config", "/app/live-browser"):
        response = client.get(path)
        assert response.status_code == 403
        assert "text/html" not in response.headers.get("content-type", "")


def test_api_serves_launch_website_static_assets_without_auth() -> None:
    client = TestClient(app)

    styles = client.get("/styles.css")
    demo_gif = client.get("/assets/scout-product-demo.gif")
    logo = client.get("/assets/scout-wordmark.svg")
    mark = client.get("/assets/scout-mark.svg")
    copy_code = client.get("/assets/copy-code.js")
    playground = client.get("/assets/playground.js")
    pricing = client.get("/assets/pricing.js")
    account = client.get("/assets/account.js")
    hosted_keygen = client.get("/assets/hosted-keygen.js")
    status_js = client.get("/assets/status.js")

    assert styles.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    # Neumorphic design-system classes present (design-system.md components).
    assert ".neu-card" in styles.text
    assert ".neu-well" in styles.text
    assert ".input-well" in styles.text
    assert ".screen-frame" in styles.text
    assert ".tab" in styles.text
    assert "--ex:" in styles.text
    assert "--in:" in styles.text
    assert "--ind:" in styles.text
    assert demo_gif.status_code == 200
    assert demo_gif.headers["content-type"] == "image/gif"
    assert demo_gif.content.startswith((b"GIF87a", b"GIF89a"))
    assert logo.status_code == 200
    assert logo.headers["content-type"] in {"image/svg+xml", "image/svg+xml; charset=utf-8"}
    assert mark.status_code == 200
    assert mark.headers["content-type"] in {"image/svg+xml", "image/svg+xml; charset=utf-8"}
    assert copy_code.status_code == 200
    assert "javascript" in copy_code.headers["content-type"]
    assert "navigator.clipboard.writeText" in copy_code.text
    assert playground.status_code == 200
    assert "javascript" in playground.headers["content-type"]
    assert pricing.status_code == 200
    assert "javascript" in pricing.headers["content-type"]
    assert "/v1/billing/packages" in pricing.text
    assert "credit_policy" in pricing.text
    assert account.status_code == 200
    assert "javascript" in account.headers["content-type"]
    assert "/v1/hosted/me" in account.text
    assert hosted_keygen.status_code == 200
    assert "javascript" in hosted_keygen.headers["content-type"]
    assert "/v1/hosted/beta-key" in hosted_keygen.text
    assert status_js.status_code == 200
    assert "javascript" in status_js.headers["content-type"]
    assert "/v1/billing/stripe/status" in status_js.text
    assert "operator_next_actions" in status_js.text


def test_beta_page_uses_email_registration_without_card_or_password() -> None:
    """The public beta page is a simple email-only signup — no card, no password."""
    html = (_WEBSITE_DIR / "beta.html").read_text(encoding="utf-8")
    hosted_keygen = (_WEBSITE_DIR / "assets" / "hosted-keygen.js").read_text(encoding="utf-8")

    assert 'id="hostedRegisterForm"' in html
    assert 'data-endpoint="/v1/hosted/beta-key"' in html
    assert 'id="hostedRegEmailBtn"' in html
    assert "Email me my API key" in html
    assert "Sign up for the beta" in html
    assert "Start $0 Beta Checkout" not in html
    assert "data-checkout-endpoint" not in html
    assert "/v1/billing/stripe/checkout-session" not in html
    assert 'name="package_id"' not in html
    assert 'type="password"' not in html
    assert 'name="invite_password"' not in html
    assert "submitEmailRegistration" in hosted_keygen
    assert "payload.raw_api_key" not in html


def test_beta_page_is_single_email_signup_with_support_contact() -> None:
    """Launch UX is one primary action — email me my key — plus a support contact line.

    The self-serve reissue form was removed (2026-07-06): support handles lost keys via
    support@scout.chowmes.com; the backend reissue endpoint remains for operator use."""
    html = (_WEBSITE_DIR / "beta.html").read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    assert "Get your Scout API key." in normalized_html
    assert "10,000 credits. 30 days. Just your email." in normalized_html
    assert 'id="hostedRegisterForm"' in html
    assert "Email me my API key" in normalized_html
    assert "No credit card." in normalized_html

    assert "Recommended beta path" not in normalized_html
    assert "Start $0 Beta Checkout" not in normalized_html
    assert 'id="hostedBetaCheckoutForm"' not in html

    # Reissue UI removed; support contact takes its place.
    assert 'id="hostedKeyReissueForm"' not in html
    assert "Lost your API key?" not in normalized_html
    assert "support@scout.chowmes.com" in html
    assert "reaches the founder directly" in normalized_html


def test_rebuilt_pages_use_reticle_wordmark_not_legacy_marks() -> None:
    """Pages rebuilt in the neumorphic language carry the reticle lockup, not
    the retired warm-industrial or flux visual system."""
    rebuilt_pages = ["index.html", "pricing.html", "beta.html", "quickstart.html", "status.html", "legal.html"]
    for page_name in rebuilt_pages:
        html = (_WEBSITE_DIR / page_name).read_text(encoding="utf-8")
        assert "warm-industrial-design-system" not in html
        assert 'stroke="#143C2B"' in html
        assert 'fill="#C77A1E"' in html


def test_rebuilt_pages_share_site_header_and_beta_cta() -> None:
    """Pages rebuilt to the neumorphic language share the site-header /
    nav-primary shell and route the primary CTA to /beta."""
    rebuilt_pages = ["index.html", "pricing.html", "beta.html", "quickstart.html", "status.html", "legal.html"]
    for page_name in rebuilt_pages:
        html = (_WEBSITE_DIR / page_name).read_text(encoding="utf-8")
        assert '<header class="site-header">' in html
        assert '<nav class="nav-primary" aria-label="Primary navigation">' in html
        assert '>Pricing</a>' in html
        assert '>Docs</a>' in html


def test_homepage_has_streamlined_primary_nav_and_reticle_hero() -> None:
    """Homepage nav is a simple top-level Product/Docs/Pricing row (locked IA);
    the console IS the hero, so there is no separate scrollspy-anchored
    features/demo section to link to. See docs/product/design-system.md."""
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

    normalized_html = " ".join(html.split())

    for nav_item in (">Product</a>", ">Docs</a>", ">Pricing</a>"):
        assert nav_item in normalized_html

    assert ">Quickstart</a>" not in normalized_html
    assert ">Examples</a>" not in normalized_html
    assert ">Guide</a>" not in normalized_html
    assert ">Use Cases</a>" not in normalized_html
    assert "API guide" not in normalized_html
    assert '<nav class="nav-primary" aria-label="Primary navigation">' in normalized_html
    assert 'id="top"' in html
    assert 'id="console"' in html
    assert 'id="scoutConsole"' in html
    assert 'class="wm wm--lg"' in html
    assert 'viewBox="0 0 40 40"' in html
    assert 'aria-label="Scout reticle mark"' in html


def test_launch_website_demo_gif_is_real_beta_safe_media() -> None:
    demo_gif = _WEBSITE_DIR / "assets" / "scout-product-demo.gif"

    data = demo_gif.read_bytes()

    assert data.startswith((b"GIF87a", b"GIF89a"))
    assert len(data) > 20_000
    assert b"sk_live_" not in data
    assert b"sk_test_" not in data


def test_launch_website_demo_gif_is_slow_enough_to_read() -> None:
    from PIL import Image, ImageSequence

    demo_gif = _WEBSITE_DIR / "assets" / "scout-product-demo.gif"

    with Image.open(demo_gif) as image:
        durations = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(image)]

    assert len(durations) >= 3
    assert min(durations) >= 10_000


def test_launch_website_has_beta_onboarding_pages() -> None:
    pages = {
        "quickstart.html": [
            "Scout Docs",
            "Technical documentation for Scout.",
            "Documentation map",
            "Start with the path you need.",
            "Try Scout in the homepage playground.",
            "Open playground",
            "Call the live Scout API.",
            "Register for your beta tester API key.",
            "provisions a finite-credit beta account",
            'href="/beta.html#beta-key"',
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
            "Scout emails the API key",
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
            "Start free. Pay only when you scale.",
            "Free",
            "5,000 credits",
            "$12",
            "50,000 credits",
            "Prefer no commitment?",
            "$10",
            "10k",
            "$25",
            "30k",
            "$100",
            "150k",
            "Never expire.",
        ],
        "status.html": [
            "Scout Launch Status",
            "Scout hosted beta is online, but self-service is still gated.",
            "Hosted service: online",
            "Beta signup: configuration blocked",
            "What changed in the blocker burndown?",
            "Arijit decisions: closed",
            "Codex gates: closed",
            "Hosted beta keys: gated by email delivery",
            "Current blockers: configuration",
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
            "Get your Scout API key.",
            "10,000 credits. 30 days. Just your email.",
            "Sign up for the beta",
            "Email me my API key",
            "No credit card.",
            "/v1/hosted/beta-key",
            "10,000 credits is plenty",
            "support@scout.chowmes.com",
        ],
        "legal.html": [
            "Scout Legal And Third-Party Notices",
            "This is not legal advice.",
            "Crawl4AI",
            "https://x.com/unclecode",
            "Apache License, Version 2.0",
            "Scout local/core is Apache-2.0",
            "Hosted beta is capped; public claims stay gated.",
        ],
        "terms.html": [
            "Scout Beta Terms Placeholder",
            "This is not a final Terms of Service.",
            "Use Scout only for websites and data you are allowed to access.",
            "No guaranteed hard-site bypass.",
            "Hosted beta is capped and metered.",
            "Hosted beta is capped and configuration-gated.",
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
            assert expected in normalized_html, f"{page_name} missing: {expected!r}"
        assert "sk_live_" not in html
        assert "sk_test_" not in html


def test_quickstart_is_hosted_first_and_localhost_is_secondary() -> None:
    html = (_WEBSITE_DIR / "quickstart.html").read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    hosted_index = html.index("https://scout.chowmes.com")
    localhost_index = html.index("http://localhost:8421")

    assert hosted_index < localhost_index
    assert "Do not use localhost for hosted calls." in normalized_html


def test_docs_beta_access_is_card_backed_first_without_password() -> None:
    html = (_WEBSITE_DIR / "quickstart.html").read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    assert '<form id="hostedKeyForm"' not in html
    assert 'name="invite_password"' not in html
    assert 'type="password"' not in html
    assert 'id="copyHostedKey"' not in html
    assert "Register for your beta tester API key." in normalized_html
    assert "provisions a finite-credit beta account" in normalized_html
    assert 'href="/beta.html#beta-key"' in html
    assert "Only after" in normalized_html
    assert "scout serve" in normalized_html
    assert "is running on your own machine" in normalized_html
    assert "http://127.0.0.1:8421" not in html
    assert 'src="./assets/copy-code.js"' in html


def test_pricing_page_reflects_locked_2026_07_06_pricing_model() -> None:
    """Pricing copy matches docs/product/pricing-model-2026-07-06.md: Free
    5,000 one-time, Monthly $12/50,000 (never called "unlimited"), pay-go
    packs demoted/secondary, dossier ~200 credits."""
    html = (_WEBSITE_DIR / "pricing.html").read_text(encoding="utf-8")
    normalized_html = " ".join(html.split())

    expected_strings = [
        "Start free. Pay only when you scale.",
        "$0",
        "5,000 credits",
        "$12",
        "50,000 credits",
        "resets monthly",
        "dossiers",
        "$10",
        "$25",
        "$100",
        "Never expire.",
    ]
    for expected in expected_strings:
        assert expected in normalized_html

    # Brand-integrity rule: never say "unlimited" for a capped plan.
    assert "unlimited" not in normalized_html.lower()
    assert "sk_live_" not in html
    assert "sk_test_" not in html


def test_public_website_describes_self_service_beta_not_invite_only() -> None:
    """Public website copy should match the no-password self-service beta model."""
    pages = [
        "index.html",
        "beta.html",
        "pricing.html",
        "quickstart.html",
        "status.html",
    ]
    banned_phrases = [
        "invite-only",
        "invited beta testers",
        "approved testers",
        "approved private beta testers",
        "waiting for manual operator provisioning",
        "shows the key once",
    ]

    for page_name in pages:
        html = (_WEBSITE_DIR / page_name).read_text(encoding="utf-8").lower()
        for phrase in banned_phrases:
            assert phrase not in html


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
    assert "/v1/hosted/me" in account_js
    assert "/v1/hosted/usage" in account_js
    assert "/v1/hosted/purchases" in account_js
    assert "Authorization" in account_js
    assert "Bearer" in account_js
    assert "standard_balance_after" in account_js
    assert "browser_balance_after" in account_js
    assert "localStorage" not in account_js
    assert "sessionStorage" not in account_js
    assert "sk_live_" not in html
    assert "sk_live_" not in account_js


def test_command_docs_include_copy_code_behavior() -> None:
    # The beta page is a clean signup form with no CLI snippets; copy-code docs
    # live on the docs and status pages.
    for page_name in ("quickstart.html", "status.html"):
        html = (_WEBSITE_DIR / page_name).read_text(encoding="utf-8")

        assert "<pre><code>" in html
        assert 'src="./assets/copy-code.js"' in html


def test_homepage_has_anonymous_console_gated_to_fast_endpoints_only() -> None:
    """Anonymous homepage console is fast-endpoints-only (scrape + map); the
    full multi-capability app playground (all workflow values, downloads,
    save) is an authed /app surface, not the public homepage. See
    docs/product/plg-playground-ux.md "Anonymous console limits"."""
    html = _WEBSITE_INDEX.read_text(encoding="utf-8")

    assert 'id="scoutConsole"' in html
    assert 'id="consoleForm"' in html
    assert 'id="consoleUrl"' in html
    assert 'inputmode="url"' in html
    assert 'data-endpoint="scrape"' in html
    assert 'data-endpoint="map"' in html
    # Heavy/costly endpoints are visible as disabled tabs, never runnable anonymously.
    for gated_capability in ("crawl", "products", "company", "screenshot"):
        assert f'data-endpoint="{gated_capability}"' in html
    assert 'aria-disabled="true"' in html
    assert "/v1/demo/scrape" in html
    assert "/v1/demo/map" in html
    assert 'id="consoleStatusMeta"' in html
    assert 'id="consoleCode"' in html
    assert "5 runs/IP/day" in html
    # No authed-only affordances (download/save) leak onto the anonymous console.
    assert "sign up to download" in html.lower() or "sign up to unlock" in html.lower()


def test_docs_page_links_to_playground_without_embedding_controls() -> None:
    html = (_WEBSITE_DIR / "quickstart.html").read_text(encoding="utf-8")

    assert "Technical documentation for Scout." in html
    assert 'class="docs-layout"' in html
    assert 'class="docs-sidebar"' in html
    assert 'class="docs-content"' in html
    assert "Try Scout in the homepage playground." in html
    assert 'href="/#playground"' in html
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
        "/beta": "Get your Scout API key.",
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
        "/beta.html": "Get your Scout API key.",
        "/account.html": "Scout Hosted Account",
        "/legal.html": "Scout Legal And Third-Party Notices",
        "/terms.html": "Scout Beta Terms Placeholder",
        "/privacy.html": "Scout Beta Privacy Placeholder",
        "/app": "Scout App",
        "/app.html": "Scout App",
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
        assert "Current blockers: external configuration" in html
        assert "SMTP delivery and Stripe checkout/webhook configuration" in html
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


def test_no_vendor_locked_destinations_copy_on_public_pages() -> None:
    """Destinations (Algolia/webhook) is an authed, post-run app surface —
    never marketed on the public GTM homepage/pricing/beta pages. See
    docs/product/plg-playground-ux.md "Destinations ... secondary surface,
    NOT the GTM homepage"."""
    public_pages = ["index.html", "beta.html", "pricing.html"]
    for page_name in public_pages:
        html = (_WEBSITE_DIR / page_name).read_text(encoding="utf-8")
        assert "Push to Algolia" not in html


def test_app_shell_has_result_tabs_and_destinations_panel() -> None:
    """The authed app shell (design-system.md IA: Playground / Your runs /
    Destinations / API keys / Usage / Docs + credit meter) renders results
    inline with tabs (Preview/JSON/JSONL/Table-CSV/cURL) and an evidence
    panel, and Destinations (Algolia/webhook) is only offered here, never on
    the public homepage."""
    html = (_WEBSITE_DIR / "app.html").read_text(encoding="utf-8")

    assert "key-gate" in html
    assert 'id="apiKeyInput"' in html
    assert 'id="appShell"' in html
    assert 'class="app-sidebar"' in html
    assert "Playground" in html
    assert "Your runs" in html
    assert "Destinations" in html
    assert "API keys" in html
    assert "Usage" in html
    assert 'class="credit-meter"' in html

    # Result tabs: Preview / JSON / JSONL / Table-CSV / cURL.
    assert 'data-rtab="preview"' in html
    assert 'data-rtab="json"' in html
    assert 'data-rtab="jsonl"' in html
    assert 'data-rtab="table"' in html
    assert 'data-rtab="curl"' in html

    # Evidence panel + destination send, authed-only.
    assert "Evidence" in html
    assert "Send to a destination" in html
    assert 'id="destinationSelect"' in html
    assert "Algolia" in html
    assert "Webhook" in html

    # Bearer-token session auth, never persisted to disk.
    assert "sessionStorage" in html
    assert "localStorage" not in html
    assert "Authorization" in html
    assert "Bearer" in html
    assert "sk_live_" not in html
    assert "sk_test_" not in html
