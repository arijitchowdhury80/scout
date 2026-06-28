# Scout Blocked Case Analysis - 2026-06-28

## Summary

Scout's current service-scope certification has no failing scenarios:

- Total scenarios: 71
- Passed: 64
- Blocked with evidence: 7
- Failed: 0

The seven blocked scenarios are not silent failures. They are live hard-site cases
where Scout produced durable blocked/fallback artifacts but did not extract usable
records. These cases should not be marketed as successful extraction.

This pass added and certified the service-first captured-DOM product path:
`products.captured_dom.fixture` now proves `POST /structure` can accept already
captured product-listing HTML, avoid re-fetching the hard-site URL, and return
Algolia-ready product records with citations. That closes the deterministic
structuring gap, but it does not by itself prove live hard-site acquisition.

It also added and certified `products.user_browser_capture.fixture`, proving
`POST /app/browser/capture` can turn a cleared user-browser product category
capture into Algolia-ready product records without asking the user to provide
CSS selectors.

It now also certifies `products.cdp_harvest.fixture`, proving `POST /harvest`
can attach to an already-open CDP browser tab, preserve harvested HTML, and
return Algolia-ready product records from that live tab DOM.

## Blocked Scenarios

| Scenario | Classification | Current Evidence | Product Meaning |
|---|---|---|---|
| `browser_workbench.estee_lauder` | hard-site/browser fallback blocked | `validation-output/current-evidence/service-live/products_estee_lauder_live/` | Browser/CDP fallback preserved blocked evidence but did not extract products. |
| `products.estee_lauder.live` | hard-site product blocked | `validation-output/current-evidence/service-live/products_estee_lauder_live/` | Estée Lauder category produced no product records through the current service crawler/fallback path. |
| `products.nike.live` | hard-site product blocked | `validation-output/current-evidence/service-live/products_nike_live/` | Nike product category produced no product records through the current service crawler/fallback path. |
| `products.ll_bean.live` | hard-site product blocked | `validation-output/current-evidence/service-live/products_ll_bean_live/` | L.L.Bean product category produced no product records through the current service crawler/fallback path. |
| `products.patagonia.live` | hard-site product blocked | `validation-output/current-evidence/service-live/products_patagonia_live/` | Patagonia product category produced no product records through the current service crawler/fallback path. |
| `products.home_depot.live` | hard-site product blocked | `validation-output/current-evidence/service-live/products_home_depot_live/` | Home Depot product category produced no product records through the current service crawler/fallback path. |
| `website_quality.british_airways.live` | hard-site/company website blocked | `validation-output/current-evidence/service-live/website_quality_british_airways_live/` | British Airways website quality extraction produced blocked evidence rather than findings. |

## What This Proves

- Scout does not silently succeed with zero records for these targets.
- Scout writes durable artifacts for blocked/fallback outcomes.
- Certification can distinguish successful extraction from blocked evidence.
- Captured product DOM can be structured into Algolia-ready records through the
  service API.
- Cleared user-browser product captures can be productized without custom
  selectors.
- CDP-harvested browser tabs can be productized through the service API.
- The service/API/CLI certification gate is materially healthier than the previous app-first validation.

## What This Does Not Prove

- It does not prove Scout can extract product records from Estée Lauder, Nike,
  L.L.Bean, Patagonia, or Home Depot in the current service configuration.
- It does not prove live crawler or browser/user-session capture can recover
  records from those hard sites without a captured DOM input.
- It does not support a launch claim that Scout can "scrape anything."

## Required Next Fix

To turn the remaining live hard-site scenarios from `blocked_with_evidence` into
`pass`, Scout needs a stronger acquisition path that feeds real captured DOM into
the now-certified product structuring path:

1. User-browser/CDP capture as a service-first feature, not an app UI feature.
2. Live/manual validation that captures actual hard-site product DOM and posts it
   to `/structure` with `record_type=products`.
3. Product extraction tests that assert product records, citations, and Algolia
   preview readiness from real captured hard-site DOM.

Until that is built, the honest claim is:

> Scout has certified service/API/CLI extraction for core modes and intelligence
> modules, and it preserves blocked evidence for hard retail sites. Hard-site
> product extraction remains a known limitation.
