# Product Catalog Example

```bash
scout products "top products" \
  --site esteelauder.com \
  --limit-per-category 10 \
  --max-categories 10 \
  --output-dir ./scout-runs/estee-lauder
```

Inspect:

```bash
jq '.[0]' ./scout-runs/estee-lauder/algolia/products.json
head ./scout-runs/estee-lauder/algolia/products.ndjson
cat ./scout-runs/estee-lauder/report.md
```
