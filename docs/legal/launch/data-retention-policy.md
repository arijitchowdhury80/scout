# Scout Data Retention Policy

**Status: DRAFT — NOT LEGAL ADVICE. Requires attorney review AND confirmation of actual system behavior before publication. Retention windows below are PROPOSED defaults, not yet implemented — confirm each against the running system.**
**Version: Draft 0.1 · Prepared: 2026-07-26 · For: public ProductHunt beta launch**

This policy supplements the [Privacy Policy](./privacy-policy.md). It describes how long Scout keeps data and how deletion works. `[PLACEHOLDER]` windows must be confirmed against the actual implementation (RunDB / SQLite persistence, artifact storage, logs, backups) before publication.

---

## 1. Principle

We retain personal data and run data only as long as needed to provide the Service, meet legal/accounting obligations, resolve disputes, and enforce our terms — then delete or anonymize it.

## 2. Local Scout (self-hosted / CLI)

Local Scout writes run artifacts to the user's own machine (records, source pages, blocked-page evidence, screenshots/DOM when captured, validation files, logs, reports). **We do not control or retain local artifacts** — retention and deletion are entirely the user's responsibility. Users should delete local run folders when the evidence is no longer needed.

## 3. Hosted Scout (scout.chowmes.com) — Proposed Retention Schedule

| Data | Proposed retention | Notes |
|---|---|---|
| **Account data** (name, email, plan) | Life of account + `[30–90]` days after closure | Then deleted or anonymized |
| **Run metadata** (URLs, timestamps, credit usage) | `[90]` days rolling, or life of account for the current period | Confirm against RunDB behavior |
| **Run artifacts** (extracted records, source pages, screenshots, DOM, blocked evidence, reports) | `[30]` days by default, then auto-purged | Users may delete sooner via account/API `[confirm this control exists]` |
| **Application / diagnostic logs** | `[30–90]` days | Security and debugging |
| **Access logs incl. IP** | `[30–90]` days | Abuse prevention, security |
| **Billing / transaction records** | `[7]` years (or as tax/accounting law requires) | Legal obligation; held even after account closure |
| **Support correspondence** | `[24]` months | |
| **Backups** | `[7–35]` days rolling | Deleted data persists in backups until the backup cycle expires |
| **Umami analytics** | Aggregated/pseudonymous; `[retention per Umami config]` | Non-identifying |

**Note on Algolia:** Where run outputs are pushed to Algolia for search, those records persist in the Algolia index until deleted by the user or by an index lifecycle rule. `[Confirm whether Scout deletes Algolia objects when a run/artifact is deleted; if not, document that gap.]`

## 4. Deletion Rights and Process

- Users may request deletion of their account and associated hosted data by `[account control / emailing PLACEHOLDER: privacy contact]`. See the [Privacy Policy](./privacy-policy.md) Section 7 for GDPR/CCPA rights.
- On an account-deletion request, we will delete or anonymize account and run data within `[30]` days, except data we must retain by law (e.g. billing records) or that persists in time-limited backups until the backup cycle expires.
- Deletion of individual run artifacts `[confirm: is this self-service in the app/API, or manual?]`.

## 5. Beta Caveat

During beta, data, artifacts, and account state may be reset, migrated, or deleted with reasonable notice where practicable. Do not use hosted beta for irreplaceable data.

## 6. Changes

We may update this policy as the system and legal requirements evolve; material changes will be notified per the Terms.

---
*End of draft. Attorney review and system-behavior confirmation required before publication.*
