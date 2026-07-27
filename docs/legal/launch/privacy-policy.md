# Scout Privacy Policy

**Status: DRAFT — NOT LEGAL ADVICE. Requires review and sign-off by a qualified attorney (ideally one with GDPR/CCPA experience) before publication.**
**Version: Draft 0.1 · Prepared: 2026-07-26 · For: public ProductHunt beta launch**

> `[PLACEHOLDER]` items (legal entity, EU/UK representative if required, DPO contact if required, precise retention windows once confirmed) must be completed before publication.

---

## 1. Who We Are

This policy explains how `[PLACEHOLDER: legal entity name]` ("Scout", "we", "us"), operator of scout.chowmes.com and the Scout HTTP API and skill (the "Service"), collects and uses personal data. For data-protection purposes, we are the **controller** of account and usage data described here.

Contact: `[PLACEHOLDER: privacy contact email]`. If we are required to appoint an EU/UK representative or a Data Protection Officer, their details will appear here: `[PLACEHOLDER]`.

## 2. Scope and a Key Distinction

This policy covers personal data **about you as a Scout user**. It also explains an important separate category: **content you direct Scout to crawl**. When you point Scout at a third-party website, Scout retrieves whatever is on the pages you target, which may include personal data about third parties. For that crawled content, **you are the controller and Scout acts as your processor / service provider** — you decide what to crawl and why, and you are responsible for having a lawful basis. See Section 8.

## 3. Personal Data We Collect (about users)

| Category | Examples | Source |
|---|---|---|
| **Identity** | Name, email address | You, at signup |
| **Account** | Hashed credentials/API-key status, plan, credit balance | You / generated |
| **Billing** | Billing name, last4 / payment references, transaction history | Stripe (we do not store full card numbers) |
| **Technical** | IP address, user agent, device/browser info | Automatically, on access |
| **Usage** | Run metadata, target URLs you submit, credit consumption, timestamps, API logs, error/diagnostic logs | Automatically, from your use |
| **Support** | Correspondence you send us | You |
| **Product analytics** | Aggregated/pseudonymous page and event data via Umami | Automatically (see Section 9) |

We do **not** intentionally collect special-category data about users. Please do not submit secrets, credentials, or regulated personal data into Scout runs (see the [Acceptable Use Policy](./acceptable-use-policy.md)).

## 4. How We Use Personal Data and Lawful Bases (GDPR Art. 6)

| Purpose | Data used | Lawful basis (GDPR) |
|---|---|---|
| Provide the Service, run crawls, meter credits | Account, usage, technical | **Contract** (Art. 6(1)(b)) |
| Process payments, prevent payment fraud | Billing, identity | **Contract** + **legal obligation** |
| Secure the Service, prevent abuse, debug | Technical, usage logs | **Legitimate interests** (Art. 6(1)(f)) — securing our service |
| Product analytics and improvement | Umami analytics, usage | **Legitimate interests** (privacy-friendly analytics) |
| Service and transactional emails | Identity, account | **Contract** |
| Marketing emails (if any) | Identity | **Consent** (opt-in) where required; opt-out always available |
| Comply with law, respond to legal requests | As needed | **Legal obligation** |

Where we rely on legitimate interests, we have balanced them against your rights; you may object (Section 7).

## 5. How We Share Data — Sub-processors

We do not sell personal data. We share it with service providers ("sub-processors") who process it on our behalf under contract, and as required by law. Current sub-processors:

| Sub-processor | Purpose | Data | Location / transfer note |
|---|---|---|---|
| **Stripe, Inc.** | Payment processing | Billing, identity, IP | US; Stripe is the payment controller/processor. `[Confirm SCCs / DPF]` |
| **Resend** | Transactional/account email delivery | Name, email | `[Confirm host region + DPA/SCCs]` |
| **Algolia** | Search indexing of run outputs (where the feature is used) | Extracted records, run data you generate | `[Confirm region + DPA]` |
| **VPS host** — `[PLACEHOLDER: Hostinger / actual provider]` | Hosting, storage, compute | All hosted data | `[Confirm region + DPA]` |

Before publication, confirm each provider's region, that a Data Processing Agreement / Standard Contractual Clauses (or an adequacy/DPF mechanism) is in place, and update this table. We will maintain the current list at `[PLACEHOLDER: URL]`.

We may also disclose data in a merger/acquisition, or to comply with law, enforce our terms, or protect rights and safety.

## 6. International Transfers

We and our sub-processors may process data in the United States and other countries. Where we transfer personal data out of the EEA/UK/Switzerland, we rely on an appropriate safeguard (Standard Contractual Clauses, UK IDTA/Addendum, or an adequacy/Data Privacy Framework mechanism). `[Counsel to confirm the exact mechanism per sub-processor.]`

## 7. Your Rights

**GDPR / UK GDPR (EEA/UK users).** You have the right to: access; rectification; erasure ("right to be forgotten"); restriction; data portability; objection (including to legitimate-interest processing and direct marketing); and to withdraw consent. You may also lodge a complaint with your supervisory authority.

**CCPA/CPRA (California users).** You have the right to: know/access the categories and specifics of personal information collected; delete; correct; and opt out of "sale"/"sharing" of personal information. **We do not sell or share personal information** as those terms are defined by the CPRA. We will not discriminate against you for exercising your rights. We do not knowingly process the personal information of anyone under 16 without required consent.

**How to exercise.** Email `[PLACEHOLDER: privacy contact email]`. We will verify your request and respond within the timeframe required by law (generally 30 days under GDPR; 45 days under CCPA, extendable). You may use an authorized agent where the law allows.

## 8. Crawled Content and Data-Subject Requests About Third Parties

When you use Scout to crawl third-party sites, you may collect personal data about people who are not Scout users. For that data:

- **You are the controller/business**; Scout is your **processor/service provider** and processes it only on your documented instructions to provide the Service. `[A Data Processing Addendum should be offered to customers who require one — counsel to prepare a DPA template.]`
- **You are responsible** for having a lawful basis, providing any required notices, and honoring data-subject requests relating to the data you collected.
- If we receive a data-subject request about crawled content, we will, where lawful, refer or forward it to the relevant customer.
- Retention of run artifacts is governed by the [Data Retention Policy](./data-retention-policy.md).

## 9. Cookies and Analytics

The marketing site and app use only what is necessary to operate, plus **Umami**, a privacy-friendly, cookieless analytics tool that collects aggregated, non-identifying usage statistics and does not track you across sites. We aim to avoid non-essential tracking cookies. Where any non-essential cookie is used, we will present a consent choice as required in your region. `[Confirm final cookie inventory and whether a consent banner is legally required for your audience; add cookie table if any non-essential cookies are introduced.]`

## 10. Data Retention

We keep personal data only as long as needed for the purposes above or as required by law. Specific windows for accounts, run metadata, artifacts, logs, and backups are set out in the [Data Retention Policy](./data-retention-policy.md).

## 11. Security

We use reasonable technical and organizational measures (access controls, encryption in transit, secret management, least-privilege) to protect personal data. No method is perfectly secure. We will notify affected users and regulators of a personal-data breach where required by law. `[Confirm at-rest encryption and breach-notification process with counsel.]`

## 12. Children

The Service is not directed to children under 16, and we do not knowingly collect their personal data.

## 13. Changes

We may update this policy; material changes will be notified by email or in-Service notice. The "Prepared/updated" date reflects the latest version.

## 14. Contact

Privacy questions or requests: `[PLACEHOLDER: privacy contact email]` · scout.chowmes.com

---
*End of draft. Attorney review required before publication.*
