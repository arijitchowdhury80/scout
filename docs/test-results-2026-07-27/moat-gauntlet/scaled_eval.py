"""Scaled auto-eval harness for the exec-extraction moat.

Runs Scout's REAL company runner against an arbitrary list of company domains
concurrently and auto-scores WITHOUT hand-labels — the metrics that scale:
  - coverage   : % of domains that returned >=1 executive
  - crash rate : % that raised / errored
  - latency    : p50 / p95 seconds per company
  - cost proxy : execs returned, pages fetched (LLM-call count is ~2/company)
Captures a sample of returned names per company for offline leak/precision
spot-checks. This is the robustness + coverage instrument the moat needs to be
called production-ready; true precision/recall still needs the labeled golden
set + external cross-refs (see moat plan Pillar B).

Usage:
  python3 scaled_eval.py <domains_file> [--limit N] [--concurrency 6]
domains_file: one entry per line, "Company Name<TAB>https://domain" OR just a
domain/URL (name inferred from the host).

Writes <domains_file>.results.jsonl + prints a summary. Needs network + a funded
LLM key (LLM_API_KEY in env or .env.local) for the adjudicated path.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scout.core.crawler import ScoutCrawler  # noqa: E402
from scout.core.platform.types import RunRequest  # noqa: E402
from scout.core.use_cases.runners.company import run_company  # noqa: E402


def _load_key() -> str:
    import os

    key = os.environ.get("LLM_API_KEY", "")
    if key:
        return key
    envf = ROOT / ".env.local"
    if envf.exists():
        for line in envf.read_text().splitlines():
            if line.startswith("LLM_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


def _parse_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "\t" in line:
        name, url = line.split("\t", 1)
        name, url = name.strip(), url.strip()
    else:
        url = line
        name = ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if not name:
        host = urlparse(url).netloc.removeprefix("www.")
        name = host.split(".")[0].replace("-", " ").title()
    return name, url


async def _run_one(name: str, url: str, key: str, sem: asyncio.Semaphore) -> dict:
    async with sem:
        started = time.monotonic()
        crawler = ScoutCrawler(llm_api_key=key, llm_extraction_fallback_enabled=True)
        try:
            records = await run_company(
                RunRequest(use_case="company", query=name, url=url, mode="auto"), crawler
            )
            execs = [r for r in records if r.get("record_type") == "executive"]
            names = [f"{r.get('name', '')} — {r.get('title', '')}".strip(" —") for r in execs][:8]
            return {
                "name": name,
                "url": url,
                "ok": True,
                "exec_count": len(execs),
                "covered": len(execs) > 0,
                "sample": names,
                "latency_s": round(time.monotonic() - started, 1),
            }
        except Exception as exc:  # noqa: BLE001 - the harness measures crash rate
            return {
                "name": name,
                "url": url,
                "ok": False,
                "error": str(exc)[:200],
                "latency_s": round(time.monotonic() - started, 1),
            }


def _pct(n: int, d: int) -> str:
    return f"{(100.0 * n / d):.0f}%" if d else "n/a"


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(p * len(s)))
    return s[idx]


async def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    domains_file = Path(sys.argv[1])
    limit = None
    concurrency = 6
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        if arg == "--concurrency" and i + 1 < len(sys.argv):
            concurrency = int(sys.argv[i + 1])

    key = _load_key()
    if not key:
        print("NO LLM_API_KEY — running heuristic-only (no adjudication).")
    entries = [p for p in (_parse_line(ln) for ln in domains_file.read_text().splitlines()) if p]
    if limit:
        entries = entries[:limit]
    print(f"Running {len(entries)} companies, concurrency={concurrency}, key={'yes' if key else 'no'}\n")

    sem = asyncio.Semaphore(concurrency)
    started = time.monotonic()
    done = 0
    results: list[dict] = []

    async def _wrapped(name: str, url: str) -> dict:
        nonlocal done
        r = await _run_one(name, url, key, sem)
        done += 1
        tag = "ok " if r["ok"] else "ERR"
        cov = f"{r.get('exec_count', 0)} execs" if r["ok"] else r.get("error", "")[:50]
        print(f"[{done}/{len(entries)}] {tag} {r['name']:<22} {r['latency_s']:>5}s  {cov}", flush=True)
        return r

    results = await asyncio.gather(*[_wrapped(n, u) for n, u in entries])

    total = len(results)
    ok = [r for r in results if r["ok"]]
    covered = [r for r in ok if r.get("covered")]
    lat = [r["latency_s"] for r in results]
    out_path = domains_file.with_suffix(domains_file.suffix + ".results.jsonl")
    out_path.write_text("\n".join(json.dumps(r) for r in results))

    print("\n" + "=" * 70)
    print("SCALED EVAL SUMMARY")
    print(f"  companies         : {total}")
    print(f"  ran without crash : {len(ok)} ({_pct(len(ok), total)})")
    print(f"  crash/error       : {total - len(ok)} ({_pct(total - len(ok), total)})")
    print(f"  coverage (>=1 exec): {len(covered)} ({_pct(len(covered), total)})")
    print(f"  latency p50 / p95 : {_percentile(lat, 0.5):.0f}s / {_percentile(lat, 0.95):.0f}s")
    print(f"  wall clock        : {time.monotonic() - started:.0f}s")
    print(f"  results           : {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
