"""Build Algolia-ready product records."""

from __future__ import annotations

import hashlib

from scout.core.products.jsonld import ProductJsonLd
from scout.core.types import AlgoliaProductRecord, ProductListingCard, ProductSource


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
        brand=product.brand if product else "",
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
        brand=card.brand,
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
    record.completeness_score = _completeness_score(record)
    return record


def _object_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]


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
