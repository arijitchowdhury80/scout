# Product Catalogs to Algolia

Scout prepares product data for Algolia by crawling public product pages and
normalizing records into a predictable ecommerce schema.

## CLI Example

```bash
scout products "men shirts" \
  --site example.com \
  --limit-per-category 10 \
  --max-categories 5 \
  --output-dir ./scout-runs/example-men-shirts
```

## HTTP Example

```bash
curl -s -X POST http://localhost:8421/products \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key" \
  -d '{
    "query": "men shirts",
    "site": "example.com",
    "limit_per_category": 10,
    "max_categories": 5,
    "output_dir": "./scout-runs/example-men-shirts",
    "persist": true
  }'
```

## Output Folder

```text
scout-runs/<run-id>/
  manifest.json
  urls.json
  blocked_pages.json
  extracted/products.raw.jsonl
  algolia/products.json
  algolia/products.ndjson
  algolia/settings.json
  report.md
```

## Algolia Record Shape

```json
{
  "objectID": "stable-hash",
  "name": "Oxford Shirt",
  "url": "https://example.com/products/oxford-shirt",
  "brand": "Example",
  "description": "A blue oxford shirt.",
  "image": "https://example.com/image.jpg",
  "images": ["https://example.com/image.jpg"],
  "price": 79.5,
  "currency": "USD",
  "categories": ["Men Shirts"],
  "hierarchicalCategories": {
    "lvl0": "Men Shirts"
  },
  "sku": "OX-1",
  "variants": [],
  "in_stock": true,
  "completeness_score": 0.75,
  "_source": {
    "url": "https://example.com/products/oxford-shirt",
    "extractor": "jsonld",
    "category_url": "https://example.com/collections/men-shirts",
    "category_name": "Men Shirts"
  }
}
```

## Current Extraction Strategy

Scout uses a fallback ladder:

1. Discover likely category and product URLs.
2. Extract product-card data from category/listing pages.
3. Scrape product detail pages and prefer JSON-LD records when available.
4. If a product detail page is blocked, retry that URL through the browser fallback channel.
5. If browser fallback succeeds, mark the record source as `*_browser_fallback`.
6. If browser fallback is still blocked, keep any listing-page fallback record.
7. Write blocked detail pages and fallback outcomes to `blocked_pages.json`.

Records include `_source.extractor` so you can distinguish `jsonld`, `listing`,
and `metadata` records. They also include `completeness_score` so downstream
indexing or PDP demos can filter partial records when needed.

## Live Retailer Examples

Lacoste category pages expose product JSON-LD and are a good live smoke test:

```bash
scout products "men polos" \
  --start-url https://www.lacoste.com/us/lacoste/men/clothing/polos \
  --limit-per-category 2 \
  --max-products 2 \
  --output-dir ./scout-runs/lacoste-men-polos \
  --js
```

Estee Lauder is a hard-site example: category pages may be crawlable while
product detail pages return Akamai "Access Denied" content. Scout now reports
blocked PDP URLs and keeps listing-page fallback records when category cards
contain product data:

```bash
scout products "skin care" \
  --start-url https://www.esteelauder.com/skin-care \
  --limit-per-category 1 \
  --max-products 1 \
  --output-dir ./scout-runs/estee-lauder-skin-care \
  --js \
  --browser-fallback \
  --stealth
```

Browser fallback is not the default crawl path. Scout only opens the fallback
browser after the regular product-page scrape returns blocked content. Disable
the fallback when you want fully headless/non-interactive behavior:

```bash
scout products "skin care" \
  --start-url https://www.esteelauder.com/skin-care \
  --no-browser-fallback
```

Inspect these files after the run:

```text
./scout-runs/estee-lauder-skin-care/report.md
./scout-runs/estee-lauder-skin-care/blocked_pages.json
./scout-runs/estee-lauder-skin-care/algolia/products.json
```

Run opt-in live tests:

```bash
SCOUT_RUN_LIVE_PRODUCT_TESTS=1 python3 -m pytest tests/integration/test_product_sites_live.py -v -m integration
```
