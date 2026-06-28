# Hosted HTTP Boundary PRD

## Summary

Add `/v1/hosted/scrape`, a hosted-mode API endpoint protected by
`Authorization: Bearer scout_live_...`. It must not require local `X-API-Key`,
but it must perform hosted admission before calling the crawler.

## Objective

- Allow `/v1/hosted/*` through the local static-key middleware.
- Reject missing/malformed Bearer tokens in the hosted route.
- Reject unknown keys, wrong scopes, unsafe URLs, and insufficient credits.
- Debit credits only for admitted requests.
- Return scrape output plus non-secret hosted admission metadata.

## API Contract

Request:

```json
{
  "url": "https://example.com",
  "formats": ["markdown"],
  "use_js": false
}
```

Headers:

```http
Authorization: Bearer scout_live_...
```

Response:

```json
{
  "success": true,
  "hosted": {
    "tenant_id": "...",
    "key_id": "...",
    "credits_charged": 1,
    "credit_type": "standard"
  },
  "scrape": { "...": "ScrapeResponse" }
}
```

## Acceptance Criteria

- Existing local `/scrape` auth behavior remains unchanged.
- `/v1/hosted/scrape` without Bearer token returns 401.
- `/v1/hosted/scrape` with unsafe URL returns 403 and does not call crawler.
- `/v1/hosted/scrape` with valid key and safe URL calls crawler once and returns
  scrape result plus hosted metadata.
- Hosted route responses never echo the raw API key.
