"""REAL precision + recall scoring against SEC DEF 14A complete rosters.

Unlike the Wikipedia-infobox scorer (recall-only, sparse labels), the DEF 14A
roster is COMPLETE, so both metrics are honest:
  PRECISION = |Scout ∩ roster| / |Scout|   (Scout names that ARE real officers/directors)
  RECALL    = |Scout ∩ roster| / |roster|  (roster people Scout found)
Fuzzy name match (surname + first-name prefix/exact). Reports per-company +
aggregate vs the launch bar (precision ≥90%, recall ≥80%).

CAVEATS: public companies only (private have no DEF 14A). A Scout exec who is a
real senior officer but NOT a named-executive-officer/director in the proxy (e.g.
a non-NEO VP) counts against precision — so this is a STRICT precision floor.

Usage: LLM_API_KEY=... python3 golden_sec_score.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scout.core.crawler import ScoutCrawler  # noqa: E402
from scout.core.enrich.reconcile import same_name as _match  # noqa: E402
from scout.core.platform.types import RunRequest  # noqa: E402
from scout.core.use_cases.runners.company import run_company  # noqa: E402

HERE = Path(__file__).parent


def _load_key() -> str:
    import os

    if os.environ.get("LLM_API_KEY"):
        return os.environ["LLM_API_KEY"]
    for line in (ROOT / ".env.local").read_text().splitlines():
        if line.startswith("LLM_API_KEY="):
            return line.split("=", 1)[1].strip()
    return ""


def _domain_for(company: str) -> str:
    for line in (HERE / "domains_seed.tsv").read_text().splitlines():
        if "\t" in line and line.split("\t", 1)[0].strip() == company:
            return line.split("\t", 1)[1].strip()
    return ""


async def score_one(entry: dict, key: str) -> dict:
    company = entry["company"]
    url = _domain_for(company) or ("https://" + company.lower().replace(" ", "") + ".com")
    if not url.startswith("http"):
        url = "https://" + url
    crawler = ScoutCrawler(llm_api_key=key, enrichment_enabled=True)
    records = await run_company(RunRequest(use_case="company", query=company, url=url, mode="auto"), crawler)
    scout = [r["name"] for r in records if r.get("record_type") == "executive"]
    # EXECUTIVE-TEAM-ONLY scope (founder decision 2026-07-28): score against the
    # exec-officer roster, and treat OUTSIDE directors separately. A Scout name
    # that is an outside director is neither a true-positive nor a false-positive
    # for the exec metric (it's out of scope), so it's excluded from precision.
    exec_roster = [p["name"] for p in entry["true_execs"] if p.get("role_type") != "director"]
    dir_roster = [p["name"] for p in entry["true_execs"] if p.get("role_type") == "director"]

    tp = [s for s in scout if any(_match(s, r) for r in exec_roster)]
    is_dir = [s for s in scout if s not in tp and any(_match(s, r) for r in dir_roster)]
    fp = [s for s in scout if s not in tp and s not in is_dir]  # genuinely unexplained
    recalled = [r for r in exec_roster if any(_match(r, s) for s in scout)]
    scored = len(tp) + len(fp)  # exclude out-of-scope directors from precision denom
    precision = len(tp) / scored if scored else 0.0
    recall = len(recalled) / len(exec_roster) if exec_roster else 0.0
    return {
        "company": company,
        "roster_size": len(exec_roster),
        "scout_size": len(scout),
        "precision": precision,
        "recall": recall,
        "false_positives": fp,
        "returned_directors": len(is_dir),
        "missed": [r for r in exec_roster if r not in recalled],
    }


async def main() -> None:
    key = _load_key()
    golden = json.loads((HERE / "golden_sec.json").read_text())
    labeled = [g for g in golden if g.get("status") == "labeled" and g["true_execs"]]
    print(f"Scoring {len(labeled)} public companies with DEF 14A rosters\n", flush=True)
    sem = asyncio.Semaphore(4)

    async def run(e):
        async with sem:
            try:
                r = await score_one(e, key)
            except Exception as exc:  # noqa: BLE001
                return {"company": e["company"], "error": str(exc)[:100], "precision": 0, "recall": 0}
            print(f"  {r['company']:<16} P {r['precision']*100:3.0f}%  R {r['recall']*100:3.0f}%  "
                  f"(scout {r['scout_size']}, exec-roster {r['roster_size']}, "
                  f"{len(r['false_positives'])} FP, {r.get('returned_directors', 0)} dir)",
                  flush=True)
            return r

    results = await asyncio.gather(*[run(e) for e in labeled])
    (HERE / "golden_sec_score_result.json").write_text(json.dumps(results, indent=2))
    ok = [r for r in results if "error" not in r]
    macro_p = sum(r["precision"] for r in ok) / len(ok) if ok else 0
    macro_r = sum(r["recall"] for r in ok) / len(ok) if ok else 0
    print("\n" + "=" * 66)
    print("SEC DEF 14A GOLDEN SCORE — EXECUTIVE-TEAM scope (outside directors excluded)")
    print(f"  companies         : {len(ok)}")
    print(f"  PRECISION (macro) : {macro_p*100:.0f}%   [bar >=90%]")
    print(f"  RECALL    (macro) : {macro_r*100:.0f}%   [bar >=80%]")
    print(f"  verdict           : {'PASS' if macro_p>=0.9 and macro_r>=0.8 else 'BELOW BAR'}")
    print("  scope: precision denom excludes Scout-returned OUTSIDE directors (out of")
    print("         scope, not errors); recall is over the exec-officer roster only.")
    print("=" * 66)


if __name__ == "__main__":
    asyncio.run(main())
