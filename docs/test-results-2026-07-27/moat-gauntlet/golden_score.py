"""Score Scout's exec extraction against the bootstrap golden set.

Runs the REAL company runner per labeled company and compares to the Wikipedia-
infobox key_people labels.

METRICS (and their honest limits):
- key_person RECALL: of the Wikipedia-listed key people, what % did Scout
  return (fuzzy name match)? CLEAN and defensible — the important number.
- PRECISION is NOT cleanly measurable here: the label set is INCOMPLETE (only a
  few "key people"), so a Scout name not in the labels may be a real additional
  exec, not an error. We therefore report confirmed vs. unconfirmed-extra counts
  (unconfirmed = needs review), NOT a precision percentage that would be a lie.
  True precision needs a complete roster or a trap-name set (next iteration).

Usage: LLM_API_KEY=... python3 golden_score.py
"""

from __future__ import annotations

import asyncio
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scout.core.crawler import ScoutCrawler  # noqa: E402
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


def _norm(name: str) -> list[str]:
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    n = "".join(c if c.isalnum() or c.isspace() else " " for c in n).lower()
    return [t for t in n.split() if len(t) > 1]


def _match(a: str, b: str) -> bool:
    """Same person if surnames match and first name (or initial) agrees."""
    ta, tb = _norm(a), _norm(b)
    if not ta or not tb or ta[-1] != tb[-1]:
        return False
    return ta[0] == tb[0] or ta[0][0] == tb[0][0]


async def score_one(entry: dict, key: str) -> dict:
    crawler = ScoutCrawler(llm_api_key=key, enrichment_enabled=True)
    records = await run_company(
        RunRequest(use_case="company", query=entry["company"], url="https://" + entry["domain"], mode="auto"),
        crawler,
    )
    scout = [r["name"] for r in records if r.get("record_type") == "executive"]
    golden = [p["name"] for p in entry["true_execs"]]
    recalled = [g for g in golden if any(_match(g, s) for s in scout)]
    confirmed = [s for s in scout if any(_match(s, g) for g in golden)]
    unconfirmed = [s for s in scout if s not in confirmed]
    return {
        "company": entry["company"],
        "golden": golden,
        "scout": scout,
        "recalled": recalled,
        "recall": len(recalled) / len(golden) if golden else 0.0,
        "confirmed": len(confirmed),
        "unconfirmed_extra": unconfirmed,
    }


async def main() -> None:
    key = _load_key()
    golden = json.loads((HERE / "golden.json").read_text())
    labeled = [g for g in golden if g.get("status") == "labeled"]
    print(f"Scoring {len(labeled)} labeled companies (of {len(golden)})\n", flush=True)
    results = []
    sem = asyncio.Semaphore(5)

    async def run(e):
        async with sem:
            try:
                r = await score_one(e, key)
            except Exception as exc:  # noqa: BLE001
                r = {"company": e["company"], "error": str(exc)[:120], "recall": 0.0, "golden": e["true_execs"]}
            print(
                f"  {r['company']:<16} recall {r.get('recall',0)*100:3.0f}%  "
                f"({len(r.get('recalled',[]))}/{len(r.get('golden',[]))})  "
                f"+{len(r.get('unconfirmed_extra',[]))} extra",
                flush=True,
            )
            return r

    results = await asyncio.gather(*[run(e) for e in labeled])
    (HERE / "golden_score_result.json").write_text(json.dumps(results, indent=2))

    total_golden = sum(len(r.get("golden", [])) for r in results)
    total_recalled = sum(len(r.get("recalled", [])) for r in results)
    total_extra = sum(len(r.get("unconfirmed_extra", [])) for r in results)
    total_conf = sum(r.get("confirmed", 0) for r in results)
    macro = sum(r.get("recall", 0) for r in results) / len(results) if results else 0
    print("\n" + "=" * 66)
    print("GOLDEN-SET SCORE (bootstrap labels: Wikipedia infobox key_people)")
    print(f"  companies scored     : {len(results)}")
    print(f"  key-person RECALL    : micro {100*total_recalled/total_golden:.0f}% "
          f"({total_recalled}/{total_golden})  |  macro {100*macro:.0f}%")
    print(f"  golden-confirmed execs: {total_conf}")
    print(f"  unconfirmed extras    : {total_extra}  (real additional execs OR false positives — review)")
    print("  NOTE: precision not scored — labels are key-people only (incomplete).")
    print("=" * 66)


if __name__ == "__main__":
    asyncio.run(main())
