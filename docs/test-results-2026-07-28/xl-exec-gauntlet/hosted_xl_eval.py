#!/usr/bin/env python3
"""XL exec-extraction e2e harness (hosted API).

For each company in a stratified corpus TSV:
  1. POST /v1/hosted/run/company (authed), poll the job, GET the run records.
  2. Capture robustness: coverage, exec list (name/title/source), total_sources,
     product/other counts, latency, errors.
  3. Track C: push the run's exec+company records to a throwaway Algolia index
     via the algoliasearch client (Scout's /algolia/push needs the master key,
     unavailable to tenant callers), then verify searchable-after-push.

Checkpoint/resume: results append to <out>.jsonl; a re-run skips companies already
present. Concurrency-capped with retry/backoff on 429/5xx. Scoring (precision/recall)
is a SEPARATE step (golden_sec_score.py) that reads this file + the golden sets.

Usage:
  SCOUT creds from test-creds.env (SCOUT_BASE_URL, SCOUT_API_KEY);
  ALGOLIA creds from Scout/.env.local (ALGOLIA_APP_ID, ALGOLIA_ADMIN_KEY).
  python3 hosted_xl_eval.py --corpus corpus_xl.tsv --out corpus_xl.results.jsonl \
      --index scout_xl_test --concurrency 6 [--limit N] [--no-push]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

DONE_STATES = {"complete", "completed", "done", "succeeded", "failed", "error"}
FAIL_STATES = {"failed", "error"}


def load_env(path: str | Path) -> None:
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def parse_corpus(path: Path) -> list[dict[str, str]]:
    """TSV: name, url, ownership, vertical, render_regime, geo, size, label_tier.
    Lines starting with # are comments. Extra/missing trailing cols tolerated."""
    cols = ["name", "url", "ownership", "vertical", "render_regime", "geo", "size", "label_tier"]
    rows: list[dict[str, str]] = []
    for line in path.read_text().splitlines():
        line = line.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        row = {c: (parts[i].strip() if i < len(parts) else "") for i, c in enumerate(cols)}
        if row["name"] and row["url"]:
            rows.append(row)
    return rows


class HostedClient:
    def __init__(self, base: str, key: str, max_records: int) -> None:
        self.base = base.rstrip("/")
        self.h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        self.max_records = max_records

    def _retry(self, fn, tries: int = 4):
        delay = 3.0
        last = None
        for _ in range(tries):
            resp = fn()
            last = resp
            if resp.status_code not in (429, 500, 502, 503, 504):
                return resp
            ra = resp.headers.get("Retry-After")
            time.sleep(float(ra) if ra and ra.isdigit() else delay)
            delay = min(delay * 2, 30)
        return last

    def run_company(self, name: str, url: str, client: httpx.Client) -> dict:
        t0 = time.time()
        body = {"query": name, "url": url, "mode": "auto", "max_records": self.max_records}
        r = self._retry(lambda: client.post(f"{self.base}/v1/hosted/run/company", headers=self.h, json=body))
        if r.status_code >= 400:
            return {"ok": False, "error": f"POST {r.status_code}: {r.text[:200]}", "latency_s": round(time.time() - t0, 1)}
        b = r.json()
        job_id, result = b.get("job_id"), b.get("result")
        if job_id and not result:
            for _ in range(150):
                time.sleep(4)
                jb = client.get(f"{self.base}/v1/hosted/jobs/{job_id}", headers=self.h).json()
                st = (jb.get("status") or "").lower()
                if st in DONE_STATES:
                    if st in FAIL_STATES:
                        return {"ok": False, "error": f"job {st}: {str(jb.get('error'))[:200]}", "latency_s": round(time.time() - t0, 1)}
                    result = jb.get("result")
                    break
            else:
                return {"ok": False, "error": "job poll timeout", "latency_s": round(time.time() - t0, 1)}
        if not result:
            return {"ok": False, "error": "no result", "latency_s": round(time.time() - t0, 1)}
        run = result.get("run", {})
        man = run.get("manifest", {})
        run_id = man.get("run_id", "")
        recs = []
        if run_id:
            rr = self._retry(lambda: client.get(f"{self.base}/v1/hosted/runs/{run_id}/records", headers=self.h))
            if rr.status_code < 400:
                recs = rr.json().get("records", [])
        return {
            "ok": True,
            "run_id": run_id,
            "total_records": run.get("total_records", 0),
            "total_sources": man.get("total_sources", 0),
            "total_blocked": man.get("total_blocked", 0),
            "records": recs,
            "latency_s": round(time.time() - t0, 1),
        }


def _exec_source(rec: dict) -> str:
    cits = rec.get("citations") or []
    if cits and isinstance(cits[0], dict):
        return cits[0].get("source_id", "") or rec.get("source", "")
    return rec.get("source", "")


def summarize_records(recs: list[dict]) -> dict:
    execs, products, sources = [], 0, {}
    for rec in recs:
        rt = rec.get("record_type") or rec.get("type") or ""
        if rt == "executive":
            src = _exec_source(rec)
            sources[src] = sources.get(src, 0) + 1
            execs.append({"name": rec.get("name"), "title": rec.get("title"), "source": src, "confidence": rec.get("confidence")})
        elif rt == "product":
            products += 1
    return {"execs": execs, "exec_count": len(execs), "product_count": products, "exec_sources": sources, "covered": len(execs) > 0}


# ---- Track C: Algolia push + verify (direct client) --------------------------
_algolia_client = None
_algolia_lock = threading.Lock()


def get_algolia():
    global _algolia_client
    if _algolia_client is None:
        with _algolia_lock:
            if _algolia_client is None:
                from algoliasearch.search.client import SearchClientSync

                app = os.environ["ALGOLIA_APP_ID"]
                key = os.environ.get("ALGOLIA_ADMIN_KEY") or os.environ["ALGOLIA_API_KEY"]
                _algolia_client = SearchClientSync(app_id=app, api_key=key)
    return _algolia_client


def push_and_verify(index: str, company: str, recs: list[dict]) -> dict:
    objs = []
    for i, rec in enumerate(recs):
        rt = rec.get("record_type") or ""
        if rt not in ("executive", "company"):
            continue
        oid = f"{company}::{rt}::{i}".replace(" ", "_")
        objs.append({**rec, "objectID": oid, "_company": company, "_record_type": rt})
    if not objs:
        return {"pushed": 0, "searchable": False, "push_error": "no exec/company records"}
    try:
        client = get_algolia()
        resp = client.save_objects(index_name=index, objects=objs, batch_size=1000)
        ids, last_task = [], None
        for br in resp:
            ids.extend(br.object_ids)
            last_task = getattr(br, "task_id", None) or last_task
        # verify: wait for indexing, then search for the company on the pushed records
        if last_task is not None:
            client.wait_for_task(index_name=index, task_id=last_task)
        sr = client.search_single_index(index_name=index, search_params={"query": company, "hitsPerPage": 3})
        hits = getattr(sr, "hits", []) or []
        return {"pushed": len(ids), "searchable": len(hits) > 0}
    except Exception as exc:  # noqa: BLE001
        return {"pushed": 0, "searchable": False, "push_error": str(exc)[:200]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--index", default="scout_xl_test")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-records", type=int, default=50)
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--creds", default="/private/tmp/claude-501/-Users-arijitchowdhury-Dropbox-AI-Development-Scout/d78fa487-5309-4a08-844e-734daf96b849/scratchpad/test-creds.env")
    ap.add_argument("--env-local", default="/Users/arijitchowdhury/Dropbox/AI-Development/Scout/.env.local")
    args = ap.parse_args()

    load_env(args.creds)
    load_env(args.env_local)
    base = os.environ.get("SCOUT_BASE_URL", "https://scout.chowmes.com")
    key = os.environ.get("SCOUT_API_KEY", "")
    if not key:
        print("NO SCOUT_API_KEY", file=sys.stderr)
        return 2

    corpus = parse_corpus(Path(args.corpus))
    if args.limit:
        corpus = corpus[: args.limit]

    out_path = Path(args.out)
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            try:
                done.add(json.loads(line)["name"])
            except Exception:  # noqa: BLE001
                pass
    todo = [c for c in corpus if c["name"] not in done]
    print(f"corpus={len(corpus)} done={len(done)} todo={len(todo)} concurrency={args.concurrency} push={not args.no_push}")

    hc = HostedClient(base, key, args.max_records)
    write_lock = threading.Lock()
    counter = {"n": 0, "cov": 0, "err": 0}

    def work(company: dict) -> dict:
        with httpx.Client(timeout=120.0) as client:
            res = hc.run_company(company["name"], company["url"], client)
        row = {**company, **{k: v for k, v in res.items() if k != "records"}}
        if res.get("ok"):
            summ = summarize_records(res.get("records", []))
            row.update(summ)
            if not args.no_push and res.get("records"):
                row["algolia"] = push_and_verify(args.index, company["name"], res["records"])
        return row

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(work, c): c for c in todo}
        for fut in as_completed(futs):
            c = futs[fut]
            try:
                row = fut.result()
            except Exception as exc:  # noqa: BLE001
                row = {**c, "ok": False, "error": f"harness: {exc}"}
            with write_lock:
                with out_path.open("a") as f:
                    f.write(json.dumps(row, default=str) + "\n")
                counter["n"] += 1
                counter["cov"] += 1 if row.get("covered") else 0
                counter["err"] += 0 if row.get("ok") else 1
                tag = "OK " if row.get("ok") else "ERR"
                print(f"[{counter['n']}/{len(todo)}] {tag} {c['name']:<22} execs={row.get('exec_count','-')} src={row.get('total_sources','-')} {row.get('latency_s','')}s")

    n = counter["n"] or 1
    print(f"\n=== DONE: {counter['n']} run, coverage={100*counter['cov']//n}%, errors={counter['err']} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
