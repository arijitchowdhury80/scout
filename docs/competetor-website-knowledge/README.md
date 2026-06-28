# Scout Competitor Website Knowledge

Date: 2026-06-28
Status: Research baseline for Scout product launch

This folder captures competitor website research, production-readiness
implications, pricing/economics notes, and the recommended website direction for
Scout.

The folder name intentionally follows the requested spelling:
`competetor-website-knowledge`.

## Files

- `competitor-matrix.md` - competitor-by-competitor positioning, website
  structure, onboarding, docs, pricing, and takeaways.
- `website-patterns.md` - common website sections and launch-page patterns seen
  across crawler, browser, and AI search infrastructure products.
- `production-readiness-and-distribution.md` - hosted vs local architecture,
  multi-tenancy, packaging, security, scale, and product data generalization.
- `pricing-and-payment-recommendation.md` - competitor pricing patterns and
  Scout's recommended commercial model.
- `market-pricing-snapshot-2026-06-28.md` - current official-site pricing
  evidence across crawler, browser, AI search, and extraction competitors.
- `scout-differentiation.md` - sharper Scout positioning beyond the
  local-owned-data claim.
- `scout-website-plan.md` - recommended Scout site map, messaging, CTA model,
  and Supadesign IndustrialGray design-system direction.
- `source-index.md` - researched source URLs and what each was used for.

## Working Position

Scout should not launch as a generic "crawler API" or a fake app platform.
That market is already crowded and better-funded. Scout's sharper position is:

> Scout is a local-first web acquisition system for AI workflows. It captures
> pages, browser evidence, source provenance, and typed records that can be
> reused by agents, search indexes, demos, and intelligence pipelines.

The website should therefore lead with:

1. evidence-grade records,
2. citations and artifact folders,
3. acquisition ladder including browser/user-session capture,
4. honest blocked/fallback reporting,
5. local-first operation,
6. optional metered hosted API for users who value convenience over local
   control.

## Current Recommendation

Launch order:

1. **Private beta website** - install/download-first, clear beta limits.
2. **Local package** - `pipx`/`pip`, Docker, and GitHub install paths.
3. **Hosted API preview** - paid, limited credits, not unlimited one-time access.
4. **Website v2** - polished docs, examples, pricing, hosted dashboard/API key
   flow once multi-tenancy exists.
