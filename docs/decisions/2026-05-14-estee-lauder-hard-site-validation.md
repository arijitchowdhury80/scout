# Estee Lauder Hard-Site Validation

Date: 2026-05-14

## Context

Scout product mode needs to support prompts such as "get the top 2 products from each top category at Estee Lauder" and prepare Algolia-ready product records. The current Crawl4AI-first implementation can crawl normal retail sites, but Estee Lauder returned zero product records in live testing.

## Validation Results

| Channel | Result | Evidence |
|---|---|---|
| Scout/Crawl4AI headless category fetch | Blocked | Direct fetch of `https://www.esteelauder.com/products/681/product-catalog/skin-care` returned title `Access Denied`, HTML length about 333 bytes, no product content. |
| Scout/Crawl4AI headed category fetch | Blocked | Same category URL with `headless=False`, stealth, JS, and 45s timeout returned `Access Denied` in about 5 seconds. |
| Crawl4AI persistent fresh profile | Blocked | `use_persistent_context=True` with a new `user_data_dir` still returned `Access Denied`. |
| Crawl4AI with realistic Mac Chrome UA/locale | Blocked | Headless and headed probes using a Mac Chrome UA, `en-US`, New York timezone, stealth, and delay still returned `Access Denied`. |
| Hosted WebFetch/WebSearch-style retrieval | Works | Hosted web retrieval can read the Double Wear PDP and skincare category page, including product title, price, description, product links, review counts, and listing content. This is not equivalent to local Crawl4AI because it uses different infrastructure and may include cached/search-indexed extraction. |
| Codex in-app browser category page | Works | Same skincare URL loaded successfully with page title `Estée Lauder Skincare | Get A Free Full-Size Skincare Gift*` and visible `88 Products`. |
| Codex in-app browser PDP page | Works | Product page for Advanced Night Repair loaded successfully with title, price, product details, benefits, and how-to-use content. |
| Browser DOM extraction dry run | Works with caveats | Top categories produced 2 product URLs each from Best Sellers, Skincare, Makeup, Fragrance, and Sets & Gifts. Listing extraction gave names, URLs, many prices/ratings; PDP enrichment filled missing fields such as foundation price. |

## Estee Lauder URL Pattern

Estee Lauder uses short landing/promo URLs and numeric product-catalog category URLs. Scout should treat these as first-class category or landing seeds, not infer them from generic slugs such as `/skin-care`.

Known examples:

- `https://www.esteelauder.com/gift-with-purchase-summer-26`
- `https://www.esteelauder.com/products/681/product-catalog/skin-care`
- `https://www.esteelauder.com/products/631/product-catalog/makeup`
- `https://www.esteelauder.com/products/571/product-catalog/fragrance`

Rule implication: site-specific seed config can map user intent like "top categories" to these canonical URLs, then the extractor can collect product cards and PDP links from those pages.

## Decision

A generic "open a headed Crawl4AI browser after block" fallback is not sufficient for Estee Lauder. The validated path is a provider ladder:

1. Crawl4AI regular fetch for normal sites.
2. Hosted WebFetch/WebSearch provider when Scout is running as a host skill and those tools are available.
3. Crawl4AI headed/persistent/profile/CDP fetch when a site can be unblocked by local session state.
4. Real browser/session handoff for hard sites where the user's existing browser is trusted.
5. PDP enrichment after listing extraction to fill missing product fields.
6. Structured blocked-page artifact when no provider can access the site.

Scout also needs to apply fallback during category/listing discovery, not only after a blocked PDP scrape. Estee Lauder blocks the category pages themselves in fresh Crawl4AI sessions.

## Build Implications

- Split product crawling into fetch providers and pure extractors.
- Add a `HostWebFetchProvider` for Claude/Codex skill mode so hosted web retrieval output can be passed into Scout extractors.
- Add a `BrowserSessionProvider` or equivalent handoff interface that can consume current-browser HTML/DOM for the Claude/Codex skill path.
- Add a `ProfileProvider`/CDP option for standalone CLI users who can launch or attach a trusted browser profile.
- Add retailer seed/category config so "top categories" does not depend on weak generic URL discovery.
- Keep blocked artifacts explicit so Scout can say when a site requires a trusted session or proxy instead of silently returning empty results.
