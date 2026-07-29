#!/usr/bin/env python3
"""Score the HOSTED harness output (results.jsonl) against golden rosters.

Decoupled from extraction: reads the exec names the hosted API already returned
(hosted_xl_eval.py output) and scores precision/recall with the SAME production
matcher the product uses (reconcile.same_name), so the score is honest.

Exec-team-only scope (founder decision 2026-07-28): score vs the exec-officer
roster; outside directors are out-of-scope (neither TP nor FP). Also runs a
cross-company leak detector: a returned exec that is another company's known CEO.

Bar: precision >= 0.90, recall >= 0.80 (golden_sec_score.py).

Usage: python3 score_results.py --results pilot_corpus.results.jsonl \
    --golden ../test-results-2026-07-27/moat-gauntlet/golden_sec.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scout.core.enrich.reconcile import same_name as _match  # noqa: E402

PREC_BAR, RECALL_BAR = 0.90, 0.80


def load_results(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        rows[r["name"]] = r
    return rows


def score_company(entry: dict, scout_names: list[str]) -> dict:
    exec_roster = [p["name"] for p in entry["true_execs"] if p.get("role_type") != "director"]
    dir_roster = [p["name"] for p in entry["true_execs"] if p.get("role_type") == "director"]
    tp = [s for s in scout_names if any(_match(s, r) for r in exec_roster)]
    is_dir = [s for s in scout_names if s not in tp and any(_match(s, r) for r in dir_roster)]
    fp = [s for s in scout_names if s not in tp and s not in is_dir]
    recalled = [r for r in exec_roster if any(_match(r, s) for s in scout_names)]
    scored = len(tp) + len(fp)
    return {
        "company": entry["company"],
        "roster_size": len(exec_roster),
        "scout_size": len(scout_names),
        "precision": (len(tp) / scored) if scored else 0.0,
        "recall": (len(recalled) / len(exec_roster)) if exec_roster else 0.0,
        "false_positives": fp,
        "returned_directors": len(is_dir),
        "missed": [r for r in exec_roster if r not in recalled],
    }


def build_ceo_map(golden: list[dict]) -> dict[str, str]:
    """company -> first exec-officer name (proxy for 'the CEO/top officer')."""
    m = {}
    for e in golden:
        execs = [p["name"] for p in e.get("true_execs", []) if p.get("role_type") != "director"]
        if execs:
            m[e["company"]] = execs[0]
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--golden", required=True)
    args = ap.parse_args()

    results = load_results(Path(args.results))
    golden = json.loads(Path(args.golden).read_text())
    labeled = {g["company"]: g for g in golden if g.get("status") == "labeled" and g.get("true_execs")}
    ceo_map = build_ceo_map(golden)

    scored, leaks = [], []
    for name, entry in labeled.items():
        row = results.get(name)
        if not row or not row.get("ok"):
            continue
        scout_names = [e["name"] for e in row.get("execs", []) if e.get("name")]
        s = score_company(entry, scout_names)
        scored.append(s)
        # leak check: any scout exec that is a DIFFERENT company's top officer
        for sn in scout_names:
            for co, ceo in ceo_map.items():
                if co != name and _match(sn, ceo):
                    leaks.append({"company": name, "leaked_name": sn, "belongs_to": co})

    if not scored:
        print("No overlap between results and labeled golden companies.")
        return 0

    macro_p = sum(s["precision"] for s in scored) / len(scored)
    macro_r = sum(s["recall"] for s in scored) / len(scored)
    print(f"Scored {len(scored)} labeled companies (of {len(results)} in results, {len(labeled)} labeled available)\n")
    print(f"{'company':<16} {'prec':>6} {'recall':>7} {'roster':>7} {'scout':>6} {'FP':>3} {'dir':>4}  missed/fp")
    for s in sorted(scored, key=lambda x: x["recall"]):
        flag = "" if (s["precision"] >= PREC_BAR and s["recall"] >= RECALL_BAR) else "  <-- below bar"
        det = ""
        if s["missed"]:
            det += f"miss={s['missed']}"
        if s["false_positives"]:
            det += f" FP={s['false_positives']}"
        print(f"{s['company']:<16} {s['precision']*100:>5.0f}% {s['recall']*100:>6.0f}% {s['roster_size']:>7} {s['scout_size']:>6} {len(s['false_positives']):>3} {s['returned_directors']:>4}  {det}{flag}")

    print(f"\n=== MACRO precision={macro_p*100:.1f}%  recall={macro_r*100:.1f}%  (bar: P>={PREC_BAR*100:.0f}% R>={RECALL_BAR*100:.0f}%) ===")
    verdict = "PASS" if (macro_p >= PREC_BAR and macro_r >= RECALL_BAR) else "BELOW BAR"
    print(f"=== VERDICT: {verdict} ===")
    print(f"\nCross-company leaks: {len(leaks)}")
    for lk in leaks:
        print(f"  LEAK: {lk['company']} returned {lk['leaked_name']} (top officer of {lk['belongs_to']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
