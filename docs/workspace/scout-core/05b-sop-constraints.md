# SOP Constraints For Product Blocked-Page Fallbacks

Date: 2026-05-13

## Coding Constraints

- Pydantic models must guard response/artifact boundaries; no raw dictionaries should cross from extraction into product mode.
- Functions need explicit type hints and small responsibilities.
- External crawl failures must be logged with context and must not silently erase evidence.
- Structured logging via `structlog` remains the local pattern.

## Testing Constraints

- Tests precede implementation.
- Unit tests cover extraction and product-mode fallback behavior without network.
- Contract tests validate new response fields and artifact file fields.
- Live integration remains opt-in because it hits retailer websites and can fail for network or anti-bot reasons.

## Known Tradeoff

The fallback deliberately produces partial records when PDPs are blocked. This is acceptable only if each record carries extraction provenance and completeness scoring.

