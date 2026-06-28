"""Build Algolia-ready product records."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

from scout.core.platform.types import FetchProviderKind, stable_source_id
from scout.core.products.jsonld import ProductJsonLd
from scout.core.types import AlgoliaProductRecord, ProductListingCard, ProductSource

_JUNK_PATTERNS = re.compile(
    r"(?i)^("
    r"hang\s+tight|verify\s+your\s+age|access\s+denied|just\s+a\s+moment|"
    r"please\s+wait|checking\s+your\s+browser|one\s+moment|"
    r"are\s+you\s+a\s+human|captcha|robot\s+check|"
    r"your\s+cart|checkout|shopping\s+bag|order\s+summary|"
    r"page\s+not\s+found|404|error\s+\d{3}"
    r")$"
)

_VARIANT_PARAMS = {"variant", "v", "color", "size", "option", "sku", "id"}


def build_algolia_record(
    url: str,
    title: str,
    category_name: str,
    category_url: str,
    product: ProductJsonLd | None,
) -> AlgoliaProductRecord:
    """Create a stable Algolia product record from extracted page data."""
    name = product.name if product and product.name else title or url.rsplit("/", 1)[-1]
    images = product.images if product else []
    categories = [category_name] if category_name else []
    hierarchical = {"lvl0": category_name} if category_name else {}

    record = AlgoliaProductRecord(
        objectID=_object_id(url),
        name=name,
        url=url,
        brand=brand_fallback(product.brand if product else "", url),
        description=product.description if product else "",
        image=images[0] if images else "",
        images=images,
        price=product.price if product else None,
        currency=product.currency if product else "",
        categories=categories,
        hierarchicalCategories=hierarchical,
        sku=product.sku if product else "",
        in_stock=product.in_stock if product else None,
        source=ProductSource(
            url=url,
            extractor="jsonld" if product else "metadata",
            category_url=category_url,
            category_name=category_name,
        ),
    )
    record.citations = [_product_citation(record.source, field="name", claim=record.name)]
    record.completeness_score = _completeness_score(record)
    return record


def build_listing_algolia_record(card: ProductListingCard) -> AlgoliaProductRecord:
    """Create a partial Algolia product record from category/listing card data."""
    categories = [card.category_name] if card.category_name else []
    hierarchical = {"lvl0": card.category_name} if card.category_name else {}
    images = [card.image] if card.image else []
    record = AlgoliaProductRecord(
        objectID=_object_id(card.url),
        name=card.name or card.url.rsplit("/", 1)[-1],
        url=card.url,
        brand=brand_fallback(card.brand, card.url),
        image=card.image,
        images=images,
        price=card.price,
        currency=card.currency,
        categories=categories,
        hierarchicalCategories=hierarchical,
        source=ProductSource(
            url=card.url,
            extractor="listing",
            category_url=card.category_url,
            category_name=card.category_name,
        ),
    )
    record.citations = [_product_citation(record.source, field="name", claim=record.name)]
    record.completeness_score = _completeness_score(record)
    return record


def is_junk_record(name: str) -> bool:
    return bool(_JUNK_PATTERNS.match(name.strip()))


def canonical_url(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {k: v for k, v in params.items() if k.lower() not in _VARIANT_PARAMS}
    clean_query = urlencode(filtered, doseq=True) if filtered else ""
    return urlunparse(parsed._replace(query=clean_query, fragment=""))


def brand_fallback(brand: str, url: str) -> str:
    if brand:
        return brand
    hostname = urlparse(url).hostname or ""
    domain = hostname.removeprefix("www.")
    parts = domain.split(".")
    return parts[0].capitalize() if parts and parts[0] else ""


def _object_id(url: str) -> str:
    return hashlib.sha256(canonical_url(url).encode("utf-8")).hexdigest()[:24]


def _product_citation(source: ProductSource, *, field: str, claim: str) -> dict[str, object]:
    source_url = source.category_url or source.url
    provider = source.extractor or FetchProviderKind.CRAWL4AI.value
    return {
        "source_id": stable_source_id(provider, source_url, source_url),
        "source_url": source_url,
        "field": field,
        "claim": claim,
        "snippet": claim[:240],
        "selector": "",
        "confidence": 0.75 if source.extractor == "listing" else 0.85,
    }


def _completeness_score(record: AlgoliaProductRecord) -> float:
    checks = [
        bool(record.name),
        bool(record.url),
        bool(record.image),
        record.price is not None,
        bool(record.brand),
        bool(record.description),
        bool(record.categories),
        bool(record.sku),
    ]
    return round(sum(1 for item in checks if item) / len(checks), 2)
