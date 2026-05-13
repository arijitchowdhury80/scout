"""Build Algolia-ready product records."""

from __future__ import annotations

import hashlib

from scout.core.products.jsonld import ProductJsonLd
from scout.core.types import AlgoliaProductRecord, ProductSource


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

    return AlgoliaProductRecord(
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


def _object_id(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
