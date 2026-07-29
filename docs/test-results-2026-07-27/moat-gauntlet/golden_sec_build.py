"""Golden ROSTER labeler from SEC DEF 14A proxy statements (public companies).

This is the trustworthy ground truth the Wikipedia-infobox labels couldn't be:
the proxy lists a company's COMPLETE officer + director roster, authoritatively.
That lets us score REAL precision (are Scout's names in the roster?) AND recall
(did Scout get the roster?), for the first time.

Independence: the DEF 14A is a DIFFERENT document than any Scout source (Scout
uses Form 4 / Wikidata / Wikipedia-prose / on-site), so agreement is meaningful.
The roster sections cluster early in the (huge) proxy, so we extract a window
around them and LLM-extract the complete list. Caveat: same model family as one
Scout path — but over an authoritative doc that explicitly names the roster, so
it's reading comprehension, not inference.

Output: golden_sec.json. Usage: LLM_API_KEY=... python3 golden_sec_build.py <domains.tsv> [--limit N]
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import litellm  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

from scout.core.enrich.sec import (  # noqa: E402
    _ARCHIVE_URL,
    _SUBMISSIONS_URL,
    _TICKERS_URL,
    _default_fetch,
    _match_cik,
)

HERE = Path(__file__).parent
_ANCHORS = ["Information about our Executive Officers", "Election of Directors", "Nominees", "Executive Officers"]
_WINDOW = 70000  # wide enough to reach the full exec-officers section + the board


def _load_key() -> str:
    import os

    if os.environ.get("LLM_API_KEY"):
        return os.environ["LLM_API_KEY"]
    for line in (ROOT / ".env.local").read_text().splitlines():
        if line.startswith("LLM_API_KEY="):
            return line.split("=", 1)[1].strip()
    return ""


async def _latest_def14a_text(cik: int) -> str:
    sub = (await _default_fetch(_SUBMISSIONS_URL.format(cik=cik))).json()
    rec = sub.get("filings", {}).get("recent", {})
    forms, accs, docs = rec.get("form", []), rec.get("accessionNumber", []), rec.get("primaryDocument", [])
    for form, acc, doc in zip(forms, accs, docs):
        if form == "DEF 14A" and doc:
            html = (await _default_fetch(_ARCHIVE_URL.format(cik=cik, acc=acc.replace("-", ""), doc=doc))).text
            return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    return ""


def _roster_window(text: str) -> str:
    starts = [text.find(a) for a in _ANCHORS if text.find(a) >= 0]
    start = min(starts) if starts else 0
    return text[max(0, start - 500) : start + _WINDOW]


async def _extract_roster(company: str, text: str, key: str) -> list[dict]:
    prompt = (
        f"The text below is from the SEC DEF 14A proxy statement of {company}. "
        f"List EVERY person who is (a) an EXECUTIVE OFFICER (CEO, CFO, CTO, COO, other "
        f"'Chief' officers, President, EVP/SVP, General Counsel, and any other named "
        f"executive officer) or (b) a member of the BOARD OF DIRECTORS of {company}, "
        f"exactly as named in this text. Include the COMPLETE executive-officers list, "
        f"not only the named-executive-officers in the compensation table. Return ONLY a "
        f"JSON array of objects {{\"name\": str, \"title\": str, \"role_type\": str}} where "
        f"role_type is 'executive' for company officers/management (including an executive "
        f"chair) and 'director' for board members who are NOT also an executive officer. "
        f"A person who is both an officer and a director is 'executive'. Do NOT include "
        f"auditors, legal advisors, proxy solicitors, or people from other companies.\n\n"
        f"TEXT:\n{text}"
    )
    try:
        resp = await litellm.acompletion(
            model="anthropic/claude-haiku-4-5",
            api_key=key,
            temperature=0,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        content = resp["choices"][0]["message"]["content"]
        m = re.search(r"\[.*\]", content, re.S)
        if not m:
            return []
        rows = json.loads(m.group(0))
        out = []
        for r in rows:
            if isinstance(r, dict) and str(r.get("name", "")).strip():
                rt = str(r.get("role_type", "")).strip().lower()
                out.append(
                    {
                        "name": str(r["name"]).strip(),
                        "title": str(r.get("title", "")).strip(),
                        "role_type": "director" if rt == "director" else "executive",
                    }
                )
        return out
    except Exception as exc:  # noqa: BLE001
        print(f"    extract error: {exc}", file=sys.stderr)
        return []


async def build_one(name: str, tickers: dict, key: str) -> dict:
    cik = _match_cik(name, tickers)
    entry: dict = {"company": name, "cik": cik, "true_execs": [], "label_source": "", "status": ""}
    if cik is None:
        entry["status"] = "no_cik_not_public"
        return entry
    text = await _latest_def14a_text(cik)
    if not text:
        entry["status"] = "no_def14a"
        return entry
    roster = await _extract_roster(name, _roster_window(text), key)
    entry["true_execs"] = roster
    entry["label_source"] = "SEC DEF 14A"
    entry["status"] = "labeled" if roster else "def14a_no_roster_extracted"
    return entry


async def main() -> None:
    key = _load_key()
    src = Path(sys.argv[1])
    limit = None
    for i, a in enumerate(sys.argv):
        if a == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    tickers = (await _default_fetch(_TICKERS_URL)).json()
    entries = []
    for line in src.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            nm = line.split("\t", 1)[0].strip()
            entries.append(nm)
    if limit:
        entries = entries[:limit]
    golden = []
    for i, nm in enumerate(entries):
        e = await build_one(nm, tickers, key)
        golden.append(e)
        print(f"[{i+1}/{len(entries)}] {nm}: {e['status']} ({len(e['true_execs'])} roster)",
              file=sys.stderr, flush=True)
    (HERE / "golden_sec.json").write_text(json.dumps(golden, indent=2))
    labeled = [g for g in golden if g["status"] == "labeled"]
    print(f"\nWrote golden_sec.json: {len(labeled)}/{len(golden)} labeled", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
