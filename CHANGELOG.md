# Changelog

## 0.1.1 - 2026-06-27

### Added

- Added optional acquisition metadata to the shared `POST /scrape` contract.
- Added `raw_markdown`, `clean_markdown`, and nested `acquisition` response fields.
- Added opt-in request fields: `quality_analysis`, `cleanup`, `expected_markers`, `recommend_collector`, and `source_id`.
- Added explainable `quality_score`, `quality_reasons`, marker validation, content hashing, and collector recommendations.
- Added feed-like URL detection that recommends `rss_feed` without moving feed parsing into Scout.
- Added `scout benchmark` CLI to compare Scout acquisition with direct HTTP and write artifacts.
- Added runtime Crawl4AI version reporting from installed package metadata.

### Changed

- Pinned Crawl4AI to `0.9.0` for deterministic rebuilds.
- Kept default `/scrape` behavior backward-compatible unless callers opt into acquisition metadata.

### Removed

- Removed exploratory `/ci/scrape`; consumer-specific acquisition endpoints are not allowed.

### Deferred

- Broad Crawl4AI-native popup and overlay cleanup defaults remain deferred until source-by-source benchmarking proves they are worth the latency.

