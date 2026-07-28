"""SEC EDGAR executive enrichment — waterfall source #3 (US public companies).

Authoritative, keyless, STRUCTURED: every US public company files Form 3/4 insider
reports whose reportingOwner carries the person's name plus an officerTitle and
director/officer flags. That is ground truth for the CEO/CFO/officers/directors
of any SEC filer — and unlike an LLM over prose, it can't hallucinate a title.
Fixes companies that publish no on-site roster and have thin Wikidata claims
(e.g. MongoDB).

Company->CIK resolution is by normalized-name match against SEC's official ticker
list; precision-first — no confident match returns []. SEC requires a descriptive
User-Agent on every request.
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

import httpx
import structlog
from pydantic import BaseModel

from scout.core.enrich.reconcile import canonical

logger = structlog.get_logger(__name__)

_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
_USER_AGENT = "Scout/1.0 (https://scout.chowmes.com; web intelligence) exec-enrichment"

_CORP_SUFFIX_RE = re.compile(
    r"\b(inc|incorporated|corp|corporation|co|company|ltd|limited|llc|lp|plc|holdings|group|sa|ag|nv)\b",
    re.I,
)


class SecExec(BaseModel):
    name: str
    title: str = ""


def _norm_company(name: str) -> str:
    """Normalize a company name for matching: drop legal suffixes + punctuation."""
    stripped = _CORP_SUFFIX_RE.sub(" ", name.lower())
    return re.sub(r"[^a-z0-9]+", " ", stripped).strip()


def _reorder_sec_name(sec_name: str) -> str:
    """SEC reports names as 'LAST FIRST MIDDLE' (all caps). Canonicalize to a
    normal 'First Middle Last', particle-safe (Von Ahn stays a surname) — the
    shared identity canonicalizer, not a naive token swap."""
    return canonical(sec_name).display or sec_name.title()


def _match_cik(company: str, tickers: dict) -> int | None:
    """Find the CIK whose company title best matches `company` (exact-normalized
    first, then unique startswith). Ambiguous/no match -> None (precision-first)."""
    target = _norm_company(company)
    if not target:
        return None
    exact: list[int] = []
    prefix: list[int] = []
    for row in tickers.values():
        if not isinstance(row, dict):
            continue
        title = _norm_company(str(row.get("title", "")))
        cik = row.get("cik_str")
        if not isinstance(cik, int):
            continue
        if title == target:
            exact.append(cik)
        elif title.startswith(target + " ") or target.startswith(title + " "):
            prefix.append(cik)
    if len(exact) == 1:
        return exact[0]
    if not exact and len(prefix) == 1:
        return prefix[0]
    return None


def _parse_form4_owners(xml_text: str) -> list[SecExec]:
    """Extract (name, title) for officers/directors from a Form 3/4/5 XML."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    out: list[SecExec] = []
    for owner in root.iter("reportingOwner"):
        name_el = owner.find(".//rptOwnerName")
        rel = owner.find("reportingOwnerRelationship")
        if name_el is None or name_el.text is None or rel is None:
            continue
        is_officer = (rel.findtext("isOfficer") or "0").strip() in ("1", "true")
        is_director = (rel.findtext("isDirector") or "0").strip() in ("1", "true")
        if not (is_officer or is_director):
            continue
        title = (rel.findtext("officerTitle") or "").strip()
        if not title and is_director:
            title = "Director"
        out.append(SecExec(name=_reorder_sec_name(name_el.text), title=title))
    return out


async def _default_fetch(url: str) -> httpx.Response:
    async with httpx.AsyncClient(
        timeout=15.0, follow_redirects=True, headers={"User-Agent": _USER_AGENT}
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp


async def sec_executives(
    company: str,
    *,
    fetch=_default_fetch,
    max_filings: int = 12,
    max_execs: int = 15,
) -> list[SecExec]:
    """Officers/directors of `company` from SEC Form 3/4 filings, or [].

    `fetch(url) -> httpx.Response` is injectable for testing. Never raises: any
    network/parse failure returns [] so the waterfall continues.
    """
    if not company.strip():
        return []
    try:
        tickers = (await fetch(_TICKERS_URL)).json()
        cik = _match_cik(company, tickers)
        if cik is None:
            logger.info("[scout/sec] no confident CIK match", company=company)
            return []
        submissions = (await fetch(_SUBMISSIONS_URL.format(cik=cik))).json()
        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", []) or []
        accessions = recent.get("accessionNumber", []) or []
        docs = recent.get("primaryDocument", []) or []
        seen_names: set[str] = set()
        execs: list[SecExec] = []
        checked = 0
        for form, acc, doc in zip(forms, accessions, docs):
            if checked >= max_filings or len(execs) >= max_execs:
                break
            # SEC lists the primaryDocument as the XSLT-RENDERED view, e.g.
            # "xslF345X06/wk-form4_123.xml" (that path returns HTML, not parseable
            # XML). The raw Form 4 XML is the bare filename at the accession root.
            doc_file = doc.rsplit("/", 1)[-1]
            if form not in ("3", "4", "5") or not doc_file.endswith(".xml"):
                continue
            checked += 1
            acc_nodash = acc.replace("-", "")
            try:
                xml = (await fetch(_ARCHIVE_URL.format(cik=cik, acc=acc_nodash, doc=doc_file))).text
            except Exception:  # noqa: BLE001 - skip a single bad filing
                continue
            for owner in _parse_form4_owners(xml):
                key = owner.name.lower().strip()
                if key and key not in seen_names:
                    seen_names.add(key)
                    execs.append(owner)
        logger.info("[scout/sec] execs found", company=company, cik=cik, count=len(execs))
        return execs[:max_execs]
    except Exception as exc:  # noqa: BLE001 - enrichment is best-effort
        logger.info("[scout/sec] enrichment skipped", company=company, error=str(exc))
        return []
