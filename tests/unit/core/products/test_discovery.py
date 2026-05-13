"""Tests for product URL discovery heuristics."""

from scout.core.products.discovery import ProductUrlGroups, group_product_urls, normalize_start_url


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
