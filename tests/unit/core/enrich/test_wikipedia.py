"""Wikipedia exec enrichment — reuses Wikidata disambiguation to find the right
article, then the company-guarded LLM extractor. Injected deps, no network."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from scout.core.enrich.wikipedia import wikipedia_executives
from scout.core.llm_extract import LLMExecutiveItem


def _entity_with_enwiki(title: str) -> dict:
    return {"sitelinks": {"enwiki": {"title": title}}}


@pytest.mark.asyncio
async def test_wikipedia_extracts_from_disambiguated_article() -> None:
    async def resolve(company, domain):
        return "Q123", _entity_with_enwiki("Notion (productivity software)")

    async def fetch_article(title):
        assert title == "Notion (productivity software)"
        return "Notion was founded by Ivan Zhao, who serves as CEO."

    with patch(
        "scout.core.enrich.wikipedia.llm_extract_executives",
        new_callable=AsyncMock,
        return_value=[LLMExecutiveItem(name="Ivan Zhao", title="CEO")],
    ) as mock_llm:
        execs = await wikipedia_executives(
            "Notion", "notion.so", "fake-key", resolve=resolve, fetch_article=fetch_article
        )
    mock_llm.assert_called_once()
    assert [(e.name, e.title) for e in execs] == [("Ivan Zhao", "CEO")]


@pytest.mark.asyncio
async def test_wikipedia_no_key_skips() -> None:
    async def resolve(company, domain):
        raise AssertionError("must not resolve without a key")

    assert await wikipedia_executives("Notion", "notion.so", "", resolve=resolve) == []


@pytest.mark.asyncio
async def test_wikipedia_no_article_returns_empty() -> None:
    async def resolve(company, domain):
        return "", {}  # no confident entity -> no enwiki title

    with patch("scout.core.enrich.wikipedia.llm_extract_executives", new_callable=AsyncMock) as m:
        out = await wikipedia_executives("Obscure", "x.com", "fake-key", resolve=resolve)
    assert out == []
    m.assert_not_called()


@pytest.mark.asyncio
async def test_wikipedia_empty_article_text_skips_llm() -> None:
    async def resolve(company, domain):
        return "Q1", _entity_with_enwiki("Some Co")

    async def fetch_article(title):
        return "   "

    with patch("scout.core.enrich.wikipedia.llm_extract_executives", new_callable=AsyncMock) as m:
        out = await wikipedia_executives(
            "Some Co", "x.com", "fake-key", resolve=resolve, fetch_article=fetch_article
        )
    assert out == []
    m.assert_not_called()


@pytest.mark.asyncio
async def test_wikipedia_never_raises() -> None:
    async def resolve(company, domain):
        raise RuntimeError("wikidata down")

    assert await wikipedia_executives("X", "x.com", "fake-key", resolve=resolve) == []
