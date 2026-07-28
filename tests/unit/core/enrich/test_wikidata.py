"""Wikidata exec enrichment — pure disambiguation + extraction logic, injected
fetch (no network). The disambiguation is the crux: a name search for 'Vercel'
returns a French village, so we must match on the company's domain."""

from __future__ import annotations

import pytest

from scout.core.enrich.wikidata import (
    WikidataExec,
    _extract_person_refs,
    _pick_company_qid,
    wikidata_executives,
)


def _entity(qid: str, website: str = "", claims: dict | None = None, label: str = "") -> dict:
    c: dict = dict(claims or {})
    if website:
        c["P856"] = [{"mainsnak": {"datavalue": {"value": website}}}]
    return {"id": qid, "labels": {"en": {"value": label or qid}}, "claims": c}


def _person_claim(qid: str) -> dict:
    return {"mainsnak": {"datavalue": {"value": {"id": qid}}}}


def test_pick_entity_matches_on_domain() -> None:
    entities = {
        "Q1": _entity("Q1", website="https://vercel-village.fr"),  # the French village
        "Q2": _entity("Q2", website="https://vercel.com"),  # the company
    }
    assert _pick_company_qid(["Q1", "Q2"], entities, "vercel.com") == "Q2"


def test_domain_given_but_none_match_returns_empty() -> None:
    """Precision-first: a domain was given, no candidate's site matches -> no guess."""
    entities = {"Q1": _entity("Q1", website="https://someoneelse.com")}
    assert _pick_company_qid(["Q1"], entities, "vercel.com") == ""


def test_no_domain_prefers_entity_with_website() -> None:
    entities = {
        "Q1": _entity("Q1"),  # village: no website
        "Q2": _entity("Q2", website="https://acme.com"),  # company
    }
    assert _pick_company_qid(["Q1", "Q2"], entities, "") == "Q2"


def test_extract_person_refs_dedupes_by_highest_role() -> None:
    entity = _entity(
        "Q9",
        claims={
            "P169": [_person_claim("QCEO")],  # CEO
            "P112": [_person_claim("QCEO"), _person_claim("QFounder")],  # founders
        },
    )
    refs = dict(_extract_person_refs(entity))
    assert refs["QCEO"] == "CEO"  # CEO precedence over Founder for the same person
    assert refs["QFounder"] == "Founder"


@pytest.mark.asyncio
async def test_wikidata_executives_end_to_end_with_domain() -> None:
    search_resp = {"search": [{"id": "Q_VILLAGE"}, {"id": "Q_CO"}]}
    entities_resp = {
        "entities": {
            "Q_VILLAGE": _entity("Q_VILLAGE"),  # no website
            "Q_CO": _entity(
                "Q_CO",
                website="https://acme.com",
                claims={"P169": [_person_claim("Q_CEO")], "P112": [_person_claim("Q_F")]},
            ),
        }
    }
    people_resp = {
        "entities": {
            "Q_CEO": {"labels": {"en": {"value": "Jane Park"}}},
            "Q_F": {"labels": {"en": {"value": "Raj Patel"}}},
        }
    }

    async def fake_fetch(url: str) -> dict:
        if "wbsearchentities" in url:
            return search_resp
        if "claims" in url:  # props=claims|labels -> the entity-detail call
            return entities_resp
        return people_resp  # props=labels -> the person-label call

    execs = await wikidata_executives("Acme", "acme.com", fetch=fake_fetch)
    names = {e.name: e.title for e in execs}
    assert names == {"Jane Park": "CEO", "Raj Patel": "Founder"}
    assert all(isinstance(e, WikidataExec) and e.company_qid == "Q_CO" for e in execs)


@pytest.mark.asyncio
async def test_wikidata_executives_returns_empty_on_fetch_error() -> None:
    async def boom(url: str) -> dict:
        raise RuntimeError("network down")

    assert await wikidata_executives("Acme", "acme.com", fetch=boom) == []


@pytest.mark.asyncio
async def test_wikidata_executives_empty_company() -> None:
    async def fake(url: str) -> dict:
        return {}

    assert await wikidata_executives("  ", "", fetch=fake) == []
