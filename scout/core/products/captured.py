"""Product extraction from already-captured HTML/DOM."""

from __future__ import annotations

from scout.core.products.algolia import build_listing_algolia_record
from scout.core.products.listing import extract_listing_cards


def product_records_from_captured_html(
    *,
    html: str,
    source_url: str,
    category_name: str = "",
    links: list[str] | None = None,
    limit: int = 25,
) -> list[dict]:
    """Return Algolia-ready product records from held listing-page HTML."""
    cards = extract_listing_cards(
        category_url=source_url,
        category_name=category_name,
        html=html,
        links=links or [],
        limit=max(1, limit),
    )
    return [
        build_listing_algolia_record(card).model_dump(mode="json", by_alias=True) for card in cards
    ]


__all__ = ["product_records_from_captured_html"]
