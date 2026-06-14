"""Block detection — the spine of Scout's acquisition escalation ladder.

A single, shared detector so every mode (scrape/crawl/map/products) can tell
whether a fetch was blocked and, if so, by which anti-bot vendor — which lets
the escalation controller climb the ladder (stealth → undetected → proxy →
embedded browser → human) instead of silently treating a challenge page as
content.

Design notes:
- Precision over recall on prose: a 200 page that merely *mentions* "captcha"
  is not a block. We match high-precision vendor signatures, not bare words.
- A vendor signature wins over (and refines) a hard status code.
- Hard status codes (403/429/503) are blocks even without a known signature.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

_HARD_STATUSES = {403, 429, 503}

# Vendor → list of high-precision signatures (lowercased substring or regex).
# Order matters: first vendor with a hit wins.
_VENDOR_SIGNATURES: list[tuple[str, tuple[str, ...]]] = [
    (
        "cloudflare",
        (
            "just a moment",
            "cf-browser-verification",
            "cf-challenge",
            "challenge-platform",
            "cf_chl_",
            "checking your browser before accessing",
            "ray id",
        ),
    ),
    (
        "datadome",
        (
            "geo.captcha-delivery.com",
            "captcha-delivery",
            "datadome",
        ),
    ),
    (
        "perimeterx",
        (
            "px-captcha",
            "_px",
            "perimeterx",
            "press & hold",
            "press and hold",
            "hold to confirm",
        ),
    ),
    (
        "akamai",
        (
            "errors.edgesuite.net",
            "akamai",
            "reference #",
        ),
    ),
    (
        "imperva",
        (
            "powered and protected by incapsula",
            "incapsula",
            "_incap_",
            "request unsuccessful",
        ),
    ),
    (
        "generic",
        (
            "are you a human",
            "verify you are human",
            "verify you are a human",
            "unusual traffic",
            "access denied",
            "automated access",
        ),
    ),
]

# Akamai's "access denied" + "reference #" combo is classic; "access denied"
# alone is generic. Resolve the overlap by giving akamai priority when its
# reference hash is present.
_AKAMAI_REFERENCE = re.compile(r"reference\s*#", re.IGNORECASE)


class BlockSignal(BaseModel):
    """Result of a block-detection check. Frozen contract across boundaries."""

    model_config = {"frozen": True}

    blocked: bool
    vendor: str = "none"
    reason: str = ""
    matched: str = ""


def detect_block(
    status_code: int | None = None,
    *,
    title: str = "",
    html: str = "",
    markdown: str = "",
) -> BlockSignal:
    """Classify whether a fetched response is an anti-bot block.

    A vendor signature (if found) wins and names the vendor. Otherwise a hard
    HTTP status (403/429/503) is a generic block. Otherwise: not blocked.
    """
    # Normalize common HTML entities so signatures match raw_html too
    # (e.g. "Press &amp; Hold" → "press & hold").
    haystack = f"{title}\n{html}\n{markdown}".lower()
    haystack = haystack.replace("&amp;", "&").replace("&#39;", "'").replace("&nbsp;", " ")

    for vendor, signatures in _VENDOR_SIGNATURES:
        for sig in signatures:
            if sig in haystack:
                # Disambiguate the shared "access denied"/"reference #" space:
                # if an Akamai reference hash is present, attribute to akamai.
                if vendor == "generic" and _AKAMAI_REFERENCE.search(haystack):
                    return BlockSignal(
                        blocked=True,
                        vendor="akamai",
                        reason="akamai reference hash",
                        matched="reference #",
                    )
                return BlockSignal(
                    blocked=True,
                    vendor=vendor,
                    reason=f"{vendor} signature",
                    matched=sig,
                )

    if status_code in _HARD_STATUSES:
        return BlockSignal(
            blocked=True,
            vendor="generic",
            reason=f"hard status {status_code}",
            matched=f"status:{status_code}",
        )

    return BlockSignal(blocked=False, vendor="none")
