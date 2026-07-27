# Scout Acceptable Use Policy (AUP)

**Status: DRAFT — NOT LEGAL ADVICE. Requires attorney review before publication. This is the single most important legal shield for a crawler product; review it carefully with counsel familiar with the CFAA, DMCA, and web-scraping case law.**
**Version: Draft 0.1 · Prepared: 2026-07-26 · For: public ProductHunt beta launch**

This Acceptable Use Policy is incorporated into and part of the [Terms of Service](./terms-of-service.md). Capitalized terms have the meanings given there. Violating this AUP is a material breach and grounds for immediate suspension or termination.

---

## 1. The Core Rule: You Are Responsible for Lawful Use

Scout is a **neutral, general-purpose crawling tool that acts only at your direction.** You choose the targets, the configuration, and the purpose. **You — not Scout — are solely responsible for ensuring that every crawl you run, and every use you make of the data returned, is lawful and complies with:**

1. all applicable laws and regulations (including computer-access laws such as the U.S. Computer Fraud and Abuse Act (CFAA) and equivalents, copyright and database-rights law, contract law, consumer-protection law, and data-protection law such as the GDPR and CCPA/CPRA);
2. the target website's Terms of Service / Terms of Use and other posted conditions;
3. the target website's technical access controls, including `robots.txt`, rate limiting, and anti-automation measures (see the [Robots & Crawl Ethics policy](./robots-and-crawl-ethics.md)); and
4. the intellectual-property, privacy, and other rights of third parties.

If you are unsure whether a use is permitted, obtain your own legal advice before running it. Scout provides no legal advice and makes no representation that any particular crawl or downstream use is lawful.

## 2. Prohibited Uses

You must **not** use Scout to:

**Access-boundary violations**
- Access, or attempt to access, content behind a **login wall, paywall, or other authentication/authorization barrier** that you are not authorized to bypass, or circumvent access controls in violation of a site's terms or applicable law. This includes credentialed social networks and private account pages.
- **Evade, defeat, or circumvent bot-detection, CAPTCHAs, rate limits, IP blocks, or other anti-automation measures** except within limits the target expressly permits. Scout does not promise to bypass such measures, and you must not attempt to use it to do so unlawfully.
- Access a site in a manner that violates that site's Terms of Service or robots directives.

**Data-type restrictions**
- **Enrich, compile, aggregate, or build profiles of identifiable individuals** from personal data (e.g. scraping personal contact details to build marketing or people-search databases) without a valid lawful basis and all required notices/consents.
- Collect or process **regulated or special-category data** — including health/medical data, biometric data, precise geolocation, children's data, financial-account data, government IDs, or data subject to sector rules (HIPAA, GLBA, FERPA, PCI, etc.) — without independent legal review and the required safeguards.
- Scrape data in violation of the GDPR, CCPA/CPRA, or any other data-protection law.

**Content / IP violations**
- Infringe copyright, database rights, trademark, or other intellectual-property rights, including systematically copying or redistributing a site's protected content.

**Abuse / harm**
- Send spam, or build lists for spam, unlawful bulk email/SMS, or other unsolicited communications.
- Automate account creation, credential stuffing, job auto-apply, form spam, ticket/inventory scalping, or other automated abuse of a target site.
- Launch denial-of-service, excessive-load, or otherwise disruptive request patterns against any target.
- Distribute malware, or use Scout to facilitate fraud, harassment, stalking, discrimination, or any illegal activity.
- Interfere with, overload, or attempt to gain unauthorized access to the Scout Service or other users' data.

**Restricted-without-review use cases.** The following commonly raise legal risk and are **prohibited unless you have obtained separate legal review and can demonstrate a lawful basis**: crawling login-walled or credentialed pages; personal-data enrichment; scraping large social networks against their terms; job auto-apply workflows; and collecting regulated data.

## 3. Respect for Target Sites

You must operate within reasonable, good-faith crawling norms: honor `robots.txt` and posted crawl policies, use conservative rates, identify traffic honestly where required, and stop crawling a site that asks you to. See the [Robots & Crawl Ethics policy](./robots-and-crawl-ethics.md).

## 4. No Secrets or Sensitive Credentials in Scout

Do not submit passwords, API keys, private keys, tokens, or other secrets — or regulated personal data — into Scout runs, prompts, or configuration in a way that stores them in run artifacts. Keep your own credentials in a secret manager, never in public prompts, repos, or screenshots.

## 5. Enforcement and Suspension

We may investigate suspected violations and cooperate with law enforcement. We may, **at our sole discretion and without liability**, throttle, suspend, or terminate access, remove content or artifacts, or refuse service, for any actual or suspected violation of this AUP or applicable law, or to protect the Service, its users, or third parties. Where practicable and lawful we will give notice, but we may act immediately for serious or ongoing harm.

## 6. DMCA and Abuse / Takedown Contact

If you believe content processed through the Service infringes your copyright, or you are the operator of a site and wish to report abuse originating from the Service, contact our designated agent:

- **Abuse / DMCA contact:** `[PLACEHOLDER: abuse@ / dmca@ email address]`
- `[PLACEHOLDER: designated DMCA agent name and physical address — required for DMCA safe-harbor; counsel to confirm agent registration with the U.S. Copyright Office if the operator seeks safe-harbor protection.]`

A valid DMCA notice should include: identification of the copyrighted work, identification of the material and its location, your contact details, a good-faith-belief statement, an accuracy/authority statement under penalty of perjury, and your signature. We will respond to valid notices, including by removing or disabling access to identified artifacts and, where appropriate, terminating repeat infringers.

## 7. Changes

We may update this AUP as legal understanding of crawling evolves. Material changes will be notified as described in the Terms.

## 8. Contact

`[PLACEHOLDER: contact/abuse email]` · scout.chowmes.com

---
*End of draft. Attorney review required before publication.*
