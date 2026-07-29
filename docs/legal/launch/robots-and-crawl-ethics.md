# Scout Robots & Crawl Ethics Policy

**Status: DRAFT — NOT LEGAL ADVICE. Requires attorney review before publication.**
**Version: Draft 0.1 · Prepared: 2026-07-26 · For: public ProductHunt beta launch**

> ⚠️ **IMPORTANT ACCURACY NOTE FOR REVIEW:** As of this draft, Scout's crawl path does **NOT** enforce `robots.txt` by default. This policy is written to describe the **target launch posture** (respect `robots.txt` and rate limits by default). **Do not publish this policy as-is until the engineering behavior matches it** — otherwise the policy is a false statement about the product. Either (a) ship robots.txt-respecting defaults before launch, or (b) rewrite this policy to describe the actual behavior and place responsibility explicitly on the user. This gap is tracked in the [Legal Gap Report](./LEGAL-GAP-REPORT.md).

---

## 1. Our Philosophy

Scout is built for **responsible, evidence-grade** web intelligence. We believe good crawling is polite crawling: it respects site operators' expressed wishes, does not degrade their service, and stays within lawful and ethical bounds. This policy describes how Scout is intended to behave and what we expect of users.

## 2. Robots.txt (Target Behavior)

- **Default:** Scout is intended to **fetch and respect a target site's `robots.txt`** before crawling, honoring `Disallow` rules and any `Crawl-delay` for the applicable user-agent. `[ENGINEERING GAP — see note above; must be true before this line is published.]`
- **User-agent:** Scout identifies its automated traffic honestly where a user agent is sent. `[Confirm the default UA string and whether a Scout-specific UA / contact URL is published.]`
- Robots.txt is an access-management convention, not a law by itself — but ignoring it can weigh against you in contract, CFAA, and trespass-to-chattels analyses, and can breach a site's Terms of Service. Respecting it is both ethical and risk-reducing.

## 3. Rate Limiting and Load (Target Behavior)

- Scout applies conservative default request rates and concurrency limits so that crawling does not overload target sites.
- The hosted Service also applies its own platform rate limits and an active-crawl cap.
- Users must not configure Scout to generate abusive load against any target.

## 4. Overrides — What Users May and May Not Do

- **Permitted, with responsibility:** For sites **you own or operate**, or where you have **explicit written permission** from the site operator, you may configure Scout to crawl according to that permission (including areas a public robots.txt would otherwise disallow). You are responsible for proving that permission on request.
- **Not permitted:** Overriding robots or rate-limit protections to access third-party sites you do **not** own or have permission for, or to circumvent access controls, is prohibited by the [Acceptable Use Policy](./acceptable-use-policy.md).
- Any override capability, if exposed, is provided as a tool for authorized use only. Using it does not transfer legal responsibility to Scout — it remains with you.

## 5. Blocked Sites and "Evidence, Not Bypass"

Scout does **not** guarantee access to sites that block crawlers or automation. Where a site blocks access, Scout may preserve *blocked evidence* (that the page was blocked) and use browser-assisted, human-approved acquisition — but this is not a promise to defeat protections, and you must not use it to circumvent access controls unlawfully.

## 6. Personal Data and Sensitive Targets

Even where a crawl is technically permitted, collecting personal or sensitive data carries independent legal obligations (GDPR, CCPA/CPRA, and others). See the [Privacy Policy](./privacy-policy.md) and [Acceptable Use Policy](./acceptable-use-policy.md).

## 7. Reporting

Site operators who wish to report crawling they believe originates from Scout, or to request that Scout traffic avoid their site, may contact `[PLACEHOLDER: abuse contact email]`. We will act on good-faith requests.

---
*End of draft. Attorney review and engineering alignment required before publication.*
