"""Product URL discovery and categorisation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse


_PRODUCT_MARKERS = ("/products/", "/product/", "/p/")
_CATEGORY_MARKERS = ("/collections/", "/category/", "/categories/", "/c/")


@dataclass(frozen=True)
class ProductUrlGroups:
    category_url: str
    category_name: str
    product_urls: list[str]


def normalize_start_url(site: str, start_url: str) -> str:
    """Return a crawlable HTTPS URL from either explicit start_url or site."""
    value = start_url.strip() or site.strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value.rstrip("/")
    return f"https://{value.rstrip('/')}"


def group_product_urls(
    urls: list[str],
    max_categories: int,
    limit_per_category: int,
) -> list[ProductUrlGroups]:
    """Group product URLs under likely category URLs from a mapped URL list."""
    categories = [_normalise_url(u) for u in urls if _is_category_url(u)]
    products = [_normalise_url(u) for u in urls if _is_product_url(u)]
    grouped: list[ProductUrlGroups] = []
    used: set[str] = set()

    for category_url in categories:
        category_products = [
            url for url in products if url.startswith(f"{category_url}/") and url not in used
        ]
        product_urls = category_products[:limit_per_category]
        if not product_urls:
            continue
        used.update(category_products)
        grouped.append(
            ProductUrlGroups(
                category_url=category_url,
                category_name=_category_name_from_url(category_url),
                product_urls=product_urls,
            )
        )
        if len(grouped) >= max_categories:
            return grouped

    remaining = [url for url in products if url not in used]
    while remaining and len(grouped) < max_categories:
        first = remaining[0]
        category_url = _category_url_from_product(first)
        product_urls = [url for url in remaining if url.startswith(f"{category_url}/")][
            :limit_per_category
        ]
        for url in product_urls:
            remaining.remove(url)
        grouped.append(
            ProductUrlGroups(
                category_url=category_url,
                category_name=_category_name_from_url(category_url),
                product_urls=product_urls,
            )
        )

    return grouped


def _normalise_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))


def _is_product_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(marker in path for marker in _PRODUCT_MARKERS)


def _is_category_url(url: str) -> bool:
    path = urlparse(url).path.lower().rstrip("/")
    return any(marker in f"{path}/" for marker in _CATEGORY_MARKERS) and not _is_product_url(url)


def _category_url_from_product(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    for marker in ("products", "product", "p"):
        if marker in parts:
            index = parts.index(marker)
            path = "/" + "/".join(parts[:index]) if index else f"/{marker}"
            return urlunparse((parsed.scheme, parsed.netloc, path.rstrip("/"), "", "", ""))
    return urlunparse((parsed.scheme, parsed.netloc, "/products", "", "", ""))


def _category_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if not parts:
        return "Products"
    slug = parts[-1]
    if slug in {"products", "product", "p"}:
        return "Products"
    return slug.replace("-", " ").replace("_", " ").title()
