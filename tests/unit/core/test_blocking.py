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
