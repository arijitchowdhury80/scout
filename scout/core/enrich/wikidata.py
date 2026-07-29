"""Wikidata executive enrichment — source #2 in the exec waterfall.

Roughly half of companies never publish their leadership on their own website
(Stripe, Vercel, most retail brands), so on-site crawling alone caps coverage at
~50%. Wikidata is a free, structured, keyless source that fills much of the gap:
CEOs, founders, chairpersons, and board members for a large fraction of real
companies (verified live 2026-07-27: Stripe→Collison, Cloudflare→Prince,
Shopify→Lütke, Figma→Field, Glossier→Weiss, Klarna→Siemiatkowski).

PRECISION-FIRST DISAMBIGUATION is the crux: a bare name search for "Vercel"
returns a French village (Q838007), not the company. So we match the candidate
entity's official website (P856) against the company's own domain. If a domain
is given and NO candidate's website matches it, we return [] rather than risk
another entity's people — silence beats a wrong roster (the same principle as the
on-site company-identity guard).
"""

from __future__ import annotations

from urllib.parse import urlencode, urlparse

import httpx
import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

_API = "https://www.wikidata.org/w/api.php"
_USER_AGENT = "Scout/1.0 (https://scout.chowmes.com; web intelligence) exec-enrichment"

# Wikidata property -> leadership role. Order = precedence when one person holds
# several (CEO wins over Founder wins over board seat).
_ROLE_PROPS: list[tuple[str, str]] = [
    ("P169", "CEO"),
    ("P488", "Chairperson"),
    ("P1037", "Director"),
    ("P112", "Founder"),
    ("P3320", "Board member"),
]


class WikidataExec(BaseModel):
    """One leader sourced from Wikidata. `qid` is the person entity for provenance."""

    name: str
    title: str = ""
    qid: str = ""
    company_qid: str = ""


def _host(url: str) -> str:
    """Registrable-ish host: lowercase, no scheme, no www., no path."""
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    return urlparse(url).netloc.lower().removeprefix("www.")


def _entity_website_host(entity: dict) -> str:
    """Host of the entity's official website (P856), or '' if none."""
    for claim in entity.get("claims", {}).get("P856", []):
        try:
            return _host(str(claim["mainsnak"]["datavalue"]["value"]))
        except (KeyError, TypeError):
            continue
    return ""


def _pick_company_qid(candidate_qids: list[str], entities: dict[str, dict], domain: str) -> str:
    """Choose the entity that is actually THIS company.

    With a domain: only accept a candidate whose official-website host matches
    it — return '' (→ no enrichment) if candidates have websites but none match,
    so we never attach a different entity's people. Without a domain: fall back
    to the first candidate that has any official website (companies do; villages
    and generic terms usually don't).
    """
    domain_host = _host(domain)
    any_had_website = False
    for qid in candidate_qids:
        entity = entities.get(qid)
        if not entity:
            continue
        site_host = _entity_website_host(entity)
        if site_host:
            any_had_website = True
            if domain_host and (site_host == domain_host or site_host.endswith("." + domain_host)):
                return qid
    if domain_host:
        # A domain was given but nothing matched — precision-first: no guess.
        return ""
    if not any_had_website:
        return candidate_qids[0] if candidate_qids else ""
    for qid in candidate_qids:
        entity = entities.get(qid)
        if entity and _entity_website_host(entity):
            return qid
    return ""


def _extract_person_refs(entity: dict) -> list[tuple[str, str]]:
    """(person_qid, role) pairs from a company entity's leadership claims.

    De-duped by person, keeping the highest-precedence role (CEO over founder
    over board seat) so a founder-CEO shows as CEO once, not twice.
    """
    role_by_qid: dict[str, str] = {}
    for prop, role in _ROLE_PROPS:
        for claim in entity.get("claims", {}).get(prop, []):
            # Skip FORMER officeholders: a CEO/chair/director claim with an
            # end-time qualifier (P582) is a past role, not current leadership.
            # This is what leaked Siemens' ex-CEOs (Löscher, Kleinfeld) as if
            # they still ran the company.
            if "P582" in (claim.get("qualifiers") or {}):
                continue
            try:
                pid = str(claim["mainsnak"]["datavalue"]["value"]["id"])
            except (KeyError, TypeError):
                continue
            role_by_qid.setdefault(pid, role)  # first (highest-precedence) wins
    return list(role_by_qid.items())


def _is_deceased(person_entity: dict) -> bool:
    """True if the person has a date-of-death (P570) claim. Long-dead founders
    (e.g. Werner von Siemens, d. 1892) are not current leadership."""
    return bool(person_entity.get("claims", {}).get("P570"))


def _label_of(entity: dict) -> str:
    return str((entity.get("labels", {}).get("en", {}) or {}).get("value", "")).strip()


async def _default_fetch(url: str) -> dict:
    async with httpx.AsyncClient(
        timeout=15.0, follow_redirects=True, headers={"User-Agent": _USER_AGENT}
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


def _search_url(company: str, limit: int) -> str:
    return (
        _API
        + "?"
        + urlencode(
            {
                "action": "wbsearchentities",
                "search": company,
                "language": "en",
                "format": "json",
                "type": "item",
                "limit": limit,
            }
        )
    )


def _entities_url(qids: list[str], props: str) -> str:
    return (
        _API
        + "?"
        + urlencode(
            {"action": "wbgetentities", "ids": "|".join(qids), "props": props, "format": "json"}
        )
    )


def enwiki_title(entity: dict) -> str:
    """The English Wikipedia article title for a resolved company entity, or ''.

    Lets the Wikipedia source reuse Wikidata's domain-disambiguation instead of
    re-guessing the article by name (which hits the same 'Vercel village' trap).
    """
    try:
        return str(entity["sitelinks"]["enwiki"]["title"]).strip()
    except (KeyError, TypeError):
        return ""


async def resolve_company_entity(
    company: str, domain: str = "", *, fetch=_default_fetch, search_limit: int = 5
) -> tuple[str, dict]:
    """Resolve `company` (+domain) to its Wikidata (qid, entity) or ('', {}).

    Shared by the Wikidata and Wikipedia sources so both get the SAME
    domain-disambiguated entity. Entity includes claims + labels + sitelinks.
    Never raises.
    """
    if not company.strip():
        return "", {}
    try:
        search = (await fetch(_search_url(company, search_limit))).get("search") or []
        candidate_qids = [s["id"] for s in search if isinstance(s, dict) and s.get("id")]
        if not candidate_qids:
            return "", {}
        entities = (await fetch(_entities_url(candidate_qids, "claims|labels|sitelinks"))).get(
            "entities", {}
        )
        company_qid = _pick_company_qid(candidate_qids, entities, domain)
        if not company_qid:
            logger.info(
                "[scout/wikidata] no confident entity match", company=company, domain=domain
            )
            return "", {}
        return company_qid, entities.get(company_qid, {})
    except Exception as exc:  # noqa: BLE001 - enrichment is best-effort
        logger.info("[scout/wikidata] entity resolve skipped", company=company, error=str(exc))
        return "", {}


async def wikidata_executives(
    company: str,
    domain: str = "",
    *,
    fetch=_default_fetch,
    search_limit: int = 5,
    max_execs: int = 15,
) -> list[WikidataExec]:
    """Return leaders for `company` from Wikidata, or [] on no confident match.

    `domain` (the company's own site host) drives disambiguation — pass it
    whenever known. `fetch` is injectable for testing. Never raises: any network
    or parse failure returns [] so the caller's waterfall continues.
    """
    try:
        company_qid, entity = await resolve_company_entity(
            company, domain, fetch=fetch, search_limit=search_limit
        )
        if not company_qid:
            return []
        refs = _extract_person_refs(entity)[:max_execs]
        if not refs:
            return []
        person_qids = [qid for qid, _ in refs]
        # Fetch claims too so we can drop deceased people (P570 date of death).
        people = (await fetch(_entities_url(person_qids, "labels|claims"))).get("entities", {})
        execs: list[WikidataExec] = []
        for qid, role in refs:
            person = people.get(qid, {})
            if _is_deceased(person):
                continue
            name = _label_of(person)
            if name:
                execs.append(WikidataExec(name=name, title=role, qid=qid, company_qid=company_qid))
        logger.info(
            "[scout/wikidata] execs found",
            company=company,
            company_qid=company_qid,
            count=len(execs),
        )
        return execs
    except Exception as exc:  # noqa: BLE001 - enrichment is best-effort
        logger.info("[scout/wikidata] enrichment skipped", company=company, error=str(exc))
        return []
