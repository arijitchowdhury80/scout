"""LIVE exec gauntlet — run the real company runner (with LLM adjudication) end
to end and score CLEAN, not just non-empty.

For each labeled company: run_company() with a funded LLM key, then report the
executives returned and score:
  RECALL  = fraction of known_exec_surnames present in the returned names.
  CLEAN   = no obviously-foreign name (a heuristic flag list of other-company
            CEOs from the prior failure) leaked in.

Run:  LLM_API_KEY=... python3 docs/test-results-2026-07-27/moat-gauntlet/exec_gauntlet.py
Needs network + a funded Anthropic key (LLM_API_KEY in env or .env.local).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scout.core.crawler import ScoutCrawler  # noqa: E402
from scout.core.platform.types import RunRequest  # noqa: E402
from scout.core.use_cases.runners.company import run_company  # noqa: E402

HERE = Path(__file__).parent
GAUNTLET = json.loads((HERE / "gauntlet.json").read_text())

# Names that, if returned, prove a cross-company leak (the exact prior failures
# + a few well-known foreign CEOs). Purely a red-flag detector for CLEAN.
FOREIGN_LEAK = [
    "dolan",  # Lightspeed CEO (Stripe failure)
    "ittycheria",  # MongoDB CEO (Datadog failure)
    "cook",  # Apple
    "nadella",  # Microsoft
    "benioff",  # Salesforce
]


def _load_key() -> str:
    key = os.environ.get("LLM_API_KEY", "")
    if key:
        return key
    envf = ROOT / ".env.local"
    if envf.exists():
        for line in envf.read_text().splitlines():
            if line.startswith("LLM_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


async def run_one(company: dict, key: str) -> dict:
    req = RunRequest(
        use_case="company",
        query=company["name"],
        url=company["homepage"],
        mode="auto",
    )
    crawler = ScoutCrawler(llm_api_key=key, llm_extraction_fallback_enabled=True)
    records = await run_company(req, crawler)
    execs = [r for r in records if r.get("record_type") == "executive"]
    names = [f"{r['name']} — {r.get('title', '')}".strip(" —") for r in execs]
    joined = " ".join(names).lower()
    surnames = company.get("known_exec_surnames", [])
    recall_hits = [s for s in surnames if s.lower() in joined]
    leaks = [f for f in FOREIGN_LEAK if f in joined]
    return {
        "name": company["name"],
        "regime": company["regime"],
        "exec_count": len(execs),
        "names": names,
        "recall": f"{len(recall_hits)}/{len(surnames)}",
        "recall_hits": recall_hits,
        "leaks": leaks,
        "clean": not leaks,
    }


async def main() -> None:
    key = _load_key()
    if not key:
        print("NO LLM_API_KEY — cannot run adjudicated gauntlet.")
        sys.exit(1)
    print(f"key: {key[:12]}...  running {len(GAUNTLET['companies'])} companies\n")
    results = []
    for c in GAUNTLET["companies"]:
        print(f"... {c['name']} ({c['regime']})", flush=True)
        try:
            results.append(await run_one(c, key))
        except Exception as exc:  # noqa: BLE001
            results.append({"name": c["name"], "regime": c["regime"], "error": str(exc)})

    print("\n" + "=" * 96)
    print(f"{'COMPANY':<12}{'REGIME':<9}{'#EXEC':<7}{'RECALL':<9}{'CLEAN':<7}NAMES / LEAKS")
    print("-" * 96)
    for r in results:
        if "error" in r:
            print(f"{r['name']:<12}{r['regime']:<9}ERROR: {r['error'][:60]}")
            continue
        flag = "LEAK:" + ",".join(r["leaks"]) if r["leaks"] else "ok"
        preview = "; ".join(r["names"][:4]) + (" ..." if len(r["names"]) > 4 else "")
        print(f"{r['name']:<12}{r['regime']:<9}{r['exec_count']:<7}{r['recall']:<9}"
              f"{('YES' if r['clean'] else 'NO'):<7}{flag} | {preview}")
    print("=" * 96)
    (HERE / "exec_gauntlet_result.json").write_text(json.dumps(results, indent=2))
    clean = sum(1 for r in results if r.get("clean"))
    print(f"\nCLEAN: {clean}/{len(results)}   Wrote exec_gauntlet_result.json")


if __name__ == "__main__":
    asyncio.run(main())
