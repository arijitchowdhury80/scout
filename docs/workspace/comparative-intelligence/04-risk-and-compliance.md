# Comparative Intelligence Risk And Compliance

Date: 2026-07-09

## Strategic Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| Looks like a consumer shopping app | Dilutes Scout's business wedge | Use shopping as an understandable demo; position paid product as competitive market intelligence |
| Overpromises coverage | Users expect every retailer/hotel site to work | V1 starts with user-supplied sources and clear blocked-source reporting |
| Bad matching | Comparing different TV models or hotel room types destroys trust | Add explicit identity fields, confidence scores, and "not enough evidence" states |
| Price staleness | Prices change quickly | Show crawl timestamp and freshness policy on every row |
| Hidden fees/membership prices | Retail/hotel prices often have caveats | Capture visible caveats and avoid total-price claims unless all components are visible |

## Compliance And Platform Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| Terms-of-service conflicts | Some sites restrict automated extraction | V1 requires source approval policy and blocked-source handling |
| Robots and rate limits | Hosted Scout must not behave abusively | Reuse existing URL safety, rate limits, robots handling, and per-source throttles |
| Login or membership-only prices | May require credentials or violate boundaries | Exclude authenticated, cart-only, and membership-only flows from V1 |
| Hotel/OTA dynamic pricing | Dates, occupancy, taxes, fees, and room type matter | Require date/occupancy constraints and cite the observed room/rate context |
| Legal claims around "best price" | Could imply guarantee | Say "observed price at crawl time," not "best price" or "lowest guaranteed price" |

## Technical Risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| Source-specific selectors creep | Too many brittle custom parsers | Prefer schema.org/JSON-LD and generic extraction first; add templates only after evidence |
| LLM hallucination | Market summaries can invent comparisons | Keep numeric extraction deterministic where possible; LLM can summarize only cited records |
| Browser-heavy cost | Retail/hotel pages may require JS | Price browser-heavy runs separately and cap source count |
| Duplicate products | The same product appears under variants and bundles | Add identity normalization and variant grouping |
| Live test brittleness | Retail/hotel sites change often | Use fixture tests as gates; keep live smoke tests non-blocking or quarantined unless source is stable |

## Go/No-Go For V1 Build

Go if:

- The first vertical can produce reliable fixture results.
- A small live smoke set produces reviewable output with honest blocked-source
  reporting.
- Source policy and hosted credit economics are approved.

No-go if:

- Matching confidence is consistently low.
- Most target sources need login/cart/membership flows.
- The feature requires broad web search before basic user-supplied source
  comparison works.
