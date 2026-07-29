#!/usr/bin/env python3
"""Slice harness results by every stratum → the breaking-point heatmap (P5).

Reports coverage, mean exec_count, mean total_sources, error rate, and Algolia
push/searchable rates, broken down by ownership / vertical / render_regime / geo
/ size. Surfaces WHERE the feature is weak.

Usage: python3 analyze_strata.py --results pilot_corpus.results.jsonl
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

AXES = ["ownership", "vertical", "render_regime", "geo", "size", "label_tier"]


def load(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def agg(rows: list[dict]) -> dict:
    n = len(rows)
    ok = [r for r in rows if r.get("ok")]
    cov = [r for r in ok if r.get("covered")]
    execs = [r.get("exec_count", 0) or 0 for r in ok]
    srcs = [r.get("total_sources", 0) or 0 for r in ok]
    pushed = [r for r in ok if isinstance(r.get("algolia"), dict) and r["algolia"].get("pushed", 0) > 0]
    searchable = [r for r in pushed if r["algolia"].get("searchable")]
    return {
        "n": n,
        "err": n - len(ok),
        "coverage": (100 * len(cov) // len(ok)) if ok else 0,
        "mean_execs": round(sum(execs) / len(ok), 1) if ok else 0,
        "mean_sources": round(sum(srcs) / len(ok), 1) if ok else 0,
        "push_ok": len(pushed),
        "searchable": len(searchable),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    args = ap.parse_args()
    rows = load(Path(args.results))

    o = agg(rows)
    print(f"=== OVERALL (n={o['n']}) ===")
    print(f"  coverage={o['coverage']}%  mean_execs={o['mean_execs']}  mean_sources={o['mean_sources']}  errors={o['err']}")
    print(f"  algolia: pushed={o['push_ok']}  searchable={o['searchable']}\n")

    for axis in AXES:
        buckets: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            buckets[r.get(axis, "?") or "?"].append(r)
        print(f"--- by {axis} ---")
        print(f"  {'value':<14} {'n':>3} {'cov':>5} {'execs':>6} {'src':>5} {'err':>4} {'push':>5} {'srch':>5}")
        for val, rs in sorted(buckets.items()):
            a = agg(rs)
            print(f"  {val:<14} {a['n']:>3} {a['coverage']:>4}% {a['mean_execs']:>6} {a['mean_sources']:>5} {a['err']:>4} {a['push_ok']:>5} {a['searchable']:>5}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
