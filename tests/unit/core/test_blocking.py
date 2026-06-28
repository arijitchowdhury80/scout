"""Unit tests for Scout's block-detection spine (acquisition ladder P1).

A real page must not be flagged; vendor challenge pages and hard status codes
must be flagged with the right vendor so the escalation controller can climb
the ladder. Precision matters: prose mentioning "captcha" is not a block.
"""

from scout.core.blocking import BlockSignal, detect_block


def test_clean_page_is_not_blocked() -> None:
    sig = detect_block(
        status_code=200,
        title="Roswell GA Townhomes For Rent",
        html="<html><body><h1>86 homes</h1></body></html>",
    )
    assert isinstance(sig, BlockSignal)
    assert sig.blocked is False
    assert sig.vendor == "none"


def test_hard_status_codes_are_blocked_generic() -> None:
    for code in (403, 429, 503):
        sig = detect_block(status_code=code, title="", html="<html></html>")
        assert sig.blocked is True, code
        assert sig.matched == f"status:{code}"


def test_cloudflare_interstitial_detected() -> None:
    sig = detect_block(
        status_code=403,
        title="Just a moment...",
        html='<div class="cf-browser-verification">challenge-platform</div>',
    )
    assert sig.blocked is True
    assert sig.vendor == "cloudflare"


def test_datadome_detected() -> None:
    sig = detect_block(
        status_code=200,
        title="",
        html='<script src="https://geo.captcha-delivery.com/captcha/"></script>',
    )
    assert sig.blocked is True
    assert sig.vendor == "datadome"


def test_perimeterx_press_and_hold_detected() -> None:
    sig = detect_block(
        status_code=200,
        title="Access to this page has been denied",
        html="<p>Press &amp; Hold to confirm you are a human</p>",
    )
    assert sig.blocked is True
    assert sig.vendor == "perimeterx"


def test_akamai_access_denied_detected() -> None:
    sig = detect_block(
        status_code=403,
        title="Access Denied",
        html="<p>You don't have permission. Reference #18.abcd1234</p>",
    )
    assert sig.blocked is True
    assert sig.vendor == "akamai"


def test_imperva_incapsula_detected() -> None:
    sig = detect_block(
        status_code=200,
        title="",
        html="<p>Request unsuccessful. Powered and protected by Incapsula</p>",
    )
    assert sig.blocked is True
    assert sig.vendor == "imperva"


def test_prose_mentioning_captcha_is_not_a_block() -> None:
    """Precision guard: a 200 article that merely discusses CAPTCHAs is fine."""
    sig = detect_block(
        status_code=200,
        title="How CAPTCHA systems work",
        html="<article>A captcha is a challenge-response test used in computing.</article>",
    )
    assert sig.blocked is False


def test_unusual_traffic_phrase_detected() -> None:
    sig = detect_block(
        status_code=429,
        title="",
        html="<p>Our systems have detected unusual traffic from your network.</p>",
    )
    assert sig.blocked is True


def test_shopify_checkout_interstitial_detected() -> None:
    """Patagonia live finding: a routing interstitial is not product content."""
    sig = detect_block(
        status_code=200,
        title="Hang Tight! Routing to checkout...",
        html="<main>Hang Tight! Routing to checkout...</main>",
    )
    assert sig.blocked is True
    assert sig.vendor == "generic"
    assert sig.matched == "routing to checkout"


def test_generic_error_page_detected_as_acquisition_block() -> None:
    """Home Depot live finding: generic error documents should not certify as content."""
    sig = detect_block(
        status_code=200,
        title="Error Page",
        html="<h1>Error Page</h1><p>We are sorry, an unexpected error occurred while loading this page.</p>",
    )
    assert sig.blocked is True
    assert sig.vendor == "generic"
    assert sig.matched == "error page"


# --- Regression: live finding 2026-06-17 (Zillow). Anti-bot SDK scripts stay
# loaded on the CLEARED page; their mere presence must NOT read as blocked. ---


def test_cleared_perimeterx_page_with_sdk_present_is_not_blocked() -> None:
    sig = detect_block(
        status_code=200,
        title="Estée Lauder Skincare | Shop Serum, Moisturizer & More",
        html='<script src="/_px/client/main.js"></script><h1>Serums</h1>' + "content " * 100,
    )
    assert sig.blocked is False


def test_cleared_datadome_page_with_sdk_present_is_not_blocked() -> None:
    sig = detect_block(
        status_code=200,
        title="Roswell GA Rentals",
        html="<script>window.DataDome={};</script><div>86 listings</div>" + "x" * 400,
    )
    assert sig.blocked is False


def test_cleared_akamai_cdn_reference_is_not_blocked() -> None:
    # "akamai" appears in CDN asset URLs on normal pages — not a block.
    sig = detect_block(
        status_code=200,
        title="Home",
        html='<img src="https://cdn.akamai.net/logo.png"><h1>Welcome</h1>' + "y" * 400,
    )
    assert sig.blocked is False
