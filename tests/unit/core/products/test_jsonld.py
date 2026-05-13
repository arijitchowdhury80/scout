"""Tests for product JSON-LD extraction."""

# Scenario list:
# - schema.org Product JSON-LD extracts name, brand, SKU, images, price, currency, stock
# - non-product JSON-LD returns None instead of false product data

from scout.core.products.jsonld import extract_product_jsonld


def test_extract_product_jsonld_reads_product_object() -> None:
    html = """
    <html><head>
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Advanced Night Repair Serum",
        "brand": {"@type": "Brand", "name": "Estee Lauder"},
        "sku": "ANR-50ML",
        "description": "A serum for smoother-looking skin.",
        "image": ["https://example.com/serum.jpg"],
        "offers": {"@type": "Offer", "price": "85.00", "priceCurrency": "USD", "availability": "https://schema.org/InStock"}
      }
      </script>
    </head></html>
    """

    product = extract_product_jsonld(html)

    assert product is not None
    assert product.name == "Advanced Night Repair Serum"
    assert product.brand == "Estee Lauder"
    assert product.price == 85.0
    assert product.currency == "USD"
    assert product.in_stock is True
    assert product.images == ["https://example.com/serum.jpg"]


def test_extract_product_jsonld_returns_none_when_no_product_schema() -> None:
    html = '<script type="application/ld+json">{"@type": "BreadcrumbList"}</script>'

    assert extract_product_jsonld(html) is None
