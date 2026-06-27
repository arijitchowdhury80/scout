"""Product URL discovery and categorisation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse, urlunparse

from scout.core.types import ProductListingCard


_PRODUCT_MARKERS = ("/products/", "/product/", "/p/", "/t/")
_CATEGORY_MARKERS = ("/collections/", "/category/", "/categories/", "/c/")
_UTILITY_SEGMENTS = {
    "account",
    "blog",
    "cart",
    "checkout",
    "contact-us",
    "customer-service",
    "privacy",
    "returns",
    "review",
    "search",
    "signin",
    "terms-conditions",
}


@dataclass(frozen=True)
class ProductUrlGroups:
    category_url: str
    category_name: str
    product_urls: list[str]
    listing_cards: list[ProductListingCard] = field(default_factory=list)


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


def select_category_urls(urls: list[str], query: str, limit: int) -> list[str]:
    """Return likely category URLs for second-stage product link discovery."""
    query_tokens = [token for token in _slug_words(query) if len(token) > 2]
    candidates = [_normalise_url(url) for url in urls if _is_category_candidate(url)]

    def score(url: str) -> tuple[int, int]:
        path_words = set(_slug_words(urlparse(url).path))
        matches = sum(1 for token in query_tokens if token in path_words)
        return (matches, -len(urlparse(url).path))

    ranked = sorted(dict.fromkeys(candidates), key=score, reverse=True)
    return ranked[:limit]


def extract_product_links(category_url: str, links: list[str], limit: int) -> list[str]:
    """Extract product-looking links from a category page link list."""
    category = _normalise_url(category_url)
    category_domain = urlparse(category).netloc
    result: list[str] = []
    seen: set[str] = set()
    for link in links:
        normalised = _normalise_url_preserve_query(link)
        if normalised in seen or urlparse(normalised).netloc != category_domain:
            continue
        if _is_product_url(normalised) and (
            normalised.startswith(category)
            or any(marker in urlparse(normalised).path for marker in _PRODUCT_MARKERS)
        ):
            result.append(normalised)
            seen.add(normalised)
        if len(result) >= limit:
            break
    return result


def is_product_url(url: str) -> bool:
    """Return whether a URL looks like a product detail URL."""
    return _is_product_url(url)


def _normalise_url(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))


def _normalise_url_preserve_query(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", parsed.query, ""))


def _is_product_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    if "/products/" in path and "/product-catalog/" in path:
        return False
    if any(marker in path for marker in _PRODUCT_MARKERS):
        return True
    if any(marker in f"{path}/" for marker in _CATEGORY_MARKERS):
        return False
    filename = path.rsplit("/", 1)[-1]
    return filename.endswith(".html")


def _is_category_url(url: str) -> bool:
    path = urlparse(url).path.lower().rstrip("/")
    return any(marker in f"{path}/" for marker in _CATEGORY_MARKERS) and not _is_product_url(url)


def _is_category_candidate(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower().strip("/")
    parts = [part for part in path.split("/") if part]
    if not parts or _is_product_url(url):
        return False
    if any(part in _UTILITY_SEGMENTS for part in parts):
        return False
    if any(part.startswith(("blog-", "customer_")) for part in parts):
        return False
    return 1 <= len(parts) <= 6


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


def _slug_words(value: str) -> list[str]:
    text = value.lower().replace("-", " ").replace("_", " ").replace("/", " ")
    return [part for part in text.split() if part]
