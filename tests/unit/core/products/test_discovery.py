"""Tests for product URL discovery heuristics."""

# Scenario list:
# - bare domains normalize to HTTPS start URLs
# - mapped product URLs are grouped under categories with per-category limits
# - product-only URL lists still produce a usable Products bucket
# - Lacoste-style .html product links are detected from category page links
# - Estee Lauder-style /product-catalog/ links are treated as categories, not products
# - obvious utility pages are excluded from category candidates

from scout.core.products.discovery import (
    ProductUrlGroups,
    extract_product_links,
    group_product_urls,
    normalize_start_url,
    select_category_urls,
)


def test_normalize_start_url_accepts_bare_domain() -> None:
    result = normalize_start_url(site="esteelauder.com", start_url="")

    assert result == "https://esteelauder.com"


def test_group_product_urls_limits_products_per_category() -> None:
    urls = [
        "https://shop.example.com/collections/men-shirts",
        "https://shop.example.com/collections/men-shirts/products/oxford-blue",
        "https://shop.example.com/collections/men-shirts/products/linen-white",
        "https://shop.example.com/collections/women/products/dress",
        "https://shop.example.com/about",
    ]

    groups = group_product_urls(urls, max_categories=2, limit_per_category=1)

    assert groups == [
        ProductUrlGroups(
            category_url="https://shop.example.com/collections/men-shirts",
            category_name="Men Shirts",
            product_urls=["https://shop.example.com/collections/men-shirts/products/oxford-blue"],
        ),
        ProductUrlGroups(
            category_url="https://shop.example.com/collections/women",
            category_name="Women",
            product_urls=["https://shop.example.com/collections/women/products/dress"],
        ),
    ]


def test_group_product_urls_uses_uncategorized_bucket_when_only_products_exist() -> None:
    groups = group_product_urls(
        ["https://shop.example.com/products/serum"],
        max_categories=5,
        limit_per_category=10,
    )

    assert groups[0].category_name == "Products"
    assert groups[0].product_urls == ["https://shop.example.com/products/serum"]


def test_extract_product_links_finds_lacoste_html_products() -> None:
    links = [
        "https://www.lacoste.com/us/lacoste/men/clothing/polos",
        "https://www.lacoste.com/us/lacoste/men/clothing/polos/L1212-51.html?color=001",
        "https://www.lacoste.com/us/lacoste/men/clothing/polos/L1212-51.html?color=031",
    ]

    products = extract_product_links(
        "https://www.lacoste.com/us/lacoste/men/clothing/polos",
        links,
        limit=10,
    )

    assert products == [
        "https://www.lacoste.com/us/lacoste/men/clothing/polos/L1212-51.html?color=001",
        "https://www.lacoste.com/us/lacoste/men/clothing/polos/L1212-51.html?color=031",
    ]


def test_extract_product_links_rejects_product_catalog_category_links() -> None:
    products = extract_product_links(
        "https://www.esteelauder.com/skin-care",
        [
            "https://www.esteelauder.com/products/681/1799/product-catalog/skincare",
            "https://www.esteelauder.com/products/serum",
            "https://www.youtube.com/esteelauder/products/fake",
        ],
        limit=10,
    )

    assert products == ["https://www.esteelauder.com/products/serum"]


def test_select_category_urls_filters_utility_pages() -> None:
    urls = [
        "https://shop.example.com/customer-service",
        "https://shop.example.com/lacoste/men/clothing/polos",
        "https://shop.example.com/products/sku",
    ]

    categories = select_category_urls(urls, query="men polos", limit=5)

    assert categories == ["https://shop.example.com/lacoste/men/clothing/polos"]
