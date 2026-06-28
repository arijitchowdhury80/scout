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


def test_extract_listing_cards_handles_estee_lauder_liveview_product_markup() -> None:
    html = """
    <li class="block md:inline-block relative md:max-w-[232px]"
        data-product_id="77491"
        data-action="click->search#handleOverlayProductClick">
      <div class="h-full">
        <a class="group"
           href="/product/689/77491/product-catalog/skincare/repair-serum/advanced-night-repair-serum/synchronized-multi-recovery-complex"
           rel="prefetch">
          <img src="https://www.esteelauder.com/media/export/cms/products/640x640/el_prod_77491_640x640_0.jpg"
               alt="Advanced Night Repair Serum">
          <h3 class="product-name">Advanced Night Repair Serum</h3>
          <p>Synchronized Multi-Recovery Complex</p>
          <div class="font-bold">$85.00</div>
        </a>
      </div>
    </li>
    """

    cards = extract_listing_cards(
        category_url="https://www.esteelauder.com/products/681/product-catalog/skin-care",
        category_name="Skin Care",
        html=html,
        links=[],
        limit=10,
    )

    assert len(cards) == 1
    assert cards[0].name == "Advanced Night Repair Serum Synchronized Multi-Recovery Complex"
    assert cards[0].price == 85.0
    assert cards[0].image.endswith("el_prod_77491_640x640_0.jpg")


def test_extract_listing_cards_handles_llbean_shop_product_urls() -> None:
    html = """
    <li class="ProductThumbnail_container">
      <div class="ProductThumbnail_product" data-default-sku="1000316714">
        <a href="/llb/shop/20010264?page=mens-ll-bean-baseball-cap-unisex&bc=12-26-596-502857-502859&feat=502859-GN3&csp=a&attrValue_0=58110&pos=1">
          <img alt="Adults' L.L.Bean Motif Baseball Cap, New"
               src="https://cdni.llbean.net/is/image/wim/527518_58110_41?wid=302">
        </a>
      </div>
      <a class="ProductThumbnail_name"
         href="/llb/shop/20010264?page=mens-ll-bean-baseball-cap-unisex&bc=12-26-596-502857-502859&feat=502859-GN3&csp=a&attrValue_0=58110&pos=1">
        Adults' L.L.Bean Motif Baseball Cap
      </a>
      <div class="ProductThumbnail_price">
        <span class="screenreader">Price: $29.95</span>
        <span aria-hidden="true">$29.95</span>
      </div>
    </li>
    """

    cards = extract_listing_cards(
        category_url="https://www.llbean.com/llb/shop/502859",
        category_name="Baseball Caps & Visors",
        html=html,
        links=[],
        limit=10,
    )

    assert len(cards) == 1
    assert cards[0].url.startswith("https://www.llbean.com/llb/shop/20010264")
    assert cards[0].name == "Adults' L.L.Bean Motif Baseball Cap"
    assert cards[0].price == 29.95
    assert cards[0].image.startswith("https://cdni.llbean.net/is/image/wim/527518_58110_41")


def test_extract_listing_cards_cleans_llbean_live_product_noise() -> None:
    html = """
    <li class="ProductThumbnail_container">
      <a href="/llb/shop/20010264?page=mens-ll-bean-baseball-cap-unisex&bc=12-26-596-502857-502859&feat=502859-GN3&csp=a&attrValue_0=58110&pos=1">
        <img alt="Adults' L.L.Bean Motif Baseball Cap, New"
             src="https://cdni.llbean.net/is/image/wim/527518_58110_41?wid=302">
      </a>
      <a class="ProductThumbnail_name"
         href="/llb/shop/20010264?page=mens-ll-bean-baseball-cap-unisex&bc=12-26-596-502857-502859&feat=502859-GN3&csp=a&attrValue_0=58110&pos=1">
        Adults' L.L.Bean Motif Baseball Cap
      </a>
      <div class="ProductThumbnail_price"><span>Price: $29.95</span></div>
      <div class="ProductThumbnail_color-count">5 colors available</div>
      <a class="Rating_count"
         href="/llb/shop/20010264?page=mens-ll-bean-baseball-cap-unisex&bc=12-26-596-502857-502859&feat=502859-GN3&csp=a&attrValue_0=58110&pos=1&showReviews=true">
        This product has 16 reviews
      </a>
    </li>
    """

    cards = extract_listing_cards(
        category_url="https://www.llbean.com/llb/shop/502859",
        category_name="Baseball Caps & Visors",
        html=html,
        links=[],
        limit=10,
    )

    assert len(cards) == 1
    assert cards[0].name == "Adults' L.L.Bean Motif Baseball Cap"
    assert "showReviews" not in cards[0].url


def test_extract_listing_cards_reads_json_ld_product_graph() -> None:
    html = """
    <html><body>
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@graph": [{
          "@type": "ItemList",
          "itemListElement": [
            {
              "@type": "Product",
              "productID": "320326855",
              "name": "Milwaukee M18 FUEL 18V Lithium-Ion Brushless Cordless Hammer Drill",
              "brand": {"@type": "Thing", "name": "Milwaukee"},
              "image": "https://images.thdstatic.com/productImages/drill.jpg",
              "offers": {
                "@type": "Offer",
                "url": "https://www.homedepot.com/p/Milwaukee-M18-FUEL-Hammer-Drill-Driver-Tool-Only-2904-20/320326855",
                "priceCurrency": "USD",
                "price": 229
              }
            }
          ]
        }]
      }
      </script>
    </body></html>
    """

    cards = extract_listing_cards(
        category_url="https://www.homedepot.com/b/Tools-Power-Tools-Drills/Cordless/N-5yc1vZc27fZ1z140i3",
        category_name="Cordless Drills",
        html=html,
        links=[],
        limit=10,
    )

    assert len(cards) == 1
    assert cards[0].url == (
        "https://www.homedepot.com/p/"
        "Milwaukee-M18-FUEL-Hammer-Drill-Driver-Tool-Only-2904-20/320326855"
    )
    assert cards[0].name == "Milwaukee M18 FUEL 18V Lithium-Ion Brushless Cordless Hammer Drill"
    assert cards[0].brand == "Milwaukee"
    assert cards[0].price == 229.0
    assert cards[0].image == "https://images.thdstatic.com/productImages/drill.jpg"


def test_extract_listing_cards_handles_patagonia_custom_product_tile_markup() -> None:
    html = """
    <product-tile class="product-tile badges-ready" data-pid="41915">
      <a href="/product/mens-go-to-western-shirt/41915.html?dwvar_41915_color=LLNA"
         itemprop="url"
         title="M's Go-To Western Shirt - Lowlands: Natural (LLNA) (41915)">
        <product-tile-image
          alt="M's Go-To Western Shirt - Lowlands: Natural (LLNA) (41915)"
          base="https://www.patagonia.com/dw/image/v2/BDJB_PRD/41915_LLNA.jpg?sw=256">
        </product-tile-image>
      </a>
      <button class="product-tile__colors"
              data-sale-price="95.0"
              data-sale-price-formatted="$95"
              data-gtm-swatch='[{"ecommerce":{"items":[{"item_name":"M&apos;s Go-To Western Shirt","item_brand":"Patagonia","price":95}]}}]'>
      </button>
      <p class="product-tile__name">M's Go-To Western Shirt</p>
      <span class="product-tile__price">$95</span>
    </product-tile>
    """

    cards = extract_listing_cards(
        category_url="https://www.patagonia.com/shop/mens/tops",
        category_name="Men's Tops",
        html=html,
        links=[],
        limit=10,
    )

    assert len(cards) == 1
    assert cards[0].name == "M's Go-To Western Shirt"
    assert cards[0].brand == "Patagonia"
    assert cards[0].price == 95.0
    assert cards[0].image.startswith("https://www.patagonia.com/dw/image")
