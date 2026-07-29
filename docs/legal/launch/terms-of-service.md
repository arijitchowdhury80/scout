# Scout Terms of Service

**Status: DRAFT — NOT LEGAL ADVICE. Requires review and sign-off by a qualified attorney before publication.**
**Version: Draft 0.1 · Prepared: 2026-07-26 · For: public ProductHunt beta launch**

> These are launch-ready drafts prepared by a non-lawyer for a lawyer to review. Bracketed items marked `[PLACEHOLDER]` must be completed before publication (legal entity, governing law, notice addresses). Do not treat this document as final or as legal advice.

---

## 1. Agreement to Terms

These Terms of Service ("Terms") are a binding agreement between you ("you", "Customer", "User") and `[PLACEHOLDER: legal entity name — e.g. Scout / operator entity]` ("Scout", "we", "us"), operator of the Scout service at scout.chowmes.com and its HTTP API and associated tooling (the "Service").

By creating an account, purchasing credits, or using the Service (including via the HTTP API or the Scout skill for Claude/Codex), you agree to these Terms, the [Privacy Policy](./privacy-policy.md), the [Acceptable Use Policy](./acceptable-use-policy.md) ("AUP"), and the [Robots & Crawl Ethics policy](./robots-and-crawl-ethics.md). If you do not agree, do not use the Service.

If you use the Service on behalf of an organization, you represent that you are authorized to bind that organization, and "you" refers to that organization.

## 2. Beta Status

The Service is offered as a **public beta**. It is provided "as is" and may contain bugs, change without notice, experience downtime, or be discontinued. Beta features may be added, changed, metered differently, or removed at any time. Data, run artifacts, and account state during beta may be reset, migrated, or deleted with reasonable notice where practicable. **Do not rely on the beta Service for production-critical, regulated, or irreplaceable workloads.**

## 3. Description of the Service

Scout is a self-hosted web-intelligence and crawling platform (built on the open-source Crawl4AI project, Apache-2.0). It lets users programmatically retrieve, render, extract, screenshot, and structure content from **publicly accessible** third-party websites, and returns structured run artifacts. Scout is a **tool operated at the direction of the User**: you choose the target URLs, the extraction configuration, and the purpose. Scout does not select targets for you and does not independently decide what to crawl.

You are solely responsible for the targets you direct Scout to access and for your use of any data Scout returns. Your use is governed by the AUP, which is incorporated into these Terms.

## 4. Accounts and Registration

- You must provide accurate registration information (name, email) and keep it current.
- You are responsible for safeguarding your account credentials and API keys, and for all activity under your account or API key.
- You must be at least 18 years old (or the age of majority in your jurisdiction) and legally able to enter into contracts.
- Notify us promptly of any unauthorized use at `[PLACEHOLDER: security/abuse contact email]`.
- We may refuse registration, or suspend or terminate accounts, at our discretion (see Section 11).

## 5. Credits, Billing, and Payment

**5.1 Credit model.** The Service is metered in **credits**. Actions (a crawled page, an extracted record, a screenshot, a browser render, browser time, etc.) consume credits at the rates published on the pricing page. We may adjust credit rates and definitions with prospective notice; changes do not retroactively reduce credits already purchased.

**5.2 Plans.** Current plans include a free tier (one-time credit grant), a beta cohort grant, a recurring monthly subscription, and one-time pay-as-you-go credit packs, as described on the pricing page. Subscription credits reset each billing cycle and do not roll over unless expressly stated. Pay-as-you-go credit packs do not expire unless expressly stated. "Monthly" and other capped plans are **not** unlimited; the credit cap is stated as a number on the pricing page.

**5.3 Payment processor.** Payments are processed by **Stripe, Inc.** ("Stripe"). By purchasing, you also agree to Stripe's terms. We do not receive or store your full card number; card data is handled by Stripe. You authorize us (via Stripe) to charge your payment method for the plan or packs you select.

**5.4 Subscriptions and auto-renewal.** Paid subscriptions renew automatically at the then-current price each billing period until cancelled. You may cancel at any time via your account or by contacting us; cancellation takes effect at the end of the current billing period. You remain responsible for charges incurred before cancellation.

**5.5 Taxes.** Prices exclude taxes unless stated. You are responsible for applicable sales, use, VAT, GST, or similar taxes, other than taxes on our net income.

**5.6 Refunds.** Because credits are consumable digital services delivered immediately:

- **Subscriptions:** Fees are generally **non-refundable**, including for partial billing periods and unused credits. Cancelling stops future renewals; it does not refund the current period.
- **Pay-as-you-go packs:** Non-refundable once any credit in the pack has been consumed.
- **Discretionary refunds:** We may, at our sole discretion, issue a pro-rata or full refund (for example, for a sustained Service outage attributable to us, or a duplicate charge). Consumer rights that cannot be waived under applicable law (including certain EU/UK statutory withdrawal rights for digital content) are not affected by this section.
- **Chargebacks:** Initiating a chargeback without first contacting us may result in suspension pending resolution.

**5.7 Failed payments.** If a charge fails, we may retry, suspend paid features, or downgrade the account until payment succeeds.

## 6. Acceptable Use and Customer Responsibility

Your use of the Service is subject to the [Acceptable Use Policy](./acceptable-use-policy.md). **You are solely responsible for ensuring that your use of Scout — including every target you crawl and every use you make of returned data — is lawful and complies with all applicable laws, the target site's terms and technical restrictions, and third-party rights.** Scout is a neutral tool; you direct it. Violation of the AUP is a material breach of these Terms.

## 7. Intellectual Property

**7.1 Scout IP.** The Service, excluding open-source components and your data, is owned by us and our licensors. We grant you a limited, non-exclusive, non-transferable, revocable license to use the Service per these Terms.

**7.2 Open source.** The Scout core is licensed under Apache-2.0 and incorporates third-party open-source software (including Crawl4AI, Apache-2.0). See the [third-party licenses note](./third-party-licenses-note.md). Nothing here restricts your rights under those open-source licenses with respect to the open-source components themselves.

**7.3 Your content and outputs.** As between you and us, you retain rights in the configuration you supply and, subject to third-party rights in the underlying source material, in the run outputs Scout returns to you. **We claim no ownership of crawled third-party content, and we make no representation that you have the right to use it** — that is your responsibility under Section 6 and the AUP.

**7.4 Feedback.** You grant us a perpetual, royalty-free license to use feedback you provide to improve the Service.

## 8. Third-Party Sites and Data

The Service accesses third-party websites you designate. We do not control, endorse, or assume responsibility for third-party sites, their content, their terms, or their availability. Scraping and downstream use of third-party content and personal data may be regulated (including under the CFAA and similar computer-access laws, copyright law, database rights, contract/website-terms law, and data-protection laws such as the GDPR and CCPA/CPRA). You are responsible for your own legal compliance.

## 9. Disclaimers

THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE," WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, ACCURACY, AND NON-INFRINGEMENT. WE DO NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, OR SECURE, THAT ANY TARGET SITE WILL BE ACCESSIBLE, THAT EXTRACTED DATA WILL BE ACCURATE OR COMPLETE, OR THAT USE OF EXTRACTED DATA IS LAWFUL FOR YOUR PURPOSE. SCOUT DOES NOT GUARANTEE ACCESS TO SITES THAT BLOCK CRAWLERS OR AUTOMATION. NOTHING IN THE SERVICE OR DOCUMENTATION IS LEGAL ADVICE.

## 10. Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY LAW:

- WE AND OUR SUPPLIERS WILL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES, OR FOR LOST PROFITS, REVENUE, DATA, OR GOODWILL, ARISING FROM OR RELATED TO THE SERVICE, EVEN IF ADVISED OF THE POSSIBILITY.
- OUR TOTAL AGGREGATE LIABILITY FOR ALL CLAIMS ARISING FROM OR RELATED TO THE SERVICE WILL NOT EXCEED THE GREATER OF (A) THE AMOUNTS YOU PAID US IN THE **THREE (3) MONTHS** PRECEDING THE EVENT GIVING RISE TO THE CLAIM, OR (B) **USD $50**.

Some jurisdictions do not allow certain limitations; in those jurisdictions our liability is limited to the maximum extent permitted. These limits do not apply to liability that cannot be limited by law.

## 11. Indemnification

You will defend, indemnify, and hold harmless Scout and its operators, from and against any claims, damages, liabilities, costs, and expenses (including reasonable legal fees) arising from: (a) your use of the Service; (b) the targets you crawl and your use of returned data; (c) your violation of these Terms or the AUP; or (d) your violation of any law or third-party right (including intellectual-property, contract, computer-access, or data-protection rights). This is a primary shield for a crawler operator and should be reviewed carefully by counsel.

## 12. Suspension and Termination

We may suspend or terminate your access, with or without notice, if we reasonably believe you have violated these Terms or the AUP, created legal, security, or infrastructure risk, or failed to pay. You may stop using and close your account at any time. On termination: your license ends, access ceases, and we may delete your data per the [Data Retention Policy](./data-retention-policy.md). Sections that by their nature should survive (IP, disclaimers, liability limits, indemnity, governing law) survive termination. No refund is owed for termination due to your breach.

## 13. Changes to the Terms

We may update these Terms. Material changes will be notified by email or in-Service notice with reasonable advance effect where practicable. Continued use after changes take effect constitutes acceptance. If you do not agree, stop using the Service.

## 14. Governing Law and Disputes

`[PLACEHOLDER: governing law and venue — e.g. State of ____, USA / or operator's jurisdiction. Counsel to select and add any arbitration and class-action-waiver clause appropriate to the operator's jurisdiction and target markets.]` These Terms are governed by the laws of `[PLACEHOLDER: jurisdiction]`, excluding conflict-of-law rules. `[PLACEHOLDER: dispute resolution / arbitration clause to be drafted by counsel.]`

## 15. General

- **Entire agreement.** These Terms plus the incorporated policies are the entire agreement on this subject.
- **Severability.** If any provision is unenforceable, the rest remains in effect.
- **No waiver.** Failure to enforce is not a waiver.
- **Assignment.** You may not assign these Terms without our consent; we may assign in connection with a merger, acquisition, or sale of assets.
- **Force majeure.** We are not liable for delays or failures beyond our reasonable control.
- **Notices.** Legal notices to us: `[PLACEHOLDER: legal notice email/address]`. Notices to you: your account email.

## 16. Contact

`[PLACEHOLDER: contact email]` · scout.chowmes.com

---
*End of draft. Attorney review required before publication.*
