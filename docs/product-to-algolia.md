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
  "_source": {
    "url": "https://example.com/products/oxford-shirt",
    "extractor": "jsonld",
    "category_url": "https://example.com/collections/men-shirts",
    "category_name": "Men Shirts"
  }
}
```

## Current Extraction Strategy

Scout v1 uses mapped URLs plus product JSON-LD when available. If a product page
does not expose JSON-LD, Scout falls back to page metadata so the record remains
indexable and traceable.

Future improvements can add site-specific CSS schemas and LLM-assisted fallback
for pages that hide product data in custom JavaScript state.

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

Estee Lauder category pages expose product-catalog links, but product detail
requests currently return Akamai "Access Denied" content in local live tests.
Scout detects and skips those blocked pages so they do not become Algolia
records. Keep this as a known anti-bot hardening target:

```bash
scout products "skin care" \
  --start-url https://www.esteelauder.com/skin-care \
  --limit-per-category 1 \
  --max-products 1 \
  --output-dir ./scout-runs/estee-lauder-skin-care \
  --js \
  --stealth
```

Run opt-in live tests:

```bash
SCOUT_RUN_LIVE_PRODUCT_TESTS=1 python3 -m pytest tests/integration/test_product_sites_live.py -v -m integration
```
