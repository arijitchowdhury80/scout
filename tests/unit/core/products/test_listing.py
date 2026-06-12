"""Tests for listing-page product fallback extraction.

# Scenario list:
# - generic PLP product cards become typed listing cards
# - relative product and image URLs are normalized against the category URL
# - duplicate product card links are collapsed
# - unrelated navigation links are ignored
# - CTA/catalog links are ignored instead of becoming low-quality records
# - navigation promo product links are ignored unless they appear in product-card context
# - product cards with details on the enclosing tile are extracted from browser DOM
"""

from scout.core.products.listing import extract_listing_cards


def test_extract_listing_cards_from_generic_product_grid_returns_cards() -> None:
    html = """
    <html><body>
      <article class="product-grid__item">
        <a class="product-tile__link" href="/products/serum-123">
          <img alt="Advanced Night Repair Serum" src="/media/serum.jpg">
          <span class="product-name">Advanced Night Repair Serum</span>
          <span class="price">$82.00</span>
        </a>
      </article>
      <article class="product-grid__item">
        <a class="product-tile__link" href="https://shop.example.com/products/moisturizer">
          <img alt="DayWear Moisturizer" src="https://cdn.example.com/moisturizer.jpg">
          <span class="product-name">DayWear Moisturizer</span>
          <span class="price">$58</span>
        </a>
      </article>
      <a href="/customer-service">Customer Service</a>
    </body></html>
    """

    cards = extract_listing_cards(
        category_url="https://shop.example.com/skin-care",
        category_name="Skin Care",
        html=html,
        links=[],
        limit=10,
    )

    assert len(cards) == 2
    assert cards[0].url == "https://shop.example.com/products/serum-123"
    assert cards[0].name == "Advanced Night Repair Serum"
    assert cards[0].image == "https://shop.example.com/media/serum.jpg"
    assert cards[0].price == 82.0
    assert cards[0].currency == "USD"
    assert cards[0].category_name == "Skin Care"


def test_extract_listing_cards_deduplicates_product_urls() -> None:
    html = """
    <a class="product" href="/products/serum"><img alt="Serum" src="/serum.jpg"></a>
    <a class="product" href="/products/serum"><span>Serum duplicate</span></a>
    """

    cards = extract_listing_cards(
        category_url="https://shop.example.com/skin-care",
        category_name="Skin Care",
        html=html,
        links=[],
        limit=10,
    )

    assert len(cards) == 1
    assert cards[0].name == "Serum"


def test_extract_listing_cards_ignores_cta_catalog_links() -> None:
    html = """
    <a href="/products/19239/product-catalog/last-chance">Shop Now</a>
    <a href="/products/708/product-catalog/whats-new">WHAT'S NEW</a>
    """

    cards = extract_listing_cards(
        category_url="https://www.esteelauder.com/skin-care",
        category_name="Skin Care",
        html=html,
        links=[
            "https://www.esteelauder.com/products/19239/product-catalog/last-chance",
        ],
        limit=10,
    )

    assert cards == []


def test_extract_listing_cards_ignores_navigation_promo_product_links() -> None:
    html = """
    <nav class="global-nav">
      <div class="product-tile">
        <a href="/product/643/141224/try-it-free-new-double-wear-foundation">
          <img alt="Try New Double Wear For Free" src="/promo.jpg">
          Try New Double Wear For Free
        </a>
      </div>
    </nav>
    <div class="product-tile">
      <a href="/product/681/12345/advanced-night-repair-serum">
        <img alt="Advanced Night Repair Serum" src="/anr.jpg">
        Advanced Night Repair Serum
      </a>
    </div>
    """

    cards = extract_listing_cards(
        category_url="https://www.esteelauder.com/skin-care",
        category_name="Skin Care",
        html=html,
        links=[],
        limit=10,
    )

    assert len(cards) == 1
    assert cards[0].name == "Advanced Night Repair Serum"


def test_extract_listing_cards_uses_enclosing_product_tile_details() -> None:
    html = """
    <div class="product-grid">
      <div class="product-brief"
           data-product-name="Advanced Night Repair Serum"
           data-brand="Estée Lauder">
        <a class="product-brief__image"
           href="/product/681/141225/product-catalog/skincare/advanced-night-repair-serum">
          <picture>
            <source srcset="/media/anr-large.jpg 2x, /media/anr-small.jpg 1x">
            <img alt="" src="/media/anr.jpg">
          </picture>
        </a>
        <span class="product-brief__price">$85.00</span>
      </div>
      <article class="product-card" aria-label="Nike Dri-FIT Men's Fitness T-Shirt">
        <a href="/t/dri-fit-mens-fitness-t-shirt-abc123">
          <img src="https://static.nike.com/a/images/t-shirt.png" alt="">
        </a>
        <div>$35</div>
      </article>
    </div>
    """

    cards = extract_listing_cards(
        category_url="https://www.esteelauder.com/products/681/product-catalog/skin-care",
        category_name="Skin Care",
        html=html,
        links=[],
        limit=10,
    )

    assert len(cards) == 2
    assert cards[0].name == "Advanced Night Repair Serum"
    assert cards[0].brand == "Estée Lauder"
    assert cards[0].price == 85.0
    assert cards[0].image == "https://www.esteelauder.com/media/anr.jpg"
    assert cards[1].name == "Nike Dri-FIT Men's Fitness T-Shirt"
    assert cards[1].price == 35.0
