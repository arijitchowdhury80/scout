# Scout Legal Gap Report — Public Beta Launch

**Prepared: 2026-07-26 · By: non-lawyer (Claude) for attorney review · Status: DRAFT**

This report maps the gap between the current placeholder legal posture and a launch-ready one for Scout's public ProductHunt beta. Each item is tagged:

- **[Beta]** — should be closed (at least in draft form) before the public beta goes live.
- **[GA]** — can be deferred to general availability / commercial scale, but should be tracked.

Severity: 🔴 high · 🟠 medium · 🟢 low.

---

## A. Where We Are Now

- Live ToS/Privacy on the site are **explicit placeholders** ("not final, not lawyer-reviewed"): `website/terms.html`, `website/privacy.html`; drafts in `docs/legal/beta-terms-placeholder.md`, `beta-privacy-placeholder.md`.
- License posture is solid: Scout Apache-2.0, Crawl4AI Apache-2.0, all deps permissive, no copyleft.
- **No** finalized ToS, Privacy Policy, AUP, retention policy, or robots policy.
- **robots.txt is NOT enforced** in the crawl path by default.
- **No** marketing-site `robots.txt`.
- Playwright/Chromium third-party notice task is **open**.
- No GDPR/CCPA data-subject request process, no defined retention windows, no DPA template.

New launch drafts created in this folder: `terms-of-service.md`, `privacy-policy.md`, `acceptable-use-policy.md`, `robots-and-crawl-ethics.md`, `data-retention-policy.md`, `website/robots.txt`, `third-party-licenses-note.md`.

---

## B. Gaps by Area

### 1. Terms of Service
| Gap | Tag | Sev | Status |
|---|---|---|---|
| Placeholder only; no binding SaaS ToS | [Beta] | 🔴 | Draft written — needs lawyer sign-off |
| Legal entity name not stated | [Beta] | 🔴 | `[PLACEHOLDER]` — who contracts with users? Sole prop vs LLC affects liability |
| Governing law / venue / dispute resolution undefined | [Beta] | 🟠 | `[PLACEHOLDER]` — counsel to select |
| Limitation-of-liability + indemnity not yet legally reviewed | [Beta] | 🔴 | Drafted; these are the core shields, must be lawyer-checked |
| Refund terms vs consumer law (EU/UK withdrawal rights) | [Beta] | 🟠 | Drafted conservatively; confirm |
| Arbitration / class-action waiver decision | [GA] | 🟢 | Optional; counsel call |

### 2. Privacy Policy
| Gap | Tag | Sev | Status |
|---|---|---|---|
| Placeholder only; no GDPR/CCPA-aware policy | [Beta] | 🔴 | Draft written |
| Lawful bases not previously documented | [Beta] | 🟠 | Drafted (contract/legit-interest/consent) |
| Sub-processor list + DPAs/SCCs not confirmed (Stripe, Resend, Algolia, VPS host) | [Beta] | 🔴 | Listed; **must confirm DPA + transfer mechanism per processor** |
| International-transfer mechanism (SCCs/DPF) undocumented | [Beta] | 🟠 | Drafted as placeholder |
| Data-subject request process (access/delete/opt-out) not implemented | [Beta] | 🔴 | Policy drafted; **operational process + contact inbox needed** |
| Controller/processor split for crawled content + DPA template for customers | [GA] | 🟠 | Explained in policy; DPA template deferred |
| EU/UK representative or DPO — is one required? | [GA] | 🟢 | Counsel to assess based on EU user volume |
| Breach-notification process | [Beta] | 🟠 | Referenced; confirm runbook |

### 3. Acceptable Use Policy (the key crawler shield)
| Gap | Tag | Sev | Status |
|---|---|---|---|
| No standalone AUP existed | [Beta] | 🔴 | Draft written — **most important shield** |
| Prohibited-use list (login-wall/paywall bypass, PII enrichment, regulated data, spam, bot-evasion, ToS/robots violations) | [Beta] | 🔴 | Drafted |
| DMCA designated agent not registered | [Beta] | 🟠 | `[PLACEHOLDER]` — register agent with US Copyright Office for safe harbor |
| Repeat-infringer / suspension policy | [Beta] | 🟢 | Drafted |

### 4. Robots.txt Enforcement & Crawl Ethics
| Gap | Tag | Sev | Status |
|---|---|---|---|
| **robots.txt NOT enforced by default in crawl path** | [Beta] | 🔴 | **Engineering gap.** Policy claims default respect — either implement it or rewrite policy to match reality. Publishing a policy that misstates behavior is itself a legal risk (misrepresentation) |
| Default UA string / Scout identification | [Beta] | 🟠 | Confirm and document |
| Rate-limit defaults documented | [Beta] | 🟢 | Referenced |
| Override controls (owned/permissioned sites only) | [Beta] | 🟠 | Policy drafted; confirm UI/config matches |

### 5. Data Retention
| Gap | Tag | Sev | Status |
|---|---|---|---|
| No retention/deletion windows defined | [Beta] | 🟠 | Draft with proposed windows — **confirm against RunDB/artifact/log/backup behavior** |
| Self-service artifact/account deletion | [Beta] | 🟠 | Confirm whether it exists; build if not |
| Algolia object deletion on run delete | [GA] | 🟢 | Confirm behavior |

### 6. Open-Source / Third-Party Notices
| Gap | Tag | Sev | Status |
|---|---|---|---|
| Playwright/Chromium notice line | [Beta] | 🟠 | **Open task** — add to `THIRD_PARTY_NOTICES.md` + app About |
| Crawl4AI attribution in app Settings/About | [Beta] | 🟢 | README/site done; app UI pending |
| Re-run dependency inventory after any version bumps | [Beta] | 🟢 | Inventory from 2026-06-28; re-verify |
| Confirm `THIRD_PARTY_NOTICES.md` ships in all artifacts | [Beta] | 🟢 | |

### 7. Marketing Site
| Gap | Tag | Sev | Status |
|---|---|---|---|
| No `robots.txt` for the marketing site | [Beta] | 🟢 | Draft provided in `website/robots.txt` |
| "Not legal advice" notice on legal pages | [Beta] | 🟢 | Present in placeholders; carry into finals |
| Avoid "bypass bot protection" marketing language | [Beta] | 🟠 | Audit site/app copy before launch |

### 8. Corporate / Structural
| Gap | Tag | Sev | Status |
|---|---|---|---|
| Operating entity (LLC vs sole proprietorship) | [Beta] | 🔴 | Affects personal liability for a scraping product — discuss with counsel/accountant |
| Business insurance (tech E&O / cyber) | [GA] | 🟠 | Consider before scaling revenue |

---

## C. Minimum Set to Close Before Public Beta (recommended)

1. 🔴 Lawyer-reviewed **ToS + Privacy + AUP** published (replace placeholders).
2. 🔴 Decide/name the **operating entity** and governing law.
3. 🔴 **Align robots.txt behavior with the policy** (enforce by default, or rewrite the policy and put responsibility explicitly on the user).
4. 🔴 Stand up a **privacy/DSAR + abuse/DMCA inbox** and process.
5. 🟠 Confirm **sub-processor DPAs/SCCs**; publish sub-processor list.
6. 🟠 Complete **Playwright/Chromium notice** + app-About attribution.
7. 🟠 Confirm **retention windows** against the real system and publish.
8. 🟢 Ship the marketing-site **robots.txt**.

Everything tagged [GA] can follow once revenue and EU volume justify it.

---
*This is a non-lawyer's gap analysis to scope the lawyer engagement. Not legal advice.*
