"""Bootstrap golden-set builder for exec-extraction PRECISION/recall validation.

Founder decision (2026-07-28): bootstrap labels, no human audit. To minimize
circularity (Scout itself uses Wikidata + Wikipedia-prose + SEC Form 4), ground
truth here is drawn from a method Scout does NOT use: the **Wikipedia infobox
`key_people` field** (structured wikitext, human-curated on Wikipedia). This is a
different extraction path than Scout's LLM-over-article-prose, so agreement is
meaningful rather than tautological.

CAVEATS (reported on every downstream number, never hidden):
- Same underlying corpus as one Scout source (Wikipedia) — different extraction,
  but not fully independent. Not human-audited.
- Only companies WITH a Wikipedia article + key_people infobox get labeled;
  companies without one are marked `unlabeled` and EXCLUDED from precision/recall
  (they inflate nothing). This biases the labeled set toward notable companies.

Output: golden.json = [{company, domain, segment, true_execs:[{name,title}], label_source}].
Usage: python3 golden_build.py <domains.tsv> [--limit N] > /dev/null
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode, urlparse

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402

from scout.core.enrich.wikidata import enwiki_title, resolve_company_entity  # noqa: E402

HERE = Path(__file__).parent
_UA = "Scout/1.0 (https://scout.chowmes.com; research) golden-set-builder"
_WIKI_API = "https://en.wikipedia.org/w/api.php"


async def _wikitext(title: str) -> str:
    url = _WIKI_API + "?" + urlencode(
        {
            "action": "query",
            "prop": "revisions",
            "rvslots": "main",
            "rvprop": "content",
            "titles": title,
            "format": "json",
            "redirects": "1",
        }
    )
    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": _UA}, follow_redirects=True) as c:
        data = (await c.get(url)).json()
    for page in (data.get("query", {}).get("pages", {}) or {}).values():
        revs = page.get("revisions") or []
        if revs:
            return revs[0].get("slots", {}).get("main", {}).get("*", "") or ""
    return ""


def _extract_key_people_field(wikitext: str) -> str:
    """Return the raw `key_people = ...` infobox field value, or ''."""
    m = re.search(r"\|\s*key_people\s*=\s*(.+?)(?:\n\s*\|\s*[a-z_]+\s*=|\n\}\})", wikitext, re.S | re.I)
    return m.group(1).strip() if m else ""


_TEMPLATE_JUNK = {
    "plainlist",
    "ubl",
    "unbulleted list",
    "bulleted list",
    "hlist",
    "flatlist",
    "financial times",
}
# a person name: 2-4 capitalized tokens (allows initials, hyphens, apostrophes)
_NAME_RE = re.compile(r"^[A-Z][A-Za-z.'\-]+(?: [A-Z][A-Za-z.'\-]+){1,3}$")


def _deref_links(s: str) -> str:
    """[[Target|Display]] -> Display, [[Target]] -> Target (removes internal pipes
    so a later pipe-split can't break inside a wikilink)."""
    s = re.sub(r"\[\[[^\]|]*\|([^\]]+)\]\]", r"\1", s)
    return re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)


def _parse_people(field: str) -> list[dict]:
    """Parse (name, role) from a key_people infobox field.

    The NAME is the text before the first '(' (roles live in parens and are often
    the only wikilinked part — so we must NOT assume the wikilink is the name).
    Handles {{plainlist|* A (CEO)* B}}, {{ubl|A|B}}, 'Jane Doe (Founder)<br>...'.
    """
    field = _deref_links(field)
    people: list[dict] = []
    seen: set[str] = set()
    for raw in re.split(r"\n\s*\*|<br\s*/?>|\|", field):
        raw = re.sub(r"\{\{[a-z ]+", "", raw).replace("}}", "").strip().strip("*").strip()
        if not raw:
            continue
        role_m = re.search(r"\(([^)]+)\)", raw)
        role = re.sub(r"[{}\[\]]", "", role_m.group(1)).strip() if role_m else ""
        name = raw.split("(")[0]
        name = re.sub(r'"[^"]*"', "", name)  # drop "CJ" nicknames
        name = re.sub(r"[{}\[\]]", "", name)
        name = re.sub(r"\s+", " ", name).strip().strip(",")
        if not name or name.lower() in _TEMPLATE_JUNK or not _NAME_RE.match(name):
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            people.append({"name": name, "title": role})
    return people


async def build_one(name: str, url: str) -> dict:
    domain = urlparse(url if "://" in url else "https://" + url).netloc
    entry: dict = {"company": name, "domain": domain, "segment": {}, "true_execs": [], "label_source": ""}
    try:
        _qid, entity = await resolve_company_entity(name, domain)
        title = enwiki_title(entity)
        if not title:
            entry["status"] = "unlabeled_no_article"
            return entry
        wt = await _wikitext(title)
        field = _extract_key_people_field(wt)
        people = _parse_people(field)
        entry["true_execs"] = people
        entry["label_source"] = f"en.wikipedia.org infobox key_people ({title})"
        entry["status"] = "labeled" if people else "unlabeled_no_key_people"
    except Exception as exc:  # noqa: BLE001
        entry["status"] = f"error:{exc}"
    return entry


async def main() -> None:
    src = Path(sys.argv[1])
    limit = None
    for i, a in enumerate(sys.argv):
        if a == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
    entries = []
    for line in src.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, url = (line.split("\t", 1) if "\t" in line else (line, line))
        entries.append((name.strip(), url.strip()))
    if limit:
        entries = entries[:limit]
    golden = []
    for i, (name, url) in enumerate(entries):
        e = await build_one(name, url)
        golden.append(e)
        print(f"[{i+1}/{len(entries)}] {name}: {e.get('status')} ({len(e['true_execs'])} labels)",
              file=sys.stderr, flush=True)
    out = HERE / "golden.json"
    out.write_text(json.dumps(golden, indent=2))
    labeled = [g for g in golden if g.get("status") == "labeled"]
    print(f"\nWrote {out}: {len(labeled)}/{len(golden)} labeled", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
