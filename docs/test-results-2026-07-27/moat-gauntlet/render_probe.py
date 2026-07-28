"""GATE 1 render probe — does the intelligence render surface exec content the
bare render misses?

For each labeled company, fetch its leadership page (or homepage if none) twice:
  BARE  = the old Scout profile (use_js only)
  MOAT  = scan_full_page + delay_before_return_html + block_images (the fix)
and report, for each: markdown word count, and whether each known exec surname
appears in the rendered markdown. Success = MOAT surfaces surnames BARE missed
(or matches on server-rendered controls) without regressing content.

Run:  python3 docs/test-results-2026-07-27/moat-gauntlet/render_probe.py
Needs network. Prints a table + a machine-readable JSON blob at the end.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Import Scout from the repo without installing.
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scout.core.modes.scrape import scrape  # noqa: E402
from scout.core.types import ScoutFormats, ScrapeRequest  # noqa: E402

HERE = Path(__file__).parent
GAUNTLET = json.loads((HERE / "gauntlet.json").read_text())


def bare_request(url: str) -> ScrapeRequest:
    return ScrapeRequest(
        url=url,
        formats=[ScoutFormats.MARKDOWN, ScoutFormats.RAW_HTML],
        use_js=True,
        timeout_ms=45000,
        respect_robots_txt=False,  # probe: measure raw render capability
    )


def moat_request(url: str) -> ScrapeRequest:
    return ScrapeRequest(
        url=url,
        formats=[ScoutFormats.MARKDOWN, ScoutFormats.RAW_HTML],
        use_js=True,
        scan_full_page=True,
        wait_until="domcontentloaded",
        delay_before_return_html=2.5,
        block_images=True,
        timeout_ms=45000,
        respect_robots_txt=False,
    )


def surname_hits(text: str, surnames: list[str]) -> dict[str, bool]:
    low = text.lower()
    return {s: (s.lower() in low) for s in surnames}


async def probe_company(c: dict) -> dict:
    url = c.get("leadership_url") or c["homepage"]
    surnames = c.get("known_exec_surnames", [])
    out: dict = {"name": c["name"], "url": url, "regime": c["regime"], "surnames": surnames}
    for label, reqfn in (("bare", bare_request), ("moat", moat_request)):
        try:
            resp = await scrape(reqfn(url))
        except Exception as exc:  # noqa: BLE001
            out[label] = {"error": str(exc)}
            continue
        md = resp.markdown or ""
        html = resp.raw_html or ""
        out[label] = {
            "success": resp.success,
            "status": resp.status_code,
            "md_words": len(md.split()),
            "hits_md": surname_hits(md, surnames),
            "hits_html": surname_hits(html, surnames),
            "error": resp.error,
        }
    return out


async def main() -> None:
    results = []
    for c in GAUNTLET["companies"]:
        print(f"... probing {c['name']} ({c['regime']}) {c.get('leadership_url') or c['homepage']}",
              flush=True)
        results.append(await probe_company(c))

    print("\n" + "=" * 92)
    print(f"{'COMPANY':<12}{'REGIME':<9}{'BARE words':<12}{'MOAT words':<12}{'BARE hits':<12}{'MOAT hits'}")
    print("-" * 92)
    for r in results:
        bare = r.get("bare", {})
        moat = r.get("moat", {})

        def hitcount(d: dict) -> str:
            hm = d.get("hits_md", {}) or {}
            hh = d.get("hits_html", {}) or {}
            found = sum(1 for s in r["surnames"] if hm.get(s) or hh.get(s))
            return f"{found}/{len(r['surnames'])}"

        print(f"{r['name']:<12}{r['regime']:<9}"
              f"{str(bare.get('md_words', bare.get('error', '?'))):<12}"
              f"{str(moat.get('md_words', moat.get('error', '?'))):<12}"
              f"{hitcount(bare):<12}{hitcount(moat)}")
    print("=" * 92)
    (HERE / "render_probe_result.json").write_text(json.dumps(results, indent=2))
    print(f"\nWrote {HERE / 'render_probe_result.json'}")


if __name__ == "__main__":
    asyncio.run(main())
