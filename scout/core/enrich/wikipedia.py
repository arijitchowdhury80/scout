"""Wikipedia executive enrichment — waterfall source #4 (grounded, keyless).

Wikidata's STRUCTURED claims (P169/P112...) are thin for many notable private
companies — Notion has a Wikidata entity but no CEO claim, so source #2 returns
nothing. Their Wikipedia ARTICLE prose, however, almost always names the
founders/CEO. This source reuses Wikidata's domain-disambiguation to find the
RIGHT article (avoiding the "Vercel → French village" trap), fetches its plain
text, and runs the SAME company-identity-guarded LLM extractor used on-site.

Keyless and grounded: the answer comes from a cited authoritative document, not
the model's parametric memory — so it can be trusted and attributed.
"""

from __future__ import annotations

from urllib.parse import urlencode

import httpx
import structlog

from scout.core.enrich.wikidata import enwiki_title, resolve_company_entity
from scout.core.llm_extract import LLMExecutiveItem, llm_extract_executives

logger = structlog.get_logger(__name__)

_WIKI_API = "https://en.wikipedia.org/w/api.php"
_USER_AGENT = "Scout/1.0 (https://scout.chowmes.com; web intelligence) exec-enrichment"


async def _fetch_article_text(title: str) -> str:
    """Plain-text extract of an English Wikipedia article, or ''."""
    url = (
        _WIKI_API
        + "?"
        + urlencode(
            {
                "action": "query",
                "prop": "extracts",
                "explaintext": "1",
                "redirects": "1",
                "titles": title,
                "format": "json",
            }
        )
    )
    async with httpx.AsyncClient(
        timeout=15.0, follow_redirects=True, headers={"User-Agent": _USER_AGENT}
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    for page in (data.get("query", {}).get("pages", {}) or {}).values():
        extract = page.get("extract")
        if extract:
            return str(extract)
    return ""


async def wikipedia_executives(
    company: str,
    domain: str = "",
    api_key: str = "",
    *,
    resolve=resolve_company_entity,
    fetch_article=_fetch_article_text,
) -> list[LLMExecutiveItem]:
    """Extract leaders of `company` from its (domain-disambiguated) Wikipedia
    article via the company-guarded LLM extractor, or [] on no article / no key.

    `resolve` and `fetch_article` are injectable for testing. Never raises.
    """
    if not api_key or not company.strip():
        return []
    try:
        _qid, entity = await resolve(company, domain)
        title = enwiki_title(entity)
        if not title:
            return []
        text = await fetch_article(title)
        if not text.strip():
            return []
        page_url = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")
        execs = await llm_extract_executives(text, api_key, company=company, page_url=page_url)
        logger.info("[scout/wikipedia] execs found", company=company, title=title, count=len(execs))
        return execs
    except Exception as exc:  # noqa: BLE001 - enrichment is best-effort
        logger.info("[scout/wikipedia] enrichment skipped", company=company, error=str(exc))
        return []
