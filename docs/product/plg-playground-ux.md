# Scout PLG Playground + Destinations UX (decisions), 2026-07-06

**Base design language:** Direction E (demo-first console) + Scout amber accent + one tactile "inset
well" signature (the single good idea borrowed from neumorphism, used ONLY on the playground input +
record output). Chosen for PLG: the homepage *is* the product, proving evidence-grade output live.
Reference systems on file (not adopted): Poster Modernist, Neumorphism.

## PLG funnel (three tiers)
| Tier | Where | Endpoints | Output | Save/Download |
|---|---|---|---|---|
| **Anonymous (taste)** | Homepage console | **fast only**: scrape, map | Preview + evidence panel, truncated | none — "sign up to save/download" |
| **Free (10k credits)** | Authed app playground | all endpoints | full tabs (Preview/Table/JSON/JSONL/MD/cURL) | download + save to run history |
| **Paid** | Authed app | all + higher limits + Destinations | same + scheduled/bulk | same + push to Algolia/webhook |

### Anonymous console limits (abuse + cost control)
- Fast endpoints only (scrape single URL, map). NO crawl/products/company live (10–190s + cost).
- Hard cap per IP/day (start: **5 runs/IP/day**), reuse Scout's existing rate limiter + 8-active cap.
- Output is a preview: show the record + evidence, truncate long payloads, watermark "sign up to
  unlock crawl, products, downloads, and saving."
- Block obviously abusive/again-and-again targets; keep the box safe (shared with PRISM).

## Preview / download / save (answers to the open questions)
- **Preview:** tabbed output — Preview (records → table view; page → rendered markdown), JSON, JSONL,
  Markdown, cURL — always with the evidence panel (source, hash, verified, blocked). This is the E
  hero's aside, expanded.
- **Download:** format buttons — JSON / JSONL / Markdown / CSV (CSV for product/record tables).
  Anonymous = sample/preview only; signed-in = full file.
- **Save:** signed-in runs persist to the account via RunDB + run_id (already built, Plan Phase 1).
  "Your runs" history → re-open + re-download anytime. Anonymous runs are ephemeral → "sign up to
  save this run" is the conversion hook right on the result.

## Destinations (Algolia etc.) — secondary surface, NOT the GTM homepage
Keep the public homepage clean + general for mass GTM. Integration-specific flows live **inside the
authed app**, revealed after a run:
- After a products/records run: **"Send to → Download · Algolia · Webhook."**
- **Algolia push already exists** in the backend (save_objects, Plan Phase 3). This is about WHERE the
  UX lives: a "Destinations" panel in the dashboard — connect Algolia (App ID + Admin key, stored
  server-side, never in the browser), map fields → index, push. Power-user/partner UX.
- So "give it to Algolia for a test run" has a home: the authed Destinations flow, not the homepage.
- Built to extend: Algolia today; webhook, S3, BigQuery, etc. later — same "destination" abstraction.

## Support model (decided 2026-07-06)
- **Beta/signup page: NO "Lost your API key?" reissue section** — signup page has one job. (Backend
  reissue endpoint `/v1/hosted/beta-key/reissue` STAYS — capability kept, UI dropped.)
- **Support lives in docs**: a "Support" section — "Questions, stuck, lost your key? Email
  support@scout.chowmes.com — reaches the founder directly. Include your account email; lost keys are
  reissued from support (old key disabled)."
- Support email = brand touchpoint (mirrors the key-delivery email's "reply reaches me").
- Queued as first post-build tweak (build workflow owns website/ files mid-flight).

## My criticism of E (risks this commits us to)
1. **The demo must be REAL, live, rate-limited.** A fake console overpromises. E commits us to an
   unauthenticated demo endpoint = a bot magnet → needs the IP caps above. Non-trivial.
2. **Cold traffic can bounce.** A console-first hero assumes the visitor already knows what Scout is.
   Need a crisp value headline wrapping the console so ad/tweet traffic gets WHAT + WHY in 3 seconds.
3. **Limit the live demo to fast endpoints.** Heavy crawl/products in a homepage demo = long waits +
   cost. Those live behind signup.
4. **Mobile.** A dense console is hard on small screens → graceful fallback (static example record,
   not the live console, below md breakpoint).
5. **Restraint.** A console can still read "science project" if overloaded. Keep it calm; the evidence
   record is the star.
