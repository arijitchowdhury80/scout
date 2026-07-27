# Scout Third-Party Licenses Note

**Status: DRAFT — informational. Confirm against the shipped `THIRD_PARTY_NOTICES.md` and the dependency license inventory before publication.**
**Version: Draft 0.1 · Prepared: 2026-07-26**

---

## 1. Scout's License Posture

- **Scout core** is licensed under the **Apache License 2.0**. A root `LICENSE` file and `pyproject.toml` license metadata are in place.
- The **hosted service** (scout.chowmes.com) is offered as a separate commercial/service surface under the [Terms of Service](./terms-of-service.md); the open-source license governs the core software, the Terms govern the hosted service.
- All third-party dependencies are under **permissive licenses** (MIT / BSD / Apache-2.0 / Unlicense). **No copyleft (GPL/AGPL/LGPL) dependencies** are present per the dependency license inventory (`docs/legal/dependency-license-inventory-2026-06-28.md`). `[Confirm still true after any dependency bumps before launch — re-run the inventory.]`

## 2. Crawl4AI Attribution

Scout is **built on Crawl4AI**, which is licensed under the **Apache License 2.0**. Apache-2.0 requires that we:

- retain the copyright, license, and NOTICE text of Crawl4AI in our distribution;
- state prominently that Scout uses Crawl4AI; and
- preserve attribution notices.

**Attribution line (use on the website, README, and app About/Settings):**
> "Scout is built on [Crawl4AI](https://github.com/unclecode/crawl4ai), © the Crawl4AI authors, licensed under the Apache License 2.0."

Checklist:
- [x] Crawl4AI attribution in README and website.
- [ ] Crawl4AI attribution in app Settings/About (required now that the app UI is a launch surface).
- [x] `THIRD_PARTY_NOTICES.md` included in source.
- [ ] Confirm `THIRD_PARTY_NOTICES.md` ships in all final package artifacts before public publishing.

## 3. Playwright / Chromium Notice

Scout bundles / depends on **Playwright**, which downloads and runs **Chromium** (and potentially other browser binaries) for browser-assisted acquisition. These carry their own licenses and notices distinct from Scout's:

- **Playwright** — Apache License 2.0 (© Microsoft).
- **Chromium** — a BSD-style license plus a large set of third-party component licenses (LGPL, MPL, and others) shipped in Chromium's own `LICENSE`/credits. Because Chromium is a bundled binary, its notices must be reproduced or referenced, not omitted.

**Required notice line (add to `THIRD_PARTY_NOTICES.md` and the app About page):**
> "Scout uses Playwright (Apache-2.0, © Microsoft) and downloads Chromium, which is distributed under its own license and includes third-party components under their respective licenses. See Chromium's bundled license/credits for details."

Action: `[OPEN TASK]` complete the Playwright/Chromium third-party notice entry in `THIRD_PARTY_NOTICES.md`, including a pointer to Chromium's `about:credits` / bundled license file, before public launch. This closes the open third-party-notice task.

## 4. Where Notices Live

- Source: `THIRD_PARTY_NOTICES.md` (repo root) + `LICENSE`.
- Inventory: `docs/legal/dependency-license-inventory-2026-06-28.md` (re-run before launch).
- User-facing: website footer/legal page + app About/Settings.

---
*End of draft. Confirm against shipped notices before publication.*
