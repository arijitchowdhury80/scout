# Estee Lauder WebFetch Product Dry Run

Date: 2026-05-14

## Test Query

"Find me the top categories for Estee Lauder and get me 10 products each with all attributes, price, color, review, everything. Then get me top 10 best sellers as well."

## Processing Plan

1. Interpret "top categories" as major Estee Lauder commerce categories.
2. Resolve category seed URLs.
3. Fetch category pages through hosted WebFetch/WebSearch-style retrieval.
4. Extract listing product cards.
5. Fetch PDPs only when richer attributes are needed.
6. Normalize into Scout product records.

## Category Seeds

| User intent | URL | Result |
|---|---|---|
| Best sellers | `https://www.esteelauder.com/products/1799/product-catalog/bestsellers` | Fetched; 76 products visible. |
| Skincare | `https://www.esteelauder.com/products/681/product-catalog/skin-care` | Fetched; product listing visible. |
| Makeup | `https://www.esteelauder.com/products/631/product-catalog/makeup` | Fetched; 72 products visible. |
| Fragrance | `https://www.esteelauder.com/products/571/product-catalog/fragrance` | Fetched; 73 products visible. |
| Sets & Gifts | `https://www.esteelauder.com/products/19045/product-catalog/sets-gifts` | Fetched; 120 products visible. |

## Listing Data Available

Category pages expose enough structured text to create first-pass records:

- Product name
- PDP URL/link identifier
- Short description
- Review count
- Rating when the hosted result includes it
- List price
- Sale price/current marked price
- Size count or shade count
- Example selected shade/size in some cards
- Badge/promo labels such as `20% OFF`, `Best Seller`, `New`, `Limited Edition`, `Refill Available`

## Best Sellers Sample

| Rank | Product | Reviews | Price | Sale/current | Listing attributes |
|---:|---|---:|---:|---:|---|
| 1 | Advanced Night Repair Serum Synchronized Multi-Recovery Complex | 21145 | $130.00 | $104.00 | 5 sizes; sample sizes include 1.7 oz, 1.0 oz, 3.9 oz, 0.67 oz, 0.23 oz Travel Size |
| 2 | Double Wear Stay-in-Place Longwear Matte Foundation | 9209 | $52.00 | — | 70 shades; sample shade 3N1 Ivory Beige |
| 3 | Revitalizing Supreme+ Moisturizer Youth Power Creme | 5182 | $140.00 | $112.00 | 1 size shown in fetched listing |
| 4 | Advanced Night Repair Serum Duo Synchronized Multi-Recovery Complex | 21145 | $230.00 | $184.00 | 1 size; 0.50 oz |
| 5 | Advanced Night Repair Eye Lift + Sculpt Eye Cream | 5593 | $85.00 | $68.00 | 2 sizes; 1.7 oz and 2.5 oz |
| 6 | Revitalizing Supreme+ Youth Power Creme SPF 25 Moisturizer | 354 | $140.00 | $112.00 | 3 sizes |
| 7 | Revitalizing Supreme+ Night Power Bounce Creme Moisturizer | 2275 | $135.00 | $108.00 | 3 sizes; normal/combination, dry, 1.0 oz visible |
| 8 | DayWear Moisturizer Multi-Protection Anti-Oxidant 24H-Moisture Creme SPF 15 | 1790 | $52.00 | $41.60 | 2 sizes |
| 9 | Advanced Night Repair Eye Supercharged Gel-Creme Synchronized Multi-Recovery Eye Cream | 3951 | $76.00 | $60.80 | 20% off badge |
| 10 | Unfiltered Morning Radiance Advanced Night Repair Skincare Gift Set | — | — | — | Needs deeper line fetch/PDP enrichment |

## Skincare Sample

The skincare page gives dense product records directly in fetched listing text. First 10 visible products:

1. Advanced Night Repair Serum Synchronized Multi-Recovery Complex — 4.6/5, 21145 reviews, `$16.00 - $206.40`
2. Advanced Night Repair Serum Duo Synchronized Multi-Recovery Complex — 4.6/5, 21145 reviews, `$230.00 $184.00`
3. Revitalizing Supreme+ Moisturizer Youth Power Creme — 4.5/5, 5182 reviews, `$25.60 - $112.00`
4. Unfiltered Morning Radiance Advanced Night Repair Skincare Gift Set — 4.8/5, 25 reviews, `$138.00 $110.40`
5. Revitalizing Supreme+ Night Power Bounce Creme Moisturizer — 4.7/5, 2275 reviews, `$64.00 - $108.00`
6. DayWear Moisturizer Multi-Protection Anti-Oxidant 24H-Moisture Creme SPF 15 — 4.7/5, 1790 reviews, `$13.60 - $41.60`
7. Advanced Night Repair Eye Supercharged Gel-Creme Synchronized Multi-Recovery Eye Cream — 4.4/5, 3951 reviews, `$20.80 - $60.80`
8. Revitalizing Supreme+ Youth Power Creme SPF 25 Moisturizer — 4.8/5, 354 reviews, `$96.00 - $112.00`
9. Advanced Night Repair Eye Lift + Sculpt Eye Cream — 4.6/5, 5593 reviews, `$85.00 $68.00`
10. Revitalizing Supreme+ Sculpting Face Serum — 4.5/5, 4446 reviews, `$145.00 $116.00`

## Makeup Sample

First visible makeup records:

1. Double Wear Stay-in-Place Longwear Matte Foundation — 9209 reviews, `$52.00`, 70 shades, sample shade `3N1 Ivory Beige`
2. Double Wear Foundation Pump — 57 reviews, `$10.00`
3. Futurist Hydra Rescue Moisturizing Foundation SPF 45 — 4119 reviews, `$55.00`, 28 shades, sample shade `2N1 Desert Beige`
4. Futurist SkinTint Serum Foundation With Botanical Oil Infusion SPF 20 — 945 reviews, `$55.00`, 29 shades
5. Double Wear Stay-in-Place Matte Powder Foundation — 268 reviews, `$52.00`, 34 shades, sample shade `4W2 Toasty Toffee`
6. Double Wear Maximum Cover Camouflage Foundation for Face and Body SPF 15 — 884 reviews, `$55.00`, 14 shades, sample shade `1C1 Cool Bone`
7. Double Wear Stay-in-Place Matte Powder Foundation Refill — 268 reviews, `$39.00`, 15 shades, sample shade `6N1 Mocha`
8. AERIN Tinted Lip Balm — 94 reviews, `$42.00`, 1 shade, sample shade `Petal Pink`
9. Futurist HydraPlump Tinted Lip Balm — 63 reviews, `$38.00`, 8 shades, sample shade `705 Petal Boost`
10. Double Wear Stay-in-Place 24-Hour Concealer — 694 reviews, `$38.00`, 30 shades, sample shade `2C`

## Fragrance Sample

First visible fragrance records:

1. Beautiful Eau de Parfum Spray — 608 reviews, `$125.00`, 4 sizes
2. Beautiful Favorites Trio Fragrance Gift Set — 24 reviews, `$110.00`, limited edition
3. Beautiful Magnolia Deluxe Trio Fragrance Gift Set — 23 reviews, `$112.00`, limited edition
4. Beautiful Magnolia Joyful Duo Fragrance Gift Set — 24 reviews, `$40.00`, sale/current `$30.00`, limited edition

More fragrance products require additional page-line fetch or PDP enrichment.

## Sets & Gifts Sample

First visible sets/gifts records:

1. The Radiance Routine Resilience Multi-Effect Skincare Gift Set — 27 reviews, `$120.00`, sale/current `$96.00`
2. The Lifting and Firming Routine Revitalizing Supreme+ Skincare Gift Set — 20 reviews, `$125.00`, sale/current `$100.00`
3. Nightly Renewal Skincare Set Cleanse + Repair + Glow — 20 reviews, `$138.00`, limited edition

More sets/gifts products require additional page-line fetch or PDP enrichment.

## PDP Enrichment Result

Fetching the Double Wear PDP provides attributes not reliably available on category cards:

- Title: Double Wear Stay-in-Place Longwear Matte Foundation
- Review count: 9209
- Short description: 36-hour color-true long-wear foundation. The new flawless.
- Selected shade: 3N1 Ivory Beige
- Undertone: Medium with neutral undertones
- Size: 1.0 oz.
- Price: $52.00
- Product details
- Proven results
- Featured ingredients
- Benefits
- Coverage
- Finish
- Skin type
- Formula facts
- Free-from claims
- Shade list

## Conclusion

The WebFetch/WebSearch-provider hypothesis works for Estee Lauder in hosted skill mode. It can produce listing-level product records quickly and can enrich PDP records with richer attributes. Scout's missing piece is not crawling harder; it is accepting hosted fetched content as a provider and then doing extraction, normalization, deduplication, enrichment, and artifact writing.

Standalone CLI still needs Crawl4AI/CDP/profile/proxy/saved-HTML providers because hosted WebFetch is not available inside a normal pip package.

