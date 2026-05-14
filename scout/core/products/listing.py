"""Extract product-card data from category/listing pages."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from scout.core.products.discovery import is_product_url
from scout.core.types import ProductListingCard

_CTA_NAMES = {"shop now", "what's new", "whats new", "last chance", "learn more", "view all"}
_PRODUCT_CONTEXT_MARKERS = ("product", "tile", "grid", "card", "item")
_NAV_CONTEXT_MARKERS = ("nav", "gnav", "menu", "header", "footer")
_VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source"}


@dataclass
class _AnchorCandidate:
    url: str
    text_parts: list[str] = field(default_factory=list)
    image: str = ""


class _ListingParser(HTMLParser):
    def __init__(self, category_url: str) -> None:
        super().__init__()
        self.category_url = category_url
        self.candidates: list[_AnchorCandidate] = []
        self._current: _AnchorCandidate | None = None
        self._context_stack: list[bool] = []
        self._nav_stack: list[bool] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}
        context = _has_product_context(attr_map)
        nav_context = tag.lower() in {"nav", "header", "footer"} or _has_nav_context(attr_map)
        if tag.lower() not in _VOID_TAGS:
            self._context_stack.append(context)
            self._nav_stack.append(nav_context)
        if tag.lower() == "a":
            self._start_anchor(attr_map.get("href", ""), context)
        if tag.lower() == "img" and self._current:
            self._capture_image(attr_map)

    def handle_data(self, data: str) -> None:
        if self._current and data.strip():
            self._current.text_parts.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._current:
            self.candidates.append(self._current)
            self._current = None
        if tag.lower() not in _VOID_TAGS and self._context_stack:
            self._context_stack.pop()
        if tag.lower() not in _VOID_TAGS and self._nav_stack:
            self._nav_stack.pop()

    def _start_anchor(self, href: str, has_anchor_context: bool) -> None:
        url = _absolute_url(self.category_url, href)
        if (
            url
            and is_product_url(url)
            and not any(self._nav_stack)
            and (has_anchor_context or any(self._context_stack))
        ):
            self._current = _AnchorCandidate(url=url)

    def _capture_image(self, attr_map: dict[str, str]) -> None:
        current = self._current
        if current is None:
            return
        image = attr_map.get("src") or attr_map.get("data-src") or attr_map.get("data-original")
        if image:
            current.image = _absolute_url(self.category_url, image)
        alt = attr_map.get("alt", "").strip()
        if alt:
            current.text_parts.append(alt)


def extract_listing_cards(
    category_url: str,
    category_name: str,
    html: str,
    links: list[str],
    limit: int,
) -> list[ProductListingCard]:
    """Return typed product cards found on a category/listing page."""
    parser = _ListingParser(category_url)
    parser.feed(html or "")
    candidates = [*parser.candidates, *_candidates_from_links(category_url, links)]
    cards: list[ProductListingCard] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate.url in seen:
            continue
        card = _to_card(candidate, category_url, category_name)
        if not _is_usable_card(card):
            continue
        cards.append(card)
        seen.add(card.url)
        if len(cards) >= limit:
            break
    return cards


def _candidates_from_links(category_url: str, links: list[str]) -> list[_AnchorCandidate]:
    candidates: list[_AnchorCandidate] = []
    for link in links:
        url = _absolute_url(category_url, link)
        if is_product_url(url):
            candidates.append(_AnchorCandidate(url=url, text_parts=[_name_from_url(url)]))
    return candidates


def _to_card(
    candidate: _AnchorCandidate,
    category_url: str,
    category_name: str,
) -> ProductListingCard:
    text = " ".join(_unique_text_parts(candidate.text_parts))
    price = _extract_price(text)
    name = _clean_name(text)
    if not name:
        name = _name_from_url(candidate.url)
    return ProductListingCard(
        url=candidate.url,
        name=name,
        image=candidate.image,
        price=price,
        currency="USD" if price is not None else "",
        category_url=category_url,
        category_name=category_name,
    )


def _absolute_url(base_url: str, value: str) -> str:
    if not value:
        return ""
    return urljoin(base_url, value).split("#", 1)[0]


def _extract_price(value: str) -> float | None:
    match = re.search(r"\$\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", value)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def _clean_name(value: str) -> str:
    text = re.sub(r"\$\s*[0-9][0-9,]*(?:\.[0-9]{1,2})?", " ", value)
    text = re.sub(r"\s+", " ", text).strip(" -|")
    return text


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _is_usable_card(card: ProductListingCard) -> bool:
    name = card.name.strip().lower()
    if not name or name in _CTA_NAMES:
        return False
    return bool(card.image or card.price is not None)


def _has_product_context(attr_map: dict[str, str]) -> bool:
    text = f"{attr_map.get('class', '')} {attr_map.get('id', '')}".lower()
    return any(marker in text for marker in _PRODUCT_CONTEXT_MARKERS)


def _has_nav_context(attr_map: dict[str, str]) -> bool:
    text = f"{attr_map.get('class', '')} {attr_map.get('id', '')}".lower()
    return any(marker in text for marker in _NAV_CONTEXT_MARKERS)


def _unique_text_parts(values: list[str]) -> list[str]:
    parts: list[str] = []
    for value in values:
        text = _clean_text(value)
        if text and text not in parts:
            parts.append(text)
    return parts


def _name_from_url(url: str) -> str:
    slug = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    return slug.replace("-", " ").replace("_", " ").title()
