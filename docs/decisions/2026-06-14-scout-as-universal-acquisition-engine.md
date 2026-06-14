# ADR: Scout is a standalone, universal acquisition engine (not a product, not folded into PRISM)

- **Date:** 2026-06-14
- **Status:** Accepted. Supersedes the standalone-intelligence-app direction; refines 2026-06-12 (scope boundary), 2026-06-13 (ICP/use-case set), and the earlier "fold into PRISM" framing.

## Decision

Scout is **the portfolio-wide muscle for getting data off any website** — a standalone, embeddable engine that many applications consume. It is:
- **NOT** a standalone intelligence product (no company/investor/careers dossiers, no audit console).
- **NOT** folded into PRISM. PRISM is its *first consumer*, not its owner.

### Packaging — library + service (both)
- **`scout.core`** — importable Python library: in-process, zero-overhead (this is how PRISM uses it today via `from scout.core import ScoutCrawler`).
- **Scout service** — long-running HTTP API + MCP server for out-of-process, non-Python, and agent consumers. Justified because the embedded browser holds **stateful sessions** (logins, cookies, an open page) that can't live in a stateless library call.
- Own repository. **Hard boundary rule:** consumers depend on Scout; `scout.core` never imports any consumer. This is what keeps Scout reusable and independently shippable.

### What the engine is (the strong proposition)
crawl4ai-backed multi-tier crawling + **LLM-ready markdown** + structured extraction + screenshots + provenance on every record, behind a single **unblock ladder**:
`crawler → stealth headless → embedded live browser (CDP) → the user's own real browser`.

### Consumers — now and designed-for
- **PRISM** — intelligence modules call Scout for fetch (Track-1); `audit-browser` uses the embedded browser to test search on WAF-protected sites.
- **Claude / agents** — via the MCP service.
- **Future apps** (explicit design targets, not commitments): CurioQuest (crawl state education standards/curricula), a real-estate app (Zillow/Redfin/NMLS property pages where no API exists), a job-application app (open + fill applications via the real-browser rung), LENS (LinkedIn pages browsed/captured as the user).

## Consequences
- The intelligence **verticals** (company, careers, investor, news, …) are **not Scout features** — they are *consumer* specs (PRISM modules) that call Scout. The Phase-B vertical specs are re-designated consumer-side specs.
- The standalone Scout **intelligence console** is retired. Scout keeps a thin operator UI for running/inspecting crawls and the products→Algolia tool; its reason to exist is the engine, not an app.
- **The make-or-break risk is now explicit and central:** the real-world reliability of the unblock ladder. No further dependent build is committed until block rates are **measured** (see plan).

## "Certainty" — redefined honestly
100% unblock against modern anti-bot (Akamai, Cloudflare, PerimeterX/HUMAN, DataDome, Kasada, Imperva) is **not achievable by anyone** — it is a permanent adversarial arms race. Scout does not promise certainty of *success*. Scout promises:
1. **Certainty of truth** — honest degradation: every run reports what it retrieved, via which ladder rung, or that it was blocked, with evidence. Never silent, never fabricated.
2. **Maximized laddered success** — try cheap→expensive rungs in order.
3. **Human-in-the-loop backstop** — the top rung is the user's own real, logged-in browser, which is the one path that genuinely defeats most blocks because it *is* a real human session.
4. **Known, measured success rates per site-class** — so consumers can trust and route accordingly.

Legal/ToS posture (LinkedIn capture, job auto-apply, property sites) is part of "solving with certainty" and must be decided per consumer, not assumed.
